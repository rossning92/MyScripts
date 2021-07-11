require(`./${TEMPLATE}.css`);
const markdown = require(MD_FILE).default;
const marked = require("marked");

const SEP = "---\r";

let innerHtml;

if (markdown.includes(SEP)) {
  let columnHtml = "";
  for (const col of markdown.split(SEP)) {
    columnHtml += `<div class="col">${marked(col)}</div>`;
  }
  innerHtml = `<div class="outer"><div class="inner"><div class="cols">${columnHtml}</div></div></div>`;
} else {
  innerHtml = `<div class="outer"><div class="inner">${marked(
    markdown
  )}</div></div>`;
}

document.body.innerHTML = innerHtml;
