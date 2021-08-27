export function updateCodeBlocks() {
  const codeElement = document.querySelector("pre > code");
  console.log(`className for pre > code element: ${codeElement.className}`);
  const lang = codeElement.className.replace("language-", "");

  const newItem = document.createElement("textarea");
  newItem.innerHTML = codeElement.innerHTML;
  codeElement.parentNode.parentNode.replaceChild(
    newItem,
    codeElement.parentNode
  );

  const editor = CodeMirror.fromTextArea(newItem, {
    mode: "text/javascript",
    lineNumbers: true,
    styleActiveLine: true,
    matchBrackets: true,
    lineWrapping: true,
    readOnly: "nocursor",
  });
  window.editor = editor;
  editor.setOption("theme", "one-dark");

  document.onkeyup = function (e) {
    if (e.ctrlKey && e.which == 66) {
      const from = editor.getCursor("start");
      const to = editor.getCursor("end");
      editor.markText(from, to, { className: "mark" });
    }
  };

  // Set language mode.
  if (lang === "js") {
    editor.setOption("mode", "text/javascript");
  } else if (lang == "c++") {
    editor.setOption("mode", "text/x-c++src");
  } else if (lang == "py") {
    editor.setOption("mode", "python");
  } else if (lang == "sql") {
    editor.setOption("mode", "text/x-sql");
  } else if (lang == "html") {
    editor.setOption("mode", "text/html");
  }
}
