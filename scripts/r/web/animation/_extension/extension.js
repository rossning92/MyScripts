const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");
const process = require("process");
const fs = require("fs");

var child;

function openFileUnderCursor() {
  if (!isDocumentActive) {
    return;
  }

  const editor = vscode.window.activeTextEditor;

  if (editor.selection.isEmpty) {
    const position = editor.selection.active;
    const line = editor.document.lineAt(position).text;
    const found = line.match(/'(.*?)'/);
    if (found !== null) {
      const filePath = path.join(getProjectDir(), found[1]);

      const args = ["-m", "r.open_with.open_with_", filePath];
      cp.spawnSync("python", args);
    }
  }
}

function initializeDecorations(context) {
  let timeout = undefined;

  const decorationType = vscode.window.createTextEditorDecorationType({
    cursor: "crosshair",
    // use a themable color. See package.json for the declaration and default values.
    backgroundColor: { id: "myextension.largeNumberBackground" },
  });
  let activeEditor = vscode.window.activeTextEditor;
  function updateDecorations() {
    if (!activeEditor) {
      return;
    }
    const regEx = /\d+/g;
    const text = activeEditor.document.getText();
    const smallNumbers = [];
    const largeNumbers = [];
    let match;
    const myContent = new vscode.MarkdownString(
      "*yoyo* [link](command:yo.hello)"
    );
    myContent.isTrusted = true;

    while ((match = regEx.exec(text))) {
      const startPos = activeEditor.document.positionAt(match.index);
      const endPos = activeEditor.document.positionAt(
        match.index + match[0].length
      );
      const decoration = {
        range: new vscode.Range(startPos, endPos),
        hoverMessage: myContent,
      };
      if (match[0].length < 3) {
        smallNumbers.push(decoration);
      } else {
        largeNumbers.push(decoration);
      }
    }

    activeEditor.setDecorations(decorationType, largeNumbers);
  }

  function triggerUpdateDecorations() {
    if (timeout) {
      clearTimeout(timeout);
      timeout = undefined;
    }
    timeout = setTimeout(updateDecorations, 500);
  }

  if (activeEditor) {
    triggerUpdateDecorations();
  }

  vscode.window.onDidChangeActiveTextEditor(
    (editor) => {
      activeEditor = editor;
      if (editor) {
        triggerUpdateDecorations();
      }
    },
    null,
    context.subscriptions
  );

  vscode.workspace.onDidChangeTextDocument(
    (event) => {
      if (activeEditor && event.document === activeEditor.document) {
        triggerUpdateDecorations();
      }
    },
    null,
    context.subscriptions
  );
}

function isDocumentActive() {
  const editor = vscode.window.activeTextEditor;
  if (editor == null) {
    return false;
  }

  const fileName = editor.document.fileName;
  if (path.basename(fileName) != "index.md") {
    return false;
  }

  return true;
}

function getProjectDir() {
  const editor = vscode.window.activeTextEditor;
  if (editor == null) {
    return null;
  }

  return path.dirname(editor.document.fileName);
}

function getFiles(dir, filter, files = []) {
  fs.readdirSync(dir).forEach((file) => {
    const filePath = path.join(dir, file);
    const fileStat = fs.lstatSync(filePath);

    if (fileStat.isDirectory()) {
      // If not in excluded folders
      if (!/(tmp|out)$/g.test(file)) {
        getFiles(filePath, filter, files);
      }
    } else if (filter(filePath)) {
      files.push(filePath);
    }
  });

  return files;
}

function registerAutoComplete(context) {
  const provider = vscode.languages.registerCompletionItemProvider(
    { pattern: "**/index.md" },
    {
      provideCompletionItems(document, position) {
        const projectDir = getProjectDir();
        if (projectDir == null) return undefined;

        if (
          position.character < 2 ||
          document.lineAt(position).text[position.character - 2] !== "{"
        ) {
          return undefined;
        }

        let files = [];
        getFiles(projectDir, (x) => /\.(png|jpg|mp4)$/g.test(x), files);
        files = files.sort(function (a, b) {
          return -(
            fs.statSync(a).mtime.getTime() - fs.statSync(b).mtime.getTime()
          );
        });

        // Convert to relative path
        files = files.map((x) =>
          x.replace(projectDir + path.sep, "").replace(/\\/g, "/")
        );

        const completionItems = [];
        files.forEach((file, i) => {
          const label = ` clip('${file}') `; // Auto closing single quote
          const item = new vscode.CompletionItem(
            label,
            vscode.CompletionItemKind.File
          );
          item.sortText = i.toString().padStart(5, "0");
          completionItems.push(item);
        });

        return completionItems;
      },
    },
    "{" // trigger key
  );

  context.subscriptions.push(provider);
}

function getRecorderProcess() {
  if (child == null) {
    if (!isDocumentActive()) {
      return null;
    }

    child = cp.spawn("python", ["-u", "-m", "r.audio.recorder"], {
      env: {
        ...process.env,
        RECORD_OUT_DIR: path.resolve(getProjectDir() + "/record"),
        RECODER_INTERACTIVE: "0",
      },
    });

    child.on("close", (code) => {
      vscode.window.showInformationMessage(
        `recorder process exited with code ${code}`
      );
    });

    child.stdout.on("data", (data) => {
      vscode.window.showInformationMessage(`${data}`);
      const s = data.toString("utf8").trim();
      if (s.startsWith("stop recording:")) {
        const fileName = s.split(":")[1].trim();

        const editor = vscode.window.activeTextEditor;
        if (editor) {
          const selection = editor.selection;
          editor.edit((editBuilder) => {
            editBuilder.replace(selection, `{{ record('${fileName}') }}`);
          });
        }
      }
    });

    child.stderr.on("data", (data) => {
      vscode.window.showInformationMessage(`${data}`);
    });
  }

  return child;
}

function export_animation({ audioOnly = false } = {}) {
  let editor = vscode.window.activeTextEditor;
  if (editor) {
    let document = editor.document;
    let selection = editor.selection;
    let selectionText = document.getText(selection);

    var activeFilePath = vscode.window.activeTextEditor.document.fileName;
    var activeDirectory = path.dirname(activeFilePath);
    // vscode.window.showInformationMessage(activeDirectory);

    const shellArgs = [
      "-m",
      "r.web.animation.export_animation",
      "-i",
      selectionText,
    ];
    if (audioOnly) {
      shellArgs.push("--audio_only");
    }

    const terminal = vscode.window.createTerminal({
      name: "yoyo",
      cwd: activeDirectory,
      shellPath: "python.exe",
      shellArgs: shellArgs,
    });
    terminal.show();
  }
}

function activate(context) {
  const config = vscode.workspace.getConfiguration();
  config.update("[markdown]", { "editor.quickSuggestions": true });

  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((status) => {})
  );

  vscode.commands.registerCommand("yo.runSelection", function () {
    export_animation();
  });

  vscode.commands.registerCommand("yo.exportAudio", function () {
    export_animation({ audioOnly: true });
  });

  vscode.commands.registerCommand("yo.startRecording", function () {
    getRecorderProcess().stdin.write("r\n");
  });

  vscode.commands.registerCommand("yo.stopRecording", function () {
    getRecorderProcess().stdin.write("s\n");
  });

  vscode.commands.registerCommand("yo.collectNoiseProfile", function () {
    getRecorderProcess().stdin.write("n\n");
  });

  vscode.commands.registerCommand("yo.openFileUnderCursor", function () {
    openFileUnderCursor();
  });

  registerAutoComplete(context);

  // initializeDecorations(context);
}

exports.activate = activate;
