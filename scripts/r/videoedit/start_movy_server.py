import argparse
import os
import signal
import subprocess

from _shutil import call_echo, get_files


def start_server(file=None, port=None):
    script_root = os.path.realpath(os.path.dirname(__file__))
    movy_root = os.path.join(script_root, "movy")

    if not os.path.exists(os.path.join(movy_root, "node_modules")):
        call_echo(["yarn"], cwd=movy_root)

    launch_script = os.path.join(movy_root, "bin", "movy.js")

    args = ["node", launch_script]
    if port is not None:
        args += ["--port", "%d" % port, "--no-open"]
    args += [file]

    ps = subprocess.Popen(
        args,
        cwd=movy_root,
        # CTRL+C signals will be disabled in current process
        creationflags=0x00000200,
    )
    return ps


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=None)
    parser.add_argument(
        "file", type=str, help="animation js file", nargs="?", default=None
    )

    args = parser.parse_args()
    if args.file is not None:
        file = args.file
    else:
        file = get_files()[0]

    ps = start_server(file, port=args.port)

    try:
        ps.wait()
    except KeyboardInterrupt:
        ps.send_signal(signal.CTRL_C_EVENT)
