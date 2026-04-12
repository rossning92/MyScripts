import { withActivePage, refToSelector } from "../browser-core.js";

export async function check(ref) {
  return withActivePage(async (page) => {
    const selector = refToSelector(ref);
    await page.check(selector);
  });
}

export async function uncheck(ref) {
  return withActivePage(async (page) => {
    const selector = refToSelector(ref);
    await page.uncheck(selector);
  });
}
