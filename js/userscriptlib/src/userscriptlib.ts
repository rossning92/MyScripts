import { register } from "@violentmonkey/shortcut";

const defaultPanelBorderStyle = "1px solid lightgray";
const defaultPanelCollapse = false;
const defaultFontSize = "9pt";
const defaultPanelOpacity = "0.8";

export {};

declare global {
  interface Navigator {
    msSaveOrOpenBlob: any;
  }
  var GM_xmlhttpRequest: any;

  function addButton(name: string, onclick: () => void, hotkey?: string): void;
  function highlight(el: HTMLElement, text?: string): void;
  function addText(text: string, { color = "black" }: { color?: string }): void;
  function click(el: HTMLElement): void;
  function download(url: string, filename?: string): void;
  function findElementByPartialText(text: string): Node | null;
  function findElementBySelector(selector: string): Node | null;
  function findElementByText(text: string): Node | null;
  function findElementsByText(text: string): Node[];
  function findElementByXPath(exp: string): Node | null;
  function findElementsByXPath(exp: string): Node[];
  function getSelectedText(): string;
  function loadData(name: string): Promise<object>;
  function loadFile(file: string): Promise<string>;
  function logd(message: string): void;
  function openInNewWindow(url: string): void;
  function saveData(name: string, data: object): Promise<void>;
  function saveFile(file: string, content: string): Promise<void>;
  function saveTextAsFile(data: string, filename: string, type?: string): void;
  function sendKey(keyCode: number, type?: "up" | "press"): void; // test the keyCode: https://unixpapa.com/js/testkey.html
  function sendText(text: string): void;
  function sleep(callback: () => void, ms: number): void;
  function system(args: string | string[]): Promise<string>;
  function waitForPartialText(text: string): Promise<Node>;
  function waitForSelector(selector: string): Promise<Node>;
  function waitForSelectorAll(selector: string): Promise<NodeList>;
  function waitForText(text: string): Promise<Node>;
  function waitForXPath(xpath: string): Promise<Node>;
}

const _global = window /* browser */ || global; /* node */

function createPanel() {
  const panel = document.createElement("div");
  panel.style.all = "revert";
  panel.style.opacity = defaultPanelOpacity;
  panel.style.position = "fixed";
  panel.style.left = "0";
  panel.style.top = "0";
  panel.style.zIndex = "9999";
  panel.style.border = defaultPanelBorderStyle;

  addNoPrintStyle();
  panel.className = "no-print";

  document.body.appendChild(panel);
  return panel;
}

function getButtonContainer() {
  let buttonContainer = document.getElementById("userscriptlib-container");
  if (buttonContainer) {
    return buttonContainer;
  } else {
    const panel = createPanel();
    let collapsed = defaultPanelCollapse;

    function updateContainerStyle() {
      container.style.display = collapsed ? "none" : "block";
    }

    createHandle({
      panel,
      onClick: () => {
        collapsed = !collapsed;
        updateContainerStyle();
      },
    });

    const container = document.createElement("div");

    panel.appendChild(container);
    updateContainerStyle();

    buttonContainer = createButtonContainer(buttonContainer, container);
    createLogPane(container);

    return buttonContainer;
  }
}

function createButtonContainer(
  buttonContainer: HTMLElement,
  panel: HTMLDivElement
) {
  buttonContainer = document.createElement("div");
  buttonContainer.id = "userscriptlib-container";
  panel.appendChild(buttonContainer);
  return buttonContainer;
}

function createLogPane(panel: HTMLDivElement) {
  const textarea = document.createElement("textarea");
  textarea.id = "userscriptlib-log-pane";
  textarea.readOnly = true;
  textarea.rows = 5;
  textarea.style.display = "none";
  textarea.style.boxSizing = "border-box";
  textarea.style.fontSize = defaultFontSize;
  textarea.style.resize = "none";
  textarea.style.width = "100%";
  textarea.style.border = defaultPanelBorderStyle;
  panel.appendChild(textarea);
}

function logd(message: string) {
  getButtonContainer();
  const textarea = document.getElementById(
    "userscriptlib-log-pane"
  ) as HTMLTextAreaElement;
  textarea.style.display = "block";
  if (textarea.value !== "") {
    textarea.value += "\n" + message;
  } else {
    textarea.value = message;
  }
  textarea.scrollTop = textarea.scrollHeight;
}

function createHandle({
  panel,
  onClick,
}: {
  panel: HTMLDivElement;
  onClick?: () => void;
}) {
  const handle = document.createElement("div");
  handle.innerText = "[userscript]";
  handle.style.fontSize = defaultFontSize;
  handle.style.backgroundColor = "lightgray";
  handle.style.userSelect = "none";
  handle.style.cursor = "default";
  panel.appendChild(handle);

  handle.addEventListener("mousedown", (ev) => {
    ev.preventDefault();

    let lastX = ev.clientX;
    let lastY = ev.clientY;
    let mouseMoved = false;

    const onMouseMove = (ev: MouseEvent) => {
      ev.preventDefault();

      const relX = lastX - ev.clientX;
      const relY = lastY - ev.clientY;

      lastX = ev.clientX;
      lastY = ev.clientY;

      panel.style.top = `${panel.offsetTop - relY}px`;
      panel.style.left = `${panel.offsetLeft - relX}px`;

      mouseMoved = true;
    };

    const onMouseUp = () => {
      document.removeEventListener("mouseup", onMouseUp);
      document.removeEventListener("mousemove", onMouseMove);

      if (!mouseMoved && onClick) {
        onClick();
      }
    };

    document.addEventListener("mouseup", onMouseUp);
    document.addEventListener("mousemove", onMouseMove);
  });

  return handle;
}

async function waitFor<Type>(
  evaluate: () => Type | null
): Promise<Type | null> {
  const evaluateWrapper: () => Type | null = () => {
    const ele = evaluate();
    if (ele && ele instanceof HTMLElement) {
      ele.scrollIntoView();
      ele.style.backgroundColor = "#FDFF47";
    }
    return ele;
  };

  return new Promise<Type | null>((resolve) => {
    const ele = evaluateWrapper();
    if (ele) {
      resolve(ele);
      return;
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
  const button = document.createElement("button");
  button.style.backgroundColor = "white";
  button.style.border = "none";
  button.style.color = "black";
  button.style.display = "block";
  button.style.fontSize = defaultFontSize;
  button.style.margin = "0";
  button.style.padding = "0px 8px";
  button.style.width = "100%";
  button.style.textAlign = "left";
  button.textContent = name;
  if (hotkey) {
    button.textContent += ` (${hotkey})`;
  }
  button.onclick = onclick;
  getButtonContainer().appendChild(button);

  if (hotkey) {
    register(hotkey, onclick);
  }
};

_global.addText = (text, { color = "black" }) => {
  const div = document.createElement("div");
  div.textContent = text;
  div.style.color = color;
  getButtonContainer().appendChild(div);
};

_global.findElementsByXPath = (exp) => {
  const query = document.evaluate(
    exp,
    document,
    null,
    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
    null
  );
  let results: Node[] = [];
  for (let i = 0, length = query.snapshotLength; i < length; ++i) {
    results.push(query.snapshotItem(i));
  }
  return results;
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

_global.findElementBySelector = (selector) => {
  return document.querySelector(selector);
};

_global.findElementByText = (text) => {
  return findElementByXPath(`//*[text() = '${text}']`);
};

_global.findElementsByText = (text) => {
  return findElementsByXPath(`//*[text() = '${text}']`);
};

_global.findElementByPartialText = (text) => {
  return findElementByXPath(`//*[contains(text(),'${text}')]`);
};

_global.waitForSelector = (selector) => {
  return waitFor(() => document.querySelector(selector));
};

_global.waitForSelectorAll = (selector) => {
  return waitFor(() => document.querySelectorAll(selector));
};

_global.waitForText = (text) => {
  return waitFor(() => findElementByText(text));
};

_global.waitForPartialText = (text) => {
  return waitFor(() => findElementByPartialText(text));
};

_global.waitForXPath = (xpath) => {
  return waitFor(() => findElementByXPath(xpath));
};

_global.saveTextAsFile = (data, filename, type = "text/plain") => {
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

function addNoPrintStyle() {
  if (!document.getElementById("no-print-style")) {
    const style = document.createElement("style");
    style.id = "no-print-style";
    style.innerHTML = `
        @media print {
            .no-print {
                display: none !important;
            }
        }
      `;
    document.getElementsByTagName("head")[0].appendChild(style);
  }
}

function checkXmlHttpRequest() {
  if (!GM_xmlhttpRequest) {
    throw new Error(
      'ERROR: please make sure "@grant GM_xmlhttpRequest" is present.'
    );
  }
}

_global.system = (args) => {
  checkXmlHttpRequest();

  return new Promise((resolve) => {
    GM_xmlhttpRequest({
      method: "POST",
      url: "http://127.0.0.1:4312/system",
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

_global.loadData = async (name) => {
  const content = await loadFile(`${name}.json`);
  return JSON.parse(content);
};

_global.saveData = async (name, data) => {
  return saveFile(`${name}.json`, JSON.stringify(data, null, 4));
};

_global.loadFile = (file) => {
  checkXmlHttpRequest();

  return new Promise((resolve) => {
    GM_xmlhttpRequest({
      method: "POST",
      url: "http://127.0.0.1:4312/load-file",
      responseType: "json",
      data: JSON.stringify({ file }),
      headers: {
        "Content-Type": "application/json; charset=UTF-8",
      },
      onload: (resp: any) => {
        resolve(resp.response.content);
      },
    });
  });
};

_global.saveFile = (file, content) => {
  checkXmlHttpRequest();

  return new Promise((resolve) => {
    GM_xmlhttpRequest({
      method: "POST",
      url: "http://127.0.0.1:4312/save-file",
      responseType: "json",
      data: JSON.stringify({
        file,
        content,
      }),
      headers: {
        "Content-Type": "application/json; charset=UTF-8",
      },
      onload: (resp: any) => {
        resolve(resp.response);
      },
    });
  });
};

_global.openInNewWindow = (url: string) => {
  window.open(url, "_blank");
};

_global.getSelectedText = () => {
  let text = "";
  const activeEl = document.activeElement as HTMLInputElement;
  const activeElTagName = activeEl ? activeEl.tagName.toLowerCase() : null;
  if (
    activeElTagName == "textarea" ||
    (activeElTagName == "input" &&
      /^(?:text|search|password|tel|url)$/i.test(activeEl.type) &&
      typeof activeEl.selectionStart == "number")
  ) {
    text = activeEl.value.slice(activeEl.selectionStart, activeEl.selectionEnd);
  } else if (window.getSelection) {
    text = window.getSelection().toString();
  }
  return text;
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

_global.click = (el) => {
  const simulateMouseEvent = function (
    element: HTMLElement,
    eventName: string,
    coordX: number,
    coordY: number
  ) {
    element.dispatchEvent(
      new MouseEvent(eventName, {
        // view: window,
        bubbles: true,
        cancelable: true,
        clientX: coordX,
        clientY: coordY,
        button: 0,
      })
    );
  };

  var box = el.getBoundingClientRect(),
    coordX = box.left + (box.right - box.left) / 2,
    coordY = box.top + (box.bottom - box.top) / 2;

  simulateMouseEvent(el, "mousedown", coordX, coordY);
  simulateMouseEvent(el, "mouseup", coordX, coordY);
  simulateMouseEvent(el, "click", coordX, coordY);
};

_global.sendKey = (keyCode, type) => {
  const evtName = typeof type === "string" ? "key" + type : "keydown";

  const event: any = document.createEvent("HTMLEvents");
  event.initEvent(evtName, true, false);
  event.keyCode = keyCode;

  document.dispatchEvent(event);
};

_global.sleep = (callback, durationMs) => {
  const start = Date.now();

  function timer() {
    const diff = durationMs / 1000 - (((Date.now() - start) / 1000) | 0);
    const minutes = (diff / 60) | 0;
    const seconds = diff % 60 | 0;
    if (diff <= 0) {
      clearInterval(intervalID);
      callback();
    } else {
      logd(
        `${minutes < 10 ? "0" + minutes : minutes}:${
          seconds < 10 ? "0" + seconds : seconds
        }`
      );
    }
  }

  // Start the timer immediately instead of waiting for 1 second
  timer();

  const intervalID = setInterval(timer, 1000);
};

_global.highlight = (ele, message = "👆") => {
  ele.scrollIntoView({
    behavior: "auto",
    block: "center",
    inline: "center",
  });

  const tooltip = document.createElement("div");

  tooltip.style.position = "absolute";
  tooltip.style.zIndex = "9999";
  tooltip.style.backgroundColor = "rgba(255, 255, 0, 0.5)"; // semi-transparent
  tooltip.style.color = "black";
  tooltip.style.padding = "5px";
  tooltip.style.fontSize = "0.5rem";
  tooltip.style.pointerEvents = "none"; // So it doesn't interfere with any interactions

  tooltip.innerText = message;

  document.body.appendChild(tooltip);

  function positionTooltip() {
    const rect = ele.getBoundingClientRect();
    const x = rect.left + window.pageXOffset;
    const y = rect.bottom + window.pageYOffset;
    tooltip.style.left = Math.max(0, x) + "px";
    tooltip.style.top = Math.max(0, y) + "px";
  }

  // Call immediately and also on window resize
  positionTooltip();
  window.addEventListener("resize", positionTooltip);
};

_global.logd = logd;
