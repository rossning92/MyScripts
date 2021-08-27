import json
import os
import subprocess
import sys
import traceback

import _appmanager
from _shutil import run_elevated

config = None


def load_config():
    global config
    with open(
        os.path.join(os.path.dirname(__file__), "open_with.config.json"),
        "r",
        encoding="utf-8",
    ) as f:
        config = json.load(f)


load_config()


def open_with_hook(files, program_id):
    ext = os.path.splitext(files[0])[1].lower()

    # HACK: hijack extension handling
    if ext == ".vhd":
        run_elevated(["powershell", "-Command", "Mount-VHD -Path '%s'" % files])
        return True

    if program_id == 1 and ext in [".mp4", ".webm"]:
        from videoedit.video_editor import edit_video

        edit_video(files[0])

        return True

    return False


def open_with(files, program_id=0):
    if type(files) == str:
        files = [files]

    ext = os.path.splitext(files[0])[1].lower()

    if open_with_hook(files, program_id):
        return

    if ext not in config:
        raise Exception('Extension "%s" is not supported.' % ext)

    program = config[ext][program_id]

    if type(program) == str:
        executable = _appmanager.get_executable(program)
        assert executable is not None
        args = [executable] + files

    elif type(program) == list:
        args = program + files

    else:
        raise Exception("Unsupported program definition.")

    subprocess.Popen(args, close_fds=True)


if __name__ == "__main__":
    try:
        program_id = int(sys.argv[1])

        with open(os.path.join(os.environ["TEMP"], "ow_explorer_info.json")) as f:
            data = json.load(f)

        if data["current_folder"]:
            os.environ["_CUR_DIR"] = data["current_folder"]

        files = data["selected_files"]

        open_with(files, program_id)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(e)
        input("Press enter to exit...")
