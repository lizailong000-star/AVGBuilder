"""AVG Builder V0.1a FastAPI application."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .asset_scanner import scan_assets
from .git_status import read_git_status
from .models import AssetScanResult, GitStatus, ProjectOpenRequest, ProjectSummary, normalize_project_path
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


def _require_summary() -> ProjectSummary:
    if _current_summary is None:
        raise HTTPException(status_code=404, detail="No project has been scanned yet")
    return _current_summary
