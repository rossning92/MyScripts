import argparse
import glob
import importlib
import importlib.util
import inspect
import os
import re
import shutil
import socket
import sys
from pathlib import Path
from typing import List, Optional

import yaml
from _shutil import (
    format_time,
    get_time_str,
    keep_awake,
    print2,
)
from utils.confirm import confirm
from utils.process import start_process

from videoedit.project import create_project

os.environ["FFMPEG_BINARY"] = shutil.which("ffmpeg")

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


def _write_timestamp(t, section_name, out_filename):
    os.makedirs(os.path.dirname(out_filename), exist_ok=True)

    with open("%s.timestamp.txt" % out_filename, "a", encoding="utf-8") as f:
        f.write(
            "%s - %s\n"
            % (
                _convert_to_readable_time(t),
                section_name.lstrip("# "),
            )
        )


def _parse_text(text, apis=common.apis, should_write_timestamp=True, **kwargs):
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

            if out_filename and should_write_timestamp:
                line = text[p:end].strip()
                _write_timestamp(editor.get_current_audio_pos(), line, out_filename)

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
    DEFAULT_CONFIG = {"fps": 30}

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


def _import_from_path(module_name: str, path: str):
    path_ = Path(path).resolve()
    if not path_.exists():
        raise FileNotFoundError(path_)

    spec = importlib.util.spec_from_file_location(module_name, path_)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for module {module_name!r} from {path_}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _open_mpv_single_instance(file: str, extra_args: Optional[List[str]] = None):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        try:
            sock.connect("/tmp/mpv-socket")
            sock.sendall(b'{ "command": ["quit"] }\n')
        except FileNotFoundError:
            pass
        except ConnectionRefusedError:
            pass

    args = ["mpv", "--input-ipc-server=/tmp/mpv-socket", "--force-window", file]
    if extra_args:
        args.extend(extra_args)
    start_process(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--proj_dir", type=str, default=None)
    parser.add_argument("-i", "--input", type=str, default=None)
    parser.add_argument("-a", "--audio_only", action="store_true")
    parser.add_argument("--remove_unused_recordings", action="store_true")
    parser.add_argument("--stat", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--closed-captions", action="store_true")

    args = parser.parse_args()

    # Change working directory to project directory.
    if args.proj_dir is not None:
        proj_dir = args.proj_dir
        os.chdir(proj_dir)
        sys.path.append(proj_dir)
    elif args.input:
        proj_dir = os.path.dirname(args.input)
        os.chdir(proj_dir)
        sys.path.append(proj_dir)
    else:
        proj_dir = os.getcwd()
    print("Project dir: %s" % proj_dir)

    create_project(proj_dir)

    # Load config
    config = load_config()
    editor.fps(config["fps"])
    editor.closed_captions = args.closed_captions

    # Check if it's in preview mode.
    if not args.remove_unused_recordings:
        if args.preview:
            os.makedirs("tmp/out", exist_ok=True)
            out_filename = "tmp/out/" + get_time_str()
        else:
            os.makedirs("export", exist_ok=True)
            out_filename = "export/export"

        if args.closed_captions:
            out_filename += "_cc"
    else:
        out_filename = None
    editor.out_filename = out_filename

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
        module = _import_from_path("api", os.path.join(os.getcwd(), "api.py"))
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

            out: str = editor.export_video(resolution=(1920, 1080))

            mpv_extra_args = []
            if args.preview:
                mpv_extra_args.append("--geometry=33%-0%+0%")
            _open_mpv_single_instance(out, mpv_extra_args)

    except common.VideoEditException as ex:
        print2("ERROR: %s" % ex, color="red")
        sys.exit(1)
