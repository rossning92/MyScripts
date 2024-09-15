#!/usr/bin/env python3


import glob
import os
import shutil

from _shutil import to_valid_file_name
from utils.yaml import load_yaml

if __name__ == "__main__":
    vproject_root = r"{{VPROJECT_ROOT}}"
    export_dir = os.path.expanduser("~/Desktop/video-export")
    os.makedirs(export_dir, exist_ok=True)

    for f in glob.glob(os.path.join(vproject_root, "*", "config.yaml")):
        name = os.path.basename(os.path.dirname(f))

        project = load_yaml(f)

        exported_files_found = list(
            glob.glob(os.path.join(os.path.dirname(f), "export", "*.mp4"))
        )

        if exported_files_found:
            print("Exporting: %s" % project["title"])
            src_video = os.path.join(
                os.path.dirname(f), "export", exported_files_found[0]
            )
            dest_video = os.path.join(
                export_dir, to_valid_file_name(project["title"] + ".mp4")
            )
            shutil.copy(src_video, dest_video)

            src_thumbnail = glob.glob(
                os.path.join(os.path.dirname(f), "thumbnail", "*.png")
            )[0]
            dest_thumbnail = os.path.join(
                export_dir, to_valid_file_name(project["title"] + ".png")
            )
            shutil.copy(src_thumbnail, dest_thumbnail)
