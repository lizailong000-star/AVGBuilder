"""FastAPI routes for the mock AI Gateway."""

from __future__ import annotations

from fastapi import APIRouter, Query

from .models import (
    AICapabilities,
    AIJsonRequest,
    AIModerateRequest,
    AIModerateResponse,
    AIResponse,
    AITaskResult,
    AITaskStatus,
    AITaskSubmitRequest,
    AITextRequest,
)
from .service import (
    generate_json,
    generate_text,
    get_capabilities,
    get_task_result,
    get_task_status,
    moderate,
    submit_task,
)

router = APIRouter(prefix="/api/ai", tags=["ai-gateway"])


@router.get("/capabilities", response_model=AICapabilities)
def ai_capabilities() -> AICapabilities:
    return get_capabilities()


@router.post("/text", response_model=AIResponse)
def ai_text(request: AITextRequest) -> AIResponse:
    return generate_text(request)


@router.post("/json", response_model=AIResponse)
def ai_json(request: AIJsonRequest) -> AIResponse:
    return generate_json(request)


@router.post("/moderate", response_model=AIModerateResponse)
def ai_moderate(request: AIModerateRequest) -> AIModerateResponse:
    return moderate(request)


@router.post("/task/submit", response_model=AITaskStatus)
def ai_task_submit(request: AITaskSubmitRequest) -> AITaskStatus:
    return submit_task(request)


@router.get("/task/status", response_model=AITaskStatus)
def ai_task_status(task_id: str = Query(...)) -> AITaskStatus:
    return get_task_status(task_id)


@router.get("/task/result", response_model=AITaskResult)
def ai_task_result(task_id: str = Query(...)) -> AITaskResult:
    return get_task_result(task_id)
