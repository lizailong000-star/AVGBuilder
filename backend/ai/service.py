"""Mock AI Gateway service.

This module intentionally does not call external AI providers and does not read API keys.
It reserves future-compatible interfaces for AVGBuilder AI features.
"""

from __future__ import annotations

from uuid import uuid4

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

CAPABILITIES = [
    "text",
    "json",
    "prompt",
    "renpy_snippet",
    "moderate",
    "image_generate_placeholder",
    "audio_tts_placeholder",
    "embeddings_placeholder",
    "agent_placeholder",
]

_TASKS: dict[str, dict] = {}


def get_capabilities() -> AICapabilities:
    return AICapabilities(capabilities=CAPABILITIES)


def generate_text(request: AITextRequest) -> AIResponse:
    return AIResponse(
        task_type=request.task_type,
        result="AI text generation is reserved. Real provider is not enabled.",
        warnings=["Mock response only. No external AI API was called."],
    )


def generate_json(request: AIJsonRequest) -> AIResponse:
    return AIResponse(
        task_type=request.task_type,
        result={
            "placeholder": True,
            "message": "Structured JSON generation is reserved.",
            "schema_name": request.schema_name,
        },
        warnings=["Mock response only. No external AI API was called."],
    )


def moderate(request: AIModerateRequest) -> AIModerateResponse:
    return AIModerateResponse(flagged=False)


def submit_task(request: AITaskSubmitRequest) -> AITaskStatus:
    task_id = f"mock-task-{uuid4().hex[:8]}"
    _TASKS[task_id] = {
        "task_type": request.task_type,
        "input_text": request.input_text,
        "context": request.context,
        "status": "done",
        "progress": 100,
        "result": {
            "message": "Mock AI task result.",
            "task_type": request.task_type,
            "placeholder": True,
        },
    }
    return AITaskStatus(task_id=task_id)


def get_task_status(task_id: str) -> AITaskStatus:
    task = _TASKS.get(task_id)
    if not task:
        return AITaskStatus(ok=False, task_id=task_id, status="not_found", progress=0)
    return AITaskStatus(task_id=task_id, status=task["status"], progress=task["progress"])


def get_task_result(task_id: str) -> AITaskResult:
    task = _TASKS.get(task_id)
    if not task:
        return AITaskResult(ok=False, task_id=task_id, status="not_found", result={"message": "Task not found."})
    return AITaskResult(task_id=task_id, status=task["status"], result=task["result"])
