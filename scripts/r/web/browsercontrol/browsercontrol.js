const child_process = require("child_process");
const os = require("os");
const path = require("path");
const { connect } = require("puppeteer");
const TurndownService = require("turndown");

const userDataDir = path.join(os.homedir(), ".browsercontrol-user-data");

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function getActivePage(browser) {
  const pages = await browser.pages();
  const arr = [];
  for (const page of pages) {
    if (
      await page.evaluate(() => {
        return document.visibilityState == "visible";
      })
    ) {
      arr.push(page);
    }
  }
  if (arr.length == 1) return arr[0];
  throw "Unable to get active page";
}

async function withActivePage(handler) {
  const browser = await launchOrConnectBrowser();
  try {
    const page = await getActivePage(browser);
    return await handler(page, browser);
  } finally {
    browser.disconnect();
  }
}

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
  return withActivePage(async (page) => {
    return await page.evaluate(() => {
      const element = document.getElementById("content");
      return element ? element.innerText : document.body.innerText;
    });
  });
}

async function getMarkdown() {
  return withActivePage(async (page) => {
    const content = await page.evaluate(() => {
      const element = document.getElementById("content");
      return element ? element.innerHTML : document.body.innerHTML;
    });

    const turndownService = new TurndownService();
    turndownService.remove("script");
    turndownService.remove("style");
    return turndownService.turndown(content);
  });
}

async function scrollToBottom() {
  return withActivePage(async (page) => {
    await page.evaluate(async () => {
      await new Promise((resolve) => {
        const scrollDistance = 200;
        const scrollInterval = 100;
        const scrollTimeout = 2000;

        let lastScrollY = 0;
        let lastChange = Date.now();
        const timer = setInterval(() => {
          window.scrollBy(0, scrollDistance);

          if (window.scrollY > lastScrollY) {
            lastScrollY = window.scrollY;
            lastChange = Date.now();
          }

          if (Date.now() - lastChange >= scrollTimeout) {
            clearInterval(timer);
            resolve();
          }
        }, scrollInterval);
      });
    });
  });
}

async function click(text) {
  return withActivePage(async (page) => {
    const success = await page.evaluate((searchText) => {
      const normalize = (value) =>
        (value || "").replace(/\s+/g, " ").trim().toLowerCase();

      const target = normalize(searchText);
      if (!target) return false;

      const isVisible = (el) => {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (
          !style ||
          style.visibility === "hidden" ||
          style.display === "none"
        ) {
          return false;
        }
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      };

      const candidates = Array.from(
        document.querySelectorAll(
          "button, a, [role='button'], [role='link'], [role='tab'], [onclick], input[type='button'], input[type='submit'], input[type='reset']"
        )
      );

      for (const el of candidates) {
        if (!isVisible(el)) continue;
        const label = normalize(
          el.innerText ||
            el.textContent ||
            el.value ||
            el.getAttribute("aria-label") ||
            el.getAttribute("title")
        );
        if (label && (label === target || label.includes(target))) {
          el.click();
          return true;
        }
      }

      return false;
    }, text);

    if (!success) {
      throw new Error(`Unable to find clickable element with text "${text}"`);
    }
  });
}

function showHelp() {
  console.log("Usage:");
  console.log("  node browsercontrol.js open <url>");
  console.log("  node browsercontrol.js get-text");
  console.log("  node browsercontrol.js get-markdown");
  console.log("  node browsercontrol.js scroll-bottom");
  console.log("  node browsercontrol.js click <text>");
  console.log("  node browsercontrol.js scrape [--filter <class> ...]");
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
  return withActivePage(async (page) => {
    const children = await page.evaluate(extractMostDirectChildren, filters);
    console.log(JSON.stringify(children, null, 2));
  });
}

(async () => {
  const args = process.argv.slice(2);
  if (args.length === 2 && args[0] === "open") {
    let url = args[1];
    if (!/^https?:\/\//i.test(url)) {
      url = `http://${url}`;
    }

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

  if (args.length === 1 && args[0] === "scroll-bottom") {
    try {
      await scrollToBottom();
      return;
    } catch (err) {
      console.error(err.message);
      process.exit(1);
    }
  }

  if (args.length === 2 && args[0] === "click") {
    try {
      await click(args[1]);
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
