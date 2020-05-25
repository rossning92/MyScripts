const vscode = require("vscode");
const cp = require("child_process");
const path = require("path");
const process = require("process");

var child;

function activate(context) {
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((status) => {
      const editor = vscode.window.activeTextEditor;
      if (editor) {
        const fileName = editor.document.fileName;
        if (path.basename(fileName) == "index.md") {
          child = cp.spawn("python", ["-u", "-m", "r.audio.recorder"], {
            env: {
              ...process.env,
              RECORD_OUT_DIR: path.resolve(path.dirname(fileName) + "/record"),
              RECODER_INTERACTIVE: "0",
            },
          });

          child.on("close", (code) => {
            vscode.window.showInformationMessage(
              `child process exited with code ${code}`
            );
          });

          child.stdout.on("data", (data) => {
            vscode.window.showInformationMessage(`stdout: ${data}`);
          });

          child.stderr.on("data", (data) => {
            vscode.window.showInformationMessage(`stderr: ${data}`);
          });

          // child.stdin.setEncoding("utf-8");
          // child.stdout.pipe(process.stdout);

          // child.stdin.write(selectionText);
          // child.stdin.end();

          vscode.window.showInformationMessage("yoyo");
        }
      }
    })
  );

  // const child = cp.spawn("python", [

  // ]);
  // child.stdin.setEncoding("utf-8");
  // child.stdout.pipe(process.stdout);

  // child.stdin.write(selectionText);
  // child.stdin.end();

  vscode.commands.registerCommand("yo.runSelection", function () {
    let editor = vscode.window.activeTextEditor;
    if (editor) {
      let document = editor.document;
      let selection = editor.selection;
      let selectionText = document.getText(selection);

      var activeFilePath = vscode.window.activeTextEditor.document.fileName;
      var activeDirectory = path.dirname(activeFilePath);
      vscode.window.showInformationMessage(activeDirectory);

      const terminal = vscode.window.createTerminal({
        name: "yoyo",
        cwd: activeDirectory,
        shellPath: "python.exe",
        shellArgs: [
          "-m",
          "r.web.animation.export_animation",
          "-i",
          selectionText,
        ],
      });
      // terminal.sendText("echo 'Sent text immediately after creating'");
      terminal.show();
    }
  });

  vscode.commands.registerCommand("yo.startRecording", function () {
    if (child != null) {
      child.stdin.write("r\n");
    }
  });
  vscode.commands.registerCommand("yo.stopRecording", function () {
    if (child != null) {
      child.stdin.write("s\n");
    }
  });

  // console.log("decorator sample is activated");
  // let timeout = undefined;

  // const decorationType = vscode.window.createTextEditorDecorationType(
  //   {
  //     cursor: "crosshair",
  //     // use a themable color. See package.json for the declaration and default values.
  //     backgroundColor: { id: "myextension.largeNumberBackground" },
  //   }
  // );
  // let activeEditor = vscode.window.activeTextEditor;
  // function updateDecorations() {
  //   if (!activeEditor) {
  //     return;
  //   }
  //   const regEx = /\d+/g;
  //   const text = activeEditor.document.getText();
  //   const smallNumbers = [];
  //   const largeNumbers = [];
  //   let match;
  //   const myContent = new vscode.MarkdownString(
  //     "*yoyo* [link](command:yo.hello)"
  //   );
  //   myContent.isTrusted = true;

  //   while ((match = regEx.exec(text))) {
  //     const startPos = activeEditor.document.positionAt(match.index);
  //     const endPos = activeEditor.document.positionAt(
  //       match.index + match[0].length
  //     );
  //     const decoration = {
  //       range: new vscode.Range(startPos, endPos),
  //       hoverMessage: myContent,
  //     };
  //     if (match[0].length < 3) {
  //       smallNumbers.push(decoration);
  //     } else {
  //       largeNumbers.push(decoration);
  //     }
  //   }

  //   activeEditor.setDecorations(decorationType, largeNumbers);
  // }
  // function triggerUpdateDecorations() {
  //   if (timeout) {
  //     clearTimeout(timeout);
  //     timeout = undefined;
  //   }
  //   timeout = setTimeout(updateDecorations, 500);
  // }
  // if (activeEditor) {
  //   triggerUpdateDecorations();
  // }
  // vscode.window.onDidChangeActiveTextEditor(
  //   (editor) => {
  //     activeEditor = editor;
  //     if (editor) {
  //       triggerUpdateDecorations();
  //     }
  //   },
  //   null,
  //   context.subscriptions
  // );
  // vscode.workspace.onDidChangeTextDocument(
  //   (event) => {
  //     if (activeEditor && event.document === activeEditor.document) {
  //       triggerUpdateDecorations();
  //     }
  //   },
  //   null,
  //   context.subscriptions
  // );
}

exports.activate = activate;
