import { withActivePage } from "../browser-core.js";

async function injectRefs(page) {
  return await page.evaluate(() => {
    // Roles that are typically interactive
    const interactiveRoles = [
      "button",
      "link",
      "checkbox",
      "combobox",
      "listbox",
      "menuitem",
      "menuitemcheckbox",
      "menuitemradio",
      "radio",
      "searchbox",
      "slider",
      "spinbutton",
      "switch",
      "textbox",
      "treeitem",
    ];

    function isInteractive(el) {
      if (
        el.tagName === "BUTTON" ||
        el.tagName === "A" ||
        (el.tagName === "INPUT" && el.type !== "hidden") ||
        el.tagName === "TEXTAREA" ||
        el.tagName === "SELECT" ||
        el.onclick != null ||
        window.getComputedStyle(el).cursor === "pointer"
      ) {
        return true;
      }
      const role = el.getAttribute("role");
      if (role && interactiveRoles.includes(role)) {
        return true;
      }
      return false;
    }

    // Clear old refs
    const oldElements = document.querySelectorAll("[data-agent-ref]");
    for (const el of oldElements) {
      el.removeAttribute("data-agent-ref");
    }

    let index = 0;
    const all = document.querySelectorAll("*");
    const interactiveElements = [];
    for (const el of all) {
      if (isInteractive(el)) {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          el.setAttribute("data-agent-ref", `e${index}`);
          interactiveElements.push({
            ref: `e${index}`,
            name:
              el.getAttribute("aria-label") ||
              el.innerText ||
              el.value ||
              el.placeholder ||
              "",
            role: el.getAttribute("role") || el.tagName.toLowerCase(),
          });
          index++;
        }
      }
    }
    return interactiveElements;
  });
}

function isInteractiveRole(role) {
  const interactiveRoles = [
    "button",
    "link",
    "checkbox",
    "combobox",
    "listbox",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "radio",
    "searchbox",
    "slider",
    "spinbutton",
    "switch",
    "textbox",
    "treeitem",
  ];
  return interactiveRoles.includes(role);
}

export function formatSnapshot(node, state = { index: 0 }, depth = 0) {
  const indent = "  ".repeat(depth);
  let line = indent;

  const isInteractive = isInteractiveRole(node.role);
  if (isInteractive) {
    line += `[@e${state.index++}] `;
  } else {
    line += "- ";
  }

  line += node.role;

  if (node.name) {
    line += ` "${node.name}"`;
  }

  const attributes = [];
  if (node.focused) attributes.push("active");
  if (node.level) attributes.push(`level=${node.level}`);
  if (node.disabled) attributes.push("disabled");
  if (node.expanded === true) attributes.push("expanded");
  if (node.expanded === false) attributes.push("collapsed");
  if (node.checked === true) attributes.push("checked");
  if (node.checked === false) attributes.push("unchecked");
  if (node.selected) attributes.push("selected");
  if (node.pressed) attributes.push("pressed");
  if (node.readonly) attributes.push("readonly");
  if (node.required) attributes.push("required");

  if (attributes.length > 0) {
    line += " [" + attributes.join("] [") + "]";
  }

  const value = node.value !== undefined ? node.value : node.valuetext;
  if (value !== undefined && value !== "" && value !== null) {
    line += `: ${value}`;
  }

  let result = line + "\n";
  if (node.children) {
    for (const child of node.children) {
      if (
        isInteractive &&
        child.role === "StaticText" &&
        child.name === node.name &&
        (!child.children || child.children.length === 0)
      ) {
        continue;
      }
      result += formatSnapshot(child, state, depth + 1);
    }
  }
  return result;
}

export async function snapshot() {
  return withActivePage(async (page) => {
    // First, inject refs into the DOM.
    await injectRefs(page);

    const title = await page.title();
    const url = await page.url();
    let output = `Title: ${title}\nURL: ${url}\n\n`;

    const snapshotData = await page.accessibility.snapshot({
      interestingOnly: true,
    });
    if (!snapshotData) return output + "(No accessibility data)";

    output += formatSnapshot(snapshotData).trim();
    return output;
  });
}
