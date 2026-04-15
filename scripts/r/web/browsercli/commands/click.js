import { sleep, withActivePage, refToSelector } from "../browser-core.js";
import { POST_CLICK_DELAY } from "../config.js";

export async function click(ref) {
  return withActivePage(async (page) => {
    const selector = refToSelector(ref);
    if (!selector) {
      throw new Error(`Invalid ref: "${ref}"`);
    }

    // Try normal DOM first, then deep search through shadow roots
    const rect = await page.evaluate((sel) => {
      function deepQuery(root, s) {
        const el = root.querySelector(s);
        if (el) return el;
        for (const host of root.querySelectorAll("*")) {
          if (host.shadowRoot) {
            const found = deepQuery(host.shadowRoot, s);
            if (found) return found;
          }
        }
        return null;
      }
      const el = deepQuery(document, sel);
      if (!el) return null;
      el.scrollIntoView({ block: "center", inline: "center" });
      const { left, top, width, height } = el.getBoundingClientRect();
      return { left, top, width, height };
    }, selector);

    if (!rect) {
      throw new Error(`Unable to find element with ref "${ref}"`);
    }

    await sleep(500); // Wait for scroll

    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    await page.mouse.click(centerX, centerY);

    // Wait briefly to allow any beforeunload/leave-site dialogs to be auto-accepted
    await sleep(POST_CLICK_DELAY);
  });
}
