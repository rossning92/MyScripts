// ==UserScript==
// @name        chatgpt
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
    getCompletions('Say "hello!"').then((s) => {
      sendText(s);
    });
  },
  "c-i"
);

function getCompletions(content) {
  return new Promise((resolve, reject) => {
    // https://platform.openai.com/docs/api-reference/making-requests
    const apiKey = "{{OPEN_AI_API_KEY}}";

    fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "gpt-3.5-turbo",
        messages: [{ role: "user", content }],
        temperature: 0.7,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        const content = data["choices"][0]["message"]["content"];
        console.log(content);
        resolve(content);
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  });
}
