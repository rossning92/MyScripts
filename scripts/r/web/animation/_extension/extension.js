const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");
const process = require("process");
const fs = require("fs");
const os = require("os");

var recorderProcess = null;
var currentProjectDir = null;

async function openFile(filePath) {
  if (fs.existsSync(filePath)) {
    if (filePath.endsWith(".md")) {
      const document = await vscode.workspace.openTextDocument(filePath);
      await vscode.window.showTextDocument(document);
    } else {
      // const args = [
      //   "-c",
      //   `from r.open_with.open_with_ import open_with; open_with(r'${filePath}', 0)`,
      //   filePath,
      // ];
      // cp.spawnSync("python", args);

      const args = [
        "-c",
        `from r.web.animation.video_editor import edit_video; edit_video(r"${filePath}")`,
        filePath,
      ];
      cp.spawnSync("python", args);
    }
  }
}

async function openFileUnderCursor() {
  if (!isDocumentActive) {
    return;
  }

  const editor = vscode.window.activeTextEditor;

  if (editor.selection.isEmpty) {
    const position = editor.selection.active;
    const line = editor.document.lineAt(position).text;
    const found = line.match(/'(.*?)'/);
    if (found !== null) {
      const filePath = path.resolve(path.join(getProjectDir(), found[1]));
      openFile(filePath);
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
      if (!/(tmp|out)$/g.test(file)) {
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
        if (projectDir == null) return undefined;

        if (
          position.character < 2 ||
          document.lineAt(position).text[position.character - 2] !== "{"
        ) {
          return undefined;
        }

        let files = [];
        const filter = (x) => /\.(png|jpg|mp4|gif|mp3|md)$/g.test(x);

        getFiles(projectDir, filter, files);
        getFiles(projectDir + "/../assets", filter, files);

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

function export_animation({ extraArgs = null } = {}) {
  let editor = vscode.window.activeTextEditor;
  if (editor) {
    let document = editor.document;
    let selection = editor.selection;
    let selectionText = document.getText(selection);

    var activeFilePath = vscode.window.activeTextEditor.document.fileName;
    var activeDirectory = path.dirname(activeFilePath);
    // vscode.window.showInformationMessage(activeDirectory);

    const textFile = writeTempTextFile(selectionText);
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
  if (editor == null) return undefined;

  const projectDir = getProjectDir();
  if (projectDir == null) return undefined;

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

async function createSlide() {
  const fileName = await vscode.window.showInputBox({
    placeHolder: "slide-file-name",
  });
  if (fileName === undefined) {
    return;
  }

  const outFile = path.resolve(getProjectDir(), "slide", fileName + ".pptx");
  const outDir = path.resolve(getProjectDir(), "slide");
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir);
  }

  cp.spawn("cscript", [
    path.resolve(__dirname, "ppt", "potx2pptx.vbs"),
    outFile,
  ]);

  insertText(`{{ clip('slide/${fileName}.pptx') }}`);
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
    export_animation({ extraArgs: ["--audio_only"] });
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

  vscode.commands.registerCommand(
    "yo.insertAllClipsInFolder",
    insertAllClipsInFolder
  );

  vscode.commands.registerCommand("yo.removeUnusedRecordings", function () {
    export_animation({
      extraArgs: ["--audio_only", "--remove_unused_recordings"],
    });
  });

  vscode.commands.registerCommand("yo.showStats", function () {
    export_animation({
      extraArgs: ["--show_stats"],
    });
  });

  vscode.commands.registerCommand("yo.createSlide", createSlide);

  registerAutoComplete(context);

  // initializeDecorations(context);
}

exports.activate = activate;
