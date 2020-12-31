import yo from "yo";

const n = 5;
const d = 6;

const positions = [];
for (let i = 0; i < n; i++) {
  const angle = (i / n) * Math.PI * 2;

  positions.push({ x: Math.cos(angle) * d, y: Math.sin(angle) * d, z: -0.01 });
}

for (const pos of positions) {
  const u = yo.add("user.png", {
    x: pos.x,
    y: pos.y,
    scale: 2,
  });
  yo.fadeIn(u, { t: 0 });
}

for (let i = 0; i < n; i++) {
  for (let j = i + 1; j < n; j++) {
    const l = yo.add("line", { start: positions[i], end: positions[j] });
    yo.fadeIn(l, { t: 0 });
  }
}

for (const pos of positions) {
  for (let i = 0; i < n - 1; i++) {
    const k = yo.add("key.svg", {
      x: pos.x + 1 + i * 0.7,
      y: pos.y + 1,
      scale: 1,
      color: yo.rainbowPalette[i],
      ccw: false,
    });
    yo.fadeIn(k, { duration: 0.1 });
  }
}

yo.run();
