const WebpackDevServer = require("webpack-dev-server");
const webpack = require("webpack");
const process = require("process");
const path = require("path");

const config = require("../webpack.config.js")({
  entry: process.env.ENTRY,
});

const compiler = webpack(config);

const server = new WebpackDevServer(compiler, {
  open: false,
  contentBase: process.env.ENTRY
    ? path.dirname(process.env.ENTRY)
    : path.join(__dirname, "pages"),
});

server.listen(8080, "localhost", () => {
  if (process.env.ENTRY) {
    const url =
      "http://localhost:8080/" +
      path.basename(process.env.ENTRY, ".js") +
      ".html";

    // const start =
    //   process.platform == "darwin"
    //     ? "open"
    //     : process.platform == "win32"
    //     ? "start"
    //     : "xdg-open";
    // require("child_process").exec(start + " " + url);
  }
});
