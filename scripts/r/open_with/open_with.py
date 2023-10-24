import json
import os
import re
import subprocess
import sys
import traceback
from typing import List, Union

from _pkgmanager import find_executable, require_package
from _shutil import is_in_termux, run_elevated, shell_open


def load_config():
    with open(
        os.path.join(os.path.dirname(__file__), "open_with.config.json"),
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


config = load_config()


def open_with_hook(files, program_id):
    file_name = os.path.basename(files[0])
    ext = os.path.splitext(files[0])[1].lower()

    # HACK: hijack extension handling
    if ext == ".vhd":
        run_elevated(["powershell", "-Command", "Mount-VHD -Path '%s'" % files])
        return True

    if file_name == "trace":
        subprocess.check_call(
            ["run_script", "r/android/perfetto/open_perfetto_trace.py", files[0]],
            close_fds=True,
        )
        return True

    if program_id == 1 and ext in [".mp4", ".webm"]:
        from videoedit.video_editor import edit_video

        edit_video(files[0])

        return True

    return False


def open_with(files: Union[str, List[str]], program_id=0):
    if isinstance(files, str):
        files = [files]

    if is_in_termux():
        shell_open(files[0])
        return

    if open_with_hook(files, program_id):
        return

    # Try to match ext by regex
    for patt, programs in config["matchByRegex"].items():
        if re.search(patt, files[0]):
            print(f"Matched file type: {patt}")
            open_files_with_program(files, programs, program_id)
            return

    ext = os.path.splitext(files[0])[1].lower()
    if ext in config["matchByExt"]:
        open_files_with_program(files, config["matchByExt"][ext], program_id)
        return

    raise Exception("File type is not supported.")


def open_files_with_program(files, programs, program_id):
    program = programs[program_id]

    if isinstance(program, str):
        require_package(program)
        executable = find_executable(program)
        assert executable is not None
        args = [executable] + files

    elif isinstance(program, list):
        args = program + files

    else:
        raise Exception("A program must be str or list.")

    subprocess.Popen(args, close_fds=True)


if __name__ == "__main__":
    try:
        program_id = int(sys.argv[1])

        with open(os.path.join(os.environ["TEMP"], "ow_explorer_info.json")) as f:
            data = json.load(f)

        if data["current_folder"]:
            os.environ["CWD"] = data["current_folder"]

        files = data["selected_files"]

        open_with(files, program_id)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(e)
        input("Press enter to exit...")
