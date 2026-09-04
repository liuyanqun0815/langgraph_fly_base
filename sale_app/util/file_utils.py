import os
from pathlib import Path

# Django 已移除；用 FastAPI 时代仍存在的根目录标记
PROJECT_ROOT_MARKERS = ("config.py", "app/main.py", "requirements.txt")


def find_project_root(start_path: str | os.PathLike[str]) -> str | None:
    """从 start_path 向上查找项目根目录。"""
    path = Path(start_path).resolve()
    if path.is_file():
        path = path.parent

    while True:
        if any((path / marker).is_file() for marker in PROJECT_ROOT_MARKERS):
            return str(path)
        parent = path.parent
        if parent == path:
            return None
        path = parent
