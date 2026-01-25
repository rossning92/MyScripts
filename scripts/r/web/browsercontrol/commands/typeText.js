import { sleep, withActivePage } from "../browser-core.js";
import { DEFAULT_DELAY_MS } from "../config.js";

export async function typeText(text) {
  return withActivePage(async (page) => {
    await page.keyboard.type(text);
    await sleep(DEFAULT_DELAY_MS);
  });
}
