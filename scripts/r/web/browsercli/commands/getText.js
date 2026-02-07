import { withActivePage } from "../browser-core.js";

export async function getText(url) {
  return withActivePage(
    async (page) => {
      return await page.evaluate(() => {
        const el = document.getElementById("content");
        return el ? el.innerText : document.body.innerText;
      });
    },
    { url },
  );
}
