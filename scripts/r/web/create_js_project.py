from _shutil import *
import pathlib

cd("~")
project_dir = os.path.realpath(r"{{JS_PROJECT_DIR}}")
cd(project_dir)
print("Project dir: %s" % project_dir)


@menu_item(key="w")
def add_webpack():
    call_echo(
        "yarn add webpack webpack-cli webpack-dev-server html-webpack-plugin --dev"
    )

    config_file = "webpack.config.js"
    if not os.path.exists(config_file):
        with open(config_file, "w") as f:
            f.write(
                """var HtmlWebpackPlugin = require('html-webpack-plugin');
var path = require('path');

module.exports = {
entry: './src/index.js',
output: {
    path: path.resolve(__dirname, './dist'),
    filename: 'index_bundle.js'
},
plugins: [new HtmlWebpackPlugin()],
devServer: {
    contentBase: path.join(__dirname, 'dist'),
    open: true
}
};"""
            )

    if not os.path.exists("src/index.js"):
        os.makedirs("src", exist_ok=True)
        pathlib.Path("src/index.js").touch()

    webpack_start()


def webpack_start():
    os.environ["PATH"] += os.pathsep + os.path.join(project_dir, "node_modules", ".bin")
    threading.Thread(
        target=lambda: call_echo("webpack serve --mode development")
    ).start()


@menu_item(key="r")
def add_react():
    if os.path.exists("package.json"):
        with open("package.json", "r") as f:
            s = f.read()

        if "react-scripts start" in s:
            call_echo("yarn start")
            return

        else:
            print2("package.json will be removed (y/n)", color="green")
            ch = getch()
            if ch != "y":
                return
            os.remove("package.json")

    # https://create-react-app.dev/docs/getting-started/
    call_echo("yarn create react-app .")


@menu_item(key="d")
def add_dat_gui():
    call_echo("yarn add dat.gui")


@menu_item(key="p")
def add_p5():
    call_echo("yarn add p5")


@menu_item(key="b")
def add_bootstrap():
    call_echo("yarn add react-bootstrap bootstrap")


if __name__ == "__main__":
    if not exists("package.json"):
        call_echo("yarn init")

    menu_loop()

