import yo, { gsap, THREE } from "yo";
import { Vector3 } from "three";

yo.newScene(async () => {
  yo.scene.background = 0;

  const group = yo.addGroup();

  let h1_text = yo.getQueryString().h1;
  if (!h1_text) h1_text = "标题动画测试";
  const h1 = await yo.addAsync(h1_text, {
    y: 1,
    animation: "jump"
  });
  group.add(h1);

  let h2_text = yo.getQueryString().h2;
  if (!h2_text) h2_text = "Title Animation Test";
  const h2 = await yo.addAsync(h2_text, {
    fontSize: 0.6,
    color: yo.palette[3]
  });
  group.add(h2);
  h2.position.y = -0.8;

  const bb = yo.getBoundingBox(group);
  const center = bb.getCenter(new THREE.Vector3());
  const size = bb.getSize(new THREE.Vector3());

  {
    const MARGIN = 2;
    const leftBracket = await yo.addAsync("[", {
      color: yo.palette[1],
      animation: null
    });
    leftBracket.position.x = center.x - size.x * 0.5 - MARGIN;

    const rightBracket = await yo.addAsync("]", {
      color: yo.palette[1],
      animation: null
    });
    rightBracket.position.x = center.x + size.x * 0.5 + MARGIN;

    yo.addFlash(leftBracket, { position: 0, repeat: 10 });
    yo.addFlash(rightBracket, { position: 0, repeat: 10 });
  }
});
