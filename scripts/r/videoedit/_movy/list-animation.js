import yo, { gsap, THREE } from "yo";
import { Vector3 } from "three";

const LINE_SPACE = 2;

yo.newScene(async () => {
  yo.scene.background = 0;

  let s = yo.getQueryString().s;
  if (!s) {
    s = "Item 1\nItem 2\n测试 3\nThis is Item 4";
  }

  const items = s.split("\n");
  const height = LINE_SPACE * items.length;

  for (let i = 0; i < items.length; i++) {
    await yo.addAsync(items[i], {
      y: 0.5 * height - i * LINE_SPACE - 0.5 * LINE_SPACE,
      aniEnter: "fastType",
      font: "zh",
      fontSize: 0.8
    });
  }
});
