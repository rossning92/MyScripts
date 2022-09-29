import mermaid from "mermaid";

require(`./mermaid.css`);

// https://mermaid-js.github.io/mermaid/#/theming?id=flowchart
export function updateMermaid() {
  mermaid.initialize({
    startOnLoad: true,
    theme: "base",
    flowchart: {},
    themeVariables: {
      primaryColor: "#303030",
      primaryBorderColor: "#ffffff",
      primaryTextColor: "#ffffff",
      lineColor: "#ffffff",
      fontFamily: '"Roboto", "Noto Sans SC", sans-serif',
    },
  });
}
