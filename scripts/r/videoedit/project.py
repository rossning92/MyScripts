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

    jsconfig = proj_path / "animation" / "jsconfig.json"
    base_path = proj_path.resolve().as_posix()
    movy_dist = f"{base_path}/movy/dist/*"
    movy_utils = f"{base_path}/movyutils/*"
    jsconfig.write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "module": "es6",
                    "target": "es2016",
                    "jsx": "preserve",
                    "baseUrl": base_path,
                    "paths": {
                        "*": [
                            movy_dist,
                            movy_utils,
                        ]
                    },
                },
                "include": [
                    movy_dist,
                    movy_utils,
                    "*.js",
                ],
                "exclude": ["node_modules", "**/node_modules/*"],
            },
            indent=4,
        )
    )

    index_file = proj_path / "index.md"
    if not index_file.exists():
        index_file.touch()

    api_file = proj_path / "api.py"
    if not api_file.exists():
        api_file.touch()
