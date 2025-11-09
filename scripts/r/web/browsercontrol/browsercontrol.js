const os = require("os");
const path = require("path");
const { spawn } = require("child_process");
const puppeteer = require("puppeteer");
const TurndownService = require("turndown");

const userDataDir = path.join(os.homedir(), ".browsercontrol-user-data");

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function launchDetachedChrome() {
  const executablePath = puppeteer.executablePath();
  const chromeArgs = [
    `--remote-debugging-port=21222`,
    `--user-data-dir=${userDataDir}`,
    "--remote-allow-origins=*",
    "--no-sandbox",
  ];
  const chromeProcess = spawn(executablePath, chromeArgs, {
    detached: true,
    stdio: "ignore",
  });
  chromeProcess.unref();
}

async function getActivePage(browser) {
  const pages = await browser.pages();
  const vis_results = await Promise.all(
    pages.map(async (p) => {
      const state = await p.evaluate(() => document.webkitHidden);
      return !state;
    })
  );
  let visiblePage = pages.filter((_v, index) => vis_results[index])[0];
  return visiblePage;
}

async function withActivePage(handler) {
  const browser = await launchOrConnectBrowser();
  try {
    const page = await getActivePage(browser);
    if (!page) {
      throw "Failed to get active page";
    }
    return await handler(page, browser);
  } finally {
    browser.disconnect();
  }
}

async function launchOrConnectBrowser(browserURL = "http://127.0.0.1:21222") {
  try {
    return await puppeteer.connect({ browserURL });
  } catch (err) {
    console.log("Failed to connect, launching a new browser instance...");
  }

  await launchDetachedChrome();

  const maxRetries = 5;
  const retryDelay = 1000;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await puppeteer.connect({ browserURL });
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
      const el = document.getElementById("content");
      return el ? el.innerText : document.body.innerText;
    });
  });
}

async function getMarkdown() {
  return withActivePage(async (page) => {
    const content = await page.evaluate(() => {
      const el = document.getElementById("content");
      return el ? el.innerHTML : document.body.innerHTML;
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

async function typeText(text) {
  return withActivePage(async (page) => {
    await page.keyboard.type(text);
  });
}

async function pressKey(key) {
  return withActivePage(async (page) => {
    await page.keyboard.press(key);
  });
}

async function debug() {
  return withActivePage(async (page) => {
    const clickableElements = await page.evaluate(getClickableElements);
    console.log(clickableElements);
  });
}

const getClickableElements = () => {
  let elements = Array.prototype.slice
    .call(document.querySelectorAll("*"))
    .filter((el) => {
      if (
        el.tagName === "BUTTON" ||
        el.tagName === "A" ||
        (el.tagName === "INPUT" && el.type !== "hidden") ||
        el.tagName === "TEXTAREA" ||
        el.tagName === "SELECT" ||
        el.onclick != null ||
        window.getComputedStyle(el).cursor === "pointer"
      ) {
        const rect = el.getBoundingClientRect();
        return (rect.right - rect.left) * (rect.bottom - rect.top) >= 20;
      }
      return false;
    })
    .map((el) => {
      const rect = el.getBoundingClientRect();
      return {
        el,
        rect: {
          left: rect.left,
          top: rect.top,
          right: rect.right,
          bottom: rect.bottom,
        },
        text: (() => {
          const label =
            el.getAttribute("aria-label") ||
            el.getAttribute("title") ||
            el.innerText ||
            el.textContent ||
            el.value;
          return label ? label.replace(/\s+/g, " ").trim() : "";
        })(),
      };
    })
    // Filter out elements without text
    .filter((x) => Boolean(x.text));

  // Only keep inner clickable elements
  elements = elements.filter(
    (x) => !elements.some((y) => x.el.contains(y.el) && !(x == y))
  );

  const boxes = [];
  elements.forEach(function (el) {
    const width = el.rect.right - el.rect.left;
    const height = el.rect.bottom - el.rect.top;
    if (width <= 0 || height <= 0) return;
    const box = document.createElement("div");
    box.style.position = "fixed";
    box.style.left = el.rect.left + "px";
    box.style.top = el.rect.top + "px";
    box.style.width = width + "px";
    box.style.height = height + "px";
    box.style.pointerEvents = "none";
    box.style.boxSizing = "border-box";
    box.style.zIndex = 2147483647;
    box.style.backgroundColor = "white";
    box.style.border = "2px solid red";
    const label = document.createElement("div");
    label.textContent = el.text;
    label.style.position = "absolute";
    label.style.top = "0";
    label.style.left = "0";
    label.style.width = "100%";
    label.style.height = "100%";
    label.style.display = "flex";
    label.style.alignItems = "center";
    label.style.justifyContent = "center";
    label.style.fontSize = "8pt";
    label.style.whiteSpace = "wrap";
    label.style.pointerEvents = "none";
    label.style.color = "red";
    box.appendChild(label);
    document.body.appendChild(box);
    boxes.push(box);
  });
  setTimeout(() => boxes.forEach((box) => box.remove()), 1000);

  return elements.map(({ text, rect }) => ({ text, rect }));
};

async function click(text) {
  return withActivePage(async (page) => {
    const clickableElements = await page.evaluate(getClickableElements);

    const target =
      clickableElements.find((el) => el.text === text) ||
      clickableElements.find((el) => el.text.includes(text));

    if (target) {
      const { rect } = target;
      const centerX = rect.left + (rect.right - rect.left) / 2;
      const centerY = rect.top + (rect.bottom - rect.top) / 2;
      await page.mouse.click(centerX, centerY);
      return;
    }

    throw new Error(`Unable to find clickable el with text "${text}"`);
  });
}

function showHelp() {
  console.log("Usage:");
  console.log("  node browsercontrol.js open <url>");
  console.log("  node browsercontrol.js get-text");
  console.log("  node browsercontrol.js get-markdown");
  console.log("  node browsercontrol.js scroll-bottom");
  console.log("  node browsercontrol.js click <text>");
  console.log("  node browsercontrol.js type <text>");
  console.log("  node browsercontrol.js press <key>");
  console.log("  node browsercontrol.js scrape [--filter <class> ...]");
}

const extractMostDirectChildren = (filters) => {
  // Prepare filters for fast lookups when limiting results
  const filterSet =
    Array.isArray(filters) && filters.length ? new Set(filters) : null;
  const body = document.body;
  if (!body) return [];

  // Find the element with the most direct children as the main container
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

  // Recursively extract text content and map it by class name
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

    return result;
  };

  // Convert the top-level children into structured objects
  let items = Array.from(maxEl.children).map(extract).filter(Boolean);
  if (filterSet) {
    items = items
      .map((item) => {
        const filtered = {};
        Object.keys(item).forEach((key) => {
          if (filterSet.has(key)) {
            filtered[key] = item[key];
          }
        });
        return filtered;
      })
      .filter((item) => Object.keys(item).length);
  }
  return items;
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

  if (args.length === 2 && args[0] === "press") {
    try {
      await pressKey(args[1]);
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

  if (args.length === 2 && args[0] === "type") {
    try {
      await typeText(args[1]);
      return;
    } catch (err) {
      console.error(err.message);
      process.exit(1);
    }
  }

  if (args.length === 1 && args[0] === "debug") {
    try {
      await debug(args[1]);
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
