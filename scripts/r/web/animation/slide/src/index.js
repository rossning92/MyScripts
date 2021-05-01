require("./markdown.html");
require("./base-font.css");
require("./markdown.css");
const marked = require("marked");

import example from "./example.md";

document.body.innerHTML = marked(example);
