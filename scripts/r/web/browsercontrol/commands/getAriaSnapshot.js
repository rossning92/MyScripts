import { withActivePage } from "../browser-core.js";

export function formatAriaSnapshot(node, depth = 0) {
  const indent = "  ".repeat(depth);
  let line = `${indent}- ${node.role}`;

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
  const hasValue = value !== undefined && value !== "" && value !== null;
  const hasChildren = node.children && node.children.length > 0;

  if (hasValue) {
    line += `: ${value}`;
  } else if (hasChildren) {
    line += ":";
  }

  let result = line + "\n";
  if (node.children) {
    for (const child of node.children) {
      result += formatAriaSnapshot(child, depth + 1);
    }
  }
  return result;
}

export async function getAriaSnapshot() {
  return withActivePage(async (page) => {
    const snapshot = await page.accessibility.snapshot({
      interestingOnly: true,
    });
    if (!snapshot) return "";

    return formatAriaSnapshot(snapshot).trim();
  });
}
