from _shutil import *
import argparse


def start_server(file=None, content_base=None, port=None):
    MOVY_ROOT = os.path.join(os.path.realpath(os.path.dirname(__file__)), "movy")

    if not os.path.exists(os.path.join(MOVY_ROOT, "node_modules")):
        call_echo(["yarn"], cwd=MOVY_ROOT)

    launch_script = os.path.join(MOVY_ROOT, "bin", "movy.js")

    args = ["node", launch_script]
    if port is not None:
        args += ["--port", "%d" % port, "--no-open"]
    args += [file]

    ps = subprocess.Popen(args, cwd=MOVY_ROOT)
    return ps


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file", type=str, help="animation js file", nargs="?", default=None
    )

    args = parser.parse_args()
    if args.file is not None:
        file = args.file
    else:
        file = get_files()[0]

    ps = start_server(file)

    # url = "http://localhost:8080/%s.html" % os.path.splitext(os.path.basename(file))[0]
    # shell_open(url)

    try:
        ps.wait()
    except KeyboardInterrupt:
        ps.send_signal(signal.CTRL_C_EVENT)
