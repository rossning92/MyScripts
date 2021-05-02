require("./base-font.css");
require("./markdown.css");

import example from "./example.md";
import marked from "marked";

console.log(MARKDOWN);

document.body.innerHTML =
  "<div id='content'>" +
  marked(MARKDOWN ? MARKDOWN : "# 测试标题\n## Test Caption");
+"</div>";
