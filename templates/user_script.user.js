// ==UserScript==
// @name        {{USER_SCRIPT_NAME}}
// @namespace   Violentmonkey Scripts
// @match       https://www.google.com/*
// @grant       GM_xmlhttpRequest
// @version     1.0
// @author      -
// @description 9/10/2022, 2:52:23 PM
// @require https://cdn.jsdelivr.net/combine/npm/@violentmonkey/dom@2,npm/@violentmonkey/ui@0.7
// @require https://cdn.jsdelivr.net/npm/@violentmonkey/shortcut@1
// @require {{USER_SCRIPT_LIB}}
// ==/UserScript==

let btn = document.createElement("button");
btn.innerHTML = "Click Me";
btn.onclick = function () {
  findText("Terms");
};

const panel = VM.getPanel({
  content: btn,
});
panel.wrapper.style.top = "0";
panel.setMovable(true);
panel.show();

VM.shortcut.register("c-i", () => {
  alert("c-i pressed");
});
