import { getBrowser } from "../browser-core.js";

export async function close() {
  const browser = await getBrowser();
  await browser.close();
}
