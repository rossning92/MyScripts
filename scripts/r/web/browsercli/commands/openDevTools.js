import { spawn } from "child_process";
import { getOrOpenPage, launchOrConnectBrowser } from "../browser-core.js";
import { DEBUG_PORT } from "../config.js";

export async function openDevTools(url) {
  const browser = await launchOrConnectBrowser();
  try {
    if (url) {
      await getOrOpenPage(browser, url);
    }
    const res = await fetch(`http://127.0.0.1:${DEBUG_PORT}/json`);
    const json = await res.json();
    const page = json.find((t) => t.type === "page");
    if (page && page.devtoolsFrontendUrl) {
      const opener =
        process.platform === "win32"
          ? "start"
          : process.platform === "darwin"
            ? "open"
            : "xdg-open";
      spawn(opener, [page.devtoolsFrontendUrl], {
        detached: true,
        stdio: "ignore",
        shell: process.platform === "win32",
      }).unref();
    }
  } finally {
    browser.disconnect();
  }
}
