from _shutil import *
import pathlib
from _code import prepend_line, patch_code
from _editor import open_in_vscode
from _template import render_template_file

OVERWRITE = bool("{{_OVERWRITE}}")

REACT_INDEX_JS = "src/client/index.js"
SERVER_INDEX_JS = "src/server/index.js"
MODEL_DIR = "src/server/models"
INDEX_JS = "src/index.js"
SCRIPT_ROOT = os.getcwd()


def add_packages(packages, dev=False):
    with open("package.json", "r") as f:
        data = json.load(f)

    try:
        existing_packages = (
            data["devDependencies"].keys() if dev else data["dependencies"].keys()
        )
    except KeyError:
        existing_packages = []

    for pkg in packages:
        if pkg not in existing_packages:
            if dev:
                call_echo(["yarn", "add", "--dev", pkg])
            else:
                call_echo(["yarn", "add", pkg])


@menu_item(key="w")
def add_webpack(index_js="src/index.js"):
    WEBPACK_CONFIG = "webpack.config.js"

    add_packages(
        ["webpack", "webpack-cli", "webpack-dev-server", "html-webpack-plugin"],
        dev=True,
    )

    if not os.path.exists(WEBPACK_CONFIG) or OVERWRITE:
        with open(WEBPACK_CONFIG, "w") as f:
            f.write(
                """var HtmlWebpackPlugin = require('html-webpack-plugin');
var path = require('path');

module.exports = {
  entry: './%s',
  output: {
    path: path.resolve(__dirname, './dist'),
    filename: 'index_bundle.js'
  },
  plugins: [new HtmlWebpackPlugin()],
  devServer: {
    contentBase: path.join(__dirname, 'dist'),
    open: true,
    port: 3000,
    proxy: {
      "/api": "http://localhost:8080"
    },
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: 'babel-loader'
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"]
      },
    ]
  }
};
"""
                % (index_js)
            )

    if not os.path.exists(index_js):
        os.makedirs(os.path.dirname(index_js), exist_ok=True)
        # pathlib.Path(index_js).touch()

    add_script_to_package(
        "start", "webpack serve --mode development --devtool inline-source-map --hot",
    )

    # webpack_start()


def webpack_start():
    os.environ["PATH"] += os.pathsep + os.path.join(project_dir, "node_modules", ".bin")
    threading.Thread(
        target=lambda: call_echo("webpack serve --mode development")
    ).start()


def add_script_to_package(name, script):
    # Package.json
    with open("package.json", "r") as f:
        data = json.load(f)

    if "scripts" not in data.keys():
        data["scripts"] = {}

    data["scripts"][name] = script

    with open("package.json", "w") as f:
        json.dump(data, f, indent=2)


@menu_item(key="r")
def add_react(index_js=REACT_INDEX_JS):
    add_webpack(index_js=REACT_INDEX_JS)

    # # https://create-react-app.dev/docs/getting-started/
    # call_echo("yarn create react-app client")

    add_packages(["react", "react-dom"])

    # CSS loader
    add_packages(["style-loader", "css-loader"])

    # Babel: transcompile jsx
    add_packages(
        [
            "babel-loader",
            "@babel/core",
            "@babel/preset-env",
            "@babel/preset-react",
            "babel-plugin-react-html-attrs",  # transform class → className
        ],
        dev=True,
    )

    with open(".babelrc", "w") as f:
        f.write(
            """{
  "presets": ["@babel/preset-env", "@babel/preset-react"],
  "plugins": ["react-html-attrs"]
}
"""
        )

    mkdir(os.path.dirname(REACT_INDEX_JS))
    if not os.path.exists(REACT_INDEX_JS) or OVERWRITE:
        with open(REACT_INDEX_JS, "w") as f:
            f.write(
                """import { render } from 'react-dom';

import React, { useState, useEffect } from 'react';

function App() {
  const [username, setUsername] = useState('loading...');

  useEffect(() => {
    fetch('/api/getUsername')
      .then(res => res.json())
      .then(data => setUsername(data.username));
  });

  return (
      <button>username: {username}</button>
  );
}

const root = document.createElement('div');
document.body.appendChild(root);
render(<App />, root);
"""
            )

    add_script_to_package(
        "client", "webpack serve --mode development --devtool inline-source-map --hot",
    )


@menu_item(key="1")
def add_MERN_stack():
    add_react()
    add_express()
    add_mongodb()

    add_script_to_package("dev", 'concurrently "npm run server" "npm run client"')

    # add "dev" to run server and client concurrently
    add_packages(["concurrently"], dev=True)
    call_echo("npm run dev")


@menu_item(key="d")
def add_dat_gui():
    add_packages(["dat.gui"])


@menu_item(key="p")
def add_p5():
    add_packages(["p5"])


@menu_item(key="b")
def add_bootstrap():
    add_packages(["react-bootstrap", "bootstrap"])

    # https://react-bootstrap.netlify.app/getting-started/introduction/
    prepend_line(REACT_INDEX_JS, "import 'bootstrap/dist/css/bootstrap.min.css';")


@menu_item(key="e")
def add_express():
    add_packages(["express"])
    add_packages(["nodemon"], dev=True)  # Monitor js changes and and hot reload

    # Package.json
    add_script_to_package("server", "nodemon src/server/index.js")

    # Server index.js
    if not os.path.exists(SERVER_INDEX_JS) or OVERWRITE:
        mkdir(os.path.dirname(SERVER_INDEX_JS))
        with open(SERVER_INDEX_JS, "w") as f:
            f.write(
                """const express = require('express');
const os = require('os');

const app = express();

app.use(express.static('dist'));

app.get("/api/getUsername", (req, res) =>
  res.send({ username: os.userInfo().username })
);

app.listen(process.env.PORT || 8080, () => console.log(`Listening on port ${process.env.PORT || 8080}!`));
"""
            )


@menu_item(key="m")
def add_mongodb():
    add_packages(["mongoose"])

    mkdir(MODEL_DIR)
    with open(MODEL_DIR + "/contact.js", "w") as f:
        f.write(
            """const mongoose = require("mongoose");

module.exports.Contact = mongoose.model(
  "contact",
  mongoose.Schema({
    name: {
      type: String,
      required: true,
    },
    phone: String,
    createDate: {
      type: Date,
      default: Date.now,
    },
  })
);
"""
        )

    patch_code(
        SERVER_INDEX_JS,
        "^",
        """const mongoose = require("mongoose");
mongoose
  .connect("mongodb://localhost/test_db", { useNewUrlParser: true })
  .then(() => {
    console.log("Database connected.");
  })
  .catch((err) => console.log(err));
""",
        count=1,
    )


@menu_item(key="3")
def add_threejs():
    add_packages(["three"])

    os.makedirs(os.path.dirname(INDEX_JS), exist_ok=True)
    if os.path.exists(INDEX_JS) and yes("overwrite %s" % INDEX_JS):
        render_template_file(SCRIPT_ROOT + "/template/hello-three.js", INDEX_JS)


@menu_item(key="v")
def open_vscode():
    open_in_vscode(os.getcwd())


if __name__ == "__main__":
    cd("~")
    project_dir = os.path.realpath(r"{{JS_PROJECT_DIR}}")
    cd(project_dir)
    print("Project dir: %s" % project_dir)

    if not exists("package.json"):
        call_echo("yarn init -y")

    menu_loop()
