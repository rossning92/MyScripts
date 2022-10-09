import { launch } from "puppeteer";

let browser;
let page;

export function delay(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

export async function openPage(url) {
  if (!browser) {
    browser = await launch({
      headless: false,
      userDataDir: "/tmp/chrome-data-puppeteer",
      executablePath:
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
      defaultViewport: {
        width: 1280,
        height: 800,
      },
    });

    page = await browser.newPage();
    await page.goto(url, { waitUntil: "networkidle0" });
    return page;
  } else {
    return undefined;
  }
}

export async function waitForText(text, { timeout = 3000 } = {}) {
  try {
    await page.waitForFunction(
      (text) =>
        document.querySelector("body")
          ? document.querySelector("body").innerText.includes(text)
          : false,
      { timeout },
      text
    );
    console.log(`Found text '${text}'`);
    return true;
  } catch (e) {
    console.log(`waitForText('${text}') timeout.`);
    return false;
  }
}

export async function clickLinkByText(page, text) {
  console.log(`Click link ${text}...`);
  const linkXPath = `//a[contains(., '${text}')]`;
  await page.waitForXPath(linkXPath);

  const [link] = await page.$x(linkXPath);
  await page.evaluate((link) => link.scrollIntoView(), link);
  await link.click();
}
