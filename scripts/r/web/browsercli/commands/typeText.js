import { withActivePage, refToSelector } from "../browser-core.js";

export async function typeText(text, ref) {
  return withActivePage(async (page) => {
    if (ref) {
      const selector = refToSelector(ref);
      if (!selector) {
        throw new Error(`Invalid ref: "${ref}"`);
      }
      const found = await page.evaluate((sel) => {
        const el = document.querySelector(sel);
        if (el) {
          el.focus();
          return true;
        }
        return false;
      }, selector);
      if (!found) {
        throw new Error(`Unable to find element with ref "${ref}"`);
      }
    }
    await page.keyboard.type(text);
  });
}
