"""Read-only resource manager inspection for Ren'Py projects."""

from __future__ import annotations

import re
from pathlib import Path

from .models import MissingReferenceItem, ResourceInfo, ResourceInspectionResult, ResourceIssue, ResourceSummary, UnusedResourceItem

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
AUDIO_EXTENSIONS = {".ogg", ".mp3", ".wav", ".flac", ".opus", ".m4a"}
RESOURCE_ROOTS = [Path("game/images"), Path("game/gui"), Path("game/audio"), Path("game/sounds")]
REFERENCE_STRING_PATTERN = re.compile(r"[\"']([^\"']+\.(?:png|jpg|jpeg|webp|bmp|gif|ogg|mp3|wav|flac|opus|m4a))[\"']", re.IGNORECASE)
SCENE_SHOW_PATTERN = re.compile(r"^\s*(?:scene|show)\s+([A-Za-z_][A-Za-z0-9_]*)")
IMAGE_DEFINE_PATTERN = re.compile(r"^\s*image\s+[^=]+?=\s*[\"']([^\"']+)[\"']")
PLAY_PATTERN = re.compile(r"^\s*play\s+(?:music|sound|audio)\s+[\"']([^\"']+)[\"']")
CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]")
SPECIAL_PATTERN = re.compile(r"[^A-Za-z0-9_.\- ]")


def inspect_resources(project_path: Path) -> ResourceInspectionResult:
    """Inspect resources without modifying the managed project."""

    resources = _scan_resources(project_path)
    resource_by_rel = {resource.relative_path: resource for resource in resources}
    resource_names = {Path(resource.relative_path).stem: resource for resource in resources}
    references = _scan_references(project_path)
    existing_refs: set[str] = set()
    missing: list[MissingReferenceItem] = []

    for reference, file, line in references:
        resolved = _resolve_reference(reference, resource_by_rel, resource_names)
        if resolved:
            existing_refs.add(resolved.relative_path)
        elif _looks_like_path(reference):
            missing.append(MissingReferenceItem(reference=reference, file=file, line=line))

    naming = [issue for resource in resources for issue in _naming_issues(resource)]
    unused = [UnusedResourceItem(resource=resource) for resource in resources if resource.relative_path not in existing_refs]
    summary = _summary(resources, naming, missing, unused)
    return ResourceInspectionResult(
        summary=summary,
        resources=resources,
        naming_issues=naming,
        missing_references=missing,
        unused_resources=unused,
    )


def _scan_resources(project_path: Path) -> list[ResourceInfo]:
    resources: list[ResourceInfo] = []
    for root in RESOURCE_ROOTS:
        abs_root = project_path / root
        if not abs_root.is_dir():
            continue
        for file_path in sorted(path for path in abs_root.rglob("*") if path.is_file()):
            ext = file_path.suffix.lower()
            if ext not in IMAGE_EXTENSIONS | AUDIO_EXTENSIONS:
                continue
            rel = file_path.relative_to(project_path).as_posix()
            resources.append(ResourceInfo(
                name=file_path.name,
                relative_path=rel,
                category=_category_for(root, file_path),
                extension=ext,
                size_bytes=file_path.stat().st_size,
                is_image=ext in IMAGE_EXTENSIONS,
            ))
    return resources


def _category_for(root: Path, file_path: Path) -> str:
    parts = {part.lower() for part in file_path.parts}
    stem = file_path.stem.lower()
    if file_path.suffix.lower() in AUDIO_EXTENSIONS:
        return "audio"
    if "gui" in parts or root.as_posix() == "game/gui":
        return "ui"
    if "character" in parts or "avatar" in parts or "sprite" in parts or stem.startswith(("zhou_", "woman_", "char_")):
        return "characters"
    if "bg" in parts or stem.startswith("bg_"):
        return "backgrounds"
    return "other_images"


def _scan_references(project_path: Path) -> list[tuple[str, str, int]]:
    game_dir = project_path / "game"
    references: list[tuple[str, str, int]] = []
    if not game_dir.is_dir():
        return references
    for file_path in sorted(game_dir.rglob("*.rpy")):
        rel_file = file_path.relative_to(project_path).as_posix()
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line_no, line in enumerate(lines, start=1):
            for pattern in (IMAGE_DEFINE_PATTERN, PLAY_PATTERN):
                match = pattern.match(line)
                if match:
                    references.append((match.group(1), rel_file, line_no))
            match = SCENE_SHOW_PATTERN.match(line)
            if match:
                references.append((match.group(1), rel_file, line_no))
            for match in REFERENCE_STRING_PATTERN.finditer(line):
                references.append((match.group(1), rel_file, line_no))
    return references


def _resolve_reference(reference: str, resource_by_rel: dict[str, ResourceInfo], resource_names: dict[str, ResourceInfo]) -> ResourceInfo | None:
    normalized = reference.replace("\\", "/")
    candidates = [normalized]
    if not normalized.startswith("game/"):
        candidates.extend([f"game/{normalized}", f"game/images/{normalized}", f"game/gui/{normalized}", f"game/audio/{normalized}", f"game/sounds/{normalized}"])
    for candidate in candidates:
        if candidate in resource_by_rel:
            return resource_by_rel[candidate]
    if "." not in Path(normalized).name and normalized in resource_names:
        return resource_names[normalized]
    return None


def _looks_like_path(reference: str) -> bool:
    lower = reference.lower()
    return "/" in reference or "\\" in reference or any(lower.endswith(ext) for ext in IMAGE_EXTENSIONS | AUDIO_EXTENSIONS)


def _naming_issues(resource: ResourceInfo) -> list[ResourceIssue]:
    issues: list[ResourceIssue] = []
    name = resource.name
    stem = Path(name).stem
    lower = name.lower()
    checks = [
        ("space", "File name contains spaces", " " in name),
        ("chinese", "File name contains Chinese characters", bool(CHINESE_PATTERN.search(name))),
        ("special", "File name contains special characters", bool(SPECIAL_PATTERN.search(name))),
    ]
    for code, message, triggered in checks:
        if triggered:
            issues.append(ResourceIssue(code=code, message=message, resource=resource))
    if resource.category == "backgrounds" and not stem.startswith("bg_"):
        issues.append(ResourceIssue(code="background_prefix", message="Background resources should start with bg_", resource=resource))
    if resource.category == "ui" and not (stem.startswith("ui_") or stem.lower() in _renpy_gui_names()):
        issues.append(ResourceIssue(code="ui_prefix", message="UI resources should start with ui_ or use Ren'Py gui conventional names", resource=resource))
    if resource.category == "audio" and not stem.startswith(("bgm_", "sfx_", "amb_")):
        issues.append(ResourceIssue(code="audio_prefix", message="Audio resources should start with bgm_, sfx_, or amb_", resource=resource))
    return issues


def _renpy_gui_names() -> set[str]:
    return {"main_menu", "game_menu", "textbox", "namebox", "button", "choice", "slider", "scrollbar", "overlay"}


def _summary(resources, naming, missing, unused) -> ResourceSummary:
    counts = {category: sum(1 for resource in resources if resource.category == category) for category in ["backgrounds", "characters", "ui", "audio", "other_images"]}
    return ResourceSummary(
        total=len(resources),
        backgrounds=counts["backgrounds"],
        characters=counts["characters"],
        ui=counts["ui"],
        audio=counts["audio"],
        other_images=counts["other_images"],
        other=0,
        naming_warnings=len(naming),
        missing_references=len(missing),
        unused_resources=len(unused),
    )
