import { runAction, sleep, withActivePage } from "../browser-core.js";

export async function click(text) {
  return withActivePage(async (page) => {
    if (text.startsWith("@e")) {
      const ref = text.substring(1);
      const found = await page.evaluate((ref) => {
        const el = document.querySelector(`[data-agent-ref="${ref}"]`);
        if (el) {
          el.scrollIntoView({ block: "center", inline: "center" });
          return true;
        }
        return false;
      }, ref);

      if (!found) {
        throw new Error(`Unable to find element with ref "${text}"`);
      }

      await sleep(500); // Wait for scroll

      const rect = await page.evaluate((ref) => {
        const el = document.querySelector(`[data-agent-ref="${ref}"]`);
        const { left, top, width, height } = el.getBoundingClientRect();
        return { left, top, width, height };
      }, ref);

      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      await page.mouse.click(centerX, centerY);
      return;
    }

    const start = Date.now();
    let found = false;
    while (Date.now() - start < 5 * 1000) {
      found = await page.evaluate(runAction, { type: "scrollIntoView", text });
      if (found) break;
      await sleep(500);
    }

    if (!found) {
      throw new Error(`Unable to find clickable el with text "${text}"`);
    }

    const clickables = await page.evaluate(runAction, {
      type: "getClickables",
    });

    if (clickables) {
      const match =
        clickables.find(({ text: elementText }) => elementText === text) ||
        clickables.find(({ text: elementText }) => elementText.includes(text));

      if (!match) {
        throw new Error(`Unable to find clickable el with text "${text}"`);
      }

      const { rect } = match;
      const centerX = rect.left + (rect.right - rect.left) / 2;
      const centerY = rect.top + (rect.bottom - rect.top) / 2;
      await page.mouse.click(centerX, centerY);
      return;
    }
  });
}
