import { sleep, withActivePage } from "../browser-core.js";
import { DEFAULT_DELAY_MS } from "../config.js";

export async function pressKey(key) {
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
