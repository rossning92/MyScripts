import path from "path";
import { withActivePage, refToSelector } from "../browser-core.js";

export async function upload(ref, filePath) {
  return withActivePage(async (page) => {
    const selector = refToSelector(ref);
    if (!selector) {
      throw new Error(`Invalid ref: "${ref}"`);
    }

    const absolutePath = path.resolve(filePath);

    const el = await page.$(selector);
    if (!el) {
      throw new Error(`Unable to find element with ref "${ref}"`);
    }

    await el.uploadFile(absolutePath);
  });
}
