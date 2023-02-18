var TRange = null;

function findText(str) {
  if (parseInt(navigator.appVersion) < 4) return;
  var strFound;
  if (window.find) {
    // If browser supports window.find()
    strFound = self.find(str);
    if (!strFound) {
      strFound = self.find(str, 0, 1);
      while (self.find(str, 0, 1)) continue;
    }
  } else if (navigator.appName.indexOf("Microsoft") != -1) {
    if (TRange != null) {
      TRange.collapse(false);
      strFound = TRange.findText(str);
      if (strFound) TRange.select();
    }
    if (TRange == null || strFound == 0) {
      TRange = self.document.body.createTextRange();
      strFound = TRange.findText(str);
      if (strFound) TRange.select();
    }
  } else if (navigator.appName == "Opera") {
    alert("Opera browsers not supported, sorry...");
    return;
  }
  if (!strFound) alert("String '" + str + "' not found!");
  return;
}

var container;
function addButton(name, onclick, hotkey = null) {
  if (!container) {
    container = document.createElement("div");
    const panel = VM.getPanel({
      content: container,
    });
    panel.wrapper.style.top = "0";
    panel.setMovable(true);
    panel.show();
  }

  let button = document.createElement("button");
  button.innerHTML = name;
  if (hotkey) {
    button.innerHTML += ` (${hotkey})`;
  }
  button.onclick = onclick;
  container.appendChild(button);

  if (hotkey) {
    VM.shortcut.register(hotkey, onclick);
  }
}

function xpath(exp) {
  const node = document.evaluate(
    exp,
    document,
    null,
    XPathResult.FIRST_ORDERED_NODE_TYPE,
    null
  ).singleNodeValue;
  console.log(node);
  return node;
}

function findElementByText(text) {
  return xpath(`//*[contains(text(),'${text}')]`);
}

function waitForSelector(selector) {
  return new Promise((resolve) => {
    if (document.querySelector(selector)) {
      return resolve(document.querySelector(selector));
    }

    const observer = new MutationObserver((mutations) => {
      if (document.querySelector(selector)) {
        resolve(document.querySelector(selector));
        observer.disconnect();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  });
}

function saveAsFile(data, filename, type = "text/plain") {
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
}

function download(url, filename = undefined) {
  fetch(url)
    .then((response) => response.blob())
    .then((blob) => {
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = filename || url.split("/").pop().split("?")[0];
      link.click();
    })
    .catch(console.error);
}

function openInNewWindow(url) {
  window.open(url, "_blank");
}

/*! @violentmonkey/shortcut v1.2.6 | ISC License */
// prettier-ignore
!function(t,e){"object"==typeof exports&&"undefined"!=typeof module?e(exports):"function"==typeof define&&define.amd?define(["exports"],e):e(((t="undefined"!=typeof globalThis?globalThis:t||self).VM=t.VM||{},t.VM.shortcut=t.VM.shortcut||{}))}(this,(function(t){"use strict";function e(){return e=Object.assign||function(t){for(var e=1;e<arguments.length;e++){var n=arguments[e];for(var i in n)Object.prototype.hasOwnProperty.call(n,i)&&(t[i]=n[i])}return t},e.apply(this,arguments)}const n={c:"c",s:"s",a:"a",m:"m",ctrl:"c",control:"c",shift:"s",alt:"a",meta:"m",ctrlcmd:navigator.userAgent.includes("Macintosh")?"m":"c"},i={c:"^",s:"⇧",a:"⌥",m:"⌘"},o={arrowup:"up",arrowdown:"down",arrowleft:"left",arrowright:"right",enter:"cr",escape:"esc"," ":"space"};function s(t,e,n=!1){const{c:i,s:s,a:r,m:c}=e;return(!n||t.length>1)&&(t=t.toLowerCase()),[c&&"m",i&&"c",s&&"s",r&&"a",t=o[t]||t].filter(Boolean).join("-")}function r(t,e=!1){const i=t.split("-"),o=i.pop(),r={};for(const t of i){const e=n[t.toLowerCase()];if(!e)throw new Error(`Unknown modifier key: ${t}`);r[e]=!0}return s(o,r,e)}function c(t,e){return t.split(" ").map((t=>r(t,e)))}function a(t){return t.split("&&").map((t=>{if(t=t.trim())return"!"===t[0]?{not:!0,field:t.slice(1).trim()}:{not:!1,field:t}})).filter(Boolean)}class l{constructor(){this.children=new Map,this.shortcuts=new Set}add(t,e){let n=this;for(const e of t){let t=n.children.get(e);t||(t=new l,n.children.set(e,t)),n=t}n.shortcuts.add(e)}get(t){let e=this;for(const n of t)if(e=e.children.get(n),!e)return null;return e}remove(t,e){let n=this;const i=[n];for(const e of t){if(n=n.children.get(e),!n)return;i.push(n)}e?n.shortcuts.delete(e):n.shortcuts.clear();let o=i.length-1;for(;o>1&&(n=i[o],!n.shortcuts.size&&!n.children.size);){i[o-1].children.delete(t[o-1]),o-=1}}}class h{constructor(){this._context={},this._conditionData={},this._dataCI=[],this._dataCS=[],this._rootCI=new l,this._rootCS=new l,this.options={sequenceTimeout:500},this._reset=()=>{this._curCI=null,this._curCS=null,this._resetTimer()},this.handleKey=t=>{if(!t.key||t.key.length>1&&n[t.key.toLowerCase()])return;this._resetTimer();const e=s(t.key,{c:t.ctrlKey,a:t.altKey,m:t.metaKey},!0),i=s(t.key,{c:t.ctrlKey,s:t.shiftKey,a:t.altKey,m:t.metaKey});this.handleKeyOnce(e,i,!1)&&(t.preventDefault(),this._reset()),this._timer=setTimeout(this._reset,this.options.sequenceTimeout)}}_resetTimer(){this._timer&&(clearTimeout(this._timer),this._timer=null)}_addCondition(t){let e=this._conditionData[t];if(!e){const n=a(t);e={count:0,value:n,result:this._evalCondition(n)},this._conditionData[t]=e}e.count+=1}_removeCondition(t){const e=this._conditionData[t];e&&(e.count-=1,e.count||delete this._conditionData[t])}_evalCondition(t){return t.every((t=>{let e=this._context[t.field];return t.not&&(e=!e),e}))}_checkShortcut(t){const e=t.condition&&this._conditionData[t.condition],n=!e||e.result;t.enabled!==n&&(t.enabled=n,this._enableShortcut(t))}_enableShortcut(t){const e=t.caseSensitive?this._rootCS:this._rootCI;t.enabled?e.add(t.sequence,t):e.remove(t.sequence,t)}enable(){this.disable(),document.addEventListener("keydown",this.handleKey)}disable(){document.removeEventListener("keydown",this.handleKey)}register(t,n,i){const{caseSensitive:o,condition:s}=e({caseSensitive:!1},i),r=c(t,o),a=o?this._dataCS:this._dataCI,l={sequence:r,condition:s,callback:n,enabled:!1,caseSensitive:o};return s&&this._addCondition(s),this._checkShortcut(l),a.push(l),()=>{const t=a.indexOf(l);t>=0&&(a.splice(t,1),s&&this._removeCondition(s),l.enabled=!1,this._enableShortcut(l))}}setContext(t,e){this._context[t]=e;for(const t of Object.values(this._conditionData))t.result=this._evalCondition(t.value);for(const t of[this._dataCS,this._dataCI])for(const e of t)this._checkShortcut(e)}handleKeyOnce(t,e,n){var i,o;let s=this._curCS,r=this._curCI;(n||!s&&!r)&&(n=!0,s=this._rootCS,r=this._rootCI),s&&(s=s.get([t])),r&&(r=r.get([e]));const c=[...r?r.shortcuts:[],...s?s.shortcuts:[]].reverse();if(this._curCS=s,this._curCI=r,!(n||c.length||null!=(i=s)&&i.children.size||null!=(o=r)&&o.children.size))return this.handleKeyOnce(t,e,!0);for(const t of c){try{t.callback()}catch(t){}return!0}}}let d;function u(){return d||(d=new h,d.enable()),d}const f=(...t)=>u().register(...t);"undefined"!=typeof VM&&(VM.registerShortcut=(t,e)=>{console.warn("[vm-shortcut] VM.registerShortcut is deprecated in favor of VM.shortcut.register, and will be removed in 2.x"),f(t,e)}),t.KeyboardService=h,t.aliases=o,t.disable=()=>u().disable(),t.enable=()=>u().enable(),t.handleKey=(...t)=>u().handleKey(...t),t.modifierSymbols=i,t.modifiers=n,t.normalizeKey=r,t.normalizeSequence=c,t.parseCondition=a,t.register=f,t.reprKey=s,t.reprShortcut=function(t,e=!1){const n=r(t,e).split("-");let o=n.pop();return o=o[0].toUpperCase()+o.slice(1),[...n.map((t=>i[t])).filter(Boolean),o].join("")}}));
//# sourceMappingURL=/sm/9814b670a84778013424bd86cc9c825a15b9290797fefea0480b4949dbed3ce9.map
