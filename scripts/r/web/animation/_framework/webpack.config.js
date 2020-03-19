const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const path = require("path");
const fs = require("fs");

const plugins = [
  new MiniCssExtractPlugin({
    filename: "style.css"
  })
];

module.exports = env => {
  // The folder that contains source code and resource files (images, videos,
  // etc.)
  let entryFolder = path.resolve(__dirname, "pages");
  if (env && env.entryFolder) {
    entryFolder = env.entryFolder;
  }

  // Setup HtmlWebpackPlugin for all found entries. Automatically search all
  // files under `./src/pages` folder and added as webpack entries.
  const entries = {};

  fs.readdirSync(entryFolder).forEach(file => {
    if (path.extname(file).toLowerCase() !== ".js") {
      return;
    }

    const file_path = entryFolder + "/" + file;
    const name = path.basename(file, ".js");
    entries[name] = file_path;

    plugins.push(
      new HtmlWebpackPlugin({
        filename: name + ".html",
        template: path.resolve(__dirname, "index.html"),
        chunks: [name]
      })
    );
  });

  return {
    entry: entries,
    plugins: plugins,
    module: {
      rules: [
        {
          test: /\.css$/i,
          use: [MiniCssExtractPlugin.loader, "css-loader"]
        }
      ]
    },
    mode: "development",
    devServer: {
      contentBase: entryFolder
    },
    resolve: {
      modules: [
        path.resolve(__dirname, "src"),
        path.resolve(__dirname, "node_modules"),
        "node_modules"
      ]
    }
  };
};
