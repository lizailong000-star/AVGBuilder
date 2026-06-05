"""Future-compatible AI Gateway request/response models."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


AIMode = Literal["mock"]


class AITextRequest(BaseModel):
    task_type: str = "text"
    input_text: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)


class AIJsonRequest(BaseModel):
    task_type: str = "json"
    input_text: str = ""
    schema_name: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)


class AIModerateRequest(BaseModel):
    input_text: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)


class AITaskSubmitRequest(BaseModel):
    task_type: str = "agent_placeholder"
    input_text: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)


class AIResponse(BaseModel):
    ok: bool = True
    mode: AIMode = "mock"
    task_type: str
    result: Any
    warnings: List[str] = Field(default_factory=list)


class AIModerateResponse(BaseModel):
    ok: bool = True
    mode: AIMode = "mock"
    flagged: bool = False
    categories: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=lambda: ["Mock moderation only."])


class AITaskStatus(BaseModel):
    ok: bool = True
    task_id: str
    status: str = "done"
    progress: int = 100
    mode: AIMode = "mock"


class AITaskResult(BaseModel):
    ok: bool = True
    task_id: str
    status: str = "done"
    result: Dict[str, Any]
    mode: AIMode = "mock"


class AICapabilities(BaseModel):
    ok: bool = True
    provider_enabled: bool = False
    mode: AIMode = "mock"
    capabilities: List[str]
