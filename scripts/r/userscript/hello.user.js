// ==UserScript==
// @name        hello
// @namespace   Violentmonkey Scripts
// @match       *://*/*
// @grant       GM_xmlhttpRequest
// @version     1.0
// @author      -
// @description Description
// @require     http://127.0.0.1:4312/js/userscriptlib/dist/userscriptlib.js
// ==/UserScript==

addButton(
  "Hello",
  () => {
    alert("Hello, World!");
  },
  "c-i"
);
