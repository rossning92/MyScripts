import yo, { gsap, THREE } from "yo";

let h1_text = yo.getQueryString().h1;
if (!h1_text) h1_text = "标题动画测试";
let h2_text = yo.getQueryString().h2;
if (!h2_text) h2_text = "Title Animation Test";

const g = yo.addGroup();

yo.add(h1_text, {
  y: 1,
  animation: "fadeIn|growX2",
  letterSpacing: 0.2,
  parent: g,
});

const h2 = yo.add(h2_text, {
  fontSize: 0.6,
  color: yo.palette[3],
  animation: null,
  parent: g,
  y: -1,
});

yo.addFlyInAnimation(h2, { beginDegrees: 90, beginScale: 10, t: "0.2" });

yo.newScene(async () => {
  yo.scene.background = 0;

  // const bb = yo.getBoundingBox(group);
  // const center = bb.getCenter(new THREE.Vector3());
  // const size = bb.getSize(new THREE.Vector3());

  // const MARGIN = 2;
  // for (let i = 0; i < 2; i++) {
  //   const t = i == 0 ? -1 : 1;

  //   const bracket = await yo.addAsync(i == 0 ? "{" : "}", {
  //     x: center.x + t * size.x * 0.5,
  //     y: 0.25,
  //     fontSize: 1.2,
  //     color: yo.palette[1],
  //     animation: null,
  //     parent: group,
  //   });

  //   yo.moveTo(bracket, {
  //     x: center.x + t * (size.x * 0.5 + MARGIN),
  //     duration: 2,
  //     t: "<",
  //   });
  //   yo.addAnimation(bracket, "grow", { aniPos: "<" });
  // }

  // yo.moveTo(group, { scale: 1.25, t: "0.8" });
});
