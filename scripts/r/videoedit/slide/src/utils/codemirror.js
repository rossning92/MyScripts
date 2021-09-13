export function updateCodeBlocks({ fontSize, scrollToLine, width } = {}) {
  const codeElement = document.querySelector("pre > code");
  if (!codeElement) {
    return;
  }

  let source = codeElement.innerText;
  console.log(`className for pre > code element: ${codeElement.className}`);
  const lang = codeElement.className.replace("language-", "");

  const newItem = document.createElement("textarea");

  const markRanges = [];
  {
    source = source.replaceAll("\\`", "\u2022");

    let array1;
    const regex1 = /`.*?`/g;
    let i = 0;
    while ((array1 = regex1.exec(source)) !== null) {
      markRanges.push([
        array1.index - i * 2,
        array1.index + array1[0].length - (i + 1) * 2,
      ]);
      i++;
    }

    source = source.replaceAll("`", "");
    source = source.replaceAll("\u2022", "`");
  }

  newItem.innerHTML = source;
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
    scrollbarStyle: "null",
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

  setLanguageMode(lang, editor);

  markRanges.forEach(([from, to]) => {
    markText(editor, from, to);
  });

  if (fontSize !== undefined) {
    const style = document.createElement("style");
    style.innerHTML = `.CodeMirror { font-size: ${fontSize}; }`;
    document.getElementsByTagName("head")[0].appendChild(style);
  }

  if (width !== undefined) {
    const style = document.createElement("style");
    style.innerHTML = `.CodeMirror { min-width: ${width}; }`;
    document.getElementsByTagName("head")[0].appendChild(style);
  }

  if (scrollToLine) {
    editor.scrollTo(
      null,
      editor.defaultTextHeight() * (parseInt(scrollToLine) - 0.5)
    );
  }
}

function setLanguageMode(lang, editor) {
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
  } else if (lang == "java") {
    editor.setOption("mode", "text/x-java");
  } else if (lang == "c") {
    editor.setOption("mode", "text/x-csrc");
  } else if (lang == "cpp") {
    editor.setOption("mode", "text/x-c++src");
  } else if (lang == "css") {
    editor.setOption("mode", "text/css");
  } else if (lang == "json") {
    editor.setOption("mode", "application/json");
  } else if (lang == "jsx") {
    editor.setOption("mode", "text/jsx");
  } else if (lang == "xml") {
    editor.setOption("mode", "application/xml");
  } else if (lang == "sh") {
    editor.setOption("mode", "text/x-sh");
  } else if (lang == "ts") {
    editor.setOption("mode", "text/x-typescript");
  } else if (lang == "tsx") {
    editor.setOption("mode", "text/jsx");
  } else if (lang == "md") {
    editor.setOption("mode", "text/x-markdown");
  } else if (lang == "yml") {
    editor.setOption("mode", "text/x-yaml");
  } else if (lang == "yaml") {
    editor.setOption("mode", "text/x-yaml");
  } else if (lang == "ini") {
    editor.setOption("mode", "text/x-ini");
  }
}

function markText(editor, from, to) {
  editor.markText(editor.posFromIndex(from), editor.posFromIndex(to), {
    className: "mark",
  });
}
