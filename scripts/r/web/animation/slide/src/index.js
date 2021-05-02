require(`./${TEMPLATE}.css`);

import marked from "marked";

const markdown = require(MD_FILE).default;

document.body.innerHTML = "<div id='content'>" + marked(markdown);
+"</div>";
