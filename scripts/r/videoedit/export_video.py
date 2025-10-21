import argparse
import glob
import importlib
import inspect
import os
import re
import shutil
import subprocess
import sys

import yaml
from _shutil import (
    format_time,
    get_time_str,
    keep_awake,
    print2,
    start_process,
    to_valid_file_name,
)
from utils.confirm import confirm

os.environ["FFMPEG_BINARY"] = shutil.which("ffmpeg")
from moviepy.config import change_settings

from . import automation, common, editor

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

ignore_undefined = False


config = None


@common.api
def include(file):
    with open(file, "r", encoding="utf-8") as f:
        s = f.read()

    cwd = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(file)))

    if file.endswith(".md"):
        _parse_text(s)
    elif file.endswith(".py"):
        sys.path.append(os.path.dirname(file))
        exec(s)
    else:
        raise Exception("invalid file type")

    os.chdir(cwd)


def _remove_unused_recordings(s):
    used_recordings = set()
    unused_recordings = []

    apis = {"record": (lambda f, **kargs: used_recordings.add(f))}
    _parse_text(s, apis=apis)

    files = [f for f in glob.glob("record/*") if os.path.isfile(f)]
    files = [f.replace("\\", "/") for f in files]

    for f in files:
        if f not in used_recordings:
            unused_recordings.append(f)

    total = len(files)
    assert len(used_recordings) + len(unused_recordings) == len(files)
    if confirm(
        "Delete all unused recordings (%d/%d)" % (len(unused_recordings), total)
    ):
        for f in unused_recordings:
            try:
                os.remove(f)
            except Exception:
                print("WARNING: failed to remove: %s" % f)


def _convert_to_readable_time(seconds):
    seconds = int(seconds)
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    if hour > 0:
        return "%d:%02d:%02d" % (hour, minutes, seconds)
    else:
        return "%02d:%02d" % (minutes, seconds)


def _write_timestamp(t, section_name):
    os.makedirs(os.path.dirname(out_filename), exist_ok=True)

    if not hasattr(_write_timestamp, "f"):
        _write_timestamp.f = open("%s.txt" % out_filename, "w", encoding="utf-8")

    _write_timestamp.f.write("%s (%s)\n" % (section_name, _convert_to_readable_time(t)))
    _write_timestamp.f.flush()


def _parse_text(text, apis=common.apis, should_write_timestamp=False, **kwargs):
    def find_next(text, needle, p):
        pos = text.find(needle, p)
        if pos < 0:
            pos = len(text)
        return pos

    # Remove all comments
    text = re.sub(r"<!--[\d\D]*?-->", "", text)

    p = 0  # Current position
    while p < len(text):
        if text[p : p + 2] == "{{":
            end = find_next(text, "}}", p)
            python_code = text[p + 2 : end]
            p = end + 2

            # Dealing with indentation
            lines = python_code.splitlines()
            lines = [x for x in lines if x.strip()]  # remove empty lines
            n_spaces = min([len(x) - len(x.lstrip()) for x in lines])
            lines = [x[n_spaces:] for x in lines]
            python_code = "\n".join(lines)

            if ignore_undefined:
                try:
                    exec(python_code, {**apis, **editor.get_pos_dict()})
                except NameError:  # API is not defined
                    pass  # simply ignore
            else:
                exec(python_code, {**apis, **editor.get_pos_dict()})

            continue

        if text[p : p + 1] == "#":
            end = find_next(text, "\n", p)

            if should_write_timestamp:
                line = text[p:end].strip()
                _write_timestamp(editor.get_current_audio_pos(), line)

            p = end + 1
            continue

        match = re.match("---((?:[0-9]*[.])?[0-9]+)?\n", text[p:])
        if match is not None:
            if match.group(1) is not None:
                editor.audio_gap(float(match.group(1)))
            else:
                editor.audio_gap(0.2)
            p += match.end(0) + 1
            continue

        # Parse regular text
        end = find_next(text, "\n", p)
        line = text[p:end].strip()
        p = end + 1

        if line != "" and "parse_line" in apis:
            apis["parse_line"](line)

    # Call it at the end
    common.on_api_func(None)


def _show_stats(s):
    TIME_PER_CHAR = 0.1334154351395731

    total = 0

    def parse_line(line):
        print(line)
        nonlocal total
        total += len(line)

    _parse_text(s, apis={"parse_line": parse_line}, ignore_undefined=True)

    total_secs = TIME_PER_CHAR * total
    print("Estimated Time: %s" % format_time(total_secs))

    input()


def save_config(config, config_file=None):
    if config_file is None:
        config_file = "config.yaml"

    # Always update the config file.
    with open(config_file, "w", newline="\n", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def load_config(config_file=None):
    DEFAULT_CONFIG = {"fps": 30, "title": None}

    if config_file is None:
        config_file = "config.yaml"

    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
            config = {**DEFAULT_CONFIG, **config}
    else:
        config = DEFAULT_CONFIG

    # Always update the config file.
    save_config(config, config_file=config_file)

    return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--proj_dir", type=str, default=None)
    parser.add_argument("-i", "--input", type=str, default=None)
    parser.add_argument("-a", "--audio_only", action="store_true", default=False)
    parser.add_argument(
        "--remove_unused_recordings", action="store_true", default=False
    )
    parser.add_argument("--stat", action="store_true", default=False)
    parser.add_argument("--preview", action="store_true", default=False)
    parser.add_argument("--force", action="store_true", default=False)

    args = parser.parse_args()

    # Change working directory to project directory.
    if args.proj_dir is not None:
        os.chdir(args.proj_dir)
        sys.path.append(args.proj_dir)
    elif args.input:
        proj_dir = os.path.dirname(args.input)
        os.chdir(proj_dir)
        sys.path.append(proj_dir)
    print("Project dir: %s" % os.getcwd())

    # Load config
    config = load_config()
    editor.fps(config["fps"])

    # Check if it's in preview mode.
    if not args.remove_unused_recordings:
        if args.preview:
            os.makedirs("tmp/out", exist_ok=True)
            out_filename = "tmp/out/" + get_time_str()
        else:
            # Video title
            if not config["title"]:
                title = input("please enter video title (untitled): ")
                if title:
                    config["title"] = title
                    save_config(config)
                else:
                    config["title"] = "untitled"

            os.makedirs("export", exist_ok=True)
            out_filename = "export/" + to_valid_file_name(config["title"])

    # Load custom APIs (api.py) if exists
    api_modules = []

    vproject_root = common.find_vproject_root()
    if vproject_root:
        api_dir = os.path.join(vproject_root, "api")
        if os.path.exists(api_dir):
            sys.path.append(api_dir)
            for module_file in glob.glob(os.path.join(api_dir, "*.py")):
                module_name = os.path.splitext(os.path.basename(module_file))[0]
                module = importlib.import_module(module_name)
                api_modules.append(module)

    if os.path.exists("api.py"):
        sys.path.append(os.getcwd())
        module = importlib.import_module("api")
        api_modules.append(module)

    for module in api_modules:
        global_functions = inspect.getmembers(module, inspect.isfunction)
        common.apis.update({k: v for k, v in global_functions})

    # Read input scripts
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            s = f.read()
    else:
        raise Exception("--input must be specified.")

    try:
        if args.remove_unused_recordings:
            ignore_undefined = True
            _remove_unused_recordings(s)
        elif args.stat:
            ignore_undefined = True
            _show_stats(s)
        else:
            editor.reset()
            keep_awake()

            if args.preview:
                editor.enable_preview()

            if args.force:
                common.force = True

            if args.audio_only:
                editor.set_audio_only()

            _parse_text(s, apis=common.apis)

            out = editor.export_video(
                out_filename=out_filename, resolution=(1920, 1080)
            )

            if sys.platform == "win32":
                subprocess.call(["taskkill", "/f", "/im", "mpv.exe"], shell=True)
            start_process(
                [
                    "mpv",
                    out,
                    "--force-window",
                    "--geometry=33%-0%+0%",
                ],
            )

    except common.VideoEditException as ex:
        print2("ERROR: %s" % ex, color="red")
        sys.exit(1)
