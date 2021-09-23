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

export function addFileIcon(icon, name) {
  const fontSize = 0.12;
  const g = mo.addGroup({ scale: 3 });
  g.addImage("_utils/file.png", { y: fontSize / 2 });
  g.addImage(icon, { scale: 0.6, y: fontSize / 2 });
  g.grow2();

  g.addText(name, {
    scale: fontSize,
    y: -0.5 - fontSize,
  }).reveal({ direction: "down", t: "<0.05" });
}
