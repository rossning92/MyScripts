import argparse
import glob
import importlib
import inspect
import os
import re
import sys

import numpy as np
from _appmanager import get_executable
from _shutil import format_time, get_time_str, getch, print2
from moviepy.config import change_settings

import codeapi
import core
import coreapi

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

ignore_undefined = False

change_settings({"FFMPEG_BINARY": get_executable("ffmpeg")})


@core.api
def include(file):
    with open(file, "r", encoding="utf-8") as f:
        s = f.read()

    cwd = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(file)))
    _parse_text(s)
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

    print2("Used   : %d" % len(used_recordings), color="green")
    print2("Unused : %d" % len(unused_recordings), color="red")
    assert len(used_recordings) + len(unused_recordings) == len(files)
    s = input("Press enter to confirm: ")
    if s == "":
        for f in unused_recordings:
            try:
                os.remove(f)
            except:
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


def _parse_text(text, apis=core.apis, **kwargs):
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
            python_code = text[p + 2 : end].strip()
            p = end + 2

            if ignore_undefined:
                try:
                    exec(python_code, apis)
                except NameError:  # API is not defined
                    pass  # simply ignore
            else:
                exec(python_code, apis)

            continue

        if text[p : p + 1] == "#":
            end = find_next(text, "\n", p)

            line = text[p:end].strip()
            _write_timestamp(coreapi.get_current_audio_pos(), line)

            p = end + 1
            continue

        match = re.match("---((?:[0-9]*[.])?[0-9]+)?\n", text[p:])
        if match is not None:
            if match.group(1) is not None:
                coreapi.audio_gap(float(match.group(1)))
            else:
                coreapi.audio_gap(0.2)
            p += match.end(0) + 1
            continue

        # Parse regular text
        end = find_next(text, "\n", p)
        line = text[p:end].strip()
        p = end + 1

        if line != "" and "parse_line" in apis:
            apis["parse_line"](line)

    # Call it at the end
    core.on_api_func(None)


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


def load_config():
    import yaml

    CONFIG_FILE = "config.yaml"
    DEFAULT_CONFIG = {"fps": 30}

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
    else:
        with open(CONFIG_FILE, "w", newline="\n") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
        config = DEFAULT_CONFIG

    coreapi.fps(config["fps"])


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

    args = parser.parse_args()

    # args.preview = False
    if args.preview:
        os.makedirs("tmp/out", exist_ok=True)
        out_filename = "tmp/out/" + get_time_str()
    else:
        os.makedirs("export", exist_ok=True)
        out_filename = "export/" + get_time_str()

    if args.proj_dir is not None:
        os.chdir(args.proj_dir)
    elif args.input:
        os.chdir(os.path.dirname(args.input))
    print("Project dir: %s" % os.getcwd())

    # Load custom APIs (api.py) if exists
    if os.path.exists("api.py"):
        sys.path.append(os.getcwd())
        mymodule = importlib.import_module("api")
        global_functions = inspect.getmembers(mymodule, inspect.isfunction)
        core.apis.update({k: v for k, v in global_functions})

    # Read input scripts
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            s = f.read()
    else:
        raise Exception("--input must be specified.")

    load_config()

    if args.remove_unused_recordings:
        ignore_undefined = True
        _remove_unused_recordings(s)
    elif args.stat:
        ignore_undefined = True
        _show_stats(s)
    else:
        if True:
            coreapi.reset()

            if args.preview:
                coreapi.enable_preview()

            _parse_text(s, apis=core.apis)

            coreapi.export_video(
                out_filename=out_filename,
                resolution=(1920, 1080),
                audio_only=args.audio_only,
            )
