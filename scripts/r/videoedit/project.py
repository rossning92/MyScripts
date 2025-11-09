import json
from pathlib import Path


def create_project(proj_dir: str):
    proj_path = Path(proj_dir)
    for name in [
        "animation",
        "image",
        "overlay",
        "record",
        "screencap",
        "video",
    ]:
        (proj_path / name).mkdir(parents=True, exist_ok=True)

    index_file = proj_path / "index.md"
    if not index_file.exists():
        index_file.touch()

    api_file = proj_path / "api.py"
    if not api_file.exists():
        api_file.touch()
