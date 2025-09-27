const child_process = require("child_process");
const os = require("os");
const path = require("path");
const { connect } = require("puppeteer");
const TurndownService = require("turndown");

const userDataDir = path.join(os.homedir(), ".browsercontrol-user-data");

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function launchOrConnectBrowser(browserURL = "http://127.0.0.1:21222") {
  try {
    return await connect({ browserURL });
  } catch (err) {
    // ignore and try launching a child process below
    console.log("Failed to connect, launching a new browser instance...");
  }

  // Hack: launch browser manually since browser.launch()
  // doesn't yet support a 'detach' option
  const childProcess = child_process.spawn(
    "chromium",
    [
      `--remote-debugging-port=21222`,
      `--user-data-dir=${userDataDir}`,
      "--remote-allow-origins=*",
      "--no-sandbox",
    ],
    {
      detached: true,
      stdio: "ignore",
    }
  );
  childProcess.unref();

  const maxRetries = 5;
  const retryDelay = 1000;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await connect({ browserURL });
    } catch (err) {
      if (attempt === maxRetries - 1) {
        throw err;
      }
      await sleep(retryDelay);
    }
  }
}

async function getText() {
  const browser = await launchOrConnectBrowser();
  try {
    const pages = await browser.pages();
    const page = pages.at(-1);

    if (!page) {
      throw new Error("No open pages");
    }

    return await page.evaluate(() => {
      const element = document.getElementById("content");
      return element ? element.innerText : document.body.innerText;
    });
  } finally {
    browser.disconnect();
  }
}

async function getMarkdown() {
  const browser = await launchOrConnectBrowser();
  try {
    const pages = await browser.pages();
    const page = pages.at(-1);

    if (!page) {
      throw new Error("No open pages");
    }

    const content = await page.evaluate(() => {
      const element = document.getElementById("content");
      return element ? element.innerHTML : document.body.innerHTML;
    });

    const turndownService = new TurndownService();
    return turndownService.turndown(content);
  } finally {
    browser.disconnect();
  }
}

function showHelp() {
  console.log("Usage:");
  console.log("  node browsercontrol.js open <url>");
  console.log("  node browsercontrol.js get-text");
  console.log("  node browsercontrol.js get-markdown");
}

const extractMostDirectChildren = (filters) => {
  const filterSet =
    Array.isArray(filters) && filters.length ? new Set(filters) : null;
  const body = document.body;
  if (!body) return [];

  let maxEl = null;
  let maxCount = -1;
  for (const el of body.querySelectorAll("*")) {
    if (!(el instanceof HTMLElement)) {
      continue;
    }
    const count = el.children.length;
    if (count > maxCount) {
      maxCount = count;
      maxEl = el;
    }
  }

  if (!maxEl) return [];

  const extract = (el) => {
    const className = (() => {
      if (typeof el.className === "string") {
        const trimmed = el.className.trim();
        if (trimmed) return trimmed;
      }
      if (el.classList?.length) {
        return Array.from(el.classList).join(" ");
      }
      return el.tagName?.toLowerCase() || "no-class";
    })();
    const text = Array.from(el.childNodes)
      .map((node) => {
        if (node.nodeType === Node.TEXT_NODE) {
          return (node.textContent || "").trim();
        }
        if (
          node.nodeType === Node.ELEMENT_NODE &&
          typeof node.nodeName === "string" &&
          node.nodeName.toLowerCase() === "em"
        ) {
          return (node.textContent || "").trim();
        }
        return "";
      })
      .filter(Boolean)
      .join("");
    let result = {};
    if (text) {
      result[className] = text;
    }
    Array.from(el.children).forEach((child) => {
      const childResult = extract(child);
      Object.entries(childResult).forEach(([key, value]) => {
        let newKey = key;
        let count = 2;
        while (Object.prototype.hasOwnProperty.call(result, newKey)) {
          newKey = `${key} ${count}`;
          count += 1;
        }
        result[newKey] = value;
      });
    });
    if (filterSet) {
      result = Object.fromEntries(
        Object.entries(result).filter(([key]) => filterSet.has(key))
      );
    }
    return result;
  };

  return Array.from(maxEl.children).map(extract).filter(Boolean);
};

async function scrape(filters) {
  const browser = await launchOrConnectBrowser();
  try {
    const pages = await browser.pages();
    const page = pages.at(-1);

    if (!page) {
      throw new Error("No open pages");
    }

    const children = await page.evaluate(extractMostDirectChildren, filters);

    console.log(JSON.stringify(children, null, 2));
  } finally {
    browser.disconnect();
  }
}

(async () => {
  const args = process.argv.slice(2);
  if (args.length === 2 && args[0] === "open") {
    const url = args[1];

    const browser = await launchOrConnectBrowser();
    const page = await browser.newPage();
    await page.goto(url, { waitUntil: "domcontentloaded" });

    browser.disconnect();
    return;
  }

  if (args.length === 1 && args[0] === "get-text") {
    try {
      const text = await getText();
      console.log(text);
      return;
    } catch (err) {
      console.error(err.message);
      process.exit(1);
    }
  }

  if (args.length === 1 && args[0] === "get-markdown") {
    try {
      const markdown = await getMarkdown();
      console.log(markdown);
      return;
    } catch (err) {
      console.error(err.message);
      process.exit(1);
    }
  }

  if (args.length >= 1 && args[0] === "scrape") {
    const filtersIndex = args.findIndex((arg) => arg === "--filter");
    const filters =
      filtersIndex !== -1
        ? args.slice(filtersIndex + 1).filter(Boolean)
        : undefined;
    try {
      await scrape(filters);
      return;
    } catch (err) {
      console.error(err.message);
      process.exit(1);
    }
  }

  showHelp();
  process.exit(1);
})();
