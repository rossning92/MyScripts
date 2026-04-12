import { withActivePage, refToSelector } from "../browser-core.js";

export async function select(ref, value) {
  return withActivePage(async (page) => {
    const selector = refToSelector(ref);
    await page.selectOption(selector, value);
  });
}
