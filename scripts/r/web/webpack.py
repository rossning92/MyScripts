from _shutil import *
import pathlib

proj_dir = r"{{_PROJ_PATH}}"
print(proj_dir)
os.chdir(proj_dir)

call_echo("yarn add webpack webpack-cli webpack-dev-server html-webpack-plugin --dev")

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
    contentBase: path.join(__dirname, 'dist')
  }
};"""
        )

os.environ["PATH"] += os.pathsep + os.path.join(proj_dir, "node_modules", ".bin")

if not os.path.exists("src/index.js"):
    os.makedirs("src", exist_ok=True)
    pathlib.Path("src/index.js").touch()

# call_echo("webpack --mode development")
call_echo("webpack-dev-server --mode development --open")

