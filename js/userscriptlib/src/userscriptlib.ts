import { register } from "@violentmonkey/shortcut";
import * as Toastify from "toastify-js";
import "toastify-js/src/toastify.css";
import { Pane } from "tweakpane";

export {};

const pane = new Pane({
  title: "-",
  container: createContainer(),
  expanded: false,
});

declare global {
  interface Navigator {
    msSaveOrOpenBlob: any;
  }
  var GM_xmlhttpRequest: any;

  function addButton(name: string, onclick: () => void, hotkey?: string): void;
  function addText(text: string, { color = "black" }: { color?: string }): void;
  function addTextarea(): void;
  function findElementByXPath(exp: string): Node;
  function findElementByText(text: string): Node;
  function waitForSelector(selector: string): Promise<unknown>;
  function waitForText(text: string): Promise<unknown>;
  function waitForXPath(xpath: string): Promise<unknown>;
  function saveAsFile(data: string, filename: string, type: string): void;
  function download(url: string, filename?: string): void;
  function exec(args: string | string[]): Promise<string>;
  function openInNewWindow(url: string): void;
  function getSelectedText(): string | null;
  function sendText(text: string): void;
  function showToast(text: string): void;
}

const _global = window /* browser */ || global; /* node */

function createContainer() {
  const container = document.createElement("div");
  container.style.position = "fixed";
  container.style.top = "0";
  container.style.left = "0";
  container.style.zIndex = "9999";
  document.body.appendChild(container);

  const moveable = false;
  if (moveable) {
    container.addEventListener("mousedown", (ev) => {
      ev.preventDefault();

      let x = ev.clientX;
      let y = ev.clientY;

      const onMouseMove = (ev: MouseEvent) => {
        ev.preventDefault();

        const relX = x - ev.clientX;
        const relY = y - ev.clientY;

        x = ev.clientX;
        y = ev.clientY;

        container.style.top = `${container.offsetTop - relY}px`;
        container.style.left = `${container.offsetLeft - relX}px`;
      };

      const onMouseUp = () => {
        document.removeEventListener("mouseup", onMouseUp);
        document.removeEventListener("mousemove", onMouseMove);
      };

      document.addEventListener("mouseup", onMouseUp);
      document.addEventListener("mousemove", onMouseMove);
    });
  }

  return container;
}

function waitFor(evaluate: () => Node | null) {
  const evaluateWrapper = () => {
    const ele = evaluate();
    if (ele && ele instanceof HTMLElement) {
      ele.scrollIntoView();
      ele.style.backgroundColor = "#FDFF47";
    }
    return ele;
  };

  return new Promise((resolve) => {
    const ele = evaluateWrapper();
    if (ele) {
      return resolve(ele);
    }

    const observer = new MutationObserver((mutations) => {
      const ele = evaluateWrapper();
      if (ele) {
        resolve(ele);
        observer.disconnect();
      }
    });
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  });
}

_global.addButton = (name, onclick, hotkey) => {
  if (hotkey) {
    name += ` (${hotkey})`;
    register(hotkey, onclick);
  }
  const button = pane.addButton({
    title: name,
  });
  button.on("click", () => {
    onclick();
  });
};

_global.addText = (text, { color = "black" }) => {
  const div = document.createElement("div");
  div.textContent = text;
  div.style.color = color;
  createContainer().appendChild(div);
};

_global.findElementByXPath = (exp) => {
  const query = document.evaluate(
    exp,
    document,
    null,
    XPathResult.FIRST_ORDERED_NODE_TYPE,
    null
  );
  return query.singleNodeValue;
};

_global.findElementByText = (text) => {
  return findElementByXPath(`//*[text() = '${text}']`);
};

_global.waitForSelector = (selector) => {
  return waitFor(() => document.querySelector(selector));
};

_global.waitForText = (text) => {
  return waitFor(() => findElementByText(text));
};

_global.waitForXPath = (xpath) => {
  return waitFor(() => findElementByXPath(xpath));
};

_global.saveAsFile = (data, filename, type = "text/plain") => {
  var file = new Blob([data], { type: type });
  if (window.navigator.msSaveOrOpenBlob)
    // IE10+
    window.navigator.msSaveOrOpenBlob(file, filename);
  else {
    // Others
    var a = document.createElement("a"),
      url = URL.createObjectURL(file);
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(function () {
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    }, 0);
  }
};

_global.download = (url, filename) => {
  fetch(url)
    .then((response) => response.blob())
    .then((blob) => {
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = filename || url.split("/").pop().split("?")[0];
      link.click();
    })
    .catch(console.error);
};

_global.exec = (args) => {
  if (!GM_xmlhttpRequest) {
    alert('ERROR: please make sure "@grant GM_xmlhttpRequest" is present.');
    return;
  }

  return new Promise((resolve) => {
    GM_xmlhttpRequest({
      method: "POST",
      url: "http://127.0.0.1:4312/exec",
      responseType: "text",
      data: JSON.stringify({ args }),
      headers: {
        "Content-Type": "application/json; charset=UTF-8",
      },
      onload: (response: any) => {
        resolve(response.responseText);
      },
    });
  });
};

_global.openInNewWindow = (url) => {
  window.open(url, "_blank");
};

_global.getSelectedText = () => {
  let selected = window.getSelection().toString().trim();
  if (selected) {
    return selected;
  } else {
    return null;
  }
};

function getActiveElement(doc: Document = window.document): Element | null {
  // Check if the active element is in the main web or iframe
  if (doc.body === doc.activeElement || doc.activeElement.tagName == "IFRAME") {
    // Get iframes
    var iframes = doc.getElementsByTagName("iframe");
    for (var i = 0; i < iframes.length; i++) {
      // Recall
      var focused = getActiveElement(iframes[i].contentWindow.document);
      if ((focused as any) !== null) {
        return focused; // The focused
      }
    }
  } else {
    return doc.activeElement;
  }

  return null;
}

_global.sendText = (text) => {
  const el = getActiveElement();
  if (el) {
    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      const [start, end] = [el.selectionStart, el.selectionEnd];
      el.setRangeText(text, start, end, "end");
    } else {
      // simulate key press
      for (let i = 0; i < text.length; i++) {
        const event1 = new KeyboardEvent("keypress", {
          bubbles: true,
          cancelable: true,
          keyCode: text.charCodeAt(i),
        });
        el.dispatchEvent(event1);
      }
    }
  }
};

_global.addTextarea = () => {
  const params = {
    text: "",
  };
  pane.addMonitor(params, "text", {
    interval: 1000,
    multiline: true,
    lineCount: 5,
  });
  return params;
};

_global.showToast = (s) => {
  Toastify({ text: s }).showToast();
};
