const WebpackDevServer = require("webpack-dev-server");
const webpack = require("webpack");
const process = require("process");

const config = require("../webpack.config.js")({
  entryFolder: process.env.ENTRY_FOLDER,
  entry: process.env.ENTRY,
});

const compiler = webpack(config);
const server = new WebpackDevServer(compiler, {
  open: false
});

server.listen(8080, "localhost", () => {
  console.log("dev server listening on port 8080");
});
