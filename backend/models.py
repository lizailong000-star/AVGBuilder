"""Pydantic models for AVG Builder V0.1a."""

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


def normalize_project_path(raw_path: str) -> Path:
    """Expand a user supplied path without creating or modifying it."""

    return Path(raw_path).expanduser().resolve(strict=False)


class DialogueLine(BaseModel):
    """A single V0.7 dialogue line."""

    type: str = Field(default="narration", description="narration, dialogue, or comment")
    speaker: str = ""
    text: str = ""


class DialogueBlock(BaseModel):
    """Editable AVG dialogue block for generated Ren'Py labels."""

    id: str
    label: str
    title: str = ""
    background: str = ""
    music: str = ""
    lines: List[DialogueLine] = Field(default_factory=list)
    return_label: str = ""
    enabled: bool = True


class DialogueDocument(BaseModel):
    """Persisted dialogue_blocks.json document."""

    version: str = "0.7"
    project_name: str = "DemoAVG"
    blocks: List[DialogueBlock] = Field(default_factory=list)


class DialogueDocumentRequest(BaseModel):
    """Request body containing a dialogue document."""

    document: DialogueDocument


class DialogueBlocksResponse(BaseModel):
    """Response for loading dialogue blocks."""

    ok: bool
    document: DialogueDocument


class DialogueSaveResponse(BaseModel):
    """Response for saving dialogue_blocks.json."""

    ok: bool
    path: str
    block_count: int


class DialogueValidationResponse(BaseModel):
    """Response for dialogue document validation."""

    ok: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DialogueExportResponse(BaseModel):
    """Response for generated_dialogue_blocks.rpy export."""

    ok: bool
    path: str
    exported_count: int
    skipped_count: int
