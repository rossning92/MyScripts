require(`./${TEMPLATE}.css`);
const markdown = require(MD_FILE).default;
const marked = require("marked");

document.body.innerHTML = `<div id="content">${marked(markdown)}</div>`;
