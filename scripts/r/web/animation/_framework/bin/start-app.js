const WebpackDevServer = require("webpack-dev-server");
const webpack = require("webpack");
const process = require("process");
const path = require("path");

const config = require("../webpack.config.js")({
  entry: process.env.ENTRY,
  entryFolder: process.env.ENTRY_FOLDER,
});

const compiler = webpack(config);

const server = new WebpackDevServer(compiler, {
  open: false,
  contentBase: process.env.ENTRY
    ? path.dirname(process.env.ENTRY)
    : process.env.ENTRY_FOLDER,
});

server.listen(8080, "localhost", () => {
  console.log("dev server listening on port 8080");
});
