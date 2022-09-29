const HtmlWebpackPlugin = require("html-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const path = require("path");
const webpack = require("webpack");

module.exports = ({
  template = "markdown",
  mdFile = "./example.md",
  public = undefined,
  dev = false,
}) => {
  const mdFileDir = path.dirname(path.resolve(mdFile));

  const contentBase = [
    path.resolve(__dirname, "public"),
    path.resolve(__dirname, "node_modules"),
    mdFileDir,
  ];
  if (public !== undefined) {
    contentBase.push(public);
  }

  return {
    mode: "development",
    entry: `./src/index.js`,
    output: {
      path: path.resolve(__dirname, "./dist"),
      filename: "index_bundle.js",
    },
    plugins: [
      new HtmlWebpackPlugin({ template: "src/index.html" }),
      new MiniCssExtractPlugin(),
      new webpack.DefinePlugin({
        template: JSON.stringify(template),
        markdownFile: JSON.stringify(mdFile),
        dev: JSON.stringify(dev),
      }),
    ],
    devServer: {
      contentBase,
      // open: true,
      // watchContentBase: true,
      hot: true,
      stats: "minimal",
    },
    module: {
      rules: [
        {
          test: /\.css$/,
          use: [
            MiniCssExtractPlugin.loader, // instead of style-loader
            "css-loader",
          ],
        },
        {
          test: /\.(html|md)$/,
          loader: "raw-loader",
        },
        {
          test: /\.(png|svg|jpg|jpeg|gif)$/i,
          type: "asset/resource",
        },
      ],
    },
    optimization: {
      removeAvailableModules: false,
      removeEmptyChunks: false,
      splitChunks: false,
    },
  };
};
