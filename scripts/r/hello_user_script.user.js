// ==UserScript==
// @name        HelloUserScript
// @namespace   Violentmonkey Scripts
// @match       https://www.google.com/*
// @grant       none
// @version     1.0
// @author      -
// @description 9/10/2022, 2:52:23 PM
// @require https://cdn.jsdelivr.net/combine/npm/@violentmonkey/dom@2,npm/@violentmonkey/ui@0.7
// @require ../../jslib/_userscript.js
// ==/UserScript==

let btn = document.createElement("button");
btn.innerHTML = "Click Me";
btn.onclick = function () {
  findText("Terms");
};

const panel = VM.getPanel({
  content: btn,
  theme: "dark",
});
panel.wrapper.style.top = "0";

panel.setMovable(true);

// Show panel
panel.show();
