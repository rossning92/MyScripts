const HtmlWebpackPlugin = require("html-webpack-plugin");
const path = require("path");

module.exports = {
  entry: "./{{index_js}}",
  mode: "production",
  output: {
    path: path.resolve(__dirname, "./{{build_dir}}"),
    filename: "index_bundle.js",
  },
  plugins: [new HtmlWebpackPlugin()],
  devServer: {
    contentBase: path.join(__dirname, "{{build_dir}}"),
    open: true,
    port: 3000,
    proxy: {
      "/api": "http://localhost:8080",
    },
    watchContentBase: true,
    hot: true,
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
