import mermaid from "mermaid";

export function updateMermaid() {
  mermaid.initialize({
    startOnLoad: true,
    theme: "dark",
    fontFamily: '"Roboto", "Noto Sans SC", sans-serif',
    flowchart: {},
  });
}
