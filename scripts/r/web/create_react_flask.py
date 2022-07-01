from _shutil import *
from _pkgmanager import *
import json

setup_nodejs(install=True)
get_executable("yarn")

cd(r"~/Projects")

# npx: execute a package which wasn't previously installed
# https://reactjs.org/docs/create-a-new-react-app.html
# https://create-react-app.dev/docs/getting-started/

if not exists("{{_PROJECT_NAME}}"):
    call2("yarn create react-app {{_PROJECT_NAME}}")
    call2("yarn add axios")  # Promise based AJAX library
cd("{{_PROJECT_NAME}}")

with open("package.json", "r") as f:
    data = json.load(f)

# Backend framework: Flask
if "server" not in data["scripts"]:
    data["proxy"] = "http://localhost:5000"
    data["scripts"][
        "server"
    ] = "set FLASK_APP=server.py&set FLASK_ENV=development&python -m flask run"

    call2("yarn add concurrently")  # Promise based AJAX library
    data["scripts"][
        "dev"
    ] = 'concurrently --kill-others-on-fail "yarn server" "yarn start"'

    with open("package.json", "w") as f:
        json.dump(data, f, indent=2)

FLASK_APP = """
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'
"""
if not os.path.exists("server.py"):
    call2("pip install flask")
    with open("server.py", "w", newline="\n") as f:
        f.write(FLASK_APP)

# Start dev server
call2("yarn dev")
