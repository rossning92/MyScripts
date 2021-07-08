require(`./${TEMPLATE}.css`);
const markdown = require(MD_FILE).default;
const marked = require("marked");

document.body.innerHTML = `<div class="outer"><div class="inner">${marked(
  markdown
)}</div></div>`;
