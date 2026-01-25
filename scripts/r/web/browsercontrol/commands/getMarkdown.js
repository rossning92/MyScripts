import TurndownService from "turndown";
import { withActivePage } from "../browser-core.js";

export async function getMarkdown(url) {
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
