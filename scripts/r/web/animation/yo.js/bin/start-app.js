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
  contentBase: [
    process.env.CONTENT_BASE
      ? process.env.CONTENT_BASE
      : path.dirname(animationScript),
    path.resolve(__dirname, "../node_modules/ccapture.js/build"),
  ],
  stats: "minimal",
  open: true,
  openPage: path.basename(animationScript, ".js") + ".html",
});

server.listen();
