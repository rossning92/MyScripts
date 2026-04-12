import { program } from "commander";
import { getOrOpenPage, launchOrConnectBrowser } from "./browser-core.js";
import { click } from "./commands/click.js";
import { closeAllPages } from "./commands/closeAllPages.js";
import { closeBrowser } from "./commands/closeBrowser.js";
import { fill } from "./commands/fill.js";
import { getMarkdown } from "./commands/getMarkdown.js";
import { getText } from "./commands/getText.js";
import { inspect } from "./commands/inspect.js";
import { pressKey } from "./commands/pressKey.js";
import { scrape } from "./commands/scrape.js";
import { scrollToBottom } from "./commands/scrollToBottom.js";
import { select } from "./commands/select.js";
import { snapshot } from "./commands/snapshot.js";
import { typeText } from "./commands/typeText.js";

program
  .name("browsercli")
  .description("CLI to control browser via Puppeteer")
  .version("1.0.0");

program
  .command("open")
  .description("Open a URL or connect to an existing browser")
  .argument("[url]", "URL to open")
  .option("--headed", "Open browser in headed mode")
  .action(async (url, options) => {
    const browser = await launchOrConnectBrowser({ headed: options.headed });
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
  .description("Click on an element by its ref (e.g. @e0, @e1)")
  .argument("<ref>", "Element ref from snapshot (e.g. @e0)")
  .action(async (ref) => {
    await click(ref);
  });

program
  .command("type")
  .description("Type text into the focused element or a specific element ref")
  .usage("[ref] <text>")
  .argument("[ref]", "Element ref to type into (e.g., @e1)")
  .argument("[text]", "Text to type")
  .action(async (ref, text) => {
    if (text === undefined) {
      await typeText(ref);
    } else {
      await typeText(text, ref);
    }
  });

program
  .command("fill")
  .description("Clear and type text into a specific element ref")
  .argument("<ref>", "Element ref to fill (e.g., @e1)")
  .argument("<text>", "Text to fill")
  .action(async (ref, text) => {
    await fill(ref, text);
  });

program
  .command("press")
  .description("Press a key")
  .argument("<key>", "Key to press")
  .action(async (key) => {
    await pressKey(key);
  });

program
  .command("select")
  .description("Select an option in a dropdown")
  .argument("<ref>", "Element ref of the select element (e.g. @e0)")
  .argument("<val>", "Value to select")
  .action(async (ref, val) => {
    await select(ref, val);
  });

program
  .command("inspect")
  .description("Open a screencast viewer for the page")
  .argument("[url]", "URL to inspect")
  .action(async (url) => {
    await inspect(url);
  });

program
  .command("scrape")
  .description("Scrape content with optional filters")
  .option("-f, --filter <classes...>", "CSS classes to filter")
  .action(async (options) => {
    await scrape(options.filter);
  });

await program.parseAsync(process.argv);
