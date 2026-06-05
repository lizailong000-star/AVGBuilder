"""Read-only Ren'Py label scanner."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .models import LabelInfo

LABEL_PATTERN = re.compile(r"^\s*label\s+([A-Za-z_][A-Za-z0-9_]*)\s*:")


def scan_labels(project_path: Path) -> list[LabelInfo]:
    """Scan game/**/*.rpy and return labels with source file and line number."""

    game_dir = project_path / "game"
    if not game_dir.is_dir():
        return []

    labels: list[LabelInfo] = []
    for file_path in _iter_rpy_files(game_dir):
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines, start=1):
            match = LABEL_PATTERN.match(line)
            if match:
                labels.append(
                    LabelInfo(
                        name=match.group(1),
                        file=file_path.relative_to(project_path).as_posix(),
                        line=index,
                    )
                )
    return sorted(labels, key=lambda item: (item.file, item.line, item.name))


def _iter_rpy_files(game_dir: Path) -> Iterable[Path]:
    return sorted(path for path in game_dir.rglob("*.rpy") if path.is_file())
