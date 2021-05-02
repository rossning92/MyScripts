require("./base-font.css");
require("./markdown.css");

import example from "./example.md";
import marked from "marked";

console.log(MARKDOWN);

document.body.innerHTML = marked(MARKDOWN ? MARKDOWN : example);
