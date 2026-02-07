import { extractMostDirectChildren, withActivePage } from "../browser-core.js";

export async function scrape(filters) {
  return withActivePage(async (page) => {
    const children = await page.evaluate(extractMostDirectChildren, filters);
    console.log(JSON.stringify(children, null, 2));
  });
}
