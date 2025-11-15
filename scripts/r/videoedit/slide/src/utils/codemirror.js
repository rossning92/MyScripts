import { angular } from "@codemirror/lang-angular";
import { cpp } from "@codemirror/lang-cpp";
import { css } from "@codemirror/lang-css";
import { go } from "@codemirror/lang-go";
import { html } from "@codemirror/lang-html";
import { java } from "@codemirror/lang-java";
import { javascript } from "@codemirror/lang-javascript";
import { jinja } from "@codemirror/lang-jinja";
import { json } from "@codemirror/lang-json";
import { less } from "@codemirror/lang-less";
import { lezer } from "@codemirror/lang-lezer";
import { liquid } from "@codemirror/lang-liquid";
import { markdown } from "@codemirror/lang-markdown";
import { php } from "@codemirror/lang-php";
import { python } from "@codemirror/lang-python";
import { rust } from "@codemirror/lang-rust";
import { sass } from "@codemirror/lang-sass";
import { sql } from "@codemirror/lang-sql";
import { vue } from "@codemirror/lang-vue";
import { wast } from "@codemirror/lang-wast";
import { xml } from "@codemirror/lang-xml";
import { yaml } from "@codemirror/lang-yaml";
import { EditorView, basicSetup } from "codemirror";
import { draculaInit } from "./dracula.js";

export function initializeCodeBlocks({
  fontSize,
  scrollToLine,
  width,
  height,
  lineNumbers = true,
} = {}) {
  document.querySelectorAll("pre > code").forEach((codeElement) => {
    const lang = codeElement.className.replace("language-", "");
    const langExtension = getLanguageExtension(lang);

    const preElement = codeElement.parentElement;
    const startTag = "<sel>";
    const endTag = "</sel>";

    // Check if we should highlight some selected code.
    let selection;
    let code = codeElement.textContent;
    const startIndex = code.indexOf(startTag);
    const endIndex = code.indexOf(endTag);
    if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
      const before = code.slice(0, startIndex);
      const selected = code.slice(startIndex + startTag.length, endIndex);
      const after = code.slice(endIndex + endTag.length);

      code = before + selected + after;
      selection = {
        anchor: before.length,
        head: before.length + selected.length,
      };
    }

    const editorContainer = document.createElement("div");
    preElement.replaceWith(editorContainer);

    const view = new EditorView({
      doc: code,
      extensions: [basicSetup, langExtension, draculaInit()],
      parent: editorContainer,
    });

    if (selection) {
      view.dispatch({
        selection,
        scrollIntoView: true,
        effects: [EditorView.scrollIntoView(selection.anchor, { y: "center" })],
      });
    }

    // Test smooth scrolling
    // setTimeout(() => {
    //   view.scrollDOM.scrollTo({ top: 100, behavior: "smooth" });
    // }, 1000);
  });
}

function getLanguageExtension(lang) {
  switch (lang) {
    case "js":
    case "javascript":
      return javascript();
    case "ts":
    case "typescript":
      return javascript({ typescript: true });
    case "jsx":
      return javascript({ jsx: true });
    case "tsx":
      return javascript({ jsx: true, typescript: true });
    case "py":
    case "python":
      return python();
    case "sql":
      return sql();
    case "html":
      return html();
    case "css":
      return css();
    case "json":
      return json();
    case "java":
      return java();
    case "c":
    case "cpp":
    case "c++":
      return cpp();
    case "md":
    case "markdown":
      return markdown();
    case "xml":
      return xml();
    case "yml":
    case "yaml":
      return yaml();
    case "go":
      return go();
    case "rust":
      return rust();
    case "php":
      return php();
    case "liquid":
      return liquid();
    case "jinja":
      return jinja();
    case "vue":
      return vue();
    case "angular":
      return angular();
    case "sass":
      return sass();
    case "less":
      return less();
    case "wast":
      return wast();
    case "lezer":
      return lezer();
    case "example":
      return example();
    default:
      return javascript();
  }
}
