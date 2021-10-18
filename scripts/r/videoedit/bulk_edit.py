#!/usr/bin/env python3
import glob
import os
from pprint import pprint

from _editor import open_in_vscode
from _shutil import getch, load_yaml, save_yaml, to_valid_file_name

from export_animation import load_config

if __name__ == "__main__":
    vproject_root = r"{{VPROJECT_ROOT}}"
    tmp_file = os.path.expanduser("~/Desktop/videos.yml")

    # Update existing configs
    if os.path.exists(tmp_file):
        videos = load_yaml(tmp_file)
        for name, video2 in videos.items():
            project_file = os.path.join(vproject_root, name, "config.yaml")
            video = load_yaml(project_file)
            if video2 != video:
                pprint(video2)
                print("press y to continue...")
                if getch() == "y":
                    videos[name] = video2
                    save_yaml(video2, project_file)

    # Export all configs to a single yaml file.
    videos = {}
    for f in glob.glob(os.path.join(vproject_root, "*", "config.yaml")):
        name = os.path.basename(os.path.dirname(f))

        config = load_config(f)
        title = config["title"]

        # Try to rename the video file
        if True:
            exported_files_found = list(
                glob.glob(os.path.join(os.path.dirname(f), "export", "*.mp4"))
            )
            if len(exported_files_found) > 1:
                exported_file = None
            elif len(exported_files_found) == 1:
                exported_file = os.path.basename(exported_files_found[0])
            else:
                exported_file = None

            if exported_file is not None:
                new_file = to_valid_file_name(title) + ".mp4"
                os.rename(
                    os.path.join(os.path.dirname(f), "export", exported_file),
                    os.path.join(os.path.dirname(f), "export", new_file),
                )

            videos[name] = config

    save_yaml(videos, tmp_file)

    open_in_vscode(tmp_file)
