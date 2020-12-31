import yo from "yo";

const n = 6;
const d = 4;

const positions = [];

const beginAngle = Math.PI / n - Math.PI / 2;
for (let i = 0; i < n; i++) {
  const angle = (i / n) * Math.PI * 2 + beginAngle;

  positions.push({ x: Math.cos(angle) * d, y: Math.sin(angle) * d, z: -0.01 });
}

for (const pos of positions) {
  const u = yo.add("user.png", {
    x: pos.x,
    y: pos.y,
    scale: 1.2,
  });
  yo.fadeIn(u, { t: 0 });
}

for (let i = 0; i < n; i++) {
  for (let j = i + 1; j < n; j++) {
    const l = yo.add("line", {
      start: positions[i],
      end: positions[j],
      lineWidth: 0.05,
    });
    yo.fadeIn(l, { t: 0 });
  }
}

for (const pos of positions) {
  for (let i = 0; i < n - 1; i++) {
    const k = yo.add("key.svg", {
      x: pos.x + 1 + i * 0.35,
      y: pos.y + 0.5,
      scale: 0.6,
      color: yo.rainbowPalette[i],
      ccw: false,
    });
    yo.fadeIn(k, { duration: 0.1 });
  }
}

yo.run();
