import { program } from "commander";

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
    const { getOrOpenPage, launchOrConnectBrowser } = await import(
      "./browser-core.js"
    );
    const browser = await launchOrConnectBrowser({ headed: options.headed });
    await getOrOpenPage(browser, url);
    browser.disconnect();
  });

program
  .command("close-pages")
  .description("Close all pages")
  .action(async () => {
    const { closeAllPages } = await import("./commands/closeAllPages.js");
    await closeAllPages();
  });

program
  .command("close-browser")
  .description("Close the browser")
  .action(async () => {
    const { closeBrowser } = await import("./commands/closeBrowser.js");
    await closeBrowser();
  });

program
  .command("get-text")
  .description("Get text from a page")
  .argument("[url]", "URL to get text from")
  .action(async (url) => {
    const { getText } = await import("./commands/getText.js");
    const text = await getText(url);
    console.log(text);
  });

program
  .command("get-markdown")
  .description("Get markdown content from a page")
  .argument("[url]", "URL to get markdown from")
  .action(async (url) => {
    const { getMarkdown } = await import("./commands/getMarkdown.js");
    const markdown = await getMarkdown(url);
    console.log(markdown);
  });

program
  .command("snapshot")
  .description(
    "Get a snapshot of the page with indices for interactive elements"
  )
  .action(async () => {
    const { snapshot } = await import("./commands/snapshot.js");
    const text = await snapshot();
    console.log(text);
  });

program
  .command("scroll-bottom")
  .description("Scroll to the bottom of the page")
  .action(async () => {
    const { scrollToBottom } = await import("./commands/scrollToBottom.js");
    await scrollToBottom();
  });

program
  .command("click")
  .description("Click on an element by its ref (e.g. @e0, @e1)")
  .argument("<ref>", "Element ref from snapshot (e.g. @e0)")
  .action(async (ref) => {
    const { click } = await import("./commands/click.js");
    await click(ref);
  });

program
  .command("type")
  .description("Type text into the focused element or a specific element ref")
  .usage("[ref] <text>")
  .argument("[ref]", "Element ref to type into (e.g., @e1)")
  .argument("[text]", "Text to type")
  .action(async (ref, text) => {
    const { typeText } = await import("./commands/typeText.js");
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
    const { fill } = await import("./commands/fill.js");
    await fill(ref, text);
  });

program
  .command("press")
  .description("Press a key")
  .argument("<key>", "Key to press")
  .action(async (key) => {
    const { pressKey } = await import("./commands/pressKey.js");
    await pressKey(key);
  });

program
  .command("select")
  .description("Select an option in a dropdown")
  .argument("<ref>", "Element ref of the select element (e.g. @e0)")
  .argument("<val>", "Value to select")
  .action(async (ref, val) => {
    const { select } = await import("./commands/select.js");
    await select(ref, val);
  });

program
  .command("upload")
  .description("Upload a file to a file input element")
  .argument("<ref>", "Element ref of the file input (e.g. @e5)")
  .argument("<filePath>", "Path to the file to upload")
  .action(async (ref, filePath) => {
    const { upload } = await import("./commands/upload.js");
    await upload(ref, filePath);
  });

program
  .command("screenshot")
  .description("Take a screenshot of the current page")
  .argument("[filePath]", "Path to save the screenshot (default: temp file)")
  .action(async (filePath) => {
    const { screenshot } = await import("./commands/screenshot.js");
    const savedPath = await screenshot(filePath);
    console.log(savedPath);
  });

program
  .command("inspect")
  .description("Open a screencast viewer for the page")
  .argument("[url]", "URL to inspect")
  .action(async (url) => {
    const { inspect } = await import("./commands/inspect.js");
    await inspect(url);
  });

program
  .command("scrape")
  .description("Scrape content with optional filters")
  .option("-f, --filter <classes...>", "CSS classes to filter")
  .action(async (options) => {
    const { scrape } = await import("./commands/scrape.js");
    await scrape(options.filter);
  });

await program.parseAsync(process.argv);
