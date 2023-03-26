// ==UserScript==
// @name        {{USER_SCRIPT_NAME}}
// @namespace   Violentmonkey Scripts
// @match       https://www.google.com/*
// @grant       GM_xmlhttpRequest
// @version     1.0
// @author      -
// @description Description
// @require     file://{{USER_SCRIPT_LIB}}
// ==/UserScript==

addButton(
  "Hello",
  () => {
    alert("Hello, World!");
  },
  "c-i"
);
