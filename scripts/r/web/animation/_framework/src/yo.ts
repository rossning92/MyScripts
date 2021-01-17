import * as dat from "dat.gui";
import * as THREE from "three";
import TextMesh from "./objects/TextMesh";

import gsap from "gsap";

import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { GlitchPass } from "./utils/GlitchPass";
import { MotionBlurPass } from "./utils/MotionBlurPass";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { SSAARenderPass } from "three/examples/jsm/postprocessing/SSAARenderPass.js";
import { TAARenderPass } from "three/examples/jsm/postprocessing/TAARenderPass.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";
import { WaterPass } from "./utils/WaterPass";

import Stats from "three/examples/jsm/libs/stats.module.js";

declare class CCapture {
  constructor(params: any);
}

gsap.ticker.remove(gsap.updateRoot);

let ENABLE_GLITCH_PASS = false;
let WIDTH = 1920;
let HEIGHT = 1080;
let AA_METHOD = "msaa";
let ENABLE_MOTION_BLUR_PASS = false;
let MOTION_BLUR_SAMPLES = 1;

let bloomEnabled = false;

let defaultAnimation = undefined;

var outFileName = undefined;
var captureStatus;
var globalTimeline = gsap.timeline({ onComplete: stopCapture });

const mainTimeline = gsap.timeline();
globalTimeline.add(mainTimeline, "0");

let stats = undefined;
let capturer = undefined;
let renderer = undefined;
let composer = undefined;
let scene = undefined;
let camera = undefined;
let lightGroup = undefined;
let cameraControls = undefined;
let palette = ["#1a535c", "#4ecdc4", "#ff6b6b", "#ffe66d", "#f7fff7"];

var glitchPass;
var gridHelper;
let backgroundAlpha = 1.0;

var animationCallbacks = [];

let options = {
  /* Recording options */
  format: "webm",
  framerate: 25,
  start: function () {
    startCapture();
  },
  stop: function () {
    stopCapture();
  },
  timeline: 0,
};

let subClipDurations = [];
let currentCutPoint = 0;

var gui = new dat.GUI();
gui.add(options, "format", ["webm", "png"]);
gui.add(options, "framerate", [10, 25, 30, 60, 120]);
gui.add(options, "start");
gui.add(options, "stop");

const sceneObjects = {};

function startCapture({ resetTiming = true, name = undefined } = {}) {
  if (name === undefined) {
    name = document.title;
  }
  outFileName = name;

  if (gridHelper !== undefined) {
    gridHelper.visible = false;
  }

  if (resetTiming) {
    // Reset gsap
    gsap.ticker.remove(gsap.updateRoot);

    lastTs = undefined;
  }

  capturer = new CCapture({
    verbose: true,
    display: false,
    framerate: options.framerate,
    motionBlurFrames: MOTION_BLUR_SAMPLES,
    quality: 100,
    format: options.format,
    workersPath: "dist/src/",
    timeLimit: 0,
    frameLimit: 0,
    autoSaveTime: 0,
    name,
  });

  capturer.start();

  captureStatus.innerText = "capturing";
}

declare global {
  interface Window {
    startCapture;
  }
}
window.startCapture = window.startCapture || {};

function stopCapture() {
  if (capturer !== undefined) {
    capturer.stop();
    capturer.save();
    capturer = undefined;
    captureStatus.innerText = "stopped";

    // var FileSaver = require("file-saver");
    // var blob = new Blob([JSON.stringify(metaData)], {
    //   type: "text/plain;charset=utf-8",
    // });
    // FileSaver.saveAs(
    //   blob,
    //   outFileName !==null ? outFileName + ".json" : "animation-meta-file.json"
    // );
  }
}

function resize(width, height) {
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

function createOrthoCamera({ width = WIDTH, height = HEIGHT } = {}) {
  const aspect = WIDTH / HEIGHT;
  const frustumSize = 16;
  camera = new THREE.OrthographicCamera(
    (frustumSize * aspect) / -2,
    (frustumSize * aspect) / 2,
    frustumSize / 2,
    frustumSize / -2,
    -1000,
    1000
  );
}

function setupScene({ width = WIDTH, height = HEIGHT } = {}) {
  renderer = new THREE.WebGLRenderer({
    alpha: true,
    antialias: AA_METHOD === "msaa",
  });
  renderer.localClippingEnabled = true;

  renderer.setSize(width, height);
  document.body.appendChild(renderer.domElement);

  {
    stats = Stats();
    // stats.showPanel(1); // 0: fps, 1: ms, 2: mb, 3+: custom
    document.body.appendChild(stats.dom);
  }

  renderer.setClearColor(0x000000, backgroundAlpha);
  scene.background = 0;

  if (camera === undefined) {
    // This will ensure the size of 10 in the vertical direction.
    camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 5000);
    camera.position.set(0, 0, 8.66);
    camera.lookAt(new Vector3(0, 0, 0));
  }

  cameraControls = new OrbitControls(camera, renderer.domElement);

  scene.add(new THREE.AmbientLight(0x000000));

  // Torus
  if (0) {
    let geometry = new THREE.TorusKnotBufferGeometry(2.5, 1, 150, 40);
    let material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
    let mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    mesh.onBeforeRender = () => {
      mesh.rotation.y += 0.05;
    };
  }

  let renderScene = new RenderPass(scene, camera);

  composer = new EffectComposer(renderer);
  composer.setSize(WIDTH, HEIGHT);
  composer.addPass(renderScene);

  if (ENABLE_MOTION_BLUR_PASS) {
    // Motion blur pass
    let options = {
      samples: 50,
      expandGeometry: 1,
      interpolateGeometry: 1,
      smearIntensity: 1,
      blurTransparent: true,
      renderCameraBlur: true,
    };
    let motionPass = new MotionBlurPass(scene, camera, options);
    composer.addPass(motionPass);

    motionPass.debug.display = 0;
    // motionPass.renderToScreen = true;
  }

  if (bloomEnabled) {
    // Bloom pass
    let bloomPass = new UnrealBloomPass(
      new THREE.Vector2(WIDTH, HEIGHT),
      0.5, // Strength
      0.4, // radius
      0.85 // threshold
    );
    composer.addPass(bloomPass);
  }

  if (0) {
    // Water pass
    const waterPass = new WaterPass();
    waterPass.factor = 0.1;
    composer.addPass(waterPass);
    // alert();
  }

  if (AA_METHOD === "fxaa") {
    composer.addPass(createFxaaPass(renderer));
  } else if (AA_METHOD === "ssaa") {
    let ssaaRenderPass = new SSAARenderPass(scene, camera, 0, 0);
    ssaaRenderPass.unbiased = true;
    composer.addPass(ssaaRenderPass);
  } else if (AA_METHOD === "smaa") {
    let pixelRatio = renderer.getPixelRatio();
    let smaaPass = new SMAAPass(WIDTH * pixelRatio, HEIGHT * pixelRatio);
    composer.addPass(smaaPass);
  } else if (AA_METHOD === "taa") {
    let taaRenderPass = new TAARenderPass(scene, camera, 0, 0);
    taaRenderPass.unbiased = false;
    taaRenderPass.sampleLevel = 4;
    composer.addPass(taaRenderPass);
  }

  if (ENABLE_GLITCH_PASS) {
    glitchPass = new GlitchPass();
    composer.addPass(glitchPass);
  }
}

var lastTs = undefined;
var timeElapsed = 0;
var animTimeElapsed = 0;

function animate(
  time /* `time` parameter is buggy in `ccapture`. Do not use! */
) {
  const nowInSecs = Date.now() / 1000;

  requestAnimationFrame(animate);

  let delta;
  {
    // Compute `timeElapsed`. This works for both animation preview and capture.
    if (lastTs === undefined) {
      delta = 0.000001;
      lastTs = nowInSecs;
      globalTimeline.seek(0, false);
      animTimeElapsed = 0;
    } else {
      delta = nowInSecs - lastTs;
      lastTs = nowInSecs;
    }

    timeElapsed += delta;
    animTimeElapsed += delta;
  }

  gsap.updateRoot(timeElapsed);

  cameraControls.update();

  animationCallbacks.forEach((callback) => {
    callback(delta, animTimeElapsed);
  });

  composer.render();

  stats.update();

  if (capturer) capturer.capture(renderer.domElement);
}

function moveCamera({ x = 0, y = 0, z = 10, t = undefined } = {}) {
  commandList.push(() => {
    const tl = gsap.to(camera.position, {
      x,
      y,
      z,
      onUpdate: () => {
        camera.lookAt(new Vector3(0, 0, 0));
      },
      duration: 0.5,
      ease: "expo.out",
    });
    mainTimeline.add(tl, t);
  });
}

scene = new THREE.Scene();

function generateRandomString(length) {
  var result = "";
  var characters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  var charactersLength = characters.length;
  for (var i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
}

function randomInt(min, max) {
  return Math.floor(random() * (max - min + 1)) + min;
}

function generateLinearGradientTexture() {
  var size = 512;

  // create canvas
  var canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;

  // get context
  var context = canvas.getContext("2d");

  // draw gradient
  context.rect(0, 0, size, size);
  var gradient = context.createLinearGradient(0, 0, size, size);
  gradient.addColorStop(0, "#ff0000"); // light blue
  gradient.addColorStop(1, "#00ff00"); // dark blue
  context.fillStyle = gradient;
  context.fill();

  var texture = new THREE.Texture(canvas);
  texture.needsUpdate = true; // important!
  return texture;
}

import { Vector3, Material } from "three";

import { FXAAShader } from "three/examples/jsm/shaders/FXAAShader.js";
import { SMAAPass } from "three/examples/jsm/postprocessing/SMAAPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass";

function createFxaaPass(renderer) {
  let fxaaPass = new ShaderPass(FXAAShader);

  // let pixelRatio = renderer.getPixelRatio();
  // fxaaPass.material.uniforms["resolution"].value.x = 1 / (WIDTH * pixelRatio);
  // fxaaPass.material.uniforms["resolution"].value.y = 1 / (HEIGHT * pixelRatio);

  return fxaaPass;
}

// createRingAnimation();

function createCanvas({ width = 64, height = 64 } = {}) {
  let canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

import { SVGLoader } from "three/examples/jsm/loaders/SVGLoader";
function createLine3D({
  color = "0xffffff",
  points = [],
  lineWidth = 0.1,
} = {}) {
  if (points.length === 0) {
    points.push(new THREE.Vector3(-1.73, -1, 0));
    points.push(new THREE.Vector3(1.73, -1, 0));
    points.push(new THREE.Vector3(0, 2, 0));
    points.push(points[0]);
  }

  let lineColor = new THREE.Color(0xffffff);
  let style = SVGLoader.getStrokeStyle(
    lineWidth,
    lineColor.getStyle(),
    "miter",
    "butt",
    4
  );
  // style.strokeLineJoin = "round";
  let geometry = SVGLoader.pointsToStroke(points, style, 12, 0.001);

  let material = new THREE.MeshBasicMaterial({
    color,
    side: THREE.DoubleSide,
    transparent: true,
  });

  let mesh = new THREE.Mesh(geometry, material);
  return mesh;
}

function reveal(obj, { dir = "up", t = undefined } = {}) {
  commandList.push(() => {
    const object3d = sceneObjects[obj];

    let localPlane;
    let x = 0;
    let y = 0;
    let z = 0;

    const boundingBox = getBoundingBox(object3d);
    if (dir === "right") {
    } else if (dir === "left") {
    } else if (dir === "up") {
      localPlane = new THREE.Plane(
        new THREE.Vector3(0, 1, 0),
        -boundingBox.min.y
      );
      y = object3d.position.y - (boundingBox.max.y - boundingBox.min.y);
    } else if (dir === "down") {
      localPlane = new THREE.Plane(
        new THREE.Vector3(0, -1, 0),
        boundingBox.max.y
      );
      y = object3d.position.y + (boundingBox.max.y - boundingBox.min.y);
    }

    const materials = getAllMaterials(object3d);
    for (const material of materials) {
      material.clippingPlanes = [localPlane];
    }

    const tl = gsap.from(object3d.position, {
      y,
      duration: 0.6,
      ease: "expo.out",
    });

    mainTimeline.add(tl, t);
  });
}

function createCircle2D() {
  let geometry = new THREE.CircleGeometry(0.5, 32);

  let material = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 1.0,
  });

  let circle = new THREE.Mesh(geometry, material);
  scene.add(circle);
  return circle;
}

function createObject({
  type = "sphere",
  materialType = "basic",
  segments = 32,
  color = 0xffffff,
} = {}) {
  let geometry;
  if (type === "sphere") {
    geometry = new THREE.SphereGeometry(0.5, segments, segments);
  } else if (type === "circle") {
    geometry = new THREE.CircleGeometry(0.5, segments);
  } else if (type === "cone") {
    geometry = new THREE.ConeGeometry(0.5, 1.0, segments, segments);
  }

  let material;
  if (materialType === "phong") {
    material = new THREE.MeshPhongMaterial({
      color,
    });
  } else if (materialType === "physical") {
    material = new THREE.MeshPhysicalMaterial({
      clearcoat: 1.0,
      clearcoatRoughness: 0.1,
      metalness: 0.9,
      roughness: 0.5,
      color,
      normalScale: new THREE.Vector2(0.15, 0.15),
    });
  } else {
    material = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 1.0,
    });
  }

  let mesh = new THREE.Mesh(geometry, material);
  scene.add(mesh);
  return mesh;
}

function addPulseAnimation(object3d) {
  let tl = gsap.timeline();
  tl.fromTo(
    object3d.material,
    0.8,
    { opacity: 1 },
    {
      opacity: 0.3,
      yoyo: true,
      repeat: 5,
      ease: "power2.in",
      // repeatDelay: 0.4,
    }
  );
}

function createRectMeshLine({ lineWidth = 0.1, color = "0x00ff00" } = {}) {
  const mesh = createLine3D({
    points: [
      new THREE.Vector3(-0.5, -0.5, 0),
      new THREE.Vector3(-0.5, 0.5, 0),
      new THREE.Vector3(0.5, 0.5, 0),
      new THREE.Vector3(0.5, -0.5, 0),
      new THREE.Vector3(-0.5, -0.5, 0),
    ],
    lineWidth,
    color,
  });
  return mesh;
}

function createRectLine({ color = "0x00ff00" } = {}) {
  var material = new THREE.LineBasicMaterial({
    color,
  });

  var geometry = new THREE.Geometry();
  geometry.vertices.push(
    new THREE.Vector3(-0.5, -0.5, 0),
    new THREE.Vector3(-0.5, 0.5, 0),
    new THREE.Vector3(0.5, 0.5, 0),
    new THREE.Vector3(0.5, -0.5, 0),
    new THREE.Vector3(-0.5, -0.5, 0)
  );

  var line = new THREE.Line(geometry, material);
  return line;
}

function createGrid({
  rows = 10,
  cols = 10,
  lineWidth = 0.05,
  useMeshLine = false,
  color = "0x00ff00",
} = {}) {
  const group = new THREE.Group();
  for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
      let cellObject;
      if (useMeshLine) {
        cellObject = createRectMeshLine({
          lineWidth,
          color,
        });
      } else {
        cellObject = createRectLine({
          color,
        });
      }

      cellObject.position.set(-0.5 * cols + j, -0.5 * rows + i, 0);
      group.add(cellObject);
    }
  }
  return group;
}

function getAllMaterials(object3d): THREE.Material[] {
  const materials = new Set<THREE.Material>();
  const getMaterialsRecursive = (object3d) => {
    if (object3d.material) {
      materials.add(object3d.material);
    }
    object3d.children.forEach((child) => {
      getMaterialsRecursive(child);
    });
  };
  getMaterialsRecursive(object3d);
  return Array.from(materials);
}

function createFadeInAnimation(
  object3d,
  { duration = undefined, ease = "linear" } = {}
) {
  if (duration === undefined) {
    duration = 0.25;
  }

  const tl = gsap.timeline({ defaults: { duration, ease } });

  const materials = getAllMaterials(object3d);
  for (const material of materials) {
    material.transparent = true;
    tl.from(
      material,
      {
        opacity: 0,
        duration,
      },
      "<"
    );
  }

  return tl;
}

function setOpacity(object3d, opacity = 1.0) {
  if (object3d.material !== undefined) {
    object3d.material.transparent = true;
    object3d.material.opacity = opacity;
  }

  object3d.children.forEach((x) => {
    setOpacity(x, opacity);
  });
}

function createFadeOutAnimation(
  obj,
  { duration = undefined, ease = "linear" } = {}
) {
  if (duration === undefined) {
    duration = 0.25;
  }

  const tl = gsap.timeline({ defaults: { duration, ease } });

  const materials = getAllMaterials(obj);
  materials.forEach((material) => {
    material.transparent = true;
    tl.to(
      material,
      {
        opacity: 0,
      },
      "<"
    );
  });

  return tl;
}

function addJumpIn(object3d, { ease = "elastic.out(1, 0.2)" } = {}) {
  const duration = 0.5;

  let tl = gsap.timeline();
  tl.from(object3d.position, {
    y: object3d.position.y + 1,
    ease,
    duration,
  });

  tl.add(
    createFadeInAnimation(object3d, {
      duration,
    }),
    "<"
  );

  return tl;
}

function jumpTo(object3d, { x = 0, y = 0 }) {
  let tl = gsap.timeline();
  tl.to(object3d.position, {
    x,
    y,
    ease: "elastic.out(1, 0.2)",
    duration: 0.5,
  });

  tl.from(
    object3d.material,
    {
      opacity: 0,
      duration: 0.5,
    },
    "<"
  );

  return tl;
}

function createMotionAnimation(
  object3d,
  {
    position = undefined,
    x = undefined,
    y = undefined,
    z = undefined,
    rx = undefined,
    ry = undefined,
    rz = undefined,
    sx = undefined,
    sy = undefined,
    sz = undefined,
    scale = undefined,
    dx = undefined,
    dy = undefined,
    duration = 0.5,
    ease = "power2.out",
    multiplyScale = undefined,
  } = {}
) {
  if (dx !== undefined) x = object3d.position.x + dx;
  if (dy !== undefined) y = object3d.position.y + dy;

  let tl = gsap.timeline({
    defaults: {
      duration,
      ease,
    },
  });

  if (position !== undefined) {
    tl.to(
      object3d.position,
      { x: position[0], y: position[1], z: position[2] },
      "<"
    );
  } else {
    if (x !== undefined) tl.to(object3d.position, { x }, "<");
    if (y !== undefined) tl.to(object3d.position, { y }, "<");
    if (z !== undefined) tl.to(object3d.position, { z }, "<");
  }

  if (rx !== undefined) tl.to(object3d.rotation, { x: rx }, "<");
  if (ry !== undefined) tl.to(object3d.rotation, { y: ry }, "<");
  if (rz !== undefined) tl.to(object3d.rotation, { z: rz }, "<");

  if (scale !== undefined) {
    tl.to(
      object3d.scale,
      {
        x: scale,
        y: scale,
        z: scale,
      },
      "<"
    );
  } else if (multiplyScale !== undefined) {
    tl.to(
      object3d.scale,
      {
        x: object3d.scale.x * multiplyScale,
        y: object3d.scale.y * multiplyScale,
        z: object3d.scale.z * multiplyScale,
      },
      "<"
    );
  } else {
    if (sx !== undefined) tl.to(object3d.scale, { x: sx }, "<");
    if (sy !== undefined) tl.to(object3d.scale, { y: sy }, "<");
    if (sz !== undefined) tl.to(object3d.scale, { z: sz }, "<");
  }

  return tl;
}

// TODO: remove
function flyIn(
  object3d,
  {
    dx = 0.0,
    dy = 0.0,
    duration = 0.5,
    beginDegrees = 0,
    beginScale = 0.01,
    ease = "power.in",
    t = "+=0",
  } = {}
) {
  let tl = gsap.timeline({
    defaults: {
      duration,
      ease,
    },
  });

  tl.from(object3d.position, {
    x: object3d.position.x + dx,
    y: object3d.position.y + dy,
  });

  tl.from(
    object3d.rotation,
    {
      z: object3d.rotation.z + (beginDegrees * Math.PI) / 180,
    },
    "<"
  );

  if (beginScale !== undefined) {
    tl.from(
      object3d.scale,
      {
        x: beginScale,
        y: beginScale,
        z: beginScale,
      },
      "<"
    );
  }

  tl.add(createFadeInAnimation(object3d), "<");

  mainTimeline.add(tl, t);

  return tl;
}

function addFlash(object3d, { speed = 4 } = {}) {
  const materials = getAllMaterials(object3d);

  materials.forEach((material) => {
    material.transparent = true;
  });

  animationCallbacks.push((delta, elapsed) => {
    materials.forEach((material) => {
      material.opacity = Math.max(0, Math.sin(elapsed * speed));
    });
  });
}

function addDefaultLights() {
  if (lightGroup === undefined) {
    const lightGroup = addThreeJsGroup();

    const light0 = new THREE.PointLight(0xffffff, 1, 0);
    light0.position.set(0, 200, 0);
    lightGroup.add(light0);

    const light1 = new THREE.PointLight(0xffffff, 1, 0);
    light1.position.set(100, 200, 100);
    lightGroup.add(light1);

    const light2 = new THREE.PointLight(0xffffff, 1, 0);
    light2.position.set(-100, -200, -100);
    lightGroup.add(light2);
  }
}

function createTriangle({
  vertices = [
    new THREE.Vector3(-1.732, -1, 0),
    new THREE.Vector3(1.732, -1, 0),
    new THREE.Vector3(0, 2, 0),
  ],
  color = 0xffffff,
  opacity = 1.0,
} = {}) {
  let geometry = new THREE.Geometry();

  geometry.vertices.push(vertices[0], vertices[1], vertices[2]);

  geometry.faces.push(new THREE.Face3(0, 1, 2));

  let material = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity,
  });

  let mesh = new THREE.Mesh(geometry, material);
  return mesh;
}

function shake2D(
  obj,
  { shakes = 20, duration = 0.01, strength = 0.5, t = undefined } = {}
) {
  function R(max, min) {
    return Math.random() * (max - min) + min;
  }

  commandList.push(() => {
    const object3d = sceneObjects[obj];

    var tl = gsap.timeline({ defaults: { ease: "none" } });
    tl.set(object3d, { x: "+=0" }); // this creates a full _gsTransform on object3d

    //store the transform values that exist before the shake so we can return to them later
    var initProps = {
      x: object3d.position.x,
      y: object3d.position.y,
      rotation: object3d.position.z,
    };

    //shake a bunch of times
    for (var i = 0; i < shakes; i++) {
      const offset = R(-strength, strength);
      tl.to(object3d.position, duration, {
        x: initProps.x + offset,
        y: initProps.y - offset,
        // rotation: initProps.rotation + R(-5, 5)
      });
    }
    //return to pre-shake values
    tl.to(object3d.position, duration, {
      x: initProps.x,
      y: initProps.y,
      // scale: initProps.scale,
      // rotation: initProps.rotation
    });

    mainTimeline.add(tl, t);
  });
}

function createTriangleOutline({ color = "0xffffff" } = {}) {
  const VERTICES = [
    new THREE.Vector3(-1.732, -1, 0),
    new THREE.Vector3(1.732, -1, 0),
    new THREE.Vector3(0, 2, 0),
  ];

  const triangleStroke = createLine3D({
    points: VERTICES.concat(VERTICES[0]),
    lineWidth: 0.3,
    color,
  });
  triangleStroke.position.set(-6.4, -6.4, 0.02);
  // triangleStroke.scale.set(0.2, 0.2, 0.2);
  // scene.add(triangleStroke);
  return triangleStroke;
}

// TODO: Deprecated.
// function addExplosionAnimation(
//   objectGroup,
//   { ease = "expo.out", duration = 1.5 } = {}
// ) {
//   const tl = gsap.timeline({
//     defaults: {
//       duration,
//       ease: ease,
//     },
//   });

//   tl.from(
//     objectGroup.children.map((x) => x.position),
//     {
//       x: 0,
//       y: 0,
//     },
//     0
//   );
//   tl.from(
//     objectGroup.children.map((x) => x.scale),
//     {
//       x: 0.001,
//       y: 0.001,
//     },
//     0
//   );
//   tl.from(
//     objectGroup.children.map((x) => x.rotation),
//     {
//       z: 0,
//     },
//     0
//   );
//   return tl;
// }

function halton(index, base) {
  var result = 0;
  var f = 1 / base;
  var i = index;
  while (i > 0) {
    result = result + f * (i % base);
    i = Math.floor(i / base);
    f = f / base;
  }
  return result;
}

function createExplosionAnimation(
  objectGroup,
  {
    ease = "expo.out",
    duration = 2,
    minRotation = -2 * Math.PI,
    maxRotation = 2 * Math.PI,
    minRadius = 1,
    maxRadius = 4,
    minScale = 1,
    maxScale = 1,
    stagger = 0.03,
  } = {}
) {
  const tl = gsap.timeline({
    defaults: {
      duration,
      ease: ease,
    },
  });

  let delay = 0;
  objectGroup.children.forEach((child, i) => {
    const r = minRadius + (maxRadius - minRadius) * rng();
    const theta = rng() * 2 * Math.PI;
    const x = r * 2.0 * Math.cos(theta);
    const y = r * Math.sin(theta);
    child.position.z += 0.01 * i; // z-fighting

    tl.fromTo(child.position, { x: 0, y: 0 }, { x, y }, delay);

    const rotation = minRotation + rng() * (maxRotation - minRotation);
    tl.fromTo(child.rotation, { z: 0 }, { z: rotation }, delay);

    const targetScale = child.scale.setScalar(
      minScale + (maxScale - minScale) * rng()
    );
    tl.fromTo(
      child.scale,
      { x: 0.001, y: 0.001, z: 0.001 },
      { x: targetScale.x, y: targetScale.y, z: targetScale.z },
      delay
    );

    delay += stagger;
  });

  return tl;
}

function createGroupFlyInAnimation(
  objectGroup,
  { ease = "expo.out", duration = 1, stagger = 0 } = {}
) {
  const tl = gsap.timeline({
    defaults: {
      duration,
      ease: ease,
    },
  });

  let delay = 0;
  objectGroup.children.forEach((child) => {
    const targetScale = child.scale.clone().multiplyScalar(0.01);
    tl.from(
      child.scale,
      { x: targetScale.x, y: targetScale.y, z: targetScale.z },
      delay
    );

    delay += stagger;
  });

  return tl;
}

function createImplodeAnimation(objectGroup, { duration = 0.5 } = {}) {
  const tl = gsap.timeline({
    defaults: {
      duration,
      ease: "expo.out",
    },
  });
  tl.to(
    objectGroup.children.map((x) => x.position),
    {
      x: 0,
      y: 0,
    },
    0
  );
  tl.to(
    objectGroup.children.map((x) => x.scale),
    {
      x: 0.001,
      y: 0.001,
    },
    0
  );
  return tl;
}

function getCompoundBoundingBox(object3D) {
  var box = undefined;
  object3D.traverse(function (obj3D) {
    var geometry = obj3D.geometry;
    if (geometry === undefined) return;
    geometry.computeBoundingBox();
    if (box === undefined) {
      box = geometry.boundingBox;
    } else {
      box.union(geometry.boundingBox);
    }
  });
  return box;
}

function _getNodeName(node) {
  if (!node) return "";
  if (node.id) {
    return _getNodeName(node.parentNode) + "/" + node.id;
  } else {
    return _getNodeName(node.parentNode);
  }
}

async function loadSVG(url, { color = undefined, isCCW = true } = {}) {
  return new Promise((resolve, reject) => {
    // instantiate a loader
    let loader = new SVGLoader();

    // load a SVG resource
    loader.load(
      // resource URL
      url,
      // called when the resource is loaded
      function (data) {
        let paths = data.paths;

        let parentGroup = new THREE.Group();

        const unnamedGroup = new THREE.Group();
        parentGroup.add(unnamedGroup);

        for (let i = 0; i < paths.length; i++) {
          let path = paths[i];

          let material = new THREE.MeshBasicMaterial({
            color: color !== undefined ? color : (path as any).color,
            side: THREE.DoubleSide,
            // depthWrite: false,
          });

          const shapes = path.toShapes(isCCW);

          let geometry = new THREE.ShapeBufferGeometry(shapes);

          let mesh = new THREE.Mesh(geometry, material);

          const name = _getNodeName((path as any).userData.node);

          if (name) {
            let group = parentGroup.children.filter((x) => x.name === name)[0];
            if (!group) {
              group = new THREE.Group();
              group.name = name;
              parentGroup.add(group);
            }

            group.add(mesh);
          } else {
            unnamedGroup.add(mesh);
          }
        }

        // Get bounding box of the whole object
        const box = getCompoundBoundingBox(parentGroup);

        const boxCenter = new THREE.Vector3();
        box.getCenter(boxCenter);

        const boxSize = new THREE.Vector3();
        box.getSize(boxSize);

        const scale = 1.0 / Math.max(boxSize.x, boxSize.y, boxSize.z);

        parentGroup.children.forEach((group) => {
          group.children.forEach((object3d) => {
            const subMesh = object3d as THREE.Mesh;

            // Scale and translate geometry
            subMesh.geometry.translate(
              -boxCenter.x,
              -boxCenter.y,
              -boxCenter.z
            );
            subMesh.geometry.scale(scale, -scale, scale);

            // Set center of the subMesh to (0, 0)
            const center = new THREE.Vector3();
            subMesh.geometry.boundingBox.getCenter(center);

            subMesh.geometry.translate(-center.x, -center.y, -center.z);
            subMesh.position.add(center);
          });
        });

        resolve(parentGroup);
      },
      // called when loading is in progresses
      function (xhr) {
        // console.log((xhr.loaded / xhr.total * 100) + '% loaded');
      },
      // called when loading has errors
      function (error) {
        console.log("An error happened");
        reject(error);
      }
    );
  });
}

function addGlitch({ duration = 0.2 } = {}) {
  if (glitchPass !== undefined) {
    const tl = gsap.timeline();
    tl.set(glitchPass, { factor: 1 });
    tl.set(glitchPass, { factor: 0 }, `<${duration}`);
    return tl;
  } else {
    return gsap.timeline();
  }
}

// TODO: this is just creating a timeline object but not adding to the main
// timeline.
function addTextFlyInAnimation(textMesh, { duration = 0.5 } = {}) {
  const tl = gsap.timeline();

  // Animation
  textMesh.children.forEach((letter, i) => {
    const vals = {
      position: -textMesh.size * 2,
      rotation: -Math.PI / 2,
    };
    tl.to(
      vals,
      duration,
      {
        position: 0,
        rotation: 0,

        ease: "back.out(1)", // https://greensock.com/docs/v3/Eases
        onUpdate: () => {
          letter.position.y = vals.position;
          letter.position.z = vals.position * 2;
          letter.rotation.x = vals.rotation;
        },
      },
      `-=${duration - 0.03}`
    );

    tl.add(createFadeInAnimation(letter, { duration }), "<");
  });

  return tl;
}

function groupFlyIn(object3D, { duration = 0.5, t = "+=0" } = {}) {
  const tl = gsap.timeline();

  // Animation
  const stagger = duration / object3D.children.length / 2;
  for (const obj of object3D.children) {
    const vals = {
      position: -object3D.size * 2,
      rotation: -Math.PI / 2,
    };
    tl.to(
      vals,
      duration,
      {
        position: 0,
        rotation: 0,

        ease: "back.out(1)", // https://greensock.com/docs/v3/Eases
        onUpdate: () => {
          obj.position.y = vals.position;
          obj.position.z = vals.position * 2;
          obj.rotation.x = vals.rotation;
        },
      },
      `-=${duration - stagger}`
    );

    tl.add(createFadeInAnimation(obj, { duration }), "<");
  }

  mainTimeline.add(tl, t);
  // return tl;
}

const metaData = {
  cutPoints: [],
};

function setBloom(enabled) {
  if (enabled) {
    bloomEnabled = true;
    AA_METHOD = "fxaa";
  }
}

function newScene(initFunction = undefined) {
  (async () => {
    // {
    //   let cut = getQueryString().cut;
    //   if (cut) {
    //     subClipDurations = cut.split("|").map((x) => parseFloat(x));
    //   }
    // }

    setupScene({ width: WIDTH, height: HEIGHT });

    if (initFunction !== undefined) {
      await initFunction();
    }

    for (const cmd of commandList) {
      if (typeof cmd === "function") {
        cmd();
      } else if (cmd.type === "add") {
        const mesh = await addAsync(cmd.obj, cmd.params);
        sceneObjects[cmd.id] = mesh;
      } else if (cmd.type === "addGroup") {
        const group = addThreeJsGroup();
        sceneObjects[cmd.id] = group;
      } else {
        throw `invalid command type: ${cmd.type}`;
      }
    }

    _addMarkerToTimeline();

    {
      // Create timeline GUI

      options.timeline = 0;
      gui
        .add(options, "timeline", 0, globalTimeline.totalDuration())
        .onChange((val) => {
          globalTimeline.seek(val, false);
        });

      Object.keys(globalTimeline.labels).forEach((key) => {
        console.log(`${key} ${globalTimeline.labels[key]}`);
      });

      const folder = gui.addFolder("Timeline Labels");
      var labels = new Object();
      Object.keys(globalTimeline.labels).forEach((key) => {
        const label = key;
        const time = globalTimeline.labels[key];

        console.log(this);
        labels[label] = () => {
          globalTimeline.seek(time, false);
        };
        folder.add(labels, label);
      });
    }

    if (0) {
      // Grid helper
      const size = 20;
      const divisions = 20;
      const colorCenterLine = "#008800";
      const colorGrid = "#888888";

      gridHelper = new THREE.GridHelper(
        size,
        divisions,
        new THREE.Color(colorCenterLine),
        new THREE.Color(colorGrid)
      );
      gridHelper.rotation.x = Math.PI / 2;
      scene.add(gridHelper);
    }

    // Start animation
    requestAnimationFrame(animate);
  })();
}

{
  captureStatus = document.createElement("div");
  captureStatus.id = "captureStatus";
  captureStatus.innerText = "stopped";
  document.body.appendChild(captureStatus);
}

function createArrow({
  from = new THREE.Vector3(0, 0, 0),
  to = new THREE.Vector3(0, 1, 0),
  lineWidth = 0.1,
  arrowEnd = true,
  arrowStart = false,
  color = 0xffff00,
} = {}) {
  const direction = new THREE.Vector3();
  direction.subVectors(to, from);
  const halfLength = direction.length() * 0.5;
  direction.subVectors(to, from).normalize();

  const center = new THREE.Vector3();
  center.addVectors(from, to).multiplyScalar(0.5);

  const quaternion = new THREE.Quaternion(); // create one and reuse it
  quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);

  const group = new THREE.Group();

  const material = new THREE.MeshBasicMaterial({ color });

  if (0) {
    const geometry = new THREE.CylinderBufferGeometry(
      lineWidth,
      lineWidth,
      halfLength * 2,
      32
    );
    const cylinder = new THREE.Mesh(geometry, material);
    group.add(cylinder);
  }

  {
    let length = halfLength * 2;
    let offset = halfLength;

    if (arrowEnd) {
      length -= lineWidth * 4;
      offset -= lineWidth * 4 * 0.5;
    }

    var geometry = new THREE.PlaneGeometry(lineWidth, length);

    var plane = new THREE.Mesh(geometry, material);
    plane.translateY(offset);

    group.add(plane);
  }

  for (let i = 0; i < 2; i++) {
    if (i === 0 && !arrowStart) continue;
    if (i === 1 && !arrowEnd) continue;

    const geometry = new THREE.Geometry();
    geometry.vertices = [
      new THREE.Vector3(-lineWidth * 2, -lineWidth * 4, 0),
      new THREE.Vector3(lineWidth * 2, -lineWidth * 4, 0),
      new THREE.Vector3(0, 0, 0),
    ];
    geometry.faces.push(new THREE.Face3(0, 1, 2));

    const mesh = new THREE.Mesh(geometry, material);
    group.add(mesh);

    if (i === 0) {
      mesh.rotation.z = Math.PI;
    } else {
      mesh.translateY(halfLength * 2);
    }
  }

  group.setRotationFromQuaternion(quaternion);
  group.position.set(from.x, from.y, from.z);
  scene.add(group);
  return group;
}

async function loadTexture(url): Promise<THREE.Texture> {
  return new Promise((resolve, reject) => {
    new THREE.TextureLoader().load(url, (texture) => {
      resolve(texture);
    });
  });
}

function addAnimation(
  object3d,
  animation,
  { t = undefined, aniHold = 1, duration = undefined } = {}
) {
  const tl = gsap.timeline();

  if (animation !== undefined) {
    const animationList = animation.split("|");

    // Enter animation
    animationList.forEach((animation) => {
      if (animation === "show") {
        tl.fromTo(
          object3d,
          {
            visible: false,
          },
          {
            visible: true,
            ease: "steps(1)",
            duration: 0.01,
          },
          "<"
        );
      } else if (animation === "fadeIn") {
        tl.add(createFadeInAnimation(object3d, { duration }), "<");
      } else if (animation === "jumpIn") {
        tl.add(addJumpIn(object3d), "<");
      } else if (animation === "spinIn") {
        tl.from(object3d.rotation, { y: Math.PI * 4, ease: "expo.out" }, "<");
      } else if (animation === "rotateIn") {
        tl.from(object3d.rotation, { z: -Math.PI * 2 }, "<");
      } else if (animation === "rotateIn2") {
        tl.from(
          object3d.rotation,
          { z: Math.PI * 4, ease: "power.in", duration: 0.5 },
          "<"
        );
        tl.from(
          object3d.scale,
          {
            x: Number.EPSILON,
            y: Number.EPSILON,
            z: Number.EPSILON,
            ease: "power.in",
            duration: 0.5,
          },
          "<"
        );
      } else if (animation === "grow") {
        tl.from(
          object3d.scale,
          { x: 0.01, y: 0.01, z: 0.01, ease: "expo.out" },
          "<"
        );
      } else if (animation === "grow2") {
        tl.from(
          object3d.scale,
          { x: 0.01, y: 0.01, z: 0.01, ease: "elastic.out(1, 0.75)" },
          "<"
        );
      } else if (animation === "grow3") {
        tl.from(
          object3d.scale,
          {
            x: 0.01,
            y: 0.01,
            z: 0.01,
            ease: "elastic.out(1, 0.2)",
            duration: 1,
          },
          "<"
        );
      } else if (animation === "growX") {
        tl.from(object3d.scale, { x: 0.01, ease: "expo.out" }, "<");
      } else if (animation === "growY") {
        tl.from(object3d.scale, { y: 0.01, ease: "expo.out" }, "<");
      } else if (animation === "growX2") {
        tl.from(
          object3d.scale,
          { x: 0.01, ease: "elastic.out(1, 0.75)", duration: 1 },
          "<"
        );
      } else if (animation === "growY2") {
        tl.from(object3d.scale, { y: 0.01, ease: "elastic.out(1, 0.75)" }, "<");
      } else if (animation === "growX3") {
        tl.from(object3d.scale, { x: 0.01, ease: "back.out" }, "<");
      } else if (animation === "growY3") {
        tl.from(object3d.scale, { y: 0.01, ease: "back.out" }, "<");
      } else if (animation === "type" || animation === "type2") {
        const speed = animation === "type2" ? 0.005 : 0.01;
        object3d.children.forEach((x, i) => {
          tl.fromTo(
            x,
            {
              visible: false,
            },
            {
              visible: true,
              ease: "steps(1)",
              duration: speed,
              delay: i * speed,
            },
            "<"
          );
        });
        // tl.set({}, {}, ">+0.5");
      } else if (animation === "flyIn") {
        const duration = 0.5;
        const ease = "elastic.out";
        tl.from(object3d.position, {
          x: object3d.position.x + 20,
          duration,
          ease,
        });

        tl.add(
          createFadeInAnimation(object3d, {
            duration,
          }),
          "<"
        );
      }
    });

    // Animation
    animationList.forEach((animation) => {
      if (animation === "rotation") {
        tl.to(
          object3d.rotation,
          {
            y: object3d.rotation.y + Math.PI * 2 * 4,
            duration: 2,
            ease: "none",
          },
          ">"
        );
      }
    });

    // Exit animation
    const tlExitAnimation = gsap.timeline();
    animationList.forEach((animation) => {
      if (animation === "fadeOut") {
        tlExitAnimation.add(
          createFadeInAnimation(object3d, { ease: "power1.in" }).reverse(),
          "<"
        );
      }
    });

    if (tlExitAnimation.duration() > 0) {
      // Hold the animation for a while before running exit animation
      if (aniHold > 0 && tl.duration() > 0) {
        tl.set({}, {}, "+=" + aniHold.toString());
      }
      tl.add(tlExitAnimation);
    }
  }

  if (tl.duration() > 0) {
    mainTimeline.add(tl, t);
  }
}

function createTriangleVertices({ radius = 0.5 } = {}) {
  const verts = [];
  for (let i = 0; i < 3; i++) {
    verts.push(
      new THREE.Vector3(
        radius * Math.sin(i * Math.PI * 0.33333 * 2),
        radius * Math.cos(i * Math.PI * 0.33333 * 2),
        0
      )
    );
  }
  return verts;
}

var commandList = [];

function uuidv4() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
    var r = (Math.random() * 16) | 0,
      v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function add(obj, params: AddObjectParameters) {
  const guid = uuidv4();
  commandList.push({ type: "add", obj, params, id: guid });
  return guid;
}

function toVector3(v) {
  return new THREE.Vector3(
    v.x === undefined ? 0 : v.x,
    v.y === undefined ? 0 : v.y,
    v.z === undefined ? 0 : v.z
  );
}

interface Transform {
  x?: number;
  y?: number;
  z?: number;
  rx?: number;
  ry?: number;
  rz?: number;
  sx?: number;
  sy?: number;
  sz?: number;
  position?: number[];
  scale: number;
}

interface AddObjectParameters extends Transform {
  animation?: any;
  color?: any;
  opacity?: any;
  vertices?: any;
  wireframe?: any;
  outline?: any;
  outlineWidth?: any;
  width?: any;
  height?: any;
  t?: number | string;
  parent?: any;
  lighting?: any;
  ccw?: any;
  font?: any;
  fontSize?: any;
  start?: any;
  end?: any;
  lineWidth?: any;
  gridSize?: any;
  centralAngle?: any;
  letterSpacing?: any;
  duration?: any;
  type?: any;
}

async function addAsync(
  obj,
  {
    x,
    y,
    z,
    rx,
    ry,
    rz,
    sx,
    sy,
    sz,
    position,
    scale,
    animation,
    color,
    opacity = 1.0,
    vertices = [],
    wireframe = false,
    outline = false,
    outlineWidth = 0.1,
    width = 1,
    height = 1,
    t,
    parent,
    lighting = false,
    ccw = false,
    font,
    fontSize = 1.0,
    start = { x: 0, y: 0 },
    end = { x: 0, y: 1 },
    lineWidth = 0.1,
    gridSize = 10,
    centralAngle = Math.PI * 2,
    letterSpacing = 0.05,
    duration,
  }: AddObjectParameters
) {
  let material;
  const transparent = opacity < 1.0 ? true : false;

  if (lighting) {
    addDefaultLights();
    material = new THREE.MeshPhongMaterial({
      color: color !== undefined ? color : 0xffffff,
      // emissive: 0x072534,
      // side: THREE.DoubleSide,
      flatShading: true,
    });
  } else {
    material = new THREE.MeshBasicMaterial({
      side: THREE.DoubleSide,
      color: color !== undefined ? color : 0xffffff,
      transparent,
      opacity,
      wireframe,
    });
  }

  let mesh;
  if (obj.endsWith(".svg")) {
    mesh = await loadSVG(obj, { isCCW: ccw, color });
    scene.add(mesh);
  } else if (obj.endsWith(".png") || obj.endsWith(".jpg")) {
    const texture = await loadTexture(obj);
    texture.anisotropy = 16; // renderer.getMaxAnisotropy(); TODO: do not hardcode
    const material = new THREE.MeshBasicMaterial({
      map: texture,
      side: THREE.DoubleSide,
      transparent: true,
      opacity,
      wireframe,
    });

    const geometry = new THREE.PlaneBufferGeometry(1, 1);
    mesh = new THREE.Mesh(geometry, material);

    const ratio = texture.image.width / texture.image.height;
    if (ratio > 1) {
      mesh.scale.y /= ratio;
    } else {
      mesh.scale.x *= ratio;
    }
  } else if (obj === "triangle") {
    if (vertices.length === 0) {
      vertices = createTriangleVertices();
    }

    if (outline) {
      mesh = createLine3D({
        points: vertices.concat(vertices[0]),
        lineWidth: outlineWidth,
        color: color !== undefined ? color : 0xffffff,
      });
    } else {
      const geometry = new THREE.Geometry();
      geometry.vertices.push(vertices[0], vertices[1], vertices[2]);
      geometry.faces.push(new THREE.Face3(0, 1, 2));

      mesh = new THREE.Mesh(geometry, material);
    }
  } else if (obj === "triangleOutline") {
    if (vertices.length === 0) {
      vertices = createTriangleVertices();
    }

    mesh = createLine3D({
      points: vertices.concat(vertices[0]),
      lineWidth,
      color,
    });
    // triangleStroke.scale.set(0.2, 0.2, 0.2);
    // scene.add(triangleStroke);
  } else if (obj === "rect" || obj === "rectangle") {
    const geometry = new THREE.PlaneGeometry(width, height);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj === "circle") {
    const geometry = new THREE.CircleGeometry(0.5, 32, 0, centralAngle);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj === "ring") {
    const geometry = new THREE.RingGeometry(0.85, 1, 64);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj === "sphere") {
    const geometry = new THREE.SphereGeometry(0.5, 32, 32);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj === "pyramid") {
    const geometry = new THREE.ConeGeometry(0.5, 1.0, 4, 32);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj === "arrow") {
    mesh = createArrow({
      from: toVector3(start),
      to: toVector3(end),
      color: color !== undefined ? color : 0xffffff,
      lineWidth,
    });
  } else if (obj === "line") {
    mesh = createArrow({
      from: toVector3(start),
      to: toVector3(end),
      arrowStart: false,
      arrowEnd: false,
      color: color !== undefined ? color : 0xffffff,
      lineWidth,
    });
  } else if (obj === "grid") {
    const gridHelper = new THREE.GridHelper(1, gridSize, 0x00ff00, 0xc0c0c0);
    gridHelper.rotation.x = Math.PI / 2;
    gridHelper.position.z = 0.01;

    mesh = gridHelper;
  } else if (typeof obj === "string") {
    mesh = new TextMesh({
      text: obj,
      font,
      color: color !== undefined ? color : 0xffffff,
      size: fontSize,
      letterSpacing,
    });
  }

  if (scale !== undefined) {
    mesh.scale.multiplyScalar(scale);
  } else {
    if (sx !== undefined) {
      mesh.scale.x *= sx;
    }
    if (sy !== undefined) {
      mesh.scale.y *= sy;
    }
    if (sz !== undefined) {
      mesh.scale.z *= sz;
    }
  }

  // Position
  if (position !== undefined) {
    mesh.position.set(position[0], position[1], position[2]);
  } else {
    if (x !== undefined) mesh.position.x = x;
    if (y !== undefined) mesh.position.y = y;
    if (z !== undefined) mesh.position.z = z;
  }

  // Rotation
  if (rx !== undefined) mesh.rotation.x = rx;
  if (ry !== undefined) mesh.rotation.y = ry;
  if (rz !== undefined) mesh.rotation.z = rz;

  addAnimation(mesh, animation, { t, duration });

  if (parent !== undefined) {
    sceneObjects[parent].add(mesh);
  } else {
    scene.add(mesh);
  }

  return mesh;
}

function addGroup({
  x = 0,
  y = 0,
  z = 0,
  position = undefined,
  scale = 1,
  parent = undefined,
} = {}) {
  const id = uuidv4();

  commandList.push(() => {
    const group = new THREE.Group();

    if (position !== undefined) {
      group.position.set(position[0], position[1], position[2]);
    } else {
      if (x !== undefined) group.position.x = x;
      if (y !== undefined) group.position.y = y;
      if (z !== undefined) group.position.z = z;
    }

    group.scale.setScalar(scale);

    if (parent) {
      sceneObjects[parent].add(group);
    } else {
      scene.add(group);
    }

    sceneObjects[id] = group;
  });

  return id;
}

function addThreeJsGroup({ x = 0, y = 0, z = 0, sx = 1, sy = 1, sz = 1 } = {}) {
  const group = new THREE.Group();
  group.position.x = x;
  group.position.y = y;
  group.position.z = z;

  scene.add(group);
  return group;
}

function getBoundingBox(object3D) {
  return new THREE.Box3().setFromObject(object3D);
}

function getQueryString(url = undefined) {
  // get query string from url (optional) or window
  var queryString = url ? url.split("?")[1] : window.location.search.slice(1);

  // we'll store the parameters here
  var obj = {};

  // if query string exists
  if (queryString) {
    // stuff after # is not part of query string, so get rid of it
    queryString = queryString.split("#")[0];

    // split our query string into its component parts
    var arr = queryString.split("&");

    for (var i = 0; i < arr.length; i++) {
      // separate the keys and the values
      var a = arr[i].split("=");

      // set parameter name and value (use 'true' if empty)
      var paramName = a[0];
      var paramValue = typeof a[1] === "undefined" ? true : a[1];

      // (optional) keep case consistent
      paramName = paramName.toLowerCase();
      if (typeof paramValue === "string") {
        // paramValue = paramValue.toLowerCase();
        paramValue = decodeURIComponent(paramValue);
      }

      // if the paramName ends with square brackets, e.g. colors[] or colors[2]
      if (paramName.match(/\[(\d+)?\]$/)) {
        // create key if it doesn't exist
        var key = paramName.replace(/\[(\d+)?\]/, "");
        if (!obj[key]) obj[key] = [];

        // if it's an indexed array e.g. colors[2]
        if (paramName.match(/\[\d+\]$/)) {
          // get the index value and add the entry at the appropriate position
          var index = /\[(\d+)\]/.exec(paramName)[1];
          obj[key][index] = paramValue;
        } else {
          // otherwise add the value to the end of the array
          obj[key].push(paramValue);
        }
      } else {
        // we're dealing with a string
        if (!obj[paramName]) {
          // if it doesn't exist, create property
          obj[paramName] = paramValue;
        } else if (obj[paramName] && typeof obj[paramName] === "string") {
          // if property does exist and it's a string, convert it to an array
          obj[paramName] = [obj[paramName]];
          obj[paramName].push(paramValue);
        } else {
          // otherwise add the property
          obj[paramName].push(paramValue);
        }
      }
    }
  }

  return obj;
}

var seedrandom = require("seedrandom");
var rng = seedrandom("hello.");

function setSeed(val) {
  rng = seedrandom(val);
}

function random() {
  return rng();
}

function getGridLayoutPositions({
  rows = 1,
  cols = 1,
  width = 25,
  height = 14,
} = {}) {
  const gapX = width / cols;
  const gapY = height / rows;

  const startX = (width / cols - width) * 0.5;
  const startY = (height / rows - height) * 0.5;

  const results = [];
  for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
      results.push(
        new THREE.Vector3(j * gapX + startX, -(i * gapY + startY), 0)
      );
    }
  }
  return results;
}

function add3DSpinning(object3d) {
  animationCallbacks.push((delta, elapsed) => {
    object3d.rotation.y += delta;
    object3d.rotation.x = Math.sin(elapsed) * 0.5;
  });
}

function addPulse(object3d) {
  const scaleCopy = object3d.scale.clone();
  animationCallbacks.push((delta, elapsed) => {
    const s = 1 + Math.sin(elapsed * 50) * 0.01;

    object3d.scale.x = scaleCopy.x * s;
    object3d.scale.y = scaleCopy.y * s;
    object3d.scale.z = scaleCopy.z * s;
  });
}

function add2DSpinning(object3d, { speed = 1.0 } = {}) {
  animationCallbacks.push((delta, elapsed) => {
    object3d.rotation.z -= delta * speed;
  });
}

function _addMarkerToTimeline() {
  if (subClipDurations.length > 0) {
    currentCutPoint += subClipDurations.shift();
    mainTimeline.set({}, {}, `${currentCutPoint}`);
  }
}

function addCut() {
  _addMarkerToTimeline();

  mainTimeline.call(() => {
    if (capturer !== undefined) {
      console.log("CutPoint: " + globalTimeline.time().toString());
      metaData["cutPoints"].push(globalTimeline.time());
    }
  });
}

function move(object3d, { t = undefined, ...options } = {}) {
  mainTimeline.add(createMotionAnimation(object3d, options), t);
}

function addCustomAnimation(
  callback,
  {
    startVal = 0,
    endVal = 1,
    aniPos = "+=0",
    ease = "expo.out",
    duration = 0.5,
  } = {}
) {
  const data = { val: startVal };
  mainTimeline.to(
    data,
    {
      val: endVal,
      onUpdate: () => {
        callback(data.val);
      },
      ease,
      duration,
    },
    aniPos
  );
}

function setBackgroundAlpha(alpha) {
  backgroundAlpha = alpha;
}

function enableMotionBlur(motionBlurSamples = 16) {
  MOTION_BLUR_SAMPLES = motionBlurSamples;
  AA_METHOD = "fxaa";
}

function setGlitch(enabled) {
  ENABLE_GLITCH_PASS = true;
  AA_METHOD = "fxaa";
}

function setViewportSize(w, h) {
  WIDTH = w;
  HEIGHT = h;
}

function setBackgroundColor(color) {
  commandList.push(() => {
    scene.background = new THREE.Color(color);
  });
}

function explode(
  group,
  {
    t = undefined,
    ease = "expo.out",
    duration = 2,
    minRotation = -2 * Math.PI,
    maxRotation = 2 * Math.PI,
    minRadius = 1,
    maxRadius = 4,
    minScale = 1,
    maxScale = 1,
    stagger = 0.03,
  } = {}
) {
  commandList.push(() => {
    const tl = createExplosionAnimation(sceneObjects[group], {
      ease,
      duration,
      minRotation,
      maxRotation,
      minRadius,
      maxRadius,
      minScale,
      maxScale,
      stagger,
    });
    mainTimeline.add(tl, t);
  });
}

function implode(group, { t = undefined, duration = 0.5 } = {}) {
  commandList.push(() => {
    const tl = createImplodeAnimation(sceneObjects[group], { duration });
    mainTimeline.add(tl, t);
  });
}

function flying(group, { t = undefined, duration = 5 } = {}) {
  const WIDTH = 30;
  const HEIGHT = 15;

  commandList.push(() => {
    const tl = gsap.timeline();

    sceneObjects[group].children.forEach((x) => {
      tl.fromTo(
        x.position,
        {
          x: rng() * WIDTH - WIDTH / 2,
          y: rng() * HEIGHT - HEIGHT / 2,
        },
        {
          x: rng() * WIDTH - WIDTH / 2,
          y: rng() * HEIGHT - HEIGHT / 2,
          duration,
          ease: "none",
        },
        0
      );
    });

    mainTimeline.add(tl, t);
  });
}

export default {
  run: newScene,
  palette,
  randomInt,
  addGroup,
  getQueryString,
  random,
  moveCamera,
  enableMotionBlur,
  generateRandomString,
  add,
  rainbowPalette: [
    "#9C4F96",
    "#FF6355",
    "#FBA949",
    "#FAE442",
    "#8BD448",
    "#2AA8F2",
  ],
  pause: (duration) => {
    commandList.push(() => {
      mainTimeline.set({}, {}, "+=" + duration.toString());
    });
  },
  fadeIn: (obj, params) => {
    commandList.push(() => {
      addAnimation(sceneObjects[obj], "fadeIn", params);
    });
  },
  fadeOut: (obj, params) => {
    commandList.push(() => {
      addAnimation(sceneObjects[obj], "fadeOut", params);
    });
  },
  flyIn: (obj, params) => {
    commandList.push(() => {
      addAnimation(sceneObjects[obj], "flyIn", params);
    });
  },
  rotateIn: (obj, params) => {
    commandList.push(() => {
      addAnimation(sceneObjects[obj], "rotateIn", params);
    });
  },
  rotateIn2: (obj, params) => {
    commandList.push(() => {
      addAnimation(sceneObjects[obj], "rotateIn2", params);
    });
  },
  setDefaultAnimation: (name) => {
    defaultAnimation = name;
  },
  move: (obj, params) => {
    commandList.push(() => {
      move(sceneObjects[obj], params);
    });
  },
  addEmptyAnimation: (t) => {
    commandList.push(() => {
      mainTimeline.set({}, {}, t);
    });
  },
  fadeOutAll: ({ t = undefined } = {}) => {
    commandList.push(() => {
      const tl = gsap.timeline();
      for (const [_, obj] of Object.entries(sceneObjects)) {
        tl.add(createFadeOutAnimation(obj), "<");
      }
      mainTimeline.add(tl, t);
    });
  },
  shake2D,
  setBackgroundColor,
  explode,
  implode,
  grow: (obj, params) => {
    commandList.push(() => {
      addAnimation(sceneObjects[obj], "grow", params);
    });
  },
  grow2: (obj, params) => {
    commandList.push(() => {
      addAnimation(sceneObjects[obj], "grow2", params);
    });
  },
  grow3: (obj, params) => {
    commandList.push(() => {
      addAnimation(sceneObjects[obj], "grow3", params);
    });
  },
  enableBloom: (enabled = true) => {
    bloomEnabled = enabled;
  },
  flying,
  reveal,
};
