// ==UserScript==
// @name        run_calc
// @namespace   Violentmonkey Scripts
// @match       *://*/*
// @grant       GM_xmlhttpRequest
// @version     1.0
// @author      -
// @description Description
// @require     file://C:/Users/rossning92/Dropbox (Meta)/oculus/MyScripts/js/userscriptlib/dist/userscriptlib.js
// ==/UserScript==

addButton("run calc", () => {
  exec(["calc"]);
});
