import { sleep, withActivePage } from "../browser-core.js";
import { DEFAULT_DELAY_MS } from "../config.js";

export async function fill(text, ref) {
  return withActivePage(async (page) => {
    let selector = null;
    if (ref && ref.startsWith("@e")) {
      const eRef = ref.substring(1);
      selector = `[data-agent-ref="${eRef}"]`;
    }

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
    
    await sleep(DEFAULT_DELAY_MS);
  });
}
