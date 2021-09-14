import { updateCodeBlocks } from "./utils/codemirror";
import { updateMermaid } from "./utils/diagram";
const marked = require("marked");

require(`./codemirror.css`);
require(`./${TEMPLATE}.css`);

// Parse Yaml front matter
const { markdown, matter } = parseYamlFrontMatter(
  require(MD_FILE).default.replace(/\r\n/g, "\n")
);

handleSeparator();

// HACK
if (TEMPLATE == "title") {
  document.body.innerHTML = `<div class="container"><div class="inner">${marked(
    markdown
  )}</div></div>`;
}

updateMermaid();
updateCodeBlocks({
  fontSize: matter.fontSize,
  scrollToLine: matter.scrollToLine,
  width: matter.width,
});

function handleSeparator() {
  const SEP = "\n---\n";

  let innerHTML;
  if (markdown.includes(SEP)) {
    let columnHtml = "";
    for (const col of markdown.split(SEP)) {
      columnHtml += `<div class="col">${marked(col)}</div>`;
    }
    innerHTML = `<div class="container"><div class="cols">${columnHtml}</div></div>`;
  } else {
    innerHTML = `<div class="container">${marked(markdown)}</div>`;
  }
  document.body.innerHTML = innerHTML;
}

function parseYamlFrontMatter(markdown) {
  const yamlFrontMatter = /^---\n([\s\S]*?)\n---\n/;
  const yamlFrontMatterMatch = markdown.match(yamlFrontMatter);
  const matter = new Object();
  if (yamlFrontMatterMatch) {
    const yamlString = yamlFrontMatterMatch[1];

    const yamlLines = yamlString.split("\n");
    for (const line of yamlLines) {
      const keyValue = line.split(":");
      if (keyValue.length === 2) {
        const key = keyValue[0].trim();
        const value = keyValue[1].trim();
        matter[key] = value;
      }
    }
  }

  return {
    markdown: markdown.replace(yamlFrontMatter, ""),
    matter,
  };
}
