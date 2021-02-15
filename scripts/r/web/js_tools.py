from _shutil import *
import pathlib


OVERWRITE = bool("{{_OVERWRITE}}")


cd("~")
project_dir = os.path.realpath(r"{{JS_PROJECT_DIR}}")
cd(project_dir)
print("Project dir: %s" % project_dir)


def add_packages(packages, dev=False):
    with open("package.json", "r") as f:
        data = json.load(f)

    existing_packages = (
        data["devDependencies"].keys() if dev else data["dependencies"].keys()
    )

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
      }
    ]
  }
};
"""
                % (index_js)
            )

    if not os.path.exists(index_js):
        os.makedirs(os.path.dirname(index_js), exist_ok=True)
        pathlib.Path(index_js).touch()

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
def add_react():
    REACT_INDEX_JS = "src/client/index.js"

    add_webpack(index_js=REACT_INDEX_JS)

    # if os.path.exists("package.json"):
    #     with open("package.json", "r") as f:
    #         s = f.read()

    #     if "react-scripts start" in s:
    #         call_echo("yarn start")
    #         return

    #     else:
    #         print2("package.json will be removed (y/n)", color="green")
    #         ch = getch()
    #         if ch != "y":
    #             return
    #         os.remove("package.json")

    # # https://create-react-app.dev/docs/getting-started/
    # call_echo("yarn create react-app client")

    add_packages(["react", "react-dom"])

    # Babel: transcompile jsx
    add_packages(
        ["babel-loader", "@babel/core", "@babel/preset-env", "@babel/preset-react"],
        dev=True,
    )

    with open(".babelrc", "w") as f:
        f.write(
            """{
  "presets": ["@babel/preset-env", "@babel/preset-react"]
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
def add_react_and_express():
    add_react()
    add_express()

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


@menu_item(key="e")
def add_express():
    SERVER_INDEX_JS = "src/server/index.js"

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


if __name__ == "__main__":
    if not exists("package.json"):
        call_echo("yarn init -y")

    menu_loop()
