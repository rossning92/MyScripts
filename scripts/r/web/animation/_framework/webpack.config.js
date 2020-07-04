const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const path = require("path");
const fs = require("fs");

const plugins = [
  new MiniCssExtractPlugin({
    filename: "style.css",
  }),
];

// Setup HtmlWebpackPlugin for all found entries. Automatically search all
// files under `./src/pages` folder and added as webpack entries.
const entries = {};

function addEntry(file) {
  const name = path.basename(file, ".js");
  entries[name] = file;

  plugins.push(
    new HtmlWebpackPlugin({
      filename: name + ".html",
      template: path.resolve(__dirname, "index.html"),
      chunks: [name],
      title: name,
    })
  );
}

module.exports = (env) => {
  if (env && env.entry) {
    addEntry(env.entry);
  } else {
    // The folder that contains source code and resource files (images, videos,
    // etc.)
    const entryFolders = [path.resolve(__dirname, "pages")];
    entryFolders.forEach((dir) => {
      fs.readdirSync(dir).forEach((file) => {
        if (path.extname(file).toLowerCase() !== ".js") {
          return;
        }

        const fullPath = path.join(dir, file);
        addEntry(fullPath);
      });
    });
  }

  return {
    entry: entries,
    plugins: plugins,
    module: {
      rules: [
        {
          test: /\.css$/i,
          use: [MiniCssExtractPlugin.loader, "css-loader"],
        },
      ],
    },
    mode: "development",
    resolve: {
      modules: [
        path.resolve(__dirname, "src"),
        path.resolve(__dirname, "node_modules"),
        "node_modules",
      ],
    },
  };
};
