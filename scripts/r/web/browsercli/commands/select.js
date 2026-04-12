import { withActivePage, refToSelector } from "../browser-core.js";

export async function select(ref, value) {
  return withActivePage(async (page) => {
    const selector = refToSelector(ref);
    await page.waitForSelector(selector);

    await page.evaluate(
      (sel, val) => {
        const select = document.querySelector(sel);
        if (!select) return;

        const options = Array.from(select.options);

        // 1. Try to find by value
        let option = options.find((o) => o.value === val);

        // 2. Try to find by visible text (exact, case-insensitive)
        if (!option) {
          option = options.find(
            (o) => o.text.trim().toLowerCase() === val.toLowerCase(),
          );
        }

        // 3. Try to find by visible text (substring, case-insensitive)
        if (!option) {
          option = options.find((o) =>
            o.text.toLowerCase().includes(val.toLowerCase()),
          );
        }

        if (option) {
          select.value = option.value;
          select.dispatchEvent(new Event("change", { bubbles: true }));
          select.dispatchEvent(new Event("input", { bubbles: true }));
        }
      },
      selector,
      value,
    );
  });
}
