"""AVG Builder V0.1b FastAPI application."""

from __future__ import annotations

from mimetypes import guess_type
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .asset_scanner import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, scan_assets
from .git_status import read_git_status
from .hotspot_checker import build_label_templates, check_hotspots
from .hotspot_manager import load_hotspots, save_hotspots
from .label_scanner import scan_labels
from .models import (
    AssetScanResult,
    ExportResult,
    GitStatus,
    HotspotCheckResult,
    HotspotDocument,
    LabelInfo,
    LabelTemplateResult,
    ProjectOpenRequest,
    ProjectSummary,
    ResourceInspectionResult,
    ResourceSummary,
    MissingReferenceItem,
    UnusedResourceItem,
    normalize_project_path,
)
from .project_scanner import scan_project_structure
from .renpy_exporter import export_hotspots
from .resource_inspector import inspect_resources

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="AVG Builder", version="0.1b")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

_current_summary: Optional[ProjectSummary] = None
_current_project_path: Optional[Path] = None


@app.get("/")
def index() -> FileResponse:
    """Serve the native HTML/CSS/JS frontend."""

    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/project/open", response_model=ProjectSummary)
def open_project(request: ProjectOpenRequest) -> ProjectSummary:
    """Scan a local Ren'Py project path and cache the read-only result."""

    global _current_summary, _current_project_path
    project_path = normalize_project_path(request.path)
    checks, structure_logs = scan_project_structure(project_path)
    assets = scan_assets(project_path)
    git = read_git_status(project_path)

    logs = [*structure_logs]
    logs.append("Asset scan complete")
    for category, items in assets.categories.items():
        logs.append(f"Assets {category}: {len(items)} found")
    logs.append("Git status read complete" if git.is_repository else "Git repository not detected")

    _current_project_path = project_path
    _current_summary = ProjectSummary(
        project_path=str(project_path),
        exists=project_path.exists(),
        checks=checks,
        assets=assets,
        git=git,
        logs=logs,
    )
    return _current_summary


@app.get("/api/assets/list", response_model=AssetScanResult)
def list_assets() -> AssetScanResult:
    """Return assets from the latest project scan."""

    summary = _require_summary()
    return summary.assets


@app.get("/api/assets/file")
def asset_file(path: str = Query(..., description="Project-relative asset path")) -> FileResponse:
    """Return an image/audio asset from the current project for preview.

    This is read-only and only serves files inside the latest scanned project.
    """

    project_path = _require_project_path()
    relative_path = Path(path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise HTTPException(status_code=400, detail="Asset path must be project-relative")

    file_path = (project_path / relative_path).resolve(strict=False)
    project_root = project_path.resolve(strict=False)
    if project_root not in file_path.parents and file_path != project_root:
        raise HTTPException(status_code=400, detail="Asset path escapes project root")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    if file_path.suffix.lower() not in IMAGE_EXTENSIONS | AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported asset type")

    media_type, _ = guess_type(str(file_path))
    return FileResponse(file_path, media_type=media_type)


@app.get("/api/git/status", response_model=GitStatus)
def git_status() -> GitStatus:
    """Return Git status from the latest project scan."""

    summary = _require_summary()
    return summary.git


@app.get("/api/project/summary", response_model=ProjectSummary)
def project_summary() -> ProjectSummary:
    """Return the latest complete scan summary."""

    return _require_summary()


@app.get("/api/hotspots", response_model=HotspotDocument)
def get_hotspots() -> HotspotDocument:
    """Load tools_data/hotspots.json from the current project, if present."""

    project_path = _require_project_path()
    return load_hotspots(project_path)


@app.post("/api/hotspots/save", response_model=HotspotDocument)
def post_hotspots_save(document: HotspotDocument) -> HotspotDocument:
    """Save hotspot JSON to the only allowed target: tools_data/hotspots.json."""

    project_path = _require_project_path()
    try:
        return save_hotspots(project_path, document)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/labels", response_model=list[LabelInfo])
def get_labels() -> list[LabelInfo]:
    """Return Ren'Py labels found in game/**/*.rpy for the current project."""

    return scan_labels(_require_project_path())


@app.get("/api/hotspots/check", response_model=HotspotCheckResult)
def get_hotspot_check() -> HotspotCheckResult:
    """Check hotspot target_label values against scanned Ren'Py labels."""

    return check_hotspots(_require_project_path())


@app.get("/api/hotspots/label-templates", response_model=LabelTemplateResult)
def get_hotspot_label_templates() -> LabelTemplateResult:
    """Return suggested Ren'Py label templates for missing/empty/invalid targets."""

    return build_label_templates(_require_project_path())


@app.get("/api/resources/inspect", response_model=ResourceInspectionResult)
def get_resources_inspect() -> ResourceInspectionResult:
    """Inspect resources, references, naming issues, missing refs, and unused assets."""

    return inspect_resources(_require_project_path())


@app.get("/api/resources/summary", response_model=ResourceSummary)
def get_resources_summary() -> ResourceSummary:
    """Return only resource inspection summary."""

    return inspect_resources(_require_project_path()).summary


@app.get("/api/resources/missing", response_model=list[MissingReferenceItem])
def get_resources_missing() -> list[MissingReferenceItem]:
    """Return missing resource references."""

    return inspect_resources(_require_project_path()).missing_references


@app.get("/api/resources/unused", response_model=list[UnusedResourceItem])
def get_resources_unused() -> list[UnusedResourceItem]:
    """Return resources not referenced by scanned .rpy files."""

    return inspect_resources(_require_project_path()).unused_resources


@app.post("/api/export/hotspots", response_model=ExportResult)
def post_export_hotspots() -> ExportResult:
    """Export tools_data/hotspots.json to game/generated_hotspots.rpy."""

    project_path = _require_project_path()
    try:
        return export_hotspots(project_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _require_summary() -> ProjectSummary:
    if _current_summary is None:
        raise HTTPException(status_code=404, detail="No project has been scanned yet")
    return _current_summary


def _require_project_path() -> Path:
    if _current_project_path is None:
        raise HTTPException(status_code=404, detail="No project has been scanned yet")
    return _current_project_path
