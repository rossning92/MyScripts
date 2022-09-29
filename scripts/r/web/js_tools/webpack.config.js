const HtmlWebpackPlugin = require("html-webpack-plugin");
const path = require("path");

module.exports = {
  entry: "./{{index_js}}",
  output: {
    path: path.resolve(__dirname, "./{{build_dir}}"),
    filename: "index_bundle.js",
  },
  plugins: [new HtmlWebpackPlugin()],
  devServer: {
    static: {
      directory: path.join(__dirname, "docs"),
    },
    compress: true,
    open: true,
    port: 3000,
    proxy: {
      "/api": "http://localhost:8080",
    },
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
      },
    ],
  },
};
