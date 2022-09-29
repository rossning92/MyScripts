const puppeteer = require("puppeteer");
const fs = require("fs");

let browser;

module.exports.delay = (ms) => new Promise((res) => setTimeout(res, ms));

module.exports.openPage = async (url) => {
  if (!browser) {
    browser = await puppeteer.launch({
      headless: false,
      userDataDir: "/tmp/chrome-data-puppeteer",
      executablePath:
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
      defaultViewport: {
        width: 1280,
        height: 800,
      },
    });

    let page = await browser.newPage();
    await page.goto(url, { waitUntil: "networkidle0" });
    return page;
  } else {
    return undefined;
  }
};
