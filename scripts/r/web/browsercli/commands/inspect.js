import { createServer } from "http";
import { readFileSync } from "fs";
import { spawn } from "child_process";
import { getOrOpenPage, launchOrConnectBrowser } from "../browser-core.js";
import { DEBUG_PORT } from "../config.js";

export async function inspect(url) {
  const browser = await launchOrConnectBrowser();
  try {
    if (url) {
      await getOrOpenPage(browser, url);
    }
    const res = await fetch(`http://127.0.0.1:${DEBUG_PORT}/json`);
    const json = await res.json();
    const page = json.find((t) => t.type === "page");
    if (page && page.webSocketDebuggerUrl) {
      const html = readFileSync(
        new URL("screencast.html", import.meta.url),
        "utf-8"
      );
      const server = createServer((req, res) => {
        res.writeHead(200, { "Content-Type": "text/html" });
        res.end(html);
      });
      await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
      const port = server.address().port;
      const viewerUrl = `http://127.0.0.1:${port}?ws=${encodeURIComponent(page.webSocketDebuggerUrl)}`;
      const opener =
        process.platform === "win32"
          ? "start"
          : process.platform === "darwin"
            ? "open"
            : "xdg-open";
      spawn(opener, [viewerUrl], {
        detached: true,
        stdio: "ignore",
        shell: process.platform === "win32",
      }).unref();
      // Keep server alive for a bit to serve the page, then close
      setTimeout(() => server.close(), 5000);
    }
  } finally {
    browser.disconnect();
  }
}
