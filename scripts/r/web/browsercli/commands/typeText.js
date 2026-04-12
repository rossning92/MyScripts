import { sleep, withActivePage } from "../browser-core.js";
import { DEFAULT_DELAY_MS } from "../config.js";

export async function typeText(text, ref) {
  return withActivePage(async (page) => {
    if (ref && ref.startsWith("@e")) {
      const eRef = ref.substring(1);
      const found = await page.evaluate((eRef) => {
        const el = document.querySelector(`[data-agent-ref="${eRef}"]`);
        if (el) {
          el.focus();
          return true;
        }
        return false;
      }, eRef);
      if (!found) {
        throw new Error(`Unable to find element with ref "${ref}"`);
      }
    }
    await page.keyboard.type(text);
    await sleep(DEFAULT_DELAY_MS);
  });
}
