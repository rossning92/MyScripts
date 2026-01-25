import { withActivePage } from "../browser-core.js";

export async function scrollToBottom() {
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
