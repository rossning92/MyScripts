// ==UserScript==
// @name        gmail_helper
// @namespace   Violentmonkey Scripts
// @match       https://mail.google.com/mail/*
// @grant       GM_xmlhttpRequest
// @version     1.0
// @author      -
// @description Description
// @require     http://127.0.0.1:4312/userscriptlib.js
// ==/UserScript==

addButton(
  "mark all as read",
  () => {
    waitForXPath('//*[@aria-label="More email options"]').then((el) => {
      click(el);
      waitForText("Mark all as read").then((el) => {
        click(el);
      });
    });
  },
  "a-r"
);
