const puppeteer = require("puppeteer");
const fs = require("fs");

const delay = (ms) => new Promise((res) => setTimeout(res, ms));

module.exports.openPage = async (url) => {
  let data = [];

  const browser = await puppeteer.launch({
    headless: false,
    userDataDir: "/tmp/chrome-data-puppeteer",
  });
  const page = await browser.newPage();

  await page.goto(url);

  return page;
};
