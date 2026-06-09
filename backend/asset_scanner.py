"""Read-only asset discovery for Ren'Py projects."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Set

from .models import AssetItem, AssetScanResult

IMAGE_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".svg"}
AUDIO_EXTENSIONS: Set[str] = {".ogg", ".mp3", ".wav", ".flac", ".opus", ".m4a"}
UI_HINTS = {"ui", "gui", "interface", "button", "buttons", "screen", "screens"}
BACKGROUND_HINTS = {"background", "backgrounds", "bg", "bgs", "scene", "scenes"}
CHARACTER_HINTS = {"character", "characters", "char", "chars", "sprite", "sprites", "portrait", "portraits"}
AUDIO_HINTS = {"audio", "sound", "sounds", "sfx", "music", "voice", "voices", "bgm"}
CATEGORIES = ("backgrounds", "characters", "ui", "audio")


def scan_assets(project_path: Path) -> AssetScanResult:
    """Discover assets under the project's game/ folder and group them by path hints."""

    categories: Dict[str, List[AssetItem]] = {category: [] for category in CATEGORIES}
    game_dir = project_path / "game"
    if not game_dir.is_dir():
        return AssetScanResult(categories=categories)

    for file_path in sorted(_iter_asset_files(game_dir)):
        category = _classify_asset(file_path, game_dir)
        if category is None:
            continue
        try:
            size_bytes = file_path.stat().st_size
        except OSError:
            size_bytes = 0
        categories[category].append(
            AssetItem(
                name=file_path.name,
                relative_path=file_path.relative_to(project_path).as_posix(),
                size_bytes=size_bytes,
                extension=file_path.suffix.lower(),
            )
        )

    return AssetScanResult(categories=categories)


def _iter_asset_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and not _is_hidden_path(path.relative_to(root)):
            extension = path.suffix.lower()
            if extension in IMAGE_EXTENSIONS or extension in AUDIO_EXTENSIONS:
                yield path


def _is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def _classify_asset(file_path: Path, game_dir: Path) -> str | None:
    extension = file_path.suffix.lower()
    relative_parts = [part.lower() for part in file_path.relative_to(game_dir).parts]
    stem_tokens = set(file_path.stem.lower().replace("-", "_").split("_"))
    path_tokens = set(relative_parts) | stem_tokens

    if extension in AUDIO_EXTENSIONS:
        return "audio"
    if extension not in IMAGE_EXTENSIONS:
        return None

    if path_tokens & UI_HINTS:
        return "ui"
    if path_tokens & CHARACTER_HINTS:
        return "characters"
    if path_tokens & BACKGROUND_HINTS:
        return "backgrounds"
    return "ui" if "gui" in path_tokens else None
