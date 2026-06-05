"""Read-only Ren'Py project structure scanner."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from .models import ProjectChecks


def scan_project_structure(project_path: Path) -> Tuple[ProjectChecks, List[str]]:
    """Check for expected Ren'Py project files without writing anything."""

    logs: List[str] = []
    exists = project_path.exists()
    logs.append(f"Project path: {project_path}")
    logs.append(f"Project path exists: {'yes' if exists else 'no'}")

    game_dir = project_path / "game"
    checks = ProjectChecks(
        game_dir=game_dir.is_dir(),
        script_rpy=(game_dir / "script.rpy").is_file(),
        gui_rpy=(game_dir / "gui.rpy").is_file(),
        options_rpy=(game_dir / "options.rpy").is_file(),
        gitignore=(project_path / ".gitignore").is_file(),
    )

    check_messages = {
        "game_dir": "game/ directory",
        "script_rpy": "game/script.rpy",
        "gui_rpy": "game/gui.rpy",
        "options_rpy": "game/options.rpy",
        "gitignore": ".gitignore",
    }
    for field, label in check_messages.items():
        logs.append(f"Check {label}: {'found' if getattr(checks, field) else 'missing'}")

    return checks, logs
