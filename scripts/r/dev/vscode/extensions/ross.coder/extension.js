const vscode = require("vscode");
const process = require("process");
const { spawn } = require("child_process");

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  const disposable = vscode.commands.registerCommand(
    "ross.coder.edit",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        return;
      }

      const selection = editor.selection;
      const fileName = editor.document.fileName;
      const fileAndLines = selection.isEmpty
        ? fileName
        : `${fileName}#${selection.start.line + 1}-${selection.end.line + 1}`;
      spawn("start_script", ["--cd=false", "r/ai/coder.py", fileAndLines], {
        detached: true,
        stdio: "ignore",
      });
    },
  );

  context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
