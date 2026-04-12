import { withActivePage } from "../browser-core.js";

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
    // Clear old refs
    await page.evaluate(() => {
      document.querySelectorAll("[data-agent-ref]").forEach((el) =>
        el.removeAttribute("data-agent-ref"),
      );
    });

    const title = await page.title();
    const url = await page.url();
    let output = `Title: ${title}\nURL: ${url}\n\n`;

    const snapshotData = await page.accessibility.snapshot({
      interestingOnly: true,
    });
    if (!snapshotData) return output + "(No accessibility data)";

    // Use CDP to get the full AX tree with backendDOMNodeId, then assign
    // data-agent-ref in the same depth-first order as formatSnapshot so that
    // the displayed ref indices match the DOM attributes.
    const client = await page.createCDPSession();
    try {
      const { nodes } = await client.send("Accessibility.getFullAXTree");

      const nodeMap = new Map();
      for (const node of nodes) {
        nodeMap.set(node.nodeId, node);
      }

      const rootNode = nodes.find((n) => !n.parentId);
      if (rootNode) {
        // Walk depth-first, collect interactive nodes that would survive
        // Puppeteer's interestingOnly filter.
        const backendIds = [];
        function walk(nodeId) {
          const node = nodeMap.get(nodeId);
          if (!node) return;

          if (!node.ignored) {
            const role = node.role?.value || "";
            if (isInteractiveRole(role) && node.backendDOMNodeId) {
              const name = node.name?.value || "";
              let dominated = !!name;
              if (!dominated && node.properties) {
                for (const p of node.properties) {
                  if (p.name === "focusable" && p.value?.value) {
                    dominated = true;
                    break;
                  }
                }
              }
              if (dominated) {
                backendIds.push(node.backendDOMNodeId);
              }
            }
          }

          if (node.childIds) {
            for (const childId of node.childIds) {
              walk(childId);
            }
          }
        }
        walk(rootNode.nodeId);

        // Set data-agent-ref on each DOM element via CDP
        for (let i = 0; i < backendIds.length; i++) {
          try {
            const { object } = await client.send("DOM.resolveNode", {
              backendNodeId: backendIds[i],
            });
            await client.send("Runtime.callFunctionOn", {
              objectId: object.objectId,
              functionDeclaration: `function(r) { this.setAttribute('data-agent-ref', r); }`,
              arguments: [{ value: `e${i}` }],
            });
          } catch (_e) {
            // Skip nodes that can't be resolved
          }
        }
      }
    } finally {
      await client.detach();
    }

    output += formatSnapshot(snapshotData).trim();
    return output;
  });
}
