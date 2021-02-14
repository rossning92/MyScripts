from _shutil import *
import pathlib


OVERWRITE = True


cd("~")
project_dir = os.path.realpath(r"{{JS_PROJECT_DIR}}")
cd(project_dir)
print("Project dir: %s" % project_dir)


@menu_item(key="w")
def add_webpack(index_js="src/index.js"):
    call_echo(
        "yarn add webpack webpack-cli webpack-dev-server html-webpack-plugin --dev"
    )

    webpack_config = "webpack.config.js"
    if os.path.exists(webpack_config) and OVERWRITE:
        return

    with open(webpack_config, "w") as f:
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
    open: true
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
};"""
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

    call_echo("yarn add react react-dom --dev")

    # Babel: transcompile jsx
    call_echo(
        "yarn add --dev babel-loader @babel/core @babel/preset-env @babel/preset-react"
    )

    with open(".babelrc", "w") as f:
        f.write(
            """{
  "presets": ["@babel/preset-env", "@babel/preset-react"]
}"""
        )

    mkdir(os.path.dirname(REACT_INDEX_JS))
    with open(REACT_INDEX_JS, "w") as f:
        f.write(
            """import { render } from 'react-dom';

import React, { Component } from 'react';

class App extends Component {
  render() {
    return (<h1>Hello!</h1>); 
  } 
} 
render(<App />, document.body);"""
        )

    add_script_to_package(
        "client", "webpack serve --mode development --devtool inline-source-map --hot",
    )

    call_echo("npm run client")


@menu_item(key="d")
def add_dat_gui():
    call_echo("yarn add dat.gui")


@menu_item(key="p")
def add_p5():
    call_echo("yarn add p5")


@menu_item(key="b")
def add_bootstrap():
    call_echo("yarn add react-bootstrap bootstrap")


@menu_item(key="e")
def add_express():
    SERVER_MAIN = "src/server/index.js"

    call_echo("yarn add express")
    call_echo("yarn add nodemon --dev")

    # Package.json
    with open("package.json", "r") as f:
        data = json.load(f)

    if "scripts" not in data.keys():
        data["scripts"] = {}

    data["scripts"]["server"] = "nodemon src/server/index.js"

    with open("package.json", "w") as f:
        json.dump(data, f, indent=2)

    if not os.path.exists(SERVER_MAIN) or True:
        mkdir(os.path.dirname(SERVER_MAIN))
        with open(SERVER_MAIN, "w") as f:
            f.write(
                """const express = require('express');
const os = require('os');

const app = express();

app.use(express.static('dist'));
app.get('/', (req, res) => {
res.send('Hello World!')
})

app.listen(process.env.PORT || 8080, () => console.log(`Listening on port ${process.env.PORT || 8080}!`));"""
            )


if __name__ == "__main__":
    if not exists("package.json"):
        call_echo("yarn init -y")

    menu_loop()
