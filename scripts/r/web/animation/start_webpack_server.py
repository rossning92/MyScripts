from _shutil import *


cd("_framework")
if not os.path.exists("node_modules"):
    call_echo("yarn install")
    call_echo("yarn link")

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

try:
    os.environ["ENTRY"] = get_files()[0]
except:
    print("No js file selected.")
    project_path = (
        r"{{ANIMATION_PROJECT_PATH}}" if r"{{ANIMATION_PROJECT_PATH}}" else None
    )
    cd(project_path)
    os.environ["ENTRY_FOLDER"] = project_path

script = os.path.join("node_modules", "yo", "bin", "start-app.js")
call_echo(["node", script])
