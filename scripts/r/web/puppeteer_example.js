const os = require("os");
const puppeteer = require("puppeteer");
const path = require("path");

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
    userDataDir: path.join(os.homedir(), "puppeteer-chromium-data-dir"),
    // executablePath:
    //   "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    // userDataDir: path.join(os.homedir(), "ChromeData2"),
  });
  const page = await browser.newPage();
  await page.goto("https://www.google.com");
})();
