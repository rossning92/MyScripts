require("./base-font.css");
require("./markdown.css");

import marked from "marked";

console.log(MARKDOWN);

document.body.innerHTML =
  "<div id='content'>" +
  marked(MARKDOWN ? MARKDOWN : "# 测试标题\n## Test Caption");
+"</div>";
