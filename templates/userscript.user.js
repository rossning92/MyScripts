// ==UserScript==
// @name        {{USERSCRIPT_NAME}}
// @namespace   Violentmonkey Scripts
// @match       *://*/*
// @grant       GM_xmlhttpRequest
// @version     1.0
// @author      -
// @description Description
// @require     {{USERSCRIPT_LIB}}
// ==/UserScript==

addButton(
  "Hello",
  () => {
    alert("Hello, World!");
  },
  "c-i"
);
