/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
(function webpackUniversalModuleDefinition(root, factory) {
	if(typeof exports === 'object' && typeof module === 'object')
		module.exports = factory();
	else if(typeof define === 'function' && define.amd)
		define([], factory);
	else {
		var a = factory();
		for(var i in a) (typeof exports === 'object' ? exports : root)[i] = a[i];
	}
})(self, () => {
return /******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "./node_modules/@violentmonkey/shortcut/dist/index.esm.js":
/*!****************************************************************!*\
  !*** ./node_modules/@violentmonkey/shortcut/dist/index.esm.js ***!
  \****************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"KeyboardService\": () => (/* binding */ KeyboardService),\n/* harmony export */   \"aliases\": () => (/* binding */ aliases),\n/* harmony export */   \"disable\": () => (/* binding */ disable),\n/* harmony export */   \"enable\": () => (/* binding */ enable),\n/* harmony export */   \"handleKey\": () => (/* binding */ handleKey),\n/* harmony export */   \"modifierSymbols\": () => (/* binding */ modifierSymbols),\n/* harmony export */   \"modifiers\": () => (/* binding */ modifiers),\n/* harmony export */   \"normalizeKey\": () => (/* binding */ normalizeKey),\n/* harmony export */   \"normalizeSequence\": () => (/* binding */ normalizeSequence),\n/* harmony export */   \"parseCondition\": () => (/* binding */ parseCondition),\n/* harmony export */   \"register\": () => (/* binding */ register),\n/* harmony export */   \"reprKey\": () => (/* binding */ reprKey),\n/* harmony export */   \"reprShortcut\": () => (/* binding */ reprShortcut)\n/* harmony export */ });\n/*! @violentmonkey/shortcut v1.2.6 | ISC License */\nfunction _extends() {\n  _extends = Object.assign || function (target) {\n    for (var i = 1; i < arguments.length; i++) {\n      var source = arguments[i];\n\n      for (var key in source) {\n        if (Object.prototype.hasOwnProperty.call(source, key)) {\n          target[key] = source[key];\n        }\n      }\n    }\n\n    return target;\n  };\n\n  return _extends.apply(this, arguments);\n}\n\nconst isMacintosh = navigator.userAgent.includes('Macintosh');\nconst modifiers = {\n  c: 'c',\n  s: 's',\n  a: 'a',\n  m: 'm',\n  ctrl: 'c',\n  control: 'c',\n  // macOS\n  shift: 's',\n  alt: 'a',\n  meta: 'm',\n  ctrlcmd: isMacintosh ? 'm' : 'c'\n};\nconst modifierSymbols = {\n  c: '^',\n  s: '⇧',\n  a: '⌥',\n  m: '⌘'\n};\nconst aliases = {\n  arrowup: 'up',\n  arrowdown: 'down',\n  arrowleft: 'left',\n  arrowright: 'right',\n  enter: 'cr',\n  escape: 'esc',\n  ' ': 'space'\n};\nfunction reprKey(base, mod, caseSensitive = false) {\n  const {\n    c,\n    s,\n    a,\n    m\n  } = mod;\n  if (!caseSensitive || base.length > 1) base = base.toLowerCase();\n  base = aliases[base] || base;\n  return [m && 'm', c && 'c', s && 's', a && 'a', base].filter(Boolean).join('-');\n}\nfunction normalizeKey(shortcut, caseSensitive = false) {\n  const parts = shortcut.split('-');\n  const base = parts.pop();\n  const modifierState = {};\n\n  for (const part of parts) {\n    const key = modifiers[part.toLowerCase()];\n    if (!key) throw new Error(`Unknown modifier key: ${part}`);\n    modifierState[key] = true;\n  }\n\n  return reprKey(base, modifierState, caseSensitive);\n}\nfunction normalizeSequence(sequence, caseSensitive) {\n  return sequence.split(' ').map(key => normalizeKey(key, caseSensitive));\n}\nfunction parseCondition(condition) {\n  return condition.split('&&').map(key => {\n    key = key.trim();\n    if (!key) return;\n\n    if (key[0] === '!') {\n      return {\n        not: true,\n        field: key.slice(1).trim()\n      };\n    }\n\n    return {\n      not: false,\n      field: key\n    };\n  }).filter(Boolean);\n}\nfunction reprShortcut(shortcut, caseSensitive = false) {\n  const parts = normalizeKey(shortcut, caseSensitive).split('-');\n  let base = parts.pop();\n  base = base[0].toUpperCase() + base.slice(1);\n  const modifiers = parts.map(p => modifierSymbols[p]).filter(Boolean);\n  return [...modifiers, base].join('');\n}\n\nclass KeyNode {\n  constructor() {\n    this.children = new Map();\n    this.shortcuts = new Set();\n  }\n\n  add(sequence, shortcut) {\n    let node = this;\n\n    for (const key of sequence) {\n      let child = node.children.get(key);\n\n      if (!child) {\n        child = new KeyNode();\n        node.children.set(key, child);\n      }\n\n      node = child;\n    }\n\n    node.shortcuts.add(shortcut);\n  }\n\n  get(sequence) {\n    let node = this;\n\n    for (const key of sequence) {\n      node = node.children.get(key);\n      if (!node) return null;\n    }\n\n    return node;\n  }\n\n  remove(sequence, shortcut) {\n    let node = this;\n    const ancestors = [node];\n\n    for (const key of sequence) {\n      node = node.children.get(key);\n      if (!node) return;\n      ancestors.push(node);\n    }\n\n    if (shortcut) node.shortcuts.delete(shortcut);else node.shortcuts.clear();\n    let i = ancestors.length - 1;\n\n    while (i > 1) {\n      node = ancestors[i];\n      if (node.shortcuts.size || node.children.size) break;\n      const last = ancestors[i - 1];\n      last.children.delete(sequence[i - 1]);\n      i -= 1;\n    }\n  }\n\n}\n\nclass KeyboardService {\n  constructor() {\n    this._context = {};\n    this._conditionData = {};\n    this._dataCI = [];\n    this._dataCS = [];\n    this._rootCI = new KeyNode();\n    this._rootCS = new KeyNode();\n    this.options = {\n      sequenceTimeout: 500\n    };\n\n    this._reset = () => {\n      this._curCI = null;\n      this._curCS = null;\n\n      this._resetTimer();\n    };\n\n    this.handleKey = e => {\n      // Chrome sends a trusted keydown event with no key when choosing from autofill\n      if (!e.key || e.key.length > 1 && modifiers[e.key.toLowerCase()]) return;\n\n      this._resetTimer();\n\n      const keyCS = reprKey(e.key, {\n        c: e.ctrlKey,\n        a: e.altKey,\n        m: e.metaKey\n      }, true);\n      const keyCI = reprKey(e.key, {\n        c: e.ctrlKey,\n        s: e.shiftKey,\n        a: e.altKey,\n        m: e.metaKey\n      });\n\n      if (this.handleKeyOnce(keyCS, keyCI, false)) {\n        e.preventDefault();\n\n        this._reset();\n      }\n\n      this._timer = setTimeout(this._reset, this.options.sequenceTimeout);\n    };\n  }\n\n  _resetTimer() {\n    if (this._timer) {\n      clearTimeout(this._timer);\n      this._timer = null;\n    }\n  }\n\n  _addCondition(condition) {\n    let cache = this._conditionData[condition];\n\n    if (!cache) {\n      const value = parseCondition(condition);\n      cache = {\n        count: 0,\n        value,\n        result: this._evalCondition(value)\n      };\n      this._conditionData[condition] = cache;\n    }\n\n    cache.count += 1;\n  }\n\n  _removeCondition(condition) {\n    const cache = this._conditionData[condition];\n\n    if (cache) {\n      cache.count -= 1;\n\n      if (!cache.count) {\n        delete this._conditionData[condition];\n      }\n    }\n  }\n\n  _evalCondition(conditions) {\n    return conditions.every(cond => {\n      let value = this._context[cond.field];\n      if (cond.not) value = !value;\n      return value;\n    });\n  }\n\n  _checkShortcut(item) {\n    const cache = item.condition && this._conditionData[item.condition];\n    const enabled = !cache || cache.result;\n\n    if (item.enabled !== enabled) {\n      item.enabled = enabled;\n\n      this._enableShortcut(item);\n    }\n  }\n\n  _enableShortcut(item) {\n    const root = item.caseSensitive ? this._rootCS : this._rootCI;\n\n    if (item.enabled) {\n      root.add(item.sequence, item);\n    } else {\n      root.remove(item.sequence, item);\n    }\n  }\n\n  enable() {\n    this.disable();\n    document.addEventListener('keydown', this.handleKey);\n  }\n\n  disable() {\n    document.removeEventListener('keydown', this.handleKey);\n  }\n\n  register(key, callback, options) {\n    const {\n      caseSensitive,\n      condition\n    } = _extends({\n      caseSensitive: false\n    }, options);\n\n    const sequence = normalizeSequence(key, caseSensitive);\n    const data = caseSensitive ? this._dataCS : this._dataCI;\n    const item = {\n      sequence,\n      condition,\n      callback,\n      enabled: false,\n      caseSensitive\n    };\n    if (condition) this._addCondition(condition);\n\n    this._checkShortcut(item);\n\n    data.push(item);\n    return () => {\n      const index = data.indexOf(item);\n\n      if (index >= 0) {\n        data.splice(index, 1);\n        if (condition) this._removeCondition(condition);\n        item.enabled = false;\n\n        this._enableShortcut(item);\n      }\n    };\n  }\n\n  setContext(key, value) {\n    this._context[key] = value;\n\n    for (const cache of Object.values(this._conditionData)) {\n      cache.result = this._evalCondition(cache.value);\n    }\n\n    for (const data of [this._dataCS, this._dataCI]) {\n      for (const item of data) {\n        this._checkShortcut(item);\n      }\n    }\n  }\n\n  handleKeyOnce(keyCS, keyCI, fromRoot) {\n    var _curCS, _curCI;\n\n    let curCS = this._curCS;\n    let curCI = this._curCI;\n\n    if (fromRoot || !curCS && !curCI) {\n      // set fromRoot to true to avoid another retry\n      fromRoot = true;\n      curCS = this._rootCS;\n      curCI = this._rootCI;\n    }\n\n    if (curCS) curCS = curCS.get([keyCS]);\n    if (curCI) curCI = curCI.get([keyCI]);\n    const shortcuts = [...(curCI ? curCI.shortcuts : []), ...(curCS ? curCS.shortcuts : [])].reverse();\n    this._curCS = curCS;\n    this._curCI = curCI;\n\n    if (!fromRoot && !shortcuts.length && !((_curCS = curCS) != null && _curCS.children.size) && !((_curCI = curCI) != null && _curCI.children.size)) {\n      // Nothing is matched with the last key, rematch from root\n      return this.handleKeyOnce(keyCS, keyCI, true);\n    }\n\n    for (const shortcut of shortcuts) {\n      try {\n        shortcut.callback();\n      } catch (_unused) {// ignore\n      }\n\n      return true;\n    }\n  }\n\n}\nlet service;\n\nfunction getService() {\n  if (!service) {\n    service = new KeyboardService();\n    service.enable();\n  }\n\n  return service;\n}\n\nconst register = (...args) => getService().register(...args);\nconst enable = () => getService().enable();\nconst disable = () => getService().disable();\nconst handleKey = (...args) => getService().handleKey(...args);\n\n\n\n\n//# sourceURL=webpack://userscriptlib/./node_modules/@violentmonkey/shortcut/dist/index.esm.js?");

/***/ }),

/***/ "./src/userscriptlib.ts":
/*!******************************!*\
  !*** ./src/userscriptlib.ts ***!
  \******************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"addButton\": () => (/* binding */ addButton),\n/* harmony export */   \"addText\": () => (/* binding */ addText),\n/* harmony export */   \"download\": () => (/* binding */ download),\n/* harmony export */   \"findElementByText\": () => (/* binding */ findElementByText),\n/* harmony export */   \"findElementByXPath\": () => (/* binding */ findElementByXPath),\n/* harmony export */   \"openInNewWindow\": () => (/* binding */ openInNewWindow),\n/* harmony export */   \"saveAsFile\": () => (/* binding */ saveAsFile),\n/* harmony export */   \"waitForSelector\": () => (/* binding */ waitForSelector),\n/* harmony export */   \"waitForText\": () => (/* binding */ waitForText),\n/* harmony export */   \"waitForXPath\": () => (/* binding */ waitForXPath)\n/* harmony export */ });\n/* harmony import */ var _violentmonkey_shortcut__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @violentmonkey/shortcut */ \"./node_modules/@violentmonkey/shortcut/dist/index.esm.js\");\n\nlet _container;\nfunction getContainer() {\n    if (_container) {\n        return _container;\n    }\n    _container = document.createElement(\"div\");\n    _container.style.position = \"fixed\";\n    _container.style.top = \"0\";\n    _container.style.left = \"0\";\n    _container.style.padding = \"8px\";\n    _container.style.zIndex = \"9999\";\n    _container.style.backgroundColor = \"rgba(0, 0, 0, 0.1)\";\n    document.body.appendChild(_container);\n    _container.addEventListener(\"mousedown\", (ev) => {\n        ev.preventDefault();\n        let x = ev.clientX;\n        let y = ev.clientY;\n        const onMouseMove = (ev) => {\n            ev.preventDefault();\n            const relX = x - ev.clientX;\n            const relY = y - ev.clientY;\n            x = ev.clientX;\n            y = ev.clientY;\n            _container.style.top = `${_container.offsetTop - relY}px`;\n            _container.style.left = `${_container.offsetLeft - relX}px`;\n        };\n        const onMouseUp = () => {\n            document.removeEventListener(\"mouseup\", onMouseUp);\n            document.removeEventListener(\"mousemove\", onMouseMove);\n        };\n        document.addEventListener(\"mouseup\", onMouseUp);\n        document.addEventListener(\"mousemove\", onMouseMove);\n    });\n    return _container;\n}\nfunction addButton(name, onclick, hotkey) {\n    const button = document.createElement(\"button\");\n    button.style.backgroundColor = \"#ccc\";\n    button.style.border = \"1px solid black\";\n    button.style.color = \"#000\";\n    button.style.display = \"inline-block\";\n    button.style.padding = \"2px 8px\";\n    button.innerHTML = name;\n    if (hotkey) {\n        button.innerHTML += ` (${hotkey})`;\n    }\n    button.onclick = onclick;\n    getContainer().appendChild(button);\n    if (hotkey) {\n        (0,_violentmonkey_shortcut__WEBPACK_IMPORTED_MODULE_0__.register)(hotkey, onclick);\n    }\n}\nfunction addText(text, { color = \"black\" } = {}) {\n    const div = document.createElement(\"div\");\n    div.innerHTML = text;\n    div.style.color = color;\n    getContainer().appendChild(div);\n}\nfunction findElementByXPath(exp) {\n    const query = document.evaluate(exp, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);\n    return query.singleNodeValue;\n}\nfunction findElementByText(text) {\n    return findElementByXPath(`//*[text() = '${text}']`);\n}\nfunction waitFor(evaluate) {\n    const evaluateWrapper = () => {\n        const ele = evaluate();\n        if (ele && ele instanceof HTMLElement) {\n            ele.scrollIntoView();\n            ele.style.backgroundColor = \"#FDFF47\";\n        }\n        return ele;\n    };\n    return new Promise((resolve) => {\n        const ele = evaluateWrapper();\n        if (ele) {\n            return resolve(ele);\n        }\n        const observer = new MutationObserver((mutations) => {\n            const ele = evaluateWrapper();\n            if (ele) {\n                resolve(ele);\n                observer.disconnect();\n            }\n        });\n        observer.observe(document.body, {\n            childList: true,\n            subtree: true,\n        });\n    });\n}\nfunction waitForSelector(selector) {\n    return waitFor(() => document.querySelector(selector));\n}\nfunction waitForText(text) {\n    return waitFor(() => findElementByText(text));\n}\nfunction waitForXPath(xpath) {\n    return waitFor(() => findElementByXPath(xpath));\n}\nfunction saveAsFile(data, filename, type = \"text/plain\") {\n    var file = new Blob([data], { type: type });\n    if (window.navigator.msSaveOrOpenBlob)\n        window.navigator.msSaveOrOpenBlob(file, filename);\n    else {\n        var a = document.createElement(\"a\"), url = URL.createObjectURL(file);\n        a.href = url;\n        a.download = filename;\n        document.body.appendChild(a);\n        a.click();\n        setTimeout(function () {\n            document.body.removeChild(a);\n            window.URL.revokeObjectURL(url);\n        }, 0);\n    }\n}\nfunction download(url, filename) {\n    fetch(url)\n        .then((response) => response.blob())\n        .then((blob) => {\n        const link = document.createElement(\"a\");\n        link.href = URL.createObjectURL(blob);\n        link.download = filename || url.split(\"/\").pop().split(\"?\")[0];\n        link.click();\n    })\n        .catch(console.error);\n}\nfunction openInNewWindow(url) {\n    window.open(url, \"_blank\");\n}\n\n\n//# sourceURL=webpack://userscriptlib/./src/userscriptlib.ts?");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId](module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/define property getters */
/******/ 	(() => {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = (exports, definition) => {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	(() => {
/******/ 		__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = __webpack_require__("./src/userscriptlib.ts");
/******/ 	
/******/ 	return __webpack_exports__;
/******/ })()
;
});