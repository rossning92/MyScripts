const puppeteer = require("puppeteer");
const fs = require("fs");

let browser;
let page;

module.exports.delay = (ms) => new Promise((res) => setTimeout(res, ms));

module.exports.openPage = async (url) => {
  if (!browser) {
    browser = await puppeteer.launch({
      headless: false,
      userDataDir: "/tmp/chrome-data-puppeteer",
    });

    page = await browser.newPage();
  }

  await page.goto(url);

  return page;
};
