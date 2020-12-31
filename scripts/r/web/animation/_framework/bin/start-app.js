const WebpackDevServer = require("webpack-dev-server");
const webpack = require("webpack");
const process = require("process");
const path = require("path");
const argv = require("minimist")(process.argv.slice(2));

animationScript = argv["_"][0];

const config = require("../webpack.config.js")({
  entry: animationScript,
});

const compiler = webpack(config);

const server = new WebpackDevServer(compiler, {
  open: false,
  contentBase: process.env.CONTENT_BASE
    ? process.env.CONTENT_BASE
    : path.dirname(animationScript),
});

server.listen(8080, "localhost", () => {
  if (animationScript) {
    const url =
      "http://localhost:8080/" +
      path.basename(animationScript, ".js") +
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
