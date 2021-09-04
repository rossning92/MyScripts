import { updateCodeBlocks } from "./utils/code-editor";
import { updateMermaid } from "./utils/diagram";

require(`./codemirror.css`);
require(`./${TEMPLATE}.css`);
const markdown = require(MD_FILE).default.replace(/\r\n/g, "\n");
const marked = require("marked");

handleSeparator();

updateMermaid();
updateCodeBlocks();

function handleSeparator() {
  const SEP = "\n---\n";

  let innerHtml;
  if (markdown.includes(SEP)) {
    let columnHtml = "";
    for (const col of markdown.split(SEP)) {
      columnHtml += `<div class="col">${marked(col)}</div>`;
    }
    innerHtml = `<div class="container"><div class="cols">${columnHtml}</div></div>`;
  } else {
    innerHtml = `<div class="container">${marked(markdown)}</div>`;
  }
  document.body.innerHTML = innerHtml;
}
