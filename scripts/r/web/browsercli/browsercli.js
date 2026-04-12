import { program } from "commander";
import { getOrOpenPage, launchOrConnectBrowser } from "./browser-core.js";
import { click } from "./commands/click.js";
import { closeAllPages } from "./commands/closeAllPages.js";
import { closeBrowser } from "./commands/closeBrowser.js";
import { dump } from "./commands/dump.js";
import { fill } from "./commands/fill.js";
import { getAriaSnapshot } from "./commands/getAriaSnapshot.js";
import { getMarkdown } from "./commands/getMarkdown.js";
import { getText } from "./commands/getText.js";
import { openDevTools } from "./commands/openDevTools.js";
import { pressKey } from "./commands/pressKey.js";
import { scrape } from "./commands/scrape.js";
import { scrollToBottom } from "./commands/scrollToBottom.js";
import { snapshot } from "./commands/snapshot.js";
import { typeText } from "./commands/typeText.js";

program
  .name("browsercli")
  .description("CLI to control browser via Playwright")
  .version("1.0.0");

program
  .command("open")
  .description("Open a URL or connect to an existing browser")
  .argument("[url]", "URL to open")
  .action(async (url) => {
    const browser = await launchOrConnectBrowser();
    await getOrOpenPage(browser, url);
    browser.disconnect();
  });

program
  .command("close-pages")
  .description("Close all pages")
  .action(async () => {
    await closeAllPages();
  });

program
  .command("close-browser")
  .description("Close the browser")
  .action(async () => {
    await closeBrowser();
  });

program
  .command("get-text")
  .description("Get text from a page")
  .argument("[url]", "URL to get text from")
  .action(async (url) => {
    const text = await getText(url);
    console.log(text);
  });

program
  .command("get-markdown")
  .description("Get markdown content from a page")
  .argument("[url]", "URL to get markdown from")
  .action(async (url) => {
    const markdown = await getMarkdown(url);
    console.log(markdown);
  });

program
  .command("get-aria-snapshot")
  .description("Get ARIA snapshot of the current page")
  .action(async () => {
    const text = await getAriaSnapshot();
    console.log(text);
  });

program
  .command("snapshot")
  .description("Get a snapshot of the page with indices for interactive elements")
  .action(async () => {
    const text = await snapshot();
    console.log(text);
  });

program
  .command("scroll-bottom")
  .description("Scroll to the bottom of the page")
  .action(async () => {
    await scrollToBottom();
  });

program
  .command("click")
  .description("Click on an element with the specified text")
  .argument("<text>", "Text to click")
  .action(async (text) => {
    await click(text);
  });

program
  .command("type")
  .description("Type text into the focused element or a specific element ref")
  .argument("<text>", "Text to type")
  .argument("[ref]", "Element ref to type into (e.g., @e1)")
  .action(async (text, ref) => {
    await typeText(text, ref);
  });

program
  .command("fill")
  .description("Clear and type text into a specific element ref")
  .argument("<text>", "Text to fill")
  .argument("<ref>", "Element ref to fill (e.g., @e1)")
  .action(async (text, ref) => {
    await fill(text, ref);
  });

program
  .command("press")
  .description("Press a key")
  .argument("<key>", "Key to press")
  .action(async (key) => {
    await pressKey(key);
  });

program
  .command("dump")
  .description("Dump page content")
  .action(async () => {
    await dump();
  });

program
  .command("debug")
  .description("Open DevTools")
  .argument("[url]", "URL to debug")
  .action(async (url) => {
    await openDevTools(url);
  });

program
  .command("scrape")
  .description("Scrape content with optional filters")
  .option("-f, --filter <classes...>", "CSS classes to filter")
  .action(async (options) => {
    await scrape(options.filter);
  });

await program.parseAsync(process.argv);
