import { launchOrConnectBrowser } from "../browser-core.js";

export async function closeBrowser() {
  const browser = await launchOrConnectBrowser();
  await browser.close();
}
