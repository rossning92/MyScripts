from _shutil import *
import argparse


def start_server(file=None, content_base=None):
    FRAMEWORK_ROOT = os.path.join(
        os.path.realpath(os.path.dirname(__file__)), "movy"
    )

    if not os.path.exists(os.path.join(FRAMEWORK_ROOT, "node_modules")):
        call_echo("yarn install", cwd=FRAMEWORK_ROOT)
        call_echo("yarn link", cwd=FRAMEWORK_ROOT)

    # if 0:  # To enable code suggestions and completion in vscode
    #     if not os.path.exists("package.json"):
    #         with open("package.json", "w") as f:
    #             f.write(
    #                 "{\n"
    #                 '"name": "animation"\n'
    #                 '"version": "1.0.0"\n'
    #                 '"main": "index.js"\n'
    #                 '"license": "MIT"\n'
    #                 "}\n"
    #             )
    #         call_echo("yarn link yo")

    # sample_project_path = os.path.abspath("./_sample_project")
    # copy(sample_project_path + '/', project_path + '/')

    # env = os.environ.copy()
    # if file is not None:
    #     env["ENTRY"] = file
    # if content_base is not None:
    #     env["CONTENT_BASE"] = content_base

    launch_script = os.path.join(FRAMEWORK_ROOT, "bin", "start-app.js")
    ps = subprocess.Popen(["node", launch_script, file], cwd=FRAMEWORK_ROOT)
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
