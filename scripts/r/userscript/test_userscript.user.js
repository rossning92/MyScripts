// ==UserScript==
// @name        test_userscript
// @namespace   Violentmonkey Scripts
// @match       *://*/*
// @grant       GM_xmlhttpRequest
// @version     1.0
// @author      -
// @description Description
// @require     http://127.0.0.1:4312/userscriptlib.js
// ==/UserScript==

addButton(
  "Say hello!",
  () => {
    alert("Hello, World!");
  },
  "c-i"
);

addButton("Sleep 3 secs", () => {
  sleep(() => {
    logd("Slept for 3 sec.");
  }, 3000);
});

addButton("Run calculator", () => {
  system(["calc"]);
});

addButton("Test saveData()", () => {
  saveData("test_data", { foo: "bar" }).then((result) => {
    alert(JSON.stringify(result, null, 4));
  });
});

addButton("Test loadData()", () => {
  loadData("test_data", {}).then((data) => {
    alert(JSON.stringify(data, null, 4));
  });
});
