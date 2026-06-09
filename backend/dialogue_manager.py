"""Read/write helpers for AVG Builder V0.7 dialogue block documents."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List, Tuple

from .models import DialogueBlock, DialogueDocument, DialogueLine

DIALOGUE_VERSION = "0.7"
DIALOGUE_JSON_RELATIVE = Path("tools_data") / "dialogue_blocks.json"
DIALOGUE_EXPORT_RELATIVE = Path("game") / "generated_dialogue_blocks.rpy"
LABEL_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def default_dialogue_document(project_path: Path | None = None) -> DialogueDocument:
    """Return an empty V0.7 dialogue document for the project."""

    return DialogueDocument(
        version=DIALOGUE_VERSION,
        project_name=project_path.name if project_path is not None else "DemoAVG",
        blocks=[],
    )


def read_dialogue_document(project_path: Path) -> DialogueDocument:
    """Read tools_data/dialogue_blocks.json, returning an empty document if missing."""

    document_path = dialogue_document_path(project_path)
    if not document_path.is_file():
        return default_dialogue_document(project_path)

    try:
        payload = json.loads(document_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_dialogue_document(project_path)

    return DialogueDocument.model_validate(payload)


def save_dialogue_document(project_path: Path, document: DialogueDocument) -> Tuple[Path, int]:
    """Save a dialogue document under tools_data/ without touching Ren'Py core files."""

    errors, _warnings = validate_dialogue_document(document)
    if errors:
        raise ValueError("; ".join(errors))

    document = _with_project_defaults(project_path, document)
    document_path = dialogue_document_path(project_path)
    document_path.parent.mkdir(parents=True, exist_ok=True)
    document_path.write_text(
        json.dumps(document.model_dump(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return document_path, len(document.blocks)


def validate_dialogue_document(document: DialogueDocument) -> Tuple[List[str], List[str]]:
    """Validate block-level requirements and return errors plus warnings."""

    errors: List[str] = []
    warnings: List[str] = []
    labels: dict[str, str] = {}

    for block_index, block in enumerate(document.blocks, start=1):
        prefix = f"Block {block_index}"
        if not block.id.strip():
            errors.append(f"{prefix}: id is required")
        if not block.label.strip():
            errors.append(f"{prefix}: label is required")
        elif not LABEL_PATTERN.fullmatch(block.label):
            errors.append(f"{prefix}: label '{block.label}' is not a valid Ren'Py label name")
        elif block.label in labels:
            errors.append(f"{prefix}: duplicate label '{block.label}' also used by {labels[block.label]}")
        else:
            labels[block.label] = block.id or prefix

        if not block.lines:
            errors.append(f"{prefix}: at least one line is required")

        for line_index, line in enumerate(block.lines, start=1):
            if line.type not in {"narration", "dialogue", "comment"}:
                errors.append(f"{prefix} line {line_index}: type must be narration, dialogue, or comment")
            if line.text == "":
                warnings.append(f"{prefix} line {line_index}: text is empty")

    return errors, warnings


def export_dialogue_blocks(project_path: Path, document: DialogueDocument) -> Tuple[Path, int, int]:
    """Export enabled dialogue blocks to game/generated_dialogue_blocks.rpy."""

    errors, _warnings = validate_dialogue_document(document)
    if errors:
        raise ValueError("; ".join(errors))

    game_dir = project_path / "game"
    if not game_dir.is_dir():
        raise FileNotFoundError(f"Ren'Py game directory not found: {game_dir}")

    document = _with_project_defaults(project_path, document)
    enabled_blocks = [block for block in document.blocks if block.enabled]
    skipped_count = len(document.blocks) - len(enabled_blocks)

    export_path = dialogue_export_path(project_path)
    export_path.write_text(_render_dialogue_file(enabled_blocks), encoding="utf-8")
    return export_path, len(enabled_blocks), skipped_count


def render_dialogue_preview(block: DialogueBlock) -> str:
    """Render a single dialogue block to Ren'Py text for frontend/API previews."""

    return _render_block(block).rstrip() + "\n"


def dialogue_document_path(project_path: Path) -> Path:
    return project_path / DIALOGUE_JSON_RELATIVE


def dialogue_export_path(project_path: Path) -> Path:
    return project_path / DIALOGUE_EXPORT_RELATIVE


def _with_project_defaults(project_path: Path, document: DialogueDocument) -> DialogueDocument:
    if not document.version:
        document.version = DIALOGUE_VERSION
    if not document.project_name:
        document.project_name = project_path.name
    return document


def _render_dialogue_file(blocks: Iterable[DialogueBlock]) -> str:
    parts = ["# This file is generated by AVGBuilder. Do not edit manually.", ""]
    for block in blocks:
        parts.append(_render_block(block).rstrip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def _render_block(block: DialogueBlock) -> str:
    lines = [f"label {block.label}:", ""]
    if block.background.strip():
        lines.extend([f"    scene {block.background.strip()}", ""])
    if block.music.strip():
        lines.extend([f"    play music \"{_escape_renpy_string(block.music.strip())}\"", ""])

    for line in block.lines:
        rendered = _render_line(line)
        if rendered:
            lines.extend([rendered, ""])

    if block.return_label.strip():
        lines.append(f"    jump {block.return_label.strip()}")
    else:
        lines.append("    return")
    return "\n".join(lines) + "\n"


def _render_line(line: DialogueLine) -> str:
    text = _escape_renpy_string(line.text)
    if line.type == "comment":
        return f"    # {line.text}" if line.text else "    #"
    if line.type == "dialogue" and line.speaker.strip():
        return f"    {line.speaker.strip()} \"{text}\""
    return f"    \"{text}\""


def _escape_renpy_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
