const vscode = require("vscode");
const process = require("process");

/**
 * Opens a terminal with the specified options.
 *
 * @param {Object} options - The options for opening the terminal.
 * @param {string[]} options.args - The shell command to run in the terminal.
 */
async function runCoder({ args }) {
  const name = "Coder";

  // Close any existing terminals.
  for (const term of vscode.window.terminals) {
    if (term.name === name) {
      term.dispose();
    }
  }

  const terminalName =
    process.platform === "win32" ? "run_script.exe" : "run_script";
  const terminal = vscode.window.createTerminal(name, terminalName, [
    "@command_wrapper=1",
    "r/ai/code_agent.py",
    ...args,
  ]);

  terminal.show();
}

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  const disposable = vscode.commands.registerCommand(
    "my-coder.edit",
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

      await runCoder({
        args: [fileAndLines],
      });
    }
  );

  context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
