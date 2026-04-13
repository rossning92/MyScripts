import { createServer } from "http";
import { readFileSync } from "fs";
import { spawn, spawnSync } from "child_process";
import { getOrOpenPage, launchOrConnectBrowser } from "../browser-core.js";
import { DEBUG_PORT } from "../config.js";

export async function inspect(url) {
  const browser = await launchOrConnectBrowser();
  try {
    if (url) {
      await getOrOpenPage(browser, url);
    }

    const htmlContent = readFileSync(
      new URL("screencast.html", import.meta.url),
      "utf-8"
    );

    const port = DEBUG_PORT + 1;

    // Kill existing server by sending a quit request
    try {
      await fetch(`http://127.0.0.1:${port}/quit`, { signal: AbortSignal.timeout(500) });
      await new Promise((resolve) => setTimeout(resolve, 200));
    } catch (e) {
      // Ignore errors if server is not running
    }

    const serverCode = `
      const http = require('http');
      const server = http.createServer(async (req, res) => {
        if (req.url === '/quit') {
          res.end('ok');
          process.exit(0);
        }
        if (req.url === '/active-ws') {
          try {
            const r = await fetch('http://127.0.0.1:${DEBUG_PORT}/json');
            const targets = await r.json();
            const page = targets.find(t => t.type === 'page');
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ ws: page ? page.webSocketDebuggerUrl : null }));
          } catch (e) {
            res.writeHead(500);
            res.end('error');
          }
          return;
        }
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(${JSON.stringify(htmlContent)});
      });
      server.on('error', () => process.exit(1));
      server.listen(${port}, '127.0.0.1');
    `;

    spawn("node", ["-e", serverCode], {
      detached: true,
      stdio: "ignore",
    }).unref();

    await new Promise((resolve) => setTimeout(resolve, 500));

    const viewerUrl = `http://127.0.0.1:${port}`;
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

    console.log(`Screencast viewer opened at: ${viewerUrl}`);
  } finally {
    browser.disconnect();
  }
}
