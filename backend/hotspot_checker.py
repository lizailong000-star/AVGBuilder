"""Production checks for AVGBuilder hotspot data."""

from __future__ import annotations

import re

from .hotspot_manager import load_hotspots
from .label_scanner import scan_labels
from .models import HotspotCheckItem, HotspotCheckResult, HotspotCheckSummary, LabelTemplateItem, LabelTemplateResult

LABEL_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def check_hotspots(project_path) -> HotspotCheckResult:
    """Check target_label values against labels found in game/**/*.rpy."""

    document = load_hotspots(project_path)
    labels = scan_labels(project_path)
    label_names = {label.name for label in labels}
    items: list[HotspotCheckItem] = []

    for scene in document.scenes:
        for hotspot in scene.hotspots:
            status = _status_for_hotspot(hotspot, label_names)
            suggested_label = suggest_label(hotspot.id, hotspot.name)
            items.append(
                HotspotCheckItem(
                    scene_id=scene.scene_id,
                    background=scene.background,
                    hotspot_id=hotspot.id,
                    hotspot_name=hotspot.name,
                    target_label=hotspot.target_label,
                    enabled=hotspot.enabled,
                    status=status,
                    suggested_label=suggested_label,
                    message=_message_for_status(status, hotspot.target_label),
                )
            )

    summary = HotspotCheckSummary(
        total=len(items),
        ok=sum(1 for item in items if item.status == "ok"),
        missing=sum(1 for item in items if item.status == "missing"),
        empty=sum(1 for item in items if item.status == "empty"),
        disabled=sum(1 for item in items if item.status == "disabled"),
        invalid=sum(1 for item in items if item.status == "invalid"),
    )
    return HotspotCheckResult(ok=summary.missing == 0 and summary.empty == 0 and summary.invalid == 0, summary=summary, items=items)


def build_label_templates(project_path) -> LabelTemplateResult:
    """Generate suggested Ren'Py label templates for non-ok hotspots."""

    check = check_hotspots(project_path)
    templates: list[LabelTemplateItem] = []
    for item in check.items:
        if item.status in {"ok", "disabled"}:
            continue
        label_name = item.suggested_label
        display_name = item.hotspot_name or item.hotspot_id
        template = (
            f"label {label_name}:\n\n"
            f"    n \"你点击了{display_name}。\"\n"
            "    jump expression generated_hotspot_return_label\n"
        )
        templates.append(
            LabelTemplateItem(
                scene_id=item.scene_id,
                hotspot_id=item.hotspot_id,
                suggested_label=label_name,
                template=template,
            )
        )
    return LabelTemplateResult(count=len(templates), templates=templates)


def suggest_label(hotspot_id: str, hotspot_name: str) -> str:
    """Suggest investigate_<normalized id/name>."""

    source = hotspot_id or hotspot_name or "hotspot"
    source = source.lower().replace(" ", "_")
    source = re.sub(r"[^a-z0-9_]+", "", source)
    source = re.sub(r"_+", "_", source).strip("_")
    if not source:
        source = "hotspot"
    if source.startswith("investigate_"):
        return source
    return f"investigate_{source}"


def _status_for_hotspot(hotspot, label_names: set[str]) -> str:
    if not hotspot.enabled:
        return "disabled"
    target = hotspot.target_label or ""
    if not target:
        return "empty"
    if not LABEL_NAME_PATTERN.match(target):
        return "invalid"
    if target not in label_names:
        return "missing"
    return "ok"


def _message_for_status(status: str, target_label: str) -> str:
    return {
        "ok": "target_label exists",
        "missing": f"target_label not found: {target_label}",
        "empty": "target_label is empty",
        "disabled": "hotspot disabled",
        "invalid": f"target_label is not a valid Ren'Py label name: {target_label}",
    }.get(status, status)
