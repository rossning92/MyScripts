const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");
const process = require("process");
const fs = require("fs");
const os = require("os");

var recorderProcess = null;
var currentProjectDir = null;
// let output = vscode.window.createOutputChannel("VideoEdit");

async function openFile(filePath) {
  if (fs.existsSync(filePath)) {
    if (/\.(md|c|cpp|py|txt)$/g.test(filePath)) {
      const document = await vscode.workspace.openTextDocument(filePath);
      await vscode.window.showTextDocument(document);
    } else if (/\.(png|jpg|mp4|webm)$/g.test(filePath)) {
      cp.spawn("mpv", ["--force-window", filePath]);
    } else if (/\.(wav|mp3|ogg)$/g.test(filePath)) {
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
        const filePath = path.resolve(path.join(getProjectDir(), found[1]));
        openFile(filePath);
      }
    }
  }
}

function initializeDecorations(context) {
  let timeout = undefined;

  let activeEditor = vscode.window.activeTextEditor;

  function updateDecorations() {
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
      activeEditor.setDecorations(
        vscode.window.createTextEditorDecorationType({
          color,
        }),
        decorations
      );
    }

    highlightText(/{{\s*(record|bgm|sfx)\(.*?\)\s*}}/g, "#c0392b");
    highlightText(/{{\s*(clip|overlay|md|slide)\(.*?\)\s*}}/g, "#0000ff");
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

function getActiveFile() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return undefined;

  return path.resolve(editor.document.fileName);
}

function isDocumentActive() {
  const fileName = getActiveFile();
  if (!fileName) return false;

  if (path.basename(fileName) != "index.md") {
    return false;
  }

  return true;
}

function getProjectDir() {
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
    return ` codef('${file}') `;
  } else if (/overlay\//g.test(file)) {
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
    { pattern: "**/index.md" },
    {
      provideCompletionItems(document, position) {
        const projectDir = getProjectDir();
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
  const d = getProjectDir();

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

    recorderProcess = cp.spawn("python", ["-u", "-m", "r.audio.recorder"], {
      env: {
        ...process.env,
        RECORD_OUT_DIR: path.resolve(getProjectDir() + "/record"),
        RECODER_INTERACTIVE: "0",
      },
    });

    recorderProcess.on("close", (code) => {
      vscode.window.showInformationMessage(
        `recorder process exited with code ${code}`
      );
    });

    recorderProcess.stdout.on("data", (data) => {
      vscode.window.showInformationMessage(`${data}`);
      const s = data.toString("utf8").trim();
      if (s.startsWith("stop recording:")) {
        const fileName = s.split(":")[1].trim();
        insertText(`{{ record('record/${fileName}') }}`);
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
    "--",
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
  let editor = vscode.window.activeTextEditor;
  if (editor) {
    let document = editor.document;

    let text;
    if (selectedText) {
      text = document.getText(editor.selection);
    } else {
      text = document.getText();
    }

    var activeFilePath = vscode.window.activeTextEditor.document.fileName;
    var activeDirectory = path.dirname(activeFilePath);
    // vscode.window.showInformationMessage(activeDirectory);

    const textFile = writeTempTextFile(text);
    let shellArgs = [
      "/c",
      "run_script",
      "/r/web/animation/export_animation",
      "--",
      "-i",
      textFile,
      "--proj_dir",
      getProjectDir(),
    ];
    if (extraArgs !== null) {
      shellArgs = shellArgs.concat(extraArgs);
    }

    shellArgs.push("||", "pause");

    const terminal = vscode.window.createTerminal({
      name: "yoyo",
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

  const projectDir = getProjectDir();
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

function registerCreateSlideCommand() {
  vscode.commands.registerCommand("yo.createSlide", async () => {
    const fileName = await vscode.window.showInputBox({
      placeHolder: "slide-file-name",
    });
    if (!fileName) {
      return;
    }

    const outFile = path.resolve(getProjectDir(), "slide", fileName + ".pptx");
    const outDir = path.resolve(getProjectDir(), "slide");
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
    const animationDir = path.resolve(getProjectDir(), "animation");

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

  registerCreateSlideCommand();

  registerCreateMovyCommand();

  registerAutoComplete(context);

  initializeDecorations(context);
}

exports.activate = activate;
