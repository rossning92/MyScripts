import { runAction, sleep, withActivePage } from "../browser-core.js";

export async function click(text) {
  return withActivePage(async (page) => {
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
