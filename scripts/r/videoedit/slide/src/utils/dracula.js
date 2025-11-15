import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { tags as t } from "@lezer/highlight";
import { EditorView } from "codemirror";

export const createTheme = ({ theme, settings = {}, styles = [] }) => {
  const themeOptions = {
    ".cm-gutters": {},
  };
  const baseStyle = {};
  if (settings.background) {
    baseStyle.backgroundColor = settings.background;
  }
  if (settings.backgroundImage) {
    baseStyle.backgroundImage = settings.backgroundImage;
  }
  if (settings.foreground) {
    baseStyle.color = settings.foreground;
  }
  if (settings.fontSize) {
    baseStyle.fontSize = settings.fontSize;
  }
  if (settings.background || settings.foreground) {
    themeOptions["&"] = baseStyle;
  }

  themeOptions["&.cm-editor"] = {
    width: "1280px",
    minHeight: "1080px",
    maxHeight: "1080px",
  };

  if (settings.fontFamily) {
    themeOptions["&.cm-editor .cm-scroller"] = {
      fontFamily: settings.fontFamily,
    };
  }
  if (settings.gutterBackground) {
    themeOptions[".cm-gutters"].backgroundColor = settings.gutterBackground;
  }
  if (settings.gutterForeground) {
    themeOptions[".cm-gutters"].color = settings.gutterForeground;
  }
  if (settings.gutterBorder) {
    themeOptions[".cm-gutters"].borderRightColor = settings.gutterBorder;
  }

  if (settings.caret) {
    themeOptions[".cm-content"] = {
      caretColor: settings.caret,
    };
    themeOptions[".cm-cursor, .cm-dropCursor"] = {
      borderLeftColor: settings.caret,
    };
  }
  let activeLineGutterStyle = {};
  if (settings.gutterActiveForeground) {
    activeLineGutterStyle.color = settings.gutterActiveForeground;
  }
  if (settings.lineHighlight) {
    themeOptions[".cm-activeLine"] = {
      backgroundColor: settings.lineHighlight,
    };
    activeLineGutterStyle.backgroundColor = settings.lineHighlight;
  }
  themeOptions[".cm-activeLineGutter"] = activeLineGutterStyle;

  if (settings.selection) {
    themeOptions[
      "&.cm-focused .cm-selectionBackground, & .cm-line::selection, & .cm-selectionLayer .cm-selectionBackground, .cm-content ::selection"
    ] = {
      background: settings.selection + " !important",
    };
  }
  if (settings.selectionMatch) {
    themeOptions["& .cm-selectionMatch"] = {
      backgroundColor: settings.selectionMatch,
    };
  }
  const themeExtension = EditorView.theme(themeOptions, {
    dark: theme === "dark",
  });

  const highlightStyle = HighlightStyle.define(styles);
  const extension = [themeExtension, syntaxHighlighting(highlightStyle)];

  return extension;
};

export const defaultSettingsDracula = {
  background: "#282a36",
  foreground: "#f8f8f2",
  caret: "#f8f8f0",
  selection: "#44475a",
  selectionMatch: "rgba(255, 255, 255, 0.2)",
  gutterBackground: "#282a36",
  gutterForeground: "#6272a4",
  gutterBorder: "transparent",
  lineHighlight: "transparent",
};

export const draculaDarkStyle = [
  { tag: t.comment, color: "#6272a4" },
  { tag: t.string, color: "#f1fa8c" },
  { tag: t.atom, color: "#bd93f9" },
  { tag: t.meta, color: "#f8f8f2" },
  { tag: [t.keyword, t.operator, t.tagName], color: "#ff79c6" },
  { tag: [t.function(t.propertyName), t.propertyName], color: "#66d9ef" },
  {
    tag: [
      t.definition(t.variableName),
      t.function(t.variableName),
      t.className,
      t.attributeName,
    ],
    color: "#50fa7b",
  },
  { tag: t.atom, color: "#bd93f9" },
];

export const draculaInit = (options) => {
  const { theme = "dark", settings = {}, styles = [] } = options || {};
  return createTheme({
    theme: theme,
    settings: {
      ...defaultSettingsDracula,
      ...settings,
    },
    styles: [...draculaDarkStyle, ...styles],
  });
};

export const dracula = draculaInit();
