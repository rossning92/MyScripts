#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const process = require("process");

const argv = require("minimist")(process.argv.slice(2));
const puppeteer = require("puppeteer");
const webpack = require("webpack");
const WebpackDevServer = require("webpack-dev-server");

const mdFile = argv["i"] ? path.resolve(argv["i"]) : undefined;
const template = argv["t"]; // template file
const public = argv["public"]; // public content base dir
const dev = argv["d"];
const port = argv["p"];

process.chdir(__dirname);

const webpackConfig = require("./webpack.config.js")({
  mdFile,
  template,
  public,
  dev,
});
const compiler = webpack(webpackConfig);

const server = new WebpackDevServer(compiler, webpackConfig.devServer);

async function captureImageAndExit(port) {
  const browser = await puppeteer.launch({
    headless: !dev,
    defaultViewport: { width: 1920, height: 1080 },
    args: [
      // "--no-sandbox",
      // "--disable-setuid-sandbox",
      "--enable-font-antialiasing",
      "--font-render-hinting=max",
      "--force-device-scale-factor=1",
    ],
  });
  const page = await browser.newPage();
  await page.goto(`http://localhost:${port}`, { waitUntil: "networkidle0" });

  // Screenshot DOM element only
  const element = await page.$(".container");

  const outFile = path.resolve(argv["o"]);
  await element.screenshot({ path: outFile, omitBackground: true });

  await browser.close();
  server.close();
  process.exit();
}

(async () => {
  server.listen(port, "localhost", async (err) => {
    if (err) return;

    const port = server.listeningApp.address().port;

    if (!dev) {
      captureImageAndExit(port);
    }
  });
})();
