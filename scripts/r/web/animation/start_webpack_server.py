from _shutil import *

sample_project_path = os.path.abspath("./_sample_project")

setup_nodejs()
project_path = r"{{ANIMATION_PROJECT_PATH}}" if r"{{ANIMATION_PROJECT_PATH}}" else None

cd("_framework")
if not os.path.exists("node_modules"):
    call_echo("yarn install")
    call_echo("yarn link")

cd(project_path)
if not os.path.exists("package.json"):
    with open("package.json", "w") as f:
        f.write(
            """{
  "name": "animation",
  "version": "1.0.0",
  "main": "index.js",
  "license": "MIT"
}
"""
        )
    call_echo("yarn link yo")

# copy(sample_project_path + '/', project_path + '/')

try:
    os.environ["ENTRY"] = get_files()[0]
except:
    print("No js file selected.")
    os.environ["ENTRY_FOLDER"] = project_path

script = os.path.join("node_modules", "yo", "bin", "start-app.js")
call_echo(["node", script])
