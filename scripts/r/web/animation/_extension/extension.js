const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");
const process = require("process");
const fs = require("fs");
const os = require("os");

let recorderProcess = null;
let currentProjectDir = null;
let output = vscode.window.createOutputChannel("VideoEdit");

async function openFile(filePath) {
  if (fs.existsSync(filePath)) {
    if (/\.(md|c|cpp|py|txt)$/g.test(filePath)) {
      const document = await vscode.workspace.openTextDocument(filePath);
      await vscode.window.showTextDocument(document);
    } else if (/\.(png|jpg|mp4|webm)$/g.test(filePath)) {
      cp.spawn("mpv", ["--force-window", filePath]);
    } else if (/\.(wav|mp3|ogg)$/g.test(filePath)) {
      output.appendLine(`Open with ocenaudio: ${filePath}`);
      cp.spawn("ocenaudio", [filePath]);
    } else {
      vscode.env.openExternal(vscode.Uri.file(filePath));
    }
  }
}

async function openFileUnderCursor() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  const activeFile = vscode.window.activeTextEditor.document.fileName;
  if (/animation[\\\/][a-zA-Z0-9-_]+\.js$/.test(activeFile)) {
    startAnimationServer(activeFile);
  } else if (isDocumentActive()) {
    if (editor.selection.isEmpty) {
      const position = editor.selection.active;
      const line = editor.document.lineAt(position).text;
      const found = line.match(/['"](.*?)['"]/);
      if (found !== null) {
        const filePath = path.resolve(path.join(getActiveDir(), found[1]));
        openFile(filePath);
      }
    }
  }
}

function initializeDecorations(context) {
  const decorationTypes = [];
  let timeout = undefined;
  let activeEditor = vscode.window.activeTextEditor;

  function updateDecorations() {
    for (const dt of decorationTypes) dt.dispose();
    decorationTypes.length = 0;

    if (!activeEditor) {
      return;
    }

    if (!isDocumentActive()) {
      return;
    }

    function highlightText(regex, color) {
      const text = activeEditor.document.getText();

      const decorations = [];
      let match;
      while ((match = regex.exec(text))) {
        const startPos = activeEditor.document.positionAt(match.index);
        const endPos = activeEditor.document.positionAt(
          match.index + match[0].length
        );

        decorations.push({
          range: new vscode.Range(startPos, endPos),
        });
      }
      const decorationType = vscode.window.createTextEditorDecorationType({
        color,
        fontWeight: "700",
      });
      decorationTypes.push(decorationType);
      activeEditor.setDecorations(decorationType, decorations);
    }

    highlightText(/\b(record|bgm|sfx|audio_end)(?=\()/g, "#c0392b");
    highlightText(
      /\b(clip|overlay|md|slide|codef|hl|video_end)(?=\()/g,
      "#0000ff"
    );
  }

  // Reference: https://github.com/microsoft/vscode-extension-samples/blob/main/decorator-sample/src/extension.ts
  function triggerUpdateDecorations() {
    if (timeout) {
      clearTimeout(timeout);
      timeout = undefined;
    }
    timeout = setTimeout(updateDecorations, 1000);
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
  const fileName = getActiveFile();
  if (!fileName) return false;

  if (!path.basename(fileName).endsWith(".md")) {
    return false;
  }

  return true;
}

function getActiveFile() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return undefined;

  return path.resolve(editor.document.fileName);
}

function getActiveDir() {
  const file = getActiveFile();
  if (!file) return undefined;

  return path.dirname(file);
}

function getRelativePath(prefix, p) {
  return path.relative(prefix, p).replace(/\\/g, "/");
}

function getFiles(dir, filter, files = [], dirs = []) {
  fs.readdirSync(dir).forEach((file) => {
    const filePath = path.join(dir, file);
    const fileStat = fs.lstatSync(filePath);

    if (fileStat.isDirectory()) {
      dirs.push(filePath);

      // If not in excluded folders
      if (!/tmp$/g.test(file)) {
        getFiles(filePath, filter, files, dirs);
      }
    } else if (filter(filePath)) {
      files.push(filePath);
    }
  });
}

function getCompletedExpression(file) {
  if (file.endsWith(".md")) {
    return ` include('${file}') `;
  } else if (file.endsWith(".js")) {
    return ` anim('${file}') `;
  } else if (/\.(c|cpp|py|text)$/g.test(file)) {
    return ` codef('${file}', size=(1664, 824)) `;
  } else if (/\boverlay\//g.test(file)) {
    return ` overlay('${file}', t='as') `;
  } else if (/bgm\//g.test(file)) {
    return ` bgm('${file}', norm=True); pos('c+0.5', tag='a') `;
  } else if (/sfx\//g.test(file)) {
    return ` sfx('${file}', norm=True); pos('c+0.5', tag='a') `;
  } else {
    return ` clip('${file}') `;
  }
}

function registerAutoComplete(context) {
  const provider = vscode.languages.registerCompletionItemProvider(
    { pattern: "**/vprojects/**/*.md" },
    {
      provideCompletionItems(document, position) {
        const projectDir = getActiveDir();
        if (!projectDir) return undefined;

        if (
          position.character < 2 ||
          document.lineAt(position).text[position.character - 2] !== "{"
        ) {
          return undefined;
        }

        const activeFile = getActiveFile();
        const filter = (x) => {
          if (activeFile === x) {
            // Ignore current file
            return false;
          } else {
            return /\.(png|jpg|mp4|webm|gif|mp3|md|pptx|cpp|c|py|js)$/g.test(x);
          }
        };

        let files = [];
        getFiles(projectDir, filter, files);

        // Recursively search parent `assets` folder
        let parentDir = projectDir;
        do {
          parentDir = path.dirname(parentDir);
          const assetFolder = path.resolve(parentDir, "assets");
          if (fs.existsSync(assetFolder)) {
            getFiles(assetFolder, filter, files);
          }
        } while (path.dirname(parentDir) != parentDir);

        files = files.sort(function (a, b) {
          return -(
            fs.statSync(a).mtime.getTime() - fs.statSync(b).mtime.getTime()
          );
        });

        // Convert to relative path
        files = files.map((x) => getRelativePath(projectDir, x));

        const completionItems = [];
        files.forEach((file, i) => {
          const label = getCompletedExpression(file); // Auto closing single quote
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

function insertText(text) {
  const editor = vscode.window.activeTextEditor;
  if (editor) {
    const selection = editor.selection;
    editor.edit((editBuilder) => {
      editBuilder.replace(selection, text);
    });
  }
}

function getRecorderProcess() {
  const d = getActiveDir();

  // Check if project switches
  if (d != currentProjectDir) {
    currentProjectDir = d;
    if (recorderProcess != null) {
      recorderProcess.stdin.write("q");
      recorderProcess = null;
      vscode.window.showWarningMessage(
        "Project switched. Restarting recorder..."
      );
    }
  }

  if (recorderProcess == null) {
    if (!isDocumentActive()) {
      return null;
    }

    recorderProcess = cp.spawn("run_script", ["/r/audio/recorder"], {
      env: {
        ...process.env,
        RECORD_OUT_DIR: path.resolve(getActiveDir() + "/record"),
        RECODER_INTERACTIVE: "0",
      },
    });

    recorderProcess.on("close", (code) => {
      vscode.window.showInformationMessage(
        `recorder process exited with code ${code}`
      );
    });

    recorderProcess.stdout.on("data", (data) => {
      const lines = data.toString("utf8").split(/(\r?\n)/g);
      for (const line of lines) {
        let s = line.trim();
        if (s.startsWith("LOG: ")) {
          s = s.substr(5);
          vscode.window.showInformationMessage(s);

          const match = /^stop recording: (.*)/.exec(s);
          if (match) {
            const fileName = match[1];
            insertText(`{{ record('record/${fileName}') }}`);
          }
        }
      }
    });

    recorderProcess.stderr.on("data", (data) => {
      vscode.window.showInformationMessage(`${data}`);
    });
  }

  return recorderProcess;
}

function getRandomString() {
  return (
    Math.random().toString(36).substring(2, 15) +
    Math.random().toString(36).substring(2, 15)
  );
}

function writeTempTextFile(text) {
  const fs = require("fs");

  const file = path.join(
    os.tmpdir(),
    "animation-" + getRandomString() + ".txt"
  );
  fs.writeFileSync(file, text, {
    encoding: "utf8",
  });

  return file;
}

function startAnimationServer(activeFile) {
  const shellArgs = [
    "/c",
    "run_script",
    "/r/web/animation/start_animation_server",
    activeFile,
    "||",
    "pause",
  ];
  const terminal = vscode.window.createTerminal({
    name: "AnimationServer",
    shellPath: "cmd.exe",
    shellArgs,
  });
  terminal.show();
}

function export_animation({ extraArgs = null, selectedText = true } = {}) {
  let activeEditor = vscode.window.activeTextEditor;
  if (activeEditor) {
    let document = activeEditor.document;

    let textIn = "";
    if (selectedText) {
      textIn = document.getText(activeEditor.selection);
      if (!textIn) {
        let currentLine = activeEditor.selection.active.line;

        let headerLevel = 0;
        let beginLine = 0;
        let endLine = activeEditor.document.lineCount - 1;
        for (let i = currentLine; i >= 0; i--) {
          const { text } = activeEditor.document.lineAt(i);
          const match = text.match(/^(#+) /);
          if (match) {
            headerLevel = match[1].length;
            beginLine = i;
            break;
          }
        }

        if (beginLine >= 0) {
          for (
            let i = currentLine + 1;
            i < activeEditor.document.lineCount;
            i++
          ) {
            const { text } = activeEditor.document.lineAt(i);
            const match = text.match(/^(#+) /);
            if (match && match[1].length <= headerLevel) {
              endLine = i - 1;
              break;
            }
          }
        }

        for (let i = beginLine; i <= endLine; i++) {
          const { text } = activeEditor.document.lineAt(i);
          textIn += text + "\n";
        }
      }
    } else {
      textIn = document.getText();
    }

    let activeFilePath = vscode.window.activeTextEditor.document.fileName;
    let activeDirectory = path.dirname(activeFilePath);

    const textFile = writeTempTextFile(textIn);
    let shellArgs = [
      "/c",
      "run_script",
      "/r/web/animation/export_animation",
      "-i",
      textFile,
      "--proj_dir",
      getActiveDir(),
    ];
    if (extraArgs !== null) {
      shellArgs = shellArgs.concat(extraArgs);
    }

    shellArgs.push("||", "pause");

    const terminal = vscode.window.createTerminal({
      name: "VideoEdit",
      cwd: activeDirectory,
      shellPath: "cmd.exe",
      shellArgs: shellArgs,
    });
    terminal.show();
  }
}

async function insertAllClipsInFolder() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return undefined;

  const projectDir = getActiveDir();
  if (!projectDir) return undefined;

  let dirs = [];
  getFiles(projectDir, (x) => x, [], dirs);
  // dirs = dirs.map((x) => getRelativePath(projectDir, x));

  const selectedDir = await vscode.window.showQuickPick(dirs, {
    placeHolder: "from which folder you'd like to insert all clips",
  });

  const files = [];
  getFiles(selectedDir, (x) => /\.mp4$/g.test(x), files);

  const linesToInsert = files.map(
    (x) => `{{ clip('${getRelativePath(projectDir, x)}') }}`
  );

  const selection = editor.selection;
  editor.edit((editBuilder) => {
    editBuilder.replace(selection, linesToInsert.join("\n"));
  });
}

function registerCreatePowerPointCommand() {
  vscode.commands.registerCommand("yo.createPowerPoint", async () => {
    const fileName = await vscode.window.showInputBox({
      placeHolder: "slide-file-name",
    });
    if (!fileName) {
      return;
    }

    const outFile = path.resolve(getActiveDir(), "slide", fileName + ".pptx");
    const outDir = path.resolve(getActiveDir(), "slide");
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir);
    }

    cp.spawn("cscript", [
      path.resolve(__dirname, "../../../ppt/potx2pptx.vbs"),
      outFile,
    ]);

    insertText(`{{ clip('slide/${fileName}.pptx') }}`);
  });
}

function registerCreateMovyCommand() {
  vscode.commands.registerCommand("yo.createMovyAnimation", async () => {
    const animationDir = path.resolve(getActiveDir(), "animation");

    // Create animation dir
    if (!fs.existsSync(animationDir)) {
      fs.mkdirSync(animationDir);
    }

    // Input file name
    const fileName = await vscode.window.showInputBox({
      placeHolder: "movy-animation-name",
    });
    if (!fileName) {
      return;
    }

    const filePath = path.resolve(animationDir, fileName + ".js");
    fs.writeFileSync(filePath, 'import * as mo from "movy";\n\nmo.run();');

    insertText(`{{ anim('animation/${fileName}.js') }}`);

    const document = await vscode.workspace.openTextDocument(filePath);
    await vscode.window.showTextDocument(document);
  });
}

function activate(context) {
  const config = vscode.workspace.getConfiguration();
  config.update("[markdown]", { "editor.quickSuggestions": true });

  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((status) => {})
  );

  vscode.commands.registerCommand("yo.runSelection", () => {
    export_animation();
  });

  vscode.commands.registerCommand("yo.exportAudio", () => {
    export_animation({ extraArgs: ["--audio_only"] });
  });

  vscode.commands.registerCommand("yo.startRecording", () => {
    getRecorderProcess().stdin.write("r\n");
  });

  vscode.commands.registerCommand("yo.stopRecording", () => {
    getRecorderProcess().stdin.write("s\n");
  });

  vscode.commands.registerCommand("yo.collectNoiseProfile", () => {
    getRecorderProcess().stdin.write("n\n");
  });

  vscode.commands.registerCommand("yo.openFileUnderCursor", () => {
    openFileUnderCursor();
  });

  vscode.commands.registerCommand(
    "yo.insertAllClipsInFolder",
    insertAllClipsInFolder
  );

  vscode.commands.registerCommand("yo.removeUnusedRecordings", () => {
    export_animation({
      selectedText: false,
      extraArgs: ["--audio_only", "--remove_unused_recordings"],
    });
  });

  vscode.commands.registerCommand("yo.showStats", () => {
    export_animation({
      extraArgs: ["--show_stats"],
    });
  });

  registerCreatePowerPointCommand();

  registerCreateMovyCommand();

  registerAutoComplete(context);

  initializeDecorations(context);
}

exports.activate = activate;
