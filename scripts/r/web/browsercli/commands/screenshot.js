import path from "path";
import os from "os";
import { withActivePage } from "../browser-core.js";

export async function screenshot(filePath) {
  return withActivePage(async (page) => {
    if (!filePath) {
      filePath = path.join(os.tmpdir(), `browsercli-screenshot-${Date.now()}.png`);
    }
    await page.screenshot({ path: filePath, fullPage: false });
    return filePath;
  });
}
