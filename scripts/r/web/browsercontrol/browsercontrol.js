import { getOrOpenPage, launchOrConnectBrowser } from "./browser-core.js";
import { click } from "./commands/click.js";
import { closeAllPages } from "./commands/closeAllPages.js";
import { closeBrowser } from "./commands/closeBrowser.js";
import { dump } from "./commands/dump.js";
import { getAriaSnapshot } from "./commands/getAriaSnapshot.js";
import { getMarkdown } from "./commands/getMarkdown.js";
import { getText } from "./commands/getText.js";
import { openDevTools } from "./commands/openDevTools.js";
import { pressKey } from "./commands/pressKey.js";
import { scrape } from "./commands/scrape.js";
import { scrollToBottom } from "./commands/scrollToBottom.js";
import { typeText } from "./commands/typeText.js";

function showHelp() {
  console.log("Usage:");
  console.log("  node browsercontrol.js open <url>");
  console.log("  node browsercontrol.js close-pages");
  console.log("  node browsercontrol.js close-browser");
  console.log("  node browsercontrol.js get-text [url]");
  console.log("  node browsercontrol.js get-markdown [url]");
  console.log("  node browsercontrol.js get-aria-snapshot");
  console.log("  node browsercontrol.js scroll-bottom");
  console.log("  node browsercontrol.js click <text>");
  console.log("  node browsercontrol.js type <text>");
  console.log("  node browsercontrol.js press <key>");
  console.log("  node browsercontrol.js dump");
  console.log("  node browsercontrol.js debug [url]");
  console.log("  node browsercontrol.js scrape [--filter <class> ...]");
}

const args = process.argv.slice(2);
if (args.length === 2 && args[0] === "open") {
  const url = args[1];
  const browser = await launchOrConnectBrowser();
  await getOrOpenPage(browser, url);
  browser.disconnect();
  process.exit(0);
}

if (args.length === 1 && args[0] === "close-pages") {
  await closeAllPages();
  process.exit(0);
}

if (args.length === 1 && args[0] === "close-browser") {
  await closeBrowser();
  process.exit(0);
}

if ((args.length === 1 || args.length === 2) && args[0] === "get-text") {
  const text = await getText(args[1]);
  console.log(text);
  process.exit(0);
}

if ((args.length === 1 || args.length === 2) && args[0] === "get-markdown") {
  const markdown = await getMarkdown(args[1]);
  console.log(markdown);
  process.exit(0);
}

if (args.length === 1 && args[0] === "get-aria-snapshot") {
  const text = await getAriaSnapshot();
  console.log(text);
  process.exit(0);
}

if (args.length === 1 && args[0] === "scroll-bottom") {
  await scrollToBottom();
  process.exit(0);
}

if (args.length === 2 && args[0] === "press") {
  await pressKey(args[1]);
  process.exit(0);
}

if (args.length === 2 && args[0] === "click") {
  await click(args[1]);
  process.exit(0);
}

if (args.length === 2 && args[0] === "type") {
  await typeText(args[1]);
  process.exit(0);
}

if (args.length === 1 && args[0] === "dump") {
  await dump(args[1]);
  process.exit(0);
}

if (args[0] === "debug") {
  const url = args.slice(1).find((arg) => !arg.startsWith("--"));
  await openDevTools(url);
  process.exit(0);
}

if (args.length >= 1 && args[0] === "scrape") {
  const filtersIndex = args.findIndex((arg) => arg === "--filter");
  const filters =
    filtersIndex !== -1
      ? args.slice(filtersIndex + 1).filter(Boolean)
      : undefined;
  await scrape(filters);
  process.exit(0);
}

showHelp();
process.exit(1);
