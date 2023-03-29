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
  "complete",
  () => {
    let message = getSelectedText();
    if (!message) {
      message = 'Say "hello!"';
    }
    getCompletion(message, {
      onDeltaText: (s) => {
        sendText(s);
      },
    });
  },
  "c-i"
);

async function getCompletion(content, { onText, onDeltaText }) {
  // https://platform.openai.com/docs/api-reference/making-requests
  const apiKey = "{{OPEN_AI_API_KEY}}";

  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: "gpt-3.5-turbo",
      messages: [{ role: "user", content }],
      stream: true,
    }),
  });

  if (!response.ok || !response.body) {
    console.error("OpenAI stream failed", response);
    console.error(await response.text());
    throw new Error("OpenAI stream failed");
  }

  const decoder = new TextDecoder("utf8");
  const reader = response.body.getReader();

  let result = "";

  async function readMore() {
    const { value, done } = await reader.read();

    if (done) {
      await onText(result);
    } else {
      const str = decoder.decode(value);

      // Split on newlines
      const lines = str.split(/(\r\n|\r|\n)/g);

      for (const line of lines) {
        if (!line.trim()) {
          continue;
        }

        let prefix;
        if (line.startsWith("data:")) {
          prefix = "data:";
        } else if (line.startsWith("delta:")) {
          prefix = "delta:";
        } else {
          console.error("Unexpected line:", line);
          throw new Error("Unexpected line:" + line);
        }

        const data = line.slice(prefix.length);
        if (data.trim().startsWith("[DONE]")) {
          return;
        }

        let json;
        try {
          json = JSON.parse(data);
        } catch (error) {
          console.error("Unexpected line:", data);
          throw error;
        }

        if (json.content) {
        } else if (json.choices) {
          const delta = json.choices[0].delta.content;
          if (delta) {
            result += delta;
            if (onDeltaText) {
              onDeltaText(delta);
            }
          }
        } else {
          console.warn("Unexpected line:", json);
        }
      }

      if (onText) {
        onText(result);
      }

      await readMore();
    }
  }

  await readMore();

  return result;
}
