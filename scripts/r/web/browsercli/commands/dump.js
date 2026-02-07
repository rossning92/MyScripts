import { runAction, withActivePage } from "../browser-core.js";

export async function dump() {
  return withActivePage(async (page) => {
    const clickableElements = await page.evaluate(runAction, {
      type: "getClickables",
    });
    clickableElements.forEach((el) => {
      const rect = [
        Math.round(el.rect.left),
        Math.round(el.rect.top),
        Math.round(el.rect.right - el.rect.left),
        Math.round(el.rect.bottom - el.rect.top),
      ];
      console.log(
        `text="\x1b[33m${el.text}\x1b[0m"  rect=[${rect.join(", ")}]`,
      );
    });
  });
}
