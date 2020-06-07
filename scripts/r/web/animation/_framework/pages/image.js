import yo, { gsap, THREE } from "yo";
import { Vector3 } from "three";

const LINE_SPACE = 2;

yo.newScene(async () => {
  const src = yo.getQueryString().src;

  let x = yo.getQueryString().x;
  if (!x) x = 0;

  let y = yo.getQueryString().y;
  if (!y) y = 0.5;

  let t = yo.getQueryString().t;
  if (!t) t = 5;

  yo.scene.background = 0;
  yo.setupOrthoCamera();

  const im = await yo.addAsync(src, {
    y: -y * t * 0.5,
    animation: null,
  });

  const viewportW = 28.444 + x;
  const viewportH = 16 + y * t;

  const scale =
    viewportW / im.scale.x > viewportH / im.scale.y
      ? viewportW / im.scale.x
      : viewportH / im.scale.y;

  im.scale.multiplyScalar(scale);

  yo.moveTo(im, { y: y * t * 0.5, ease: "none", duration: t }, "0");
});
