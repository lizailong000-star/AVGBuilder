"""Read-only Git status helper."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

from .models import GitStatus


def read_git_status(project_path: Path) -> GitStatus:
    """Read Git metadata without mutating the target repository."""

    if not project_path.exists():
        return GitStatus(is_repository=False, error="Project path does not exist")

    is_repo = _run_git(project_path, ["rev-parse", "--is-inside-work-tree"])
    if is_repo.returncode != 0 or is_repo.stdout.strip() != "true":
        return GitStatus(is_repository=False, error=_clean_error(is_repo.stderr) or None)

    branch_result = _run_git(project_path, ["branch", "--show-current"])
    branch: Optional[str] = branch_result.stdout.strip() or None
    if branch is None:
        detached = _run_git(project_path, ["rev-parse", "--short", "HEAD"])
        branch = f"HEAD detached at {detached.stdout.strip()}" if detached.returncode == 0 else None

    short_result = _run_git(project_path, ["status", "--short"])
    short_lines: List[str] = short_result.stdout.splitlines() if short_result.returncode == 0 else []

    latest_result = _run_git(project_path, ["log", "-1", "--pretty=format:%h %s (%ci)"])
    latest_commit = latest_result.stdout.strip() if latest_result.returncode == 0 else None

    return GitStatus(
        is_repository=True,
        branch=branch,
        clean=len(short_lines) == 0,
        short_status=short_lines,
        latest_commit=latest_commit,
        error=None if short_result.returncode == 0 else _clean_error(short_result.stderr),
    )


def _run_git(cwd: Path, args: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )


def _clean_error(stderr: str) -> str:
    return stderr.strip().splitlines()[-1] if stderr.strip() else ""
