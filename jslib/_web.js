const puppeteer = require("puppeteer");
const fs = require("fs");

let browser;

module.exports.delay = (ms) => new Promise((res) => setTimeout(res, ms));

module.exports.openPage = async (url) => {
  if (!browser) {
    browser = await puppeteer.launch({
      headless: false,
      userDataDir: "/tmp/chrome-data-puppeteer",
    });

    let page = await browser.newPage();
    await page.goto(url, { waitUntil: "networkidle0" });
    return page;
  } else {
    return undefined;
  }
};
