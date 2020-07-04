from _shutil import *


def start_server(file=None, folder=None):
    ANIME_ROOT = os.path.join(os.path.realpath(os.path.dirname(__file__)), "_framework")

    if not os.path.exists(os.path.join(ANIME_ROOT, "node_modules")):
        call_echo("yarn install", cwd=ANIME_ROOT)
        call_echo("yarn link", cwd=ANIME_ROOT)

    if 0:  # To enable code suggestions and completion in vscode
        if not os.path.exists("package.json"):
            with open("package.json", "w") as f:
                f.write(
                    "{\n"
                    '"name": "animation"\n'
                    '"version": "1.0.0"\n'
                    '"main": "index.js"\n'
                    '"license": "MIT"\n'
                    "}\n"
                )
            call_echo("yarn link yo")

    # sample_project_path = os.path.abspath("./_sample_project")
    # copy(sample_project_path + '/', project_path + '/')

    if file is not None:
        os.environ["ENTRY"] = file
    elif folder is None:
        print("No js file selected.")
        # project_path = (
        #     r"{{ANIMATION_PROJECT_PATH}}" if r"{{ANIMATION_PROJECT_PATH}}" else None
        # )
        cd(folder)
        os.environ["ENTRY_FOLDER"] = folder

    script = os.path.join(ANIME_ROOT, "bin", "start-app.js")
    ps = subprocess.Popen(["node", script])
    return ps


if __name__ == "__main__":
    ps = start_server(get_files()[0])
    ps.wait()
