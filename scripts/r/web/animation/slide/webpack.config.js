const HtmlWebpackPlugin = require("html-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const path = require("path");
const webpack = require("webpack");

module.exports = ({ markdown }) => {
  return {
    mode: "development",
    entry: "./src/index.js",
    output: {
      path: path.resolve(__dirname, "./dist"),
      filename: "index_bundle.js",
    },
    plugins: [
      new HtmlWebpackPlugin({ template: "src/markdown.html" }),
      new MiniCssExtractPlugin(),
      new webpack.DefinePlugin({
        MARKDOWN: JSON.stringify(markdown),
      }),
    ],
    devServer: {
      contentBase: path.join(__dirname, "dist"),
      open: true,
      watchContentBase: true,
      hot: true,
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
      ],
    },
  };
};
