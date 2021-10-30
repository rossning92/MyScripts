import * as mo from "movy";

export const palette = {
  red: "#e74c3c",
  purple: "#9b59b6",
  deeppurple: "#8e44ad",
  blue: "#3498db",
  teal: "#1abc9c",
  green: "#2ecc71",
  yellow: "#f1c40f",
  orange: "#e67e22",
  grey: "#95a5a6",
};

export function addIcons_Circular(icons) {
  const g = mo.addGroup();

  const r = 3;
  icons.forEach((icon, i) => {
    const angle = (i / icons.length) * Math.PI * 2;
    const x = r * Math.cos(angle);
    const y = r * Math.sin(angle) * 0.8;

    mo.addImage(icon, { g, scale: 1.2 })
      .grow2({ t: "<0.2" })
      .moveTo({ x, y, t: "<" });
  });
}

export function addIcons_List(icons, labels) {
  const dist = 6;
  const scale = 3;
  const fontSize = 0.5;

  icons.forEach((icon, i) => {
    const x = (i - icons.length * 0.5 + 0.5) * dist;
    mo.addImage(icon, {
      x,
      scale,
      y: 0.5,
    }).grow();

    if (labels) {
      mo.addText(labels[i], { x, y: -1.5, scale: fontSize }).reveal({
        direction: "down",
        t: "<0.2",
      });
    }
  });
}

export function addIcons_Grid(
  icons,
  { rows = 2, cols = 3, scale = 2, stagger = 0.1, labels } = {}
) {
  const imageScale = 0.75;
  const textScale = 0.08;

  const group = mo.addGroup({ scale });
  group.grow();

  for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
      const index = i * cols + j;
      if (index < icons.length) {
        const x = j - (cols - 1) / 2;
        const y = -(i - (rows - 1) / 2) + textScale;

        const icon = icons[index];
        group.addImage(icon, { x, y, scale: imageScale }).grow2({
          t: `<${stagger}`,
        });
        if (labels !== undefined)
          group
            .addText(labels[index], {
              scale: textScale,
              x,
              y: y - imageScale * 0.5 - textScale,
            })
            .fadeIn({ t: "<" });
      }
    }
  }
}

export function addFileIcon(icon, name, { scale = 3, x, y, t, font } = {}) {
  const fontSize = 0.12;
  const g = mo.addGroup({ scale, x, y });
  g.addImage("file.png", { y: fontSize / 2 });
  g.addImage(icon, { scale: 0.6, y: fontSize / 2 });
  g.grow2({ t });

  g.addText(name, {
    scale: fontSize,
    y: -0.5 - fontSize,
    font,
  }).reveal({ direction: "down", t: "<0.05" });
}

export function addTitle(
  title,
  {
    font = "condensed",
    t,
    textSize = 1,
    backgroundColor = "white",
    color = "black",
  } = {}
) {
  const g = mo.addGroup();
  g.scale(1.1, { duration: 5, ease: "linear", t });
  g.addRect({
    width: 8,
    height: textSize * 1.8,
    color: backgroundColor,
  }).reveal({
    t: "<",
  });
  g.addText(title, { font, color, scale: textSize }).reveal({
    direction: "right",
    t: "<0.1",
  });
  return g;
}

export function addTitle2(
  text1,
  text2,
  { font, t, textHeight1 = 1.4, textHeight2 = 1.4 * 0.75, width } = {}
) {
  if (width === undefined) {
    width =
      [...text1]
        .map((x) => (/[a-zA-Z ]/.test(x) ? 0.5 : 1))
        .reduce((a, b) => a + b) + 3;
  }

  const halfTotalHeight = (textHeight1 + textHeight2) * 0.5;

  cameraZoom();

  const y1 = halfTotalHeight - textHeight1 * 0.5;
  const g = mo.addGroup();
  //   g.scale(1.1, { duration: 5, ease: "linear", t });
  g.addRect({
    width,
    height: textHeight1,
    color: "#fc7281",
    z: -0.01,
    y: y1,
  }).reveal({
    t: "<",
  });
  g.addText(text1, {
    font,
    color: "black",
    scale: textHeight1 * 0.5,
    y: y1,
  }).reveal({
    direction: "right",
    t: "<0.15",
  });

  const y2 = -(halfTotalHeight - textHeight2 * 0.5);
  g.addRect({
    width,
    height: textHeight2,
    color: "#ffffff",
    z: -0.01,
    y: y2,
  }).reveal({
    direction: "down",
    t: "<0.15",
  });
  g.addText(text2, {
    font,
    color: "black",
    scale: textHeight2 * 0.5,
    y: y2,
    font: "condensed",
  }).reveal({
    direction: "left",
    t: "<0.15",
  });

  return g;
}

export function cameraZoom() {
  mo.cameraMoveTo({ zoom: 1.05, duration: 5, ease: "power1.out", t: 0 });
}
