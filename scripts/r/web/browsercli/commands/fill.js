import { withActivePage, refToSelector } from "../browser-core.js";

export async function fill(ref, text) {
  return withActivePage(async (page) => {
    const selector = refToSelector(ref);

    if (selector) {
      await page.focus(selector);
      // Clear the input
      await page.evaluate((sel) => {
        const el = document.querySelector(sel);
        if (el) el.value = "";
      }, selector);
      await page.type(selector, text);
    } else {
      // If no ref, we just type at current focus.
      // Clearing is hard without a selector.
      await page.keyboard.type(text);
    }

  });
}
