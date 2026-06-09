"""AVG Builder V0.1a FastAPI application."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .asset_scanner import scan_assets
from .dialogue_manager import (
    default_dialogue_document,
    export_dialogue_blocks,
    read_dialogue_document,
    save_dialogue_document,
    validate_dialogue_document,
)
from .git_status import read_git_status
from .models import (
    AssetScanResult,
    DialogueBlocksResponse,
    DialogueDocumentRequest,
    DialogueExportResponse,
    DialogueSaveResponse,
    DialogueValidationResponse,
    GitStatus,
    ProjectOpenRequest,
    ProjectSummary,
    normalize_project_path,
)
from .project_scanner import scan_project_structure

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="AVG Builder", version="0.1a")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

_current_summary: Optional[ProjectSummary] = None


@app.get("/")
def index() -> FileResponse:
    """Serve the native HTML/CSS/JS frontend."""

    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/project/open", response_model=ProjectSummary)
def open_project(request: ProjectOpenRequest) -> ProjectSummary:
    """Scan a local Ren'Py project path and cache the read-only result."""

    global _current_summary
    project_path = normalize_project_path(request.path)
    checks, structure_logs = scan_project_structure(project_path)
    assets = scan_assets(project_path)
    git = read_git_status(project_path)
    logs = [*structure_logs]
    logs.append("Asset scan complete")
    for category, items in assets.categories.items():
        logs.append(f"Assets {category}: {len(items)} found")
    logs.append("Git status read complete" if git.is_repository else "Git repository not detected")

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


@app.get("/api/git/status", response_model=GitStatus)
def git_status() -> GitStatus:
    """Return Git status from the latest project scan."""

    summary = _require_summary()
    return summary.git


@app.get("/api/project/summary", response_model=ProjectSummary)
def project_summary() -> ProjectSummary:
    """Return the latest complete scan summary."""

    return _require_summary()


@app.get("/api/dialogue/blocks", response_model=DialogueBlocksResponse)
def dialogue_blocks() -> DialogueBlocksResponse:
    """Return the current project's dialogue block document or an empty V0.7 document."""

    project_path = _current_project_path_optional()
    document = read_dialogue_document(project_path) if project_path is not None else default_dialogue_document()
    return DialogueBlocksResponse(ok=True, document=document)


@app.post("/api/dialogue/blocks/save", response_model=DialogueSaveResponse)
def save_dialogue_blocks(request: DialogueDocumentRequest) -> DialogueSaveResponse:
    """Save tools_data/dialogue_blocks.json for the latest scanned project."""

    project_path = _require_current_project_path()
    try:
        path, block_count = save_dialogue_document(project_path, request.document)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DialogueSaveResponse(ok=True, path=str(path), block_count=block_count)


@app.post("/api/dialogue/blocks/validate", response_model=DialogueValidationResponse)
def validate_dialogue_blocks(
    request: DialogueDocumentRequest | None = Body(default=None),
) -> DialogueValidationResponse:
    """Validate a supplied dialogue document, or the latest saved document if omitted."""

    if request is not None:
        document = request.document
    else:
        project_path = _current_project_path_optional()
        document = read_dialogue_document(project_path) if project_path is not None else default_dialogue_document()
    errors, warnings = validate_dialogue_document(document)
    return DialogueValidationResponse(ok=len(errors) == 0, errors=errors, warnings=warnings)


@app.post("/api/dialogue/export", response_model=DialogueExportResponse)
def export_dialogue(
    request: DialogueDocumentRequest | None = Body(default=None),
) -> DialogueExportResponse:
    """Export enabled dialogue blocks to game/generated_dialogue_blocks.rpy."""

    project_path = _require_current_project_path()
    document = request.document if request is not None else read_dialogue_document(project_path)
    errors, _warnings = validate_dialogue_document(document)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    try:
        path, exported_count, skipped_count = export_dialogue_blocks(project_path, document)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DialogueExportResponse(
        ok=True,
        path=str(path),
        exported_count=exported_count,
        skipped_count=skipped_count,
    )


def _require_summary() -> ProjectSummary:
    if _current_summary is None:
        raise HTTPException(status_code=404, detail="No project has been scanned yet")
    return _current_summary


def _current_project_path_optional() -> Path | None:
    if _current_summary is None:
        return None
    return normalize_project_path(_current_summary.project_path)


def _require_current_project_path() -> Path:
    project_path = _current_project_path_optional()
    if project_path is None:
        raise HTTPException(status_code=404, detail="No project has been scanned yet")
    return project_path
