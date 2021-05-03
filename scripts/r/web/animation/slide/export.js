#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const process = require("process");

const argv = require("minimist")(process.argv.slice(2));
const puppeteer = require("puppeteer");
const webpack = require("webpack");
const WebpackDevServer = require("webpack-dev-server");

const mdFile = argv["i"] ? path.resolve(argv["i"]) : undefined;
const template = argv["t"];
const dev = argv["d"];

const webpackConfig = require("./webpack.config.js")({
  mdFile,
  template,
});
const compiler = webpack(webpackConfig);

if (dev) {
  webpackConfig.devServer.open = true;
}

const server = new WebpackDevServer(compiler, webpackConfig.devServer);

async function captureImage(port) {
  const outFile = path.resolve(argv["o"]);

  const browser = await puppeteer.launch({
    // headless: false,
    // defaultViewport: { width: 1920, height: 1080 },
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
  const element = await page.$("#content");
  await element.screenshot({ path: outFile, omitBackground: true });

  await browser.close();

  server.close();

  process.exit();
}

(async () => {
  server.listen(undefined, "localhost", async (err) => {
    if (err) return;

    if (!dev) {
      const port = server.listeningApp.address().port;
      captureImage(port);
    }
  });
})();
