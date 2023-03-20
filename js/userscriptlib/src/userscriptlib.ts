import { register } from "@violentmonkey/shortcut";

export {};

declare global {
  interface Navigator {
    msSaveOrOpenBlob: any;
  }
  var GM_xmlhttpRequest: any;

  function addButton(name: string, onclick: () => void, hotkey?: string): void;
  function addText(text: string, { color = "black" }: { color?: string }): void;
  function findElementByXPath(exp: string): Node;
  function findElementByText(text: string): Node;
  function waitForSelector(selector: string): Promise<unknown>;
  function waitForText(text: string): Promise<unknown>;
  function waitForXPath(xpath: string): Promise<unknown>;
  function saveAsFile(data: string, filename: string, type: string): void;
  function download(url: string, filename?: string): void;
  function exec(args: string, callback?: (result: string) => void): void;
  function openInNewWindow(url: string): void;
}

const _global = window /* browser */ || global; /* node */

let _container: HTMLElement | null;

function getContainer() {
  if (_container) {
    return _container;
  }

  _container = document.createElement("div");
  _container.style.position = "fixed";
  _container.style.top = "0";
  _container.style.left = "0";
  _container.style.padding = "8px";
  _container.style.zIndex = "9999";
  _container.style.backgroundColor = "rgba(0, 0, 0, 0.1)";
  document.body.appendChild(_container);

  _container.addEventListener("mousedown", (ev) => {
    ev.preventDefault();

    let x = ev.clientX;
    let y = ev.clientY;

    const onMouseMove = (ev: MouseEvent) => {
      ev.preventDefault();

      const relX = x - ev.clientX;
      const relY = y - ev.clientY;

      x = ev.clientX;
      y = ev.clientY;

      _container.style.top = `${_container.offsetTop - relY}px`;
      _container.style.left = `${_container.offsetLeft - relX}px`;
    };

    const onMouseUp = () => {
      document.removeEventListener("mouseup", onMouseUp);
      document.removeEventListener("mousemove", onMouseMove);
    };

    document.addEventListener("mouseup", onMouseUp);
    document.addEventListener("mousemove", onMouseMove);
  });

  return _container;
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
  const button = document.createElement("button");
  button.style.backgroundColor = "#ccc";
  button.style.border = "1px solid black";
  button.style.color = "#000";
  button.style.display = "inline-block";
  button.style.padding = "2px 8px";
  button.innerHTML = name;
  if (hotkey) {
    button.innerHTML += ` (${hotkey})`;
  }
  button.onclick = onclick;

  getContainer().appendChild(button);

  if (hotkey) {
    register(hotkey, onclick);
  }
};

_global.addText = (text, { color = "black" }) => {
  const div = document.createElement("div");
  div.innerHTML = text;
  div.style.color = color;
  getContainer().appendChild(div);
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

_global.exec = (args, callback) => {
  if (!GM_xmlhttpRequest) {
    alert(
      'ERROR: please ensure "@grant GM_xmlhttpRequest" is added in user script.'
    );
    return;
  }

  GM_xmlhttpRequest({
    method: "POST",
    url: "http://127.0.0.1:4312/exec",
    responseType: "text",
    data: `args=${encodeURIComponent(args)}`,
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    onload: (response: any) => {
      if (callback) {
        callback(response.responseText);
      }
    },
  });
};

_global.openInNewWindow = (url) => {
  window.open(url, "_blank");
};