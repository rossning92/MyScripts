const os = require("os");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const TurndownService = require("turndown");
const puppeteer = require("puppeteer-extra").addExtra(
  require("puppeteer-core"),
);
const StealthPlugin = require("puppeteer-extra-plugin-stealth");

puppeteer.use(StealthPlugin());

const USER_DATA_DIR = path.join(os.homedir(), ".browsercontrol-user-data");
const DEFAULT_DELAY_MS = 3000;
const HEADLESS = true;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const getChromeUserDataDir = () => {
  if (process.platform === "win32") {
    const base =
      process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local");
    return path.join(base, "Google", "Chrome", "User Data");
  }
  if (process.platform === "darwin") {
    return path.join(
      os.homedir(),
      "Library",
      "Application Support",
      "Google",
      "Chrome",
    );
  }
  return path.join(os.homedir(), ".config", "google-chrome");
};

const copyDirectory = async (src, dest) => {
  const entries = await fs.promises.readdir(src, { withFileTypes: true });
  await fs.promises.mkdir(dest, { recursive: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      await copyDirectory(srcPath, destPath);
    } else if (entry.isSymbolicLink()) {
      const link = await fs.promises.readlink(srcPath);
      await fs.promises.symlink(link, destPath);
    } else {
      await fs.promises.copyFile(srcPath, destPath);
    }
  }
};

const ensureDefaultProfile = async () => {
  const defaultProfileSrc = path.join(getChromeUserDataDir(), "Default");
  const defaultProfileDest = path.join(USER_DATA_DIR, "Default");
  try {
    await fs.promises.access(defaultProfileDest, fs.constants.F_OK);
    return;
  } catch (_) {}
  try {
    await fs.promises.access(defaultProfileSrc, fs.constants.F_OK);
  } catch (_) {
    return;
  }
  await copyDirectory(defaultProfileSrc, defaultProfileDest);
  const localStateSrc = path.join(
    path.dirname(defaultProfileSrc),
    "Local State",
  );
  const localStateDest = path.join(USER_DATA_DIR, "Local State");
  try {
    await fs.promises.copyFile(localStateSrc, localStateDest);
  } catch (_) {}
};

const getExecutablePath = () => {
  const defaults = {
    win32: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    darwin: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    linux: "/usr/bin/chromium",
    android: "/data/data/com.termux/files/usr/bin/chromium-browser",
  };
  const defaultPath = defaults[process.platform];
  if (defaultPath && fs.existsSync(defaultPath)) {
    return defaultPath;
  }
  return puppeteer.executablePath();
};

async function launchDetachedChrome() {
  await ensureDefaultProfile();
  const executablePath = getExecutablePath();
  const chromeArgs = [
    `--remote-debugging-port=21222`,
    `--user-data-dir=${USER_DATA_DIR}`,
    "--remote-allow-origins=*",
    "--no-sandbox",
  ];
  if (HEADLESS) {
    chromeArgs.push("--headless=new");
  }
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
    }),
  );
  let visiblePage = pages.filter((_v, index) => vis_results[index])[0];
  return visiblePage;
}

async function getOrOpenPage(browser, url) {
  let page;
  if (url) {
    const pages = await browser.pages();
    page = await browser.newPage();
    // Close all existing pages to save RAM
    // console.log(`Closing ${pages.length} existing pages...`);
    await Promise.race([
      Promise.all(pages.map((p) => p.close().catch((_e) => {}))),
      new Promise((resolve) => setTimeout(resolve, 2000)),
    ]);

    if (!/^https?:\/\//i.test(url)) url = `http://${url}`;
    // console.log(`Goto: ${url}`);
    const response = await page.goto(url, { waitUntil: "domcontentloaded" });
    if (response && !response.ok()) {
      throw new Error(
        `Failed to load page: ${response.status()} ${response.statusText()}`,
      );
    }
    await sleep(3000);
  } else {
    page = await getActivePage(browser);
  }
  return page;
}

async function withActivePage(handler, { url } = {}) {
  const browser = await launchOrConnectBrowser();
  try {
    const page = await getOrOpenPage(browser, url);

    if (!page) {
      throw "Failed to get active page";
    }
    return await handler(page, browser);
  } finally {
    browser.disconnect();
  }
}

async function launchOrConnectBrowser(browserURL = "http://127.0.0.1:21222") {
  const defaultViewport = HEADLESS ? { width: 1280, height: 720 } : null;
  try {
    return await puppeteer.connect({ browserURL, defaultViewport });
  } catch (err) {
    console.log("Unable to connect, launching a new browser instance...");
  }

  await launchDetachedChrome();
  const maxRetries = 5;
  const retryDelay = 1000;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await puppeteer.connect({ browserURL, defaultViewport });
    } catch (err) {
      if (attempt === maxRetries - 1) {
        throw err;
      }
      await sleep(retryDelay);
    }
  }
}

async function getText(url) {
  return withActivePage(
    async (page) => {
      return await page.evaluate(() => {
        const el = document.getElementById("content");
        return el ? el.innerText : document.body.innerText;
      });
    },
    { url },
  );
}

async function getMarkdown(url) {
  return withActivePage(
    async (page) => {
      const content = await page.evaluate(() => {
        const el = document.getElementById("content");
        return el ? el.innerHTML : document.body.innerHTML;
      });

      const turndownService = new TurndownService();
      turndownService.remove("script");
      turndownService.remove("style");
      turndownService.addRule("remove-base64-images", {
        filter: (node) =>
          node.nodeName === "IMG" &&
          node.getAttribute("src")?.startsWith("data:"),
        replacement: () => "",
      });
      turndownService.addRule("normalize-bracketed", {
        filter: ["a", "button"],
        replacement: (content, node) => {
          const cleaned = content.trim().replace(/\s+/g, " ");
          if (node.nodeName === "A") {
            const href = node.getAttribute("href");
            if (href) return `[${cleaned}](${href})`;
          }
          return `[${cleaned}]`;
        },
      });
      return turndownService.turndown(content);
    },
    { url },
  );
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
    await sleep(DEFAULT_DELAY_MS);
  });
}

async function pressKey(key) {
  return withActivePage(async (page) => {
    const keys = key.split("+").map((k) => {
      const lower = k.trim().toLowerCase();
      if (lower === "ctrl" || lower === "control") return "Control";
      if (lower === "alt") return "Alt";
      if (lower === "shift") return "Shift";
      if (lower === "meta" || lower === "cmd" || lower === "command")
        return "Meta";
      if (lower === "enter") return "Enter";
      if (lower === "tab") return "Tab";
      if (lower === "esc" || lower === "escape") return "Escape";
      if (lower === "backspace") return "Backspace";
      if (lower === "delete") return "Delete";
      if (lower === "space") return " ";
      if (lower === "up") return "ArrowUp";
      if (lower === "down") return "ArrowDown";
      if (lower === "left") return "ArrowLeft";
      if (lower === "right") return "ArrowRight";
      return k.trim();
    });

    for (const k of keys) {
      await page.keyboard.down(k);
    }
    for (const k of [...keys].reverse()) {
      await page.keyboard.up(k);
    }

    await sleep(DEFAULT_DELAY_MS);
  });
}

async function dump() {
  return withActivePage(async (page) => {
    const clickableElements = await page.evaluate(runAction, {
      type: "getClickables",
    });
    clickableElements.forEach((el) => {
      const rect = [
        Math.round(el.rect.left),
        Math.round(el.rect.top),
        Math.round(el.rect.right - el.rect.left),
        Math.round(el.rect.bottom - el.rect.top),
      ];
      console.log(
        `text="\x1b[33m${el.text}\x1b[0m"  rect=[${rect.join(", ")}]`,
      );
    });
  });
}

const runAction = ({ type, text } = {}) => {
  let elements = getClickables();

  if (type == "scrollIntoView") {
    const target =
      elements.find(({ text: elementText }) => elementText === text) ||
      elements.find(({ text: elementText }) => elementText.includes(text)) ||
      null;

    if (!target) return false;

    const rect = target.el.getBoundingClientRect();

    const isOutsideView =
      rect.top < 0 ||
      rect.bottom > window.innerHeight ||
      rect.left < 0 ||
      rect.right > window.innerWidth;

    if (isOutsideView) {
      target.el.scrollIntoView({ block: "center", inline: "center" });
    }

    return true;
  } else if (type == "getClickables") {
    return elements.map(({ rect, text }) => ({
      rect,
      text,
    }));
  }

  function getControlLabel(el) {
    const ariaLabelledBy = el.getAttribute("aria-labelledby");
    if (ariaLabelledBy) {
      const labelEl = document.getElementById(ariaLabelledBy);
      if (labelEl) return labelEl.innerText;
    }

    if (el.id) {
      try {
        const labelEl = document.querySelector(
          `label[for="${CSS.escape(el.id)}"]`,
        );
        if (labelEl) return labelEl.innerText;
      } catch (e) {}
    }

    const parentLabel = el.closest("label");
    if (parentLabel) return parentLabel.innerText;

    return null;
  }

  function getElementText(el) {
    let label =
      el.getAttribute("aria-label") ||
      el.getAttribute("title") ||
      el.getAttribute("placeholder");

    if (
      (!label || !label.trim()) &&
      (el.tagName === "INPUT" ||
        el.tagName === "TEXTAREA" ||
        el.tagName === "SELECT")
    ) {
      label = getControlLabel(el);
    }

    if (!label) label = el.innerText || el.textContent || el.value;

    return label ? String(label).replace(/\s+/g, " ").trim() : "";
  }

  function highlightElements(elements) {
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
      box.style.border = "2px solid red";
      const label = document.createElement("div");
      label.textContent = el.text;
      label.style.position = "absolute";
      label.style.top = "0";
      label.style.left = "0";
      label.style.transform = "translateY(-100%)";
      label.style.fontSize = "8pt";
      label.style.whiteSpace = "nowrap";
      label.style.pointerEvents = "none";
      label.style.backgroundColor = "red";
      label.style.color = "white";
      box.appendChild(label);
      document.body.appendChild(box);
      boxes.push(box);
    });
    setTimeout(() => boxes.forEach((box) => box.remove()), 1000);
  }

  function getClickables() {
    let elements = Array.prototype.slice
      .call(document.querySelectorAll("*"))
      .filter((el) => {
        if (
          el.tagName === "BUTTON" ||
          el.tagName === "A" ||
          (el.tagName === "INPUT" && el.type !== "hidden") ||
          el.tagName === "TEXTAREA" ||
          el.tagName === "SELECT" ||
          el.tagName === "LABEL" ||
          el.getAttribute("role") === "textbox" ||
          el.getAttribute("role") === "button" ||
          el.getAttribute("role") === "checkbox" ||
          el.getAttribute("role") === "radio" ||
          el.onclick != null
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
          text: getElementText(el),
        };
      })
      .filter((x) => Boolean(x.text));

    // If one element contains another, return the contained one.
    elements = elements.filter(
      (x) => !elements.some((y) => x.el.contains(y.el) && !(x == y)),
    );
    return elements;
  }
};

async function click(text) {
  return withActivePage(async (page) => {
    const start = Date.now();
    let found = false;
    while (Date.now() - start < 5 * 1000) {
      found = await page.evaluate(runAction, { type: "scrollIntoView", text });
      if (found) break;
      await sleep(500);
    }

    if (!found) {
      throw new Error(`Unable to find clickable el with text "${text}"`);
    }

    const clickables = await page.evaluate(runAction, {
      type: "getClickables",
    });

    if (clickables) {
      const match =
        clickables.find(({ text: elementText }) => elementText === text) ||
        clickables.find(({ text: elementText }) => elementText.includes(text));

      if (!match) {
        throw new Error(`Unable to find clickable el with text "${text}"`);
      }

      const { rect } = match;
      const centerX = rect.left + (rect.right - rect.left) / 2;
      const centerY = rect.top + (rect.bottom - rect.top) / 2;
      await page.mouse.click(centerX, centerY);
      return;
    }
  });
}

async function closeAllPages() {
  const browser = await launchOrConnectBrowser();
  try {
    const pages = await browser.pages();
    for (const page of pages) {
      await page.close();
    }
  } finally {
    browser.disconnect();
  }
}

async function closeBrowser() {
  const browser = await launchOrConnectBrowser();
  await browser.close();
}

function showHelp() {
  console.log("Usage:");
  console.log("  node browsercontrol.js open <url>");
  console.log("  node browsercontrol.js close-pages");
  console.log("  node browsercontrol.js close-browser");
  console.log("  node browsercontrol.js get-text [url]");
  console.log("  node browsercontrol.js get-markdown [url]");
  console.log("  node browsercontrol.js scroll-bottom");
  console.log("  node browsercontrol.js click <text>");
  console.log("  node browsercontrol.js type <text>");
  console.log("  node browsercontrol.js press <key>");
  console.log("  node browsercontrol.js dump");
  console.log("  node browsercontrol.js debug [url]");
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

async function openDevTools(url) {
  const browser = await launchOrConnectBrowser();
  try {
    if (url) {
      await getOrOpenPage(browser, url);
    }
    const res = await fetch("http://127.0.0.1:21222/json");
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

async function scrape(filters) {
  return withActivePage(async (page) => {
    const children = await page.evaluate(extractMostDirectChildren, filters);
    console.log(JSON.stringify(children, null, 2));
  });
}

(async () => {
  const args = process.argv.slice(2);
  if (args.length === 2 && args[0] === "open") {
    const url = args[1];
    const browser = await launchOrConnectBrowser();
    await getOrOpenPage(browser, url);
    browser.disconnect();
    return;
  }

  if (args.length === 1 && args[0] === "close-pages") {
    await closeAllPages();
    return;
  }

  if (args.length === 1 && args[0] === "close-browser") {
    await closeBrowser();
    return;
  }

  if ((args.length === 1 || args.length === 2) && args[0] === "get-text") {
    const text = await getText(args[1]);
    console.log(text);
    return;
  }

  if ((args.length === 1 || args.length === 2) && args[0] === "get-markdown") {
    const markdown = await getMarkdown(args[1]);
    console.log(markdown);
    return;
  }

  if (args.length === 1 && args[0] === "scroll-bottom") {
    await scrollToBottom();
    return;
  }

  if (args.length === 2 && args[0] === "press") {
    await pressKey(args[1]);
    return;
  }

  if (args.length === 2 && args[0] === "click") {
    await click(args[1]);
    return;
  }

  if (args.length === 2 && args[0] === "type") {
    await typeText(args[1]);
    return;
  }

  if (args.length === 1 && args[0] === "dump") {
    await dump(args[1]);
    return;
  }

  if (args[0] === "debug") {
    const url = args.slice(1).find((arg) => !arg.startsWith("--"));
    await openDevTools(url);
    return;
  }

  if (args.length >= 1 && args[0] === "scrape") {
    const filtersIndex = args.findIndex((arg) => arg === "--filter");
    const filters =
      filtersIndex !== -1
        ? args.slice(filtersIndex + 1).filter(Boolean)
        : undefined;
    await scrape(filters);
    return;
  }

  showHelp();
  process.exit(1);
})();
