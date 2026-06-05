"""Read/write hotspot JSON for a managed Ren'Py project.

V0.1b has one permitted write target in the managed project:
    <project>/tools_data/hotspots.json
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import HotspotDocument

HOTSPOT_RELATIVE_PATH = Path("tools_data") / "hotspots.json"


def hotspots_path(project_path: Path) -> Path:
    """Return the only allowed hotspot document path for a project."""

    return project_path / HOTSPOT_RELATIVE_PATH


def load_hotspots(project_path: Path) -> HotspotDocument:
    """Load hotspot data, returning an empty document when it does not exist."""

    path = hotspots_path(project_path)
    if not path.exists():
        return HotspotDocument(project_name=project_path.name, scenes=[])

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return HotspotDocument.model_validate(payload)


def save_hotspots(project_path: Path, document: HotspotDocument) -> HotspotDocument:
    """Save hotspot data to tools_data/hotspots.json only."""

    path = hotspots_path(project_path)
    _ensure_safe_hotspot_path(project_path, path)
    path.parent.mkdir(parents=True, exist_ok=True)

    normalized = HotspotDocument(
        version=document.version or "0.1b",
        project_name=document.project_name or project_path.name,
        scenes=document.scenes,
    )
    with path.open("w", encoding="utf-8") as file:
        json.dump(normalized.model_dump(), file, ensure_ascii=False, indent=2)
        file.write("\n")
    return normalized


def _ensure_safe_hotspot_path(project_path: Path, path: Path) -> None:
    expected = hotspots_path(project_path).resolve(strict=False)
    actual = path.resolve(strict=False)
    if actual != expected:
        raise ValueError(f"Refusing to write outside allowed hotspot file: {actual}")
