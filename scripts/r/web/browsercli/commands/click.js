import { sleep, withActivePage, refToSelector } from "../browser-core.js";

export async function click(ref) {
  return withActivePage(async (page) => {
    const selector = refToSelector(ref);
    if (!selector) {
      throw new Error(`Invalid ref: "${ref}"`);
    }

    const found = await page.evaluate((sel) => {
      const el = document.querySelector(sel);
      if (el) {
        el.scrollIntoView({ block: "center", inline: "center" });
        return true;
      }
      return false;
    }, selector);

    if (!found) {
      throw new Error(`Unable to find element with ref "${ref}"`);
    }

    await sleep(500); // Wait for scroll

    const rect = await page.evaluate((sel) => {
      const el = document.querySelector(sel);
      const { left, top, width, height } = el.getBoundingClientRect();
      return { left, top, width, height };
    }, selector);

    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    await page.mouse.click(centerX, centerY);
  });
}
