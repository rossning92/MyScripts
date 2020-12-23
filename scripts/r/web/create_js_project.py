from _shutil import *
import pathlib

cd("~")
project_dir = os.path.realpath(r"{{JS_PROJECT_DIR}}")
cd(project_dir)
print("Project dir: %s" % project_dir)


def add_webpack(project_dir):
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


def create_react():
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


def print_help():
    print2(
        "[d] dat.gui\n"
        "[p] p5\n"
        "[w] webpack\n"
        "[b] bootstrap\n"
        "[r] react\n"
        "[h] help\n"
        "[x] exit\n"
    )


if __name__ == "__main__":
    if not exists("package.json"):
        call_echo("yarn init")

    while True:
        print_help()
        ch = getch()
        if ch == "x":
            sys.exit(0)
        elif ch == "d":
            call_echo("yarn add dat.gui")
        elif ch == "p":
            call_echo("yarn add p5")
        elif ch == "h":
            print_help()
        elif ch == "w":
            add_webpack(project_dir)
        elif ch == "b":
            call_echo("yarn add react-bootstrap bootstrap")
        elif ch == "r":
            create_react()
