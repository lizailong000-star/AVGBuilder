"""Read/write hotspot JSON for a managed Ren'Py project.

V0.1c has one permitted write target in the managed project:
    <project>/tools_data/hotspots.json
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import HotspotDocument, SceneHotspots

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
    normalized = HotspotDocument(
        version=document.version or "0.1b",
        project_name=document.project_name or project_path.name,
        scenes=document.scenes,
    )
    _validate_document(project_path, normalized)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(normalized.model_dump(), file, ensure_ascii=False, indent=2)
        file.write("\n")
    return normalized


def _validate_document(project_path: Path, document: HotspotDocument) -> None:
    for scene in document.scenes:
        _validate_scene_background(scene)
        seen_ids: set[str] = set()
        for hotspot in scene.hotspots:
            hotspot_id = hotspot.id.strip()
            if not hotspot_id:
                raise ValueError("Hotspot id must not be empty")
            if hotspot_id in seen_ids:
                raise ValueError(f"Duplicate hotspot id in scene {scene.scene_id}: {hotspot_id}")
            seen_ids.add(hotspot_id)
            if hotspot.w <= 0 or hotspot.h <= 0:
                raise ValueError(f"Hotspot {hotspot_id} must have w/h > 0")
            if hotspot.x < 0 or hotspot.y < 0:
                raise ValueError(f"Hotspot {hotspot_id} must have x/y >= 0")
        background_path = (project_path / scene.background).resolve(strict=False)
        project_root = project_path.resolve(strict=False)
        if project_root not in background_path.parents and background_path != project_root:
            raise ValueError(f"Scene background escapes project root: {scene.background}")


def _validate_scene_background(scene: SceneHotspots) -> None:
    background = Path(scene.background)
    if background.is_absolute() or ".." in background.parts:
        raise ValueError(f"Scene background must be project-relative: {scene.background}")
    if not scene.background:
        raise ValueError("Scene background must not be empty")


def _ensure_safe_hotspot_path(project_path: Path, path: Path) -> None:
    expected = hotspots_path(project_path).resolve(strict=False)
    actual = path.resolve(strict=False)
    if actual != expected:
        raise ValueError(f"Refusing to write outside allowed hotspot file: {actual}")
