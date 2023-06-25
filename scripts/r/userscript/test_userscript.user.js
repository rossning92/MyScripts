// ==UserScript==
// @name        test_userscript
// @namespace   Violentmonkey Scripts
// @match       https://www.google.com/
// @grant       GM_xmlhttpRequest
// @version     1.0
// @author      -
// @description Description
// @require     http://127.0.0.1:4312/userscriptlib.js
// ==/UserScript==

addButton(
  "Say Hello",
  () => {
    alert("Hello, World!");
  },
  "c-i"
);

addButton("Sleep 3 Sec", () => {
  sleep(() => {
    logd("Slept for 3 sec.");
  }, 3000);
});

addButton("Run Calc", () => {
  exec(["calc"]);
});
