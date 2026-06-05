"""Pydantic models for AVG Builder V0.1b."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal, Optional

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


class ExportResult(BaseModel):
    """Result returned by Ren'Py export endpoints."""

    ok: bool
    output_path: str
    screens: List[str] = Field(default_factory=list)
    scene_count: int = 0
    hotspot_count: int = 0
    skipped_count: int = 0
    message: str = ""


class LabelInfo(BaseModel):
    """A Ren'Py label found in game/**/*.rpy."""

    name: str
    file: str
    line: int


HotspotCheckStatus = Literal["ok", "missing", "empty", "disabled", "invalid"]


class HotspotCheckItem(BaseModel):
    """Per-hotspot production check result."""

    scene_id: str
    background: str
    hotspot_id: str
    hotspot_name: str
    target_label: str
    enabled: bool
    status: HotspotCheckStatus
    suggested_label: str
    message: str


class HotspotCheckSummary(BaseModel):
    """Aggregate hotspot check counts."""

    total: int = 0
    ok: int = 0
    missing: int = 0
    empty: int = 0
    disabled: int = 0
    invalid: int = 0


class HotspotCheckResult(BaseModel):
    """Full hotspot production check result."""

    ok: bool
    summary: HotspotCheckSummary
    items: List[HotspotCheckItem] = Field(default_factory=list)


class LabelTemplateItem(BaseModel):
    """Suggested Ren'Py label template for a hotspot."""

    scene_id: str
    hotspot_id: str
    suggested_label: str
    template: str


class LabelTemplateResult(BaseModel):
    """Collection of suggested label templates."""

    count: int = 0
    templates: List[LabelTemplateItem] = Field(default_factory=list)


class ResourceInfo(BaseModel):
    """A discovered project resource."""

    name: str
    relative_path: str
    category: str
    extension: str
    size_bytes: int
    is_image: bool = False


class ResourceIssue(BaseModel):
    """Naming or convention issue for a resource."""

    severity: str = "warning"
    code: str
    message: str
    resource: ResourceInfo


class MissingReferenceItem(BaseModel):
    """A referenced asset path that does not exist."""

    reference: str
    file: str
    line: int
    reason: str = "missing"


class UnusedResourceItem(BaseModel):
    """A discovered resource that was not referenced by scanned .rpy files."""

    resource: ResourceInfo


class ResourceSummary(BaseModel):
    """Aggregate resource inspection counts."""

    total: int = 0
    backgrounds: int = 0
    characters: int = 0
    ui: int = 0
    audio: int = 0
    other_images: int = 0
    other: int = 0
    naming_warnings: int = 0
    missing_references: int = 0
    unused_resources: int = 0


class ResourceInspectionResult(BaseModel):
    """Complete resource manager inspection result."""

    summary: ResourceSummary
    resources: List[ResourceInfo] = Field(default_factory=list)
    naming_issues: List[ResourceIssue] = Field(default_factory=list)
    missing_references: List[MissingReferenceItem] = Field(default_factory=list)
    unused_resources: List[UnusedResourceItem] = Field(default_factory=list)


class LabelGraphSummary(BaseModel):
    """Aggregate label graph counts."""

    label_count: int = 0
    edge_count: int = 0
    missing_count: int = 0
    dynamic_count: int = 0
    unused_count: int = 0


class ScriptLabelNode(BaseModel):
    """A Ren'Py label with graph metadata."""

    name: str
    file: str
    line: int
    category: str
    incoming_count: int = 0
    outgoing_count: int = 0
    status: str = "ok"


class ScriptGraphEdge(BaseModel):
    """A jump/call relationship between labels."""

    from_label: str
    to_label: str
    type: str
    file: str
    line: int
    status: str = "ok"


class LabelHotspotLink(BaseModel):
    """A hotspot targeting a label."""

    scene_id: str
    hotspot_id: str
    hotspot_name: str


class LabelGraphResult(BaseModel):
    """Full label graph scan result."""

    ok: bool = True
    summary: LabelGraphSummary
    labels: List[ScriptLabelNode] = Field(default_factory=list)
    edges: List[ScriptGraphEdge] = Field(default_factory=list)
    missing: List[ScriptGraphEdge] = Field(default_factory=list)
    unused: List[ScriptLabelNode] = Field(default_factory=list)


class LabelDetailResult(BaseModel):
    """Details for one label."""

    ok: bool = True
    label: Optional[ScriptLabelNode] = None
    incoming: List[ScriptGraphEdge] = Field(default_factory=list)
    outgoing: List[ScriptGraphEdge] = Field(default_factory=list)
    hotspots: List[LabelHotspotLink] = Field(default_factory=list)


class LabelHealthResult(BaseModel):
    """Label graph health summary."""

    ok: bool = True
    summary: Dict[str, int]


def normalize_project_path(raw_path: str) -> Path:
    """Expand a user supplied path without creating or modifying it."""

    return Path(raw_path).expanduser().resolve(strict=False)
