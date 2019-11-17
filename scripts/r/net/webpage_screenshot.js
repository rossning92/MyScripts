const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.setViewport({
    width: 1920 / 1.5,
    height: 1080 / 1.5,
    deviceScaleFactor: 1.5,
  });
  await page.goto('https://google.com');
  await page.screenshot({ path: 'example.png' });

  await browser.close();

  const exec = require('child_process').exec;
  exec('start example.png');
})();
