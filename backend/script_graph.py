"""Read-only Ren'Py label graph scanner."""

from __future__ import annotations

import re
from pathlib import Path

from .hotspot_manager import load_hotspots
from .models import (
    LabelDetailResult,
    LabelGraphResult,
    LabelGraphSummary,
    LabelHealthResult,
    LabelHotspotLink,
    ScriptGraphEdge,
    ScriptLabelNode,
)

LABEL_PATTERN = re.compile(r"^\s*label\s+([A-Za-z_][A-Za-z0-9_]*)\s*:")
JUMP_PATTERN = re.compile(r"^\s*jump\s+(.+?)\s*(?:#.*)?$")
CALL_PATTERN = re.compile(r"^\s*call\s+(.+?)\s*(?:#.*)?$")
SIMPLE_TARGET_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\b")


def build_label_graph(project_path: Path) -> LabelGraphResult:
    """Build a read-only graph of labels and simple jump/call edges."""

    labels = _scan_labels(project_path)
    label_names = set(labels)
    edges = _scan_edges(project_path, label_names)
    hotspots_by_label = _hotspots_by_label(project_path)

    incoming: dict[str, list[ScriptGraphEdge]] = {name: [] for name in labels}
    outgoing: dict[str, list[ScriptGraphEdge]] = {name: [] for name in labels}
    for edge in edges:
        if edge.from_label in outgoing:
            outgoing[edge.from_label].append(edge)
        if edge.status == "ok" and edge.to_label in incoming:
            incoming[edge.to_label].append(edge)

    nodes: list[ScriptLabelNode] = []
    for name, base in labels.items():
        status = "ok"
        if _is_possibly_unused(name, incoming.get(name, []), hotspots_by_label):
            status = "possibly_unused"
        nodes.append(ScriptLabelNode(
            name=name,
            file=base.file,
            line=base.line,
            category=base.category,
            incoming_count=len(incoming.get(name, [])),
            outgoing_count=len(outgoing.get(name, [])),
            status=status,
        ))

    nodes.sort(key=lambda item: (item.file, item.line, item.name))
    missing = [edge for edge in edges if edge.status == "missing"]
    unused = [node for node in nodes if node.status == "possibly_unused"]
    dynamic_count = sum(1 for edge in edges if edge.status == "dynamic")
    return LabelGraphResult(
        summary=LabelGraphSummary(
            label_count=len(nodes),
            edge_count=len(edges),
            missing_count=len(missing),
            dynamic_count=dynamic_count,
            unused_count=len(unused),
        ),
        labels=nodes,
        edges=edges,
        missing=missing,
        unused=unused,
    )


def get_label_detail(project_path: Path, name: str) -> LabelDetailResult:
    graph = build_label_graph(project_path)
    label = next((item for item in graph.labels if item.name == name), None)
    if label is None:
        return LabelDetailResult(ok=False)
    return LabelDetailResult(
        label=label,
        incoming=[edge for edge in graph.edges if edge.to_label == name and edge.status == "ok"],
        outgoing=[edge for edge in graph.edges if edge.from_label == name],
        hotspots=_hotspots_by_label(project_path).get(name, []),
    )


def get_label_health(project_path: Path) -> LabelHealthResult:
    graph = build_label_graph(project_path)
    return LabelHealthResult(summary={
        "label_count": graph.summary.label_count,
        "missing_links": graph.summary.missing_count,
        "possibly_unused": graph.summary.unused_count,
        "dynamic_links": graph.summary.dynamic_count,
    })


def _scan_labels(project_path: Path) -> dict[str, ScriptLabelNode]:
    game_dir = project_path / "game"
    labels: dict[str, ScriptLabelNode] = {}
    if not game_dir.is_dir():
        return labels
    for file_path in sorted(game_dir.rglob("*.rpy")):
        rel = file_path.relative_to(project_path).as_posix()
        for line_no, line in _read_lines(file_path):
            match = LABEL_PATTERN.match(line)
            if match:
                name = match.group(1)
                labels[name] = ScriptLabelNode(name=name, file=rel, line=line_no, category=_category(name))
    return labels


def _scan_edges(project_path: Path, label_names: set[str]) -> list[ScriptGraphEdge]:
    game_dir = project_path / "game"
    edges: list[ScriptGraphEdge] = []
    if not game_dir.is_dir():
        return edges
    for file_path in sorted(game_dir.rglob("*.rpy")):
        rel = file_path.relative_to(project_path).as_posix()
        current_label = "__root__"
        for line_no, line in _read_lines(file_path):
            label_match = LABEL_PATTERN.match(line)
            if label_match:
                current_label = label_match.group(1)
                continue
            for kind, pattern in (("jump", JUMP_PATTERN), ("call", CALL_PATTERN)):
                match = pattern.match(line)
                if not match:
                    continue
                raw = match.group(1).strip()
                target, status = _parse_target(raw, label_names, kind)
                edges.append(ScriptGraphEdge(
                    from_label=current_label,
                    to_label=target,
                    type=kind,
                    file=rel,
                    line=line_no,
                    status=status,
                ))
    return edges


def _parse_target(raw: str, label_names: set[str], kind: str) -> tuple[str, str]:
    if raw.startswith("expression") or raw.startswith("screen"):
        return raw, "dynamic"
    match = SIMPLE_TARGET_PATTERN.match(raw)
    if not match:
        return raw, "unknown"
    target = match.group(1)
    if kind == "call" and target == "screen":
        return raw, "dynamic"
    return target, "ok" if target in label_names else "missing"


def _hotspots_by_label(project_path: Path) -> dict[str, list[LabelHotspotLink]]:
    result: dict[str, list[LabelHotspotLink]] = {}
    try:
        document = load_hotspots(project_path)
    except Exception:
        return result
    for scene in document.scenes:
        for hotspot in scene.hotspots:
            target = (hotspot.target_label or "").strip()
            if not target:
                continue
            result.setdefault(target, []).append(LabelHotspotLink(
                scene_id=scene.scene_id,
                hotspot_id=hotspot.id,
                hotspot_name=hotspot.name,
            ))
    return result


def _is_possibly_unused(name: str, incoming: list[ScriptGraphEdge], hotspots: dict[str, list[LabelHotspotLink]]) -> bool:
    if incoming or hotspots.get(name):
        return False
    if name == "start":
        return False
    if name.startswith(("test_", "hotspot_", "generated_")):
        return False
    return True


def _category(name: str) -> str:
    if name.startswith("test_"):
        return "test"
    if name.startswith("investigate_"):
        return "investigation"
    if name.startswith("chapter_"):
        return "story"
    if name.startswith("set_scene_") or name == "start":
        return "system"
    return "unknown"


def _read_lines(file_path: Path):
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    for index, line in enumerate(lines, start=1):
        yield index, line
