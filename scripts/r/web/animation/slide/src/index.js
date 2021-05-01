require("./markdown.html");
require("./base-font.css");
require("./markdown.css");

import example from "./example.md";
import marked from "marked";

document.body.innerHTML = marked(MARKDOWN ? MARKDOWN : example);
