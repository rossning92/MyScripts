import * as vscode from "vscode";
import cp = require("child_process");
import path = require("path");
import process = require("process");
import fs = require("fs");
import os = require("os");

const SOURCE_FILE_EXT = "c|cpp|py|js|txt|html";

let recorderProcess: cp.ChildProcessWithoutNullStreams | undefined;
let currentProjectDir: string | undefined;
let output = vscode.window.createOutputChannel("VideoEdit");

declare global {
  interface String {
    replaceAll: (find: string, replace: string) => string;
    count: (substr: string) => number;
  }
}

// Helper functions for String.
String.prototype.replaceAll = function (find: string, replace: string) {
  const str = this;
  return str.replace(
    new RegExp(find.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&"), "g"),
    replace
  );
};

String.prototype.count = function (substr: string) {
  const str = this;
  return (
    str.match(
      new RegExp(substr.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&"), "g")
    ) || []
  ).length;
};

function openInBrowser(url: string) {
  cp.spawn("C:/Program Files (x86)/Chromium/Application/chrome.exe", [
    "--user-data-dir=" + path.join(os.homedir(), "ChromeDataForDev"),
    url,
  ]);
}

async function openFile(filePath: string) {
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

function getAbsPath(file: string) {
  const activeDir = getActiveDir();
  if (!activeDir) return undefined;
  return path.resolve(path.join(activeDir, file));
}

function getFileUnderCursor() {
  if (!isProjectFileActive()) return;

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
  if (!absPath) return;
  if (!fs.existsSync(absPath)) {
    vscode.window.showErrorMessage(`File does not exist: ${file}`);
    return;
  }

  return file;
}

function startSlideServer(file: string) {
  // Return random port number between 10000 and 20000
  let port = Math.floor(Math.random() * 10000) + 10000;

  const shellArgs = [
    "/c",
    "run_script",
    "slide/export.js",
    "-d",
    "-p",
    port.toString(),
    "-t",
    "slide",
    "-i",
    file,
    "||",
    "pause",
  ];

  runInTerminal("SlideServer", shellArgs);

  openInBrowser(`http://localhost:${port}`);
}

function runPython(file: string) {
  const shellArgs = [
    "/c",
    "run_script",
    "@cd=1:template=0",
    file,
    "||",
    "pause",
  ];
  runInTerminal("Python", shellArgs);
}

async function openFileUnderCursor() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  const activeFile = editor.document.fileName;
  output.appendLine(`openFileUnderCursor(): ${activeFile}`);
  if (/animation[\\\/][a-zA-Z0-9-_]+\.js$/.test(activeFile)) {
    startMovyServer(activeFile);
  } else if (/slide[\\\/].+?\.md$/.test(activeFile)) {
    startSlideServer(activeFile);
  } else if (/uiautomate[\\\/].+?\.py$/.test(activeFile)) {
    runPython(activeFile);
  } else {
    const file = getFileUnderCursor();
    if (file) {
      const absPath = getAbsPath(file);
      if (absPath) openFile(absPath);
    }
  }
}

function setupDecorations(context: vscode.ExtensionContext) {
  const decorationTypes: vscode.TextEditorDecorationType[] = [];
  let timeout: NodeJS.Timeout | undefined;
  let editor = vscode.window.activeTextEditor;

  function updateDecorations() {
    for (const dt of decorationTypes) dt.dispose();
    decorationTypes.length = 0;

    if (!editor) {
      return;
    }

    if (!isProjectFileActive()) {
      return;
    }

    function highlightText(regex: RegExp, color: string) {
      if (!editor) return;
      const text = editor.document.getText();

      const decorations = [];
      let match;
      while ((match = regex.exec(text))) {
        const startPos = editor.document.positionAt(match.index);
        const endPos = editor.document.positionAt(
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
      editor.setDecorations(decorationType, decorations);
    }

    // Highlight audio functions.
    highlightText(/\b(audio_end|bgm|record|sfx)(?=\()/g, "#c0392b");

    // Highlight video functions.
    highlightText(
      /\b(anim|clip|codef|hl|md|comment|overlay|slide|video_end|cmd|ipython|node)(?=\()/g,
      "#0000ff"
    );

    // Highlight auxiliary functions.
    highlightText(/\b(include|crossfade|audio_gap)(?=\()/g, "#008000");
  }

  // Reference: https://github.com/microsoft/vscode-extension-samples/blob/main/decorator-sample/src/extension.ts
  function triggerUpdateDecorations() {
    if (timeout) {
      clearTimeout(timeout);
      timeout = undefined;
    }
    timeout = setTimeout(updateDecorations, 500);
  }

  if (editor) {
    triggerUpdateDecorations();
  }

  vscode.window.onDidChangeActiveTextEditor(
    (editor_) => {
      editor = editor_;
      if (editor) {
        triggerUpdateDecorations();
      }
    },
    null,
    context.subscriptions
  );

  vscode.workspace.onDidChangeTextDocument(
    (event) => {
      if (editor && event.document === editor.document) {
        triggerUpdateDecorations();
      }
    },
    null,
    context.subscriptions
  );
}

function isProjectFileActive() {
  const fileName = getActiveFile();
  if (!fileName) return false;

  if (!/vprojects[\\\/]/.test(fileName)) return false;

  if (!fileName.endsWith(".md")) {
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

function getRelativePath(prefix: string, p: string) {
  return path.relative(prefix, p).replace(/\\/g, "/");
}

function getFiles(
  dir: string,
  filter: ((x: string) => boolean) | undefined,
  files: string[] = [],
  dirs: string[] = []
) {
  fs.readdirSync(dir).forEach((file) => {
    // Skip files starting with "_"
    if (file.startsWith("_")) return;

    const filePath = path.join(dir, file);
    const fileStat = fs.lstatSync(filePath);

    if (fileStat.isDirectory()) {
      dirs.push(filePath);

      // If not in excluded folders
      if (!/tmp$/g.test(file)) {
        getFiles(filePath, filter, files, dirs);
      }
    } else if (filter && filter(filePath)) {
      files.push(filePath);
    }
  });
}

function getCompletedExpression(file: string) {
  if (/slide[\\\/].+?\.md$/.test(file)) {
    return `{{ slide('${file}', template='slide') }}`;
  } else if (file.endsWith(".md")) {
    return `{{ include('${file}') }}`;
  } else if (file.endsWith(".js")) {
    return `{{ anim('${file}') }}`;
  } else if (/\bsrc\//g.test(file)) {
    return `{{ codef('${file}', size=(1664, 824)) }}`;
  } else if (/overlay[\\\/].+?\.pptx$/.test(file)) {
    return `{{ overlay('${file}', n=1, t='as') }}`;
  } else if (/\boverlay\//g.test(file)) {
    return `{{ overlay('${file}', t='as') }}`;
  } else if (/bgm\//g.test(file)) {
    return `{{ bgm('${file}', norm=True); pos('c+0.5', tag='a') }}`;
  } else if (/sfx\//g.test(file)) {
    return `{{ sfx('${file}', norm=True); pos('c+0.5', tag='a') }}`;
  } else {
    return `{{ clip('${file}') }}`;
  }
}

function getAllFiles(): string[] {
  const projectDir = getActiveDir();
  if (!projectDir) return [];

  const activeFile = getActiveFile();
  const filter = (x: string) => {
    if (activeFile === x) {
      // Ignore current file
      return false;
    } else {
      return new RegExp(
        ".(png|jpg|mp4|webm|gif|mp3|wav|ogg|md|pptx|" + SOURCE_FILE_EXT + ")$",
        "g"
      ).test(x);
    }
  };

  let files: string[] = [];
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

  files = files.sort((a, b) => {
    return fs.statSync(b).mtime.getTime() - fs.statSync(a).mtime.getTime();
  });

  // Convert to relative path
  files = files.map((x) => getRelativePath(projectDir, x));

  return files;
}

function setupAutoComplete(context: vscode.ExtensionContext) {
  const provider = vscode.languages.registerCompletionItemProvider(
    { pattern: "**/vprojects/**/*.md" },
    {
      provideCompletionItems(document, position) {
        // If not at the beginning of the line.
        if (position.character > 0) return undefined;

        const files = getAllFiles();

        const completionItems: vscode.CompletionItem[] = [];
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
    }
  );

  context.subscriptions.push(provider);
}

function insertTextAtCursor(text: string) {
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
    if (recorderProcess) {
      recorderProcess.stdin.write("q");
      recorderProcess = undefined;
      vscode.window.showWarningMessage(
        "Project switched. Restarting recorder..."
      );
    }
  }

  if (recorderProcess === undefined) {
    if (!isProjectFileActive()) {
      return undefined;
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
            insertTextAtCursor(`{{ record('record/${fileName}') }}`);
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

function writeTempTextFile(text: string) {
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

function runInTerminal(name: string, shellArgs: string[]) {
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

function startMovyServer(file: string) {
  // Return random port number between 10000 and 20000
  let port = Math.floor(Math.random() * 10000) + 10000;

  const shellArgs = [
    "/c",
    "run_script",
    "/r/videoedit/start_movy_server",
    "-p",
    port.toString(),
    file,
    "||",
    "pause",
  ];

  runInTerminal("MovyServer", shellArgs);

  openInBrowser(`http://localhost:${port}`);
}

function exportVideo({
  extraArgs,
  selectedText = true,
  preview = false,
}: { extraArgs?: string[]; selectedText?: boolean; preview?: boolean } = {}) {
  const activeDir = getActiveDir();
  if (!activeDir) return;

  const editor = vscode.window.activeTextEditor;
  if (editor) {
    let document = editor.document;

    let textIn = "";
    if (selectedText) {
      textIn = document.getText(editor.selection);
      if (!textIn) {
        let currentLine = editor.selection.active.line;

        let headerLevel = 0;
        let beginLine = 0;
        let endLine = editor.document.lineCount - 1;
        for (let i = currentLine; i >= 0; i--) {
          const { text } = editor.document.lineAt(i);
          const match = text.match(/^(#+)/);
          if (match) {
            headerLevel = match[1].length;
            beginLine = i;
            break;
          }
        }

        if (beginLine >= 0) {
          for (let i = currentLine + 1; i < editor.document.lineCount; i++) {
            const { text } = editor.document.lineAt(i);
            const match = text.match(/^(#+)/);
            if (match && match[1].length <= headerLevel) {
              endLine = i - 1;
              break;
            }
          }
        }

        for (let i = beginLine; i <= endLine; i++) {
          const { text } = editor.document.lineAt(i);
          textIn += text + "\n";
        }
      }
    } else {
      textIn = document.getText();
    }

    let activeFilePath = editor.document.fileName;
    let activeDirectory = path.dirname(activeFilePath);

    const textFile = writeTempTextFile(textIn);
    let shellArgs: string[] = [
      "/c",
      "run_script",
      "/r/videoedit/export_animation",
      "-i",
      textFile,
      "--proj_dir",
      activeDir,
    ];
    if (preview) {
      shellArgs.push("--preview");
    }

    if (extraArgs) {
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

  let dirs: string[] = [];
  getFiles(projectDir, undefined, [], dirs);
  // dirs = dirs.map((x) => getRelativePath(projectDir, x));

  const selectedDir = await vscode.window.showQuickPick(dirs, {
    placeHolder: "from which folder you'd like to insert all clips",
  });
  if (!selectedDir) return undefined;

  const files: string[] = [];
  getFiles(selectedDir, (x) => /\.mp4$/g.test(x), files);

  const linesToInsert = files.map(
    (x) => `{{ clip('${getRelativePath(projectDir, x)}') }}`
  );

  const selection = editor.selection;
  editor.edit((editBuilder) => {
    editBuilder.replace(selection, linesToInsert.join("\n"));
  });
}

function registerCreatePowerpointCommand(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.createPowerpoint", async () => {
      const activeDir = getActiveDir();
      if (!activeDir) return;

      const filePath = await promptFileName({ ext: ".pptx", subdir: "slide" });
      if (!filePath) return;

      cp.spawn("cscript", [
        path.resolve(__dirname, "../../../ppt/potx2pptx.vbs"),
        path.resolve(activeDir, filePath),
      ]);

      insertTextAtCursor(`{{ clip('${filePath}') }}`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "videoEdit.createPowerpointOverlay",
      async () => {
        const activeDir = getActiveDir();
        if (!activeDir) return;

        const filePath = await promptFileName({
          ext: ".pptx",
          subdir: "overlay",
        });
        if (!filePath) return;

        cp.spawn("cscript", [
          path.resolve(__dirname, "../../../ppt/potx2pptx.vbs"),
          path.resolve(activeDir, filePath),
        ]);

        insertTextAtCursor(
          `{{ overlay('${filePath}', n=1, pos=(960, 540), t='as') }}`
        );
      }
    )
  );
}

async function promptFileName({
  ext,
  subdir,
}: {
  ext: string;
  subdir: string;
}) {
  const activeDir = getActiveDir();
  if (!activeDir) return;

  const fileName = await vscode.window.showInputBox({
    placeHolder: "file-name",
  });
  if (!fileName) {
    return;
  }

  const outDir = path.resolve(activeDir, subdir);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir);
  }

  const outFile = `${subdir}/${fileName + ext}`;
  return outFile;
}

function registerCreateSlideCommand(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.createSlide", async () => {
      const file = await createNewDocument({
        dir: "slide",
        func: "slide",
        extension: ".md",
        extraParams: ", t='as', template='slide'",
      });
      if (!file) return;

      startSlideServer(file);
    })
  );
}

function toggleParameter(name: string, defaultValue: string) {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  const currentLine = editor.selection.active.line;
  const currentLineText = editor.document.lineAt(currentLine).text;

  const patt = new RegExp(", " + name + "=(.+?)(?=[,)])", "g");

  let newLineText: string;
  if (patt.test(currentLineText)) {
    newLineText = currentLineText.replace(patt, "");
  } else {
    newLineText = currentLineText.replace(
      /(?=\) \}\})/g,
      `, ${name}=${defaultValue}`
    );
  }

  editor.edit((editBuilder) => {
    editBuilder.replace(
      new vscode.Selection(currentLine, 0, currentLine, currentLineText.length),
      newLineText
    );
  });

  // Change selection to 1st matched group of patt.
  const result = patt.exec(newLineText);
  if (result) {
    const valueLength = result[1].length;
    const paramStartIndex = result.index + name.length + 3;
    editor.selection = new vscode.Selection(
      currentLine,
      paramStartIndex,
      currentLine,
      paramStartIndex + valueLength
    );
  }
}

function registerToggleCrossfadeCommand(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.toggleCrossfade", () => {
      toggleParameter("cf", "0.2");
    })
  );
}

function registerToggleDurationCommand(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.toggleDuration", () => {
      toggleParameter("duration", "2");
    })
  );
}

function replaceCurrentLine(oldText: string, newText: string) {
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

function replaceWholeDocument(oldText: string, newText: string) {
  const editor = vscode.window.activeTextEditor;
  if (!editor) return;

  const text = editor.document.getText();

  const occurrences = text.count(oldText);
  vscode.window.showInformationMessage(
    `${occurrences} occurrences have been replaced.`
  );

  // Replace all oldText with newText
  editor.edit((editBuilder) => {
    editBuilder.replace(
      new vscode.Range(0, 0, editor.document.lineCount, 0),
      text.replaceAll(oldText, newText)
    );
  });
}

function registerRenameFileCommand(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.renameFile", async () => {
      const file = getFileUnderCursor();
      if (!file) return;

      // Get the range of file base name without extension.
      const match = /(?<=\/|^)[^./]+(?=\.[^./]+$)/g.exec(file);
      const valueSelection: [number, number] | undefined = match
        ? [match.index, match.index + match[0].length]
        : undefined;

      const newFile = await vscode.window.showInputBox({
        value: file,
        valueSelection,
      });
      if (!newFile) return;

      const absFile = getAbsPath(file);
      if (!absFile) return;

      const newAbsFile = getAbsPath(newFile);
      if (!newAbsFile) return;

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

      replaceWholeDocument(file, newFile);
    })
  );
}

async function createNewDocument({
  dir,
  func,
  fileNamePlaceHolder = "file-name",
  initContent = "",
  extension = "",
  extraParams = "",
}: {
  dir: string;
  func: string;
  fileNamePlaceHolder?: string;
  initContent?: string;
  extension?: string;
  extraParams?: string;
}) {
  const activeDir = getActiveDir();
  if (!activeDir) return;

  const animationDir = path.resolve(activeDir, dir);

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

  insertTextAtCursor(
    `{{ ${func}('${dir}/${fileName}${extension}'${extraParams}) }}`
  );

  const document = await vscode.workspace.openTextDocument(filePath);
  await vscode.window.showTextDocument(document);

  return filePath;
}

function updateWhenClauseContext() {
  vscode.commands.executeCommand(
    "setContext",
    "videoEdit.isProjectFileActive",
    isProjectFileActive()
  );
}

function registerCommands(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.exportVideo", () => {
      exportVideo({ selectedText: false });
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.exportVideoPreview", () => {
      exportVideo({ preview: true });
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.exportAudio", () => {
      exportVideo({ preview: true, extraArgs: ["--audio_only"] });
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.startRecording", () => {
      getRecorderProcess()?.stdin.write("r\n");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.stopRecording", () => {
      getRecorderProcess()?.stdin.write("s\n");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.collectNoiseProfile", () => {
      getRecorderProcess()?.stdin.write("n\n");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.openFileUnderCursor", () => {
      openFileUnderCursor();
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "videoEdit.insertAllClipsInFolder",
      insertAllClipsInFolder
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.purgeFiles", () => {
      exportVideo({
        selectedText: false,
        extraArgs: ["--audio_only", "--remove_unused_recordings"],
      });
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.showStats", () => {
      exportVideo({
        extraArgs: ["--stat"],
      });
    })
  );

  // Create movy document
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "videoEdit.createMovyAnimation",
      async () => {
        const file = await createNewDocument({
          dir: "animation",
          func: "anim",
          fileNamePlaceHolder: "movy-animation-name",
          initContent: 'import * as mo from "movy";\n\n',
          extension: ".js",
        });

        if (file) {
          startMovyServer(file);
        }
      }
    )
  );

  // Create source code document
  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.createCode", async () => {
      createNewDocument({
        dir: "src",
        func: "codef",
        fileNamePlaceHolder: "source-code-name.ext",
      });
    })
  );

  registerCreatePowerpointCommand(context);
  registerCreateSlideCommand(context);
  registerRenameFileCommand(context);
  registerToggleCrossfadeCommand(context);
  registerToggleDurationCommand(context);

  // Start movy server
  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.startMovyServer", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;

      const activeFile = editor.document.fileName;
      if (activeFile.endsWith(".js")) {
        startMovyServer(activeFile);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("videoEdit.insertMostRecentFile", () => {
      const files = getAllFiles();
      if (files.length === 0) return;

      const expr = getCompletedExpression(files[0]);
      insertTextAtCursor(expr);
    })
  );
}

function setupWhenClause(context: vscode.ExtensionContext) {
  vscode.window.onDidChangeActiveTextEditor(
    (_) => {
      updateWhenClauseContext();
    },
    null,
    context.subscriptions
  );
  updateWhenClauseContext();
}

function activate(context: vscode.ExtensionContext) {
  const config = vscode.workspace.getConfiguration();
  config.update("[markdown]", { "editor.quickSuggestions": true });

  registerCommands(context);

  setupAutoComplete(context);
  setupDecorations(context);
  setupWhenClause(context);
}

exports.activate = activate;
