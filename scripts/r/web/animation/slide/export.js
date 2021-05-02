#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const process = require("process");

const argv = require("minimist")(process.argv.slice(2));
const puppeteer = require("puppeteer");
const webpack = require("webpack");
const WebpackDevServer = require("webpack-dev-server");

const markdown = argv["i"]
  ? fs.readFileSync(argv["i"], { encoding: "utf8", flag: "r" })
  : undefined;
const outFile = path.resolve(argv["o"]);
const template = argv["t"];

const webpackConfig = require("./webpack.config.js")({
  markdown,
  template,
});
const compiler = webpack(webpackConfig);

const server = new WebpackDevServer(compiler, webpackConfig.devServer);

(async () => {
  server.listen(8181, "localhost", async (err) => {
    if (err) return;

    const browser = await puppeteer.launch({
      // headless: false,
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
    await page.goto("http://localhost:8181", { waitUntil: "networkidle0" });

    // Screenshot DOM element only
    const element = await page.$("body");
    await element.screenshot({ path: outFile, omitBackground: true });

    await browser.close();

    server.close();

    process.exit();
  });
})();
