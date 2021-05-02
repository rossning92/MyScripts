require("./title.css");

import marked from "marked";

document.body.innerHTML =
  "<div id='content'>" +
  marked(MARKDOWN ? MARKDOWN : "# 测试标题\n## Test Caption");
+"</div>";
