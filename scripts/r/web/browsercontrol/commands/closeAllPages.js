import { launchOrConnectBrowser } from "../browser-core.js";

export async function closeAllPages() {
  const browser = await launchOrConnectBrowser();
  try {
    const pages = await browser.pages();
    for (const page of pages) {
      await page.close();
    }
  } finally {
    browser.disconnect();
  }
}
