import os
import re


def get_unreal_source_version():
    version_file = os.path.join(
        os.environ["UE_SOURCE"],
        "Engine",
        "Source",
        "Runtime",
        "Launch",
        "Resources",
        "Version.h",
    )
    if not os.path.exists(version_file):
        raise Exception("Cannot find Version.h")
    with open(version_file, "r", encoding="utf-8") as f:
        s = f.read()

    match = re.findall(r"#define\s+ENGINE_(?:MAJOR|MINOR|PATCH)_VERSION\s+(\d+)", s)
    if not match:
        raise Exception("Cannot locate version in Version.h")
    version_str = f"{match[0]}.{match[1]}.{match[2]}"
    return version_str
