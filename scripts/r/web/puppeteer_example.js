const os = require("os");
const puppeteer = require("puppeteer");
const path = require("path");

let page;
let browser;

(async () => {
  browser = await puppeteer.launch({
    headless: false,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
    userDataDir: path.join(os.homedir(), "puppeteer-chromium-data-dir"),
  });
  page = await browser.newPage();
})();
