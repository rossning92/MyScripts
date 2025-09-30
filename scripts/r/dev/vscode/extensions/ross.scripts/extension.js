// @ts-ignore
const vscode = require("vscode");
// @ts-ignore
const http = require("http");

/**
 * @param {string} url
 * @returns {Promise<string>}
 */
function httpGet(url) {
  const options = {
    method: "GET",
    timeout: 1000, // in ms
  };

  return new Promise((resolve, reject) => {
    const req = http.request(url, options, (res) => {
      if (res.statusCode < 200 || res.statusCode > 299) {
        return reject(new Error(`HTTP status code ${res.statusCode}`));
      }

      const body = [];
      res.on("data", (chunk) => body.push(chunk));
      res.on("end", () => {
        // @ts-ignore
        const resString = Buffer.concat(body).toString();
        resolve(resString);
      });
    });

    req.on("error", (err) => {
      reject(err);
    });

    req.on("timeout", () => {
      req.destroy();
      reject(new Error("Request time out"));
    });

    req.end();
  });
}

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  const disposable = vscode.commands.registerCommand(
    "ross.scripts.helloWorld",
    async () => {
      const res = await httpGet("http://localhost:4312/scripts");
      vscode.window.showInformationMessage(res);
    }
  );

  const provider2 = vscode.languages.registerCompletionItemProvider(
    "plaintext",
    {
      /**
       * @param {vscode.TextDocument} document
       * @param {vscode.Position} position
       */
      async provideCompletionItems(document, position) {
        const linePrefix = document
          .lineAt(position)
          .text.slice(0, position.character);
        if (!linePrefix.endsWith("run_script ")) {
          return undefined;
        }

        const res = await httpGet("http://localhost:4312/scripts");
        const data = JSON.parse(res);
        return data.scripts.map(
          (/** @type {{ name: string; }} */ script) =>
            new vscode.CompletionItem(
              script.name,
              vscode.CompletionItemKind.Method
            )
        );
      },
    },
    " " // triggerCharacters
  );

  context.subscriptions.push(disposable, provider2);
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
