"""Pydantic models for AVG Builder V0.1b."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectOpenRequest(BaseModel):
    """Request body for opening/scanning a Ren'Py project."""

    path: str = Field(..., description="Local path to the Ren'Py project root")


class ProjectChecks(BaseModel):
    """Presence checks for common Ren'Py project files."""

    game_dir: bool
    script_rpy: bool
    gui_rpy: bool
    options_rpy: bool
    gitignore: bool


class AssetItem(BaseModel):
    """A single discovered asset."""

    name: str
    relative_path: str
    size_bytes: int
    extension: str


class AssetScanResult(BaseModel):
    """Discovered assets grouped by category."""

    categories: Dict[str, List[AssetItem]]


class GitStatus(BaseModel):
    """Read-only Git status information for a project."""

    is_repository: bool
    branch: Optional[str] = None
    clean: Optional[bool] = None
    short_status: List[str] = Field(default_factory=list)
    latest_commit: Optional[str] = None
    error: Optional[str] = None


class ProjectSummary(BaseModel):
    """Complete scan result cached after opening a project."""

    project_path: str
    exists: bool
    checks: ProjectChecks
    assets: AssetScanResult
    git: GitStatus
    logs: List[str]


class Hotspot(BaseModel):
    """A rectangular clickable hotspot for a scene background."""

    id: str
    name: str
    target_label: str
    tooltip: str = ""
    x: int = 0
    y: int = 0
    w: int = 100
    h: int = 80
    enabled: bool = True


class SceneHotspots(BaseModel):
    """Hotspots bound to one background scene."""

    scene_id: str
    background: str
    hotspots: List[Hotspot] = Field(default_factory=list)


class HotspotDocument(BaseModel):
    """tools_data/hotspots.json document."""

    version: str = "0.1b"
    project_name: str
    scenes: List[SceneHotspots] = Field(default_factory=list)


def normalize_project_path(raw_path: str) -> Path:
    """Expand a user supplied path without creating or modifying it."""

    return Path(raw_path).expanduser().resolve(strict=False)
