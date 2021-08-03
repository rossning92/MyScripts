const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");
const process = require("process");
const fs = require("fs");
const os = require("os");

const SOURCE_FILE_EXT = "c|cpp|py|js|txt|html";

let recorderProcess = null;
let currentProjectDir = null;
let output = vscode.window.createOutputChannel("VideoEdit");

async function openFile(filePath) {
  if (fs.existsSync(filePath)) {
    if (new RegExp(".(md|" + SOURCE_FILE_EXT + ")$", "g").test(filePath)) {
      const document = await vscode.workspace.openTextDocument(filePath);
      await vscode.window.showTextDocument(document);
    } else if (/\.(png|jpg|mp4|webm)$/g.test(filePath)) {
      cp.spawn("mpv", ["--force-window", filePath]);
    } else if (/\.(wav|mp3|ogg)$/g.test(filePath)) {
      output.appendLine(`Open with ocenaudio: ${filePath}`);
      cp.spawn("ocenaudio", [filePath]);
    } else if (/\.(ppt|pptx)$/g.test(filePath)) {
      cp.spawn(
        "C:/Program Files (x86)/Microsoft Office/root/Office16/POWERPNT.EXE",
        [filePath]
      );
    } else {
      vscode.env.openExternal(vscode.Uri.file(filePath));
    }
  }
}

function getAbsPath(file) {
  return path.resolve(path.join(getActiveDir(), file));
}

function getFileUnderCursor() {
  if (!isDocumentActive()) return;

  const editor = vscode.window.activeTextEditor;
  if (!editor) return;
  if (!editor.selection.isEmpty) return;

  const position = editor.selection.active;
  const line = editor.document.lineAt(position).text;
  const found = line.match(/['"](.*?)['"]/);
  if (!found) {
    vscode.window.showErrorMessage(
      "No file path is found in the current line."
    );
    return;
  }

  const file = found[1];
  const absPath = getAbsPath(file);
  if (!fs.existsSync(absPath)) {
    vscode.window.showErrorMessage(`File does not exist: ${file}`);
    return;
  }

  return file;
}

function startSlideServer(file) {
  const shellArgs = [
    "/c",
    "run_script",
    "slide/export.js",
    "-d",
    "-t",
    "slide",
    "-i",
    file,
    "||",
    "pause",
  ];

  runInTerminal("SlideServer", shellArgs);
}

async function openFileUnderCursor() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  const activeFile = vscode.window.activeTextEditor.document.fileName;
  if (/animation[\\\/][a-zA-Z0-9-_]+\.js$/.test(activeFile)) {
    startAnimationServer(activeFile);
  } else if (/slide[\\\/][a-zA-Z0-9-_]+\.md$/.test(activeFile)) {
    startSlideServer(activeFile);
  } else {
    const file = getFileUnderCursor();
    if (file) {
      const absPath = getAbsPath(file);
      openFile(absPath);
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

    highlightText(/\b(audio_end|bgm|record|sfx)(?=\()/g, "#c0392b");
    highlightText(
      /\b(anim|clip|codef|hl|md|overlay|slide|video_end)(?=\()/g,
      "#0000ff"
    );
  }

  // Reference: https://github.com/microsoft/vscode-extension-samples/blob/main/decorator-sample/src/extension.ts
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
  } else if (/\bsrc\//g.test(file)) {
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
            return new RegExp(
              ".(png|jpg|mp4|webm|gif|mp3|wav|md|pptx|" +
                SOURCE_FILE_EXT +
                ")$",
              "g"
            ).test(x);
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

function runInTerminal(name, shellArgs) {
  // Close existing Animation Server terminal.
  for (const term of vscode.window.terminals) {
    if (term.name == name) {
      term.dispose();
    }
  }

  // Create a new terminal.
  const terminal = vscode.window.createTerminal({
    name,
    shellPath: "cmd.exe",
    shellArgs,
  });
  terminal.show();
}

function startAnimationServer(activeFile) {
  const shellArgs = [
    "/c",
    "run_script",
    "/r/videoedit/start_animation_server",
    activeFile,
    "||",
    "pause",
  ];

  runInTerminal("AnimationServer", shellArgs);
}

function exportVideo({
  extraArgs = null,
  selectedText = true,
  preview = false,
} = {}) {
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
          const match = text.match(/^(#+)/);
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
            const match = text.match(/^(#+)/);
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
      "/r/videoedit/export_animation",
      "-i",
      textFile,
      "--proj_dir",
      getActiveDir(),
    ];
    if (preview) {
      shellArgs.push("--preview");
    }

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

function registerCreatePowerpointCommand() {
  vscode.commands.registerCommand("videoEdit.createPowerpoint", async () => {
    const filePath = await promptFileName({ ext: ".pptx", subdir: "slide" });

    cp.spawn("cscript", [
      path.resolve(__dirname, "../../ppt/potx2pptx.vbs"),
      path.resolve(getActiveDir(), filePath),
    ]);

    insertText(`{{ clip('${filePath}') }}`);
  });

  vscode.commands.registerCommand(
    "videoEdit.createPowerpointOverlay",
    async () => {
      const filePath = await promptFileName({
        ext: ".pptx",
        subdir: "overlay",
      });

      cp.spawn("cscript", [
        path.resolve(__dirname, "../../ppt/potx2pptx.vbs"),
        path.resolve(getActiveDir(), filePath),
      ]);

      insertText(`{{ overlay('${filePath}', n=1, pos=(960, 540), t='as') }}`);
    }
  );
}

async function promptFileName({ ext, subdir }) {
  const fileName = await vscode.window.showInputBox({
    placeHolder: "file-name",
  });
  if (!fileName) {
    return;
  }

  const outDir = path.resolve(getActiveDir(), subdir);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir);
  }

  const outFile = `${subdir}/${fileName + ext}`;
  return outFile;
}

function registerCreateSlideCommand() {
  vscode.commands.registerCommand("videoEdit.createSlide", async () => {
    const file = await createNewDocument({
      dir: "slide",
      func: "slide",
      extension: ".md",
      extraParams: ", t='as', template='slide'",
    });

    startSlideServer(file);
  });
}

function replaceCurrentLine(oldText, newText) {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  if (editor) {
    const currentLine = editor.selection.active.line;
    const currentLineText = editor.document.lineAt(currentLine).text;
    const newLineText = currentLineText.replace(oldText, newText);
    editor.edit((editBuilder) => {
      editBuilder.replace(
        new vscode.Selection(currentLine, 0, currentLine, newLineText.length),
        newLineText
      );
    });
  }
}

function registerRenameFileCommand() {
  vscode.commands.registerCommand("videoEdit.renameFile", async () => {
    const file = getFileUnderCursor();
    if (!file) return;

    const newFile = await vscode.window.showInputBox({
      value: file,
    });
    if (!newFile) return;

    const absFile = getAbsPath(file);
    const newAbsFile = getAbsPath(newFile);

    if (fs.existsSync(newAbsFile)) {
      vscode.window.showErrorMessage("New file already exists.");
      return;
    }

    try {
      fs.renameSync(absFile, newAbsFile);
    } catch (e) {
      vscode.window.showErrorMessage("Renaming failed.");
      return;
    }

    replaceCurrentLine(file, newFile);
  });
}

async function createNewDocument({
  dir,
  func,
  fileNamePlaceHolder = "file-name",
  initContent = "",
  extension = "",
  extraParams = "",
} = {}) {
  const animationDir = path.resolve(getActiveDir(), dir);

  // Create animation dir
  if (!fs.existsSync(animationDir)) {
    fs.mkdirSync(animationDir);
  }

  // Input file name
  const fileName = await vscode.window.showInputBox({
    placeHolder: fileNamePlaceHolder,
  });
  if (!fileName) {
    return;
  }

  const filePath = path.resolve(animationDir, fileName + extension);
  fs.writeFileSync(filePath, initContent);

  insertText(`{{ ${func}('${dir}/${fileName}${extension}'${extraParams}) }}`);

  const document = await vscode.workspace.openTextDocument(filePath);
  await vscode.window.showTextDocument(document);

  return filePath;
}

function activate(context) {
  const config = vscode.workspace.getConfiguration();
  config.update("[markdown]", { "editor.quickSuggestions": true });

  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((status) => {})
  );

  vscode.commands.registerCommand("videoEdit.exportVideo", () => {
    exportVideo({ selectedText: false });
  });

  vscode.commands.registerCommand("videoEdit.exportVideoPreview", () => {
    exportVideo({ preview: true });
  });

  vscode.commands.registerCommand("videoEdit.exportAudio", () => {
    exportVideo({ preview: true, extraArgs: ["--audio_only"] });
  });

  vscode.commands.registerCommand("videoEdit.startRecording", () => {
    getRecorderProcess().stdin.write("r\n");
  });

  vscode.commands.registerCommand("videoEdit.stopRecording", () => {
    getRecorderProcess().stdin.write("s\n");
  });

  vscode.commands.registerCommand("videoEdit.collectNoiseProfile", () => {
    getRecorderProcess().stdin.write("n\n");
  });

  vscode.commands.registerCommand("videoEdit.openFileUnderCursor", () => {
    openFileUnderCursor();
  });

  vscode.commands.registerCommand(
    "videoEdit.insertAllClipsInFolder",
    insertAllClipsInFolder
  );

  vscode.commands.registerCommand("videoEdit.purgeFiles", () => {
    exportVideo({
      selectedText: false,
      extraArgs: ["--audio_only", "--remove_unused_recordings"],
    });
  });

  vscode.commands.registerCommand("videoEdit.showStats", () => {
    exportVideo({
      extraArgs: ["--stat"],
    });
  });

  registerCreatePowerpointCommand();
  registerCreateSlideCommand();
  registerRenameFileCommand();
  registerAutoComplete(context);

  initializeDecorations(context);

  // Create movy document
  vscode.commands.registerCommand("videoEdit.createMovyAnimation", async () => {
    createNewDocument({
      dir: "animation",
      func: "anim",
      fileNamePlaceHolder: "movy-animation-name",
      initContent: 'import * as mo from "movy";\n\nmo.run();',
      extension: ".js",
    });
  });

  // Create source code document
  vscode.commands.registerCommand("videoEdit.createCode", async () => {
    createNewDocument({
      dir: "src",
      func: "codef",
      fileNamePlaceHolder: "source-code-name.ext",
    });
  });
}

exports.activate = activate;
