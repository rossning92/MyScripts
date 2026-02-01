import { spawn } from "child_process";
import fs from "fs";
import os from "os";
import path from "path";
import puppeteerCore from "puppeteer-core";
import puppeteerExtra from "puppeteer-extra";
import StealthPlugin from "puppeteer-extra-plugin-stealth";
import { BROWSER_URL, DEBUG_PORT, HEADLESS, USER_DATA_DIR } from "./config.js";

const puppeteer = puppeteerExtra.addExtra(puppeteerCore);
puppeteer.use(StealthPlugin());

export const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

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
      "Chrome"
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
  const executablePath = getExecutablePath();
  const chromeArgs = [
    `--remote-debugging-port=${DEBUG_PORT}`,
    `--user-data-dir=${USER_DATA_DIR}`,
    "--remote-allow-origins=*",
    "--no-sandbox",
    "--window-size=1366,768",
    "--disable-blink-features=AutomationControlled",
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
    })
  );
  let visiblePage = pages.filter((_v, index) => vis_results[index])[0];
  return visiblePage;
}

export async function getOrOpenPage(browser, url) {
  let page;
  if (url) {
    const pages = await browser.pages();
    page = await browser.newPage();
    await Promise.race([
      Promise.all(pages.map((p) => p.close().catch((_e) => {}))),
      new Promise((resolve) => setTimeout(resolve, 2000)),
    ]);

    if (!/^https?:\/\//i.test(url)) url = `http://${url}`;
    const response = await page.goto(url, { waitUntil: "domcontentloaded" });
    if (response && !response.ok()) {
      throw new Error(
        `Failed to load page: ${response.status()} ${response.statusText()}`
      );
    }
    await sleep(3000);
  } else {
    page = await getActivePage(browser);
  }

  if (page) {
    const defaultViewport = {
      width: 1366,
      height: 768,
      deviceScaleFactor: 1,
    };
    await page.setViewport(defaultViewport);
  }

  return page;
}

export async function launchOrConnectBrowser(browserURL = BROWSER_URL) {
  const defaultViewport = {
    width: 1366,
    height: 768,
    deviceScaleFactor: 1,
  };
  let browser;
  try {
    browser = await puppeteer.connect({ browserURL, defaultViewport });
  } catch (err) {
    console.log("Unable to connect, launching a new browser instance...");

    await launchDetachedChrome();
    const maxRetries = 5;
    const retryDelay = 1000;
    let connected = false;
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        browser = await puppeteer.connect({ browserURL, defaultViewport });
        connected = true;
        break;
      } catch (err) {
        if (attempt === maxRetries - 1) {
          throw err;
        }
        await sleep(retryDelay);
      }
    }
    if (!connected) throw new Error("Failed to connect to browser");
  }

  const handleDialog = async (dialog) => {
    console.log(
      `Automatically accepting dialog: [${dialog.type()}] ${dialog.message()}`
    );
    await dialog.accept().catch(() => {});
  };

  browser.on("targetcreated", async (target) => {
    if (target.type() === "page") {
      const page = await target.page();
      if (page) {
        page.on("dialog", handleDialog);
      }
    }
  });

  return browser;
}

export async function withActivePage(handler, { url } = {}) {
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

export const runAction = ({ type, text } = {}) => {
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
          `label[for="${CSS.escape(el.id)}"]`
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
      (x) => !elements.some((y) => x.el.contains(y.el) && !(x == y))
    );
    return elements;
  }
};

export const extractMostDirectChildren = (filters) => {
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
