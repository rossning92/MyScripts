import * as dat from "dat.gui";
import * as THREE from "three";
import { MeshLine, MeshLineMaterial } from "three.meshline";
import TextMesh from "./objects/TextMesh";
import Stars from "./objects/Stars";

import gsap, { TimelineLite } from "gsap";
// import { RoughEase } from "gsap/EasePack";
// gsap.registerPlugin(RoughEase);

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

gsap.ticker.remove(gsap.updateRoot);

let ENABLE_GLITCH_PASS = false;
let RENDER_TARGET_SCALE = 1;
let WIDTH = 1920 * RENDER_TARGET_SCALE;
let HEIGHT = 1080 * RENDER_TARGET_SCALE;
let AA_METHOD = "msaa";
let ENABLE_MOTION_BLUR_PASS = false;
let MOTION_BLUR_SAMPLES = 1;
let BLOOM_ENABLED = false;

var outFileName = null;
var captureStatus;
var globalTimeline = gsap.timeline({ onComplete: stopCapture });

const mainTimeline = gsap.timeline();
globalTimeline.add(mainTimeline, "0");

let stats;
let capturer = null;
let renderer;
let composer;
let scene;
let camera;
let lightGroup;
let cameraControls;
let palette = [
  // '#1abc9c',
  // '#2ecc71',
  // '#3498db',
  // '#9b59b6',
  // '#34495e',
  // '#16a085',
  // '#27ae60',
  // '#2980b9',
  // '#8e44ad',
  // '#2c3e50',
  // '#f1c40f',
  // '#e67e22',
  // '#e74c3c',
  // '#f39c12',
  // '#d35400',
  // '#c0392b'

  "#1a535c",
  "#4ecdc4",
  "#ff6b6b",
  "#ffe66d",
  "#f7fff7",
];

var glitchPass;
var gridHelper;
let backgroundAlpha = 1.0;

var animationCallbacks = [];

let options = {
  /* Recording options */
  format: "png",
  framerate: "25FPS",
  start: function () {
    startCapture();
  },
  stop: function () {
    stopCapture();
  },
};

let subClipDurations = [];
let currentCutPoint = 0;

var gui = new dat.gui.GUI();
gui.add(options, "format", ["gif", "webm-mediarecorder", "webm", "png"]);
gui.add(options, "framerate", ["10FPS", "25FPS", "30FPS", "60FPS", "120FPS"]);
gui.add(options, "start");
gui.add(options, "stop");

const threeJsSceneObjects = {};

function startCapture({ resetTiming = true, name = "animation" } = {}) {
  outFileName = name;

  if (gridHelper != null) {
    gridHelper.visible = false;
  }

  if (resetTiming) {
    // Reset gsap
    gsap.ticker.remove(gsap.updateRoot);

    lastTs = null;
  }

  capturer = new CCapture({
    verbose: true,
    display: false,
    framerate: parseInt(options.framerate),
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

window.startCapture = startCapture;

function stopCapture() {
  if (capturer !== null) {
    capturer.stop();
    capturer.save();
    capturer = null;
    captureStatus.innerText = "stopped";

    var FileSaver = require("file-saver");
    var blob = new Blob([JSON.stringify(metaData)], {
      type: "text/plain;charset=utf-8",
    });
    FileSaver.saveAs(
      blob,
      outFileName != null ? outFileName + ".json" : "animation-meta-file.json"
    );
  }
}

function render() {
  composer.render();
}

function resize(width, height) {
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

function setupOrthoCamera({ width = WIDTH, height = HEIGHT } = {}) {
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
  let options = {
    // antialias: true,
    alpha: true,
  };
  if (AA_METHOD == "msaa") {
    options.antialias = true;
  }

  renderer = new THREE.WebGLRenderer(options);
  renderer.localClippingEnabled = true;

  renderer.setSize(width, height);
  document.body.appendChild(renderer.domElement);

  {
    stats = new Stats();
    // stats.showPanel(1); // 0: fps, 1: ms, 2: mb, 3+: custom
    document.body.appendChild(stats.dom);
  }

  renderer.setClearColor(0x000000, backgroundAlpha);
  scene.background = 0;

  if (camera == null) {
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 5000);
    camera.position.set(0, 0, 10);
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

  if (BLOOM_ENABLED) {
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

  if (AA_METHOD == "fxaa") {
    composer.addPass(createFxaaPass(renderer));
  } else if (AA_METHOD == "ssaa") {
    let ssaaRenderPass = new SSAARenderPass(scene, camera);
    ssaaRenderPass.unbiased = true;
    ssaaRenderPass.samples = 8;
    composer.addPass(ssaaRenderPass);
  } else if (AA_METHOD == "smaa") {
    let pixelRatio = renderer.getPixelRatio();
    let smaaPass = new SMAAPass(WIDTH * pixelRatio, HEIGHT * pixelRatio);
    composer.addPass(smaaPass);
  } else if (AA_METHOD == "taa") {
    let taaRenderPass = new TAARenderPass(scene, camera);
    taaRenderPass.unbiased = false;
    taaRenderPass.sampleLevel = 4;
    composer.addPass(taaRenderPass);
  }

  if (ENABLE_GLITCH_PASS) {
    glitchPass = new GlitchPass();
    composer.addPass(glitchPass);
  }
}

var lastTs = null;
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
    if (lastTs == null) {
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

  render();

  stats.update();

  if (capturer) capturer.capture(renderer.domElement);
}

function moveCameraTo({ x = 0, y = 0, z = 10 }) {
  return gsap.to(camera.position, {
    x,
    y,
    z,
    onUpdate: () => {
      camera.lookAt(new Vector3(0, 0, 0));
    },
    duration: 0.5,
    ease: "expo.out",
  });
}

scene = new THREE.Scene();

// createText({ text: '3 minute' });
// createText({ text: '\nprogramming' });
// createLine();
// createAnimatedLines();

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

// requestAnimationFrame(animate);

function randomInt(min, max) {
  return Math.floor(random() * (max - min + 1)) + min;
}

function createLine() {
  var geometry = new THREE.Geometry();
  for (var j = 0; j < Math.PI; j += (2 * Math.PI) / 100) {
    var v = new THREE.Vector3(j / 5, Math.sin(j) / 5, 0);
    geometry.vertices.push(v);
  }
  var line = new MeshLine();
  line.setGeometry(geometry, () => {
    return 0.02;
  });

  var material = new MeshLineMaterial();
  var mesh = new THREE.Mesh(line.geometry, material); // this syntax could definitely be improved!
  scene.add(mesh);
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

import LineGenerator from "./objects/LineGenerator";
import getRandomFloat from "./utils/getRandomFloat";
import getRandomItem from "./utils/getRandomItem";
import { Vector3, Material } from "three";
function createAnimatedLines() {
  /**
   * * *******************
   * * LIGNES
   * * *******************
   */
  const COLORS = [
    "#FDFFFC",
    "#FDFFFC",
    "#FDFFFC",
    "#FDFFFC",
    "#EA526F",
    "#71b9f2",
  ].map((col) => new THREE.Color(col));
  const STATIC_PROPS = {
    nbrOfPoints: 4,
    speed: 0.03,
    turbulence: new THREE.Vector3(1, 0.8, 1),
    orientation: new THREE.Vector3(1, 0, 0),
    transformLineMethod: (p) => {
      const a = (0.5 - Math.abs(0.5 - p)) * 3;
      return a;
    },
  };

  const POSITION_X = -3.2;
  const LENGTH_MIN = 5;
  const LENGTH_MAX = 7;
  class CustomLineGenerator extends LineGenerator {
    start() {
      const currentFreq = this.frequency;
      this.frequency = 1;
      setTimeout(() => {
        this.frequency = currentFreq;
      }, 500);
      super.start();
    }

    addLine() {
      const line = super.addLine({
        width: getRandomFloat(0.1, 0.3),
        length: getRandomFloat(LENGTH_MIN, LENGTH_MAX),
        visibleLength: getRandomFloat(0.05, 0.8),
        position: new THREE.Vector3(POSITION_X, 0.3, getRandomFloat(-1, 1)),
        color: getRandomItem(COLORS),
      });
      line.rotation.x = getRandomFloat(0, Math.PI * 2);

      if (Math.random() > 0.1) {
        const line = super.addLine({
          width: getRandomFloat(0.05, 0.1),
          length: getRandomFloat(5, 10),
          visibleLength: getRandomFloat(0.05, 0.5),
          speed: 0.05,
          position: new THREE.Vector3(
            getRandomFloat(-9, 5),
            getRandomFloat(-5, 5),
            getRandomFloat(-10, 6)
          ),
          color: getRandomItem(COLORS),
        });
        line.rotation.x = getRandomFloat(0, Math.PI * 2);
      }
    }
  }
  var lineGenerator = new CustomLineGenerator(
    {
      frequency: 0.1,
    },
    STATIC_PROPS
  );
  scene.add(lineGenerator);

  /**
   * * *******************
   * * START
   * * *******************
   */
  // Show
  // const tlShow = new TimelineLite({ delay: 0.2 });
  // tlShow.to('.overlay', 0.6, { autoAlpha: 0 });
  // // tlShow.fromTo(engine.lookAt, 3, { y: -4 }, { y: 0, ease: Power3.easeOut }, 0);
  // tlShow.add(lineGenerator.start, '-=2.5');
  // // tlShow.add(() => {
  // //   scene.add(text);
  // //   text.show();
  // // }, '-=1.6');

  lineGenerator.start();
}

import { FXAAShader } from "three/examples/jsm/shaders/FXAAShader.js";
import { SMAAPass } from "three/examples/jsm/postprocessing/SMAAPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass";

function createFxaaPass(renderer) {
  let fxaaPass = new ShaderPass(FXAAShader);

  let pixelRatio = renderer.getPixelRatio();
  fxaaPass.material.uniforms["resolution"].value.x = 1 / (WIDTH * pixelRatio);
  fxaaPass.material.uniforms["resolution"].value.y = 1 / (HEIGHT * pixelRatio);

  return fxaaPass;
}

function createTextParticles(text = "Hello Codepen ♥") {
  // Inspared by https://codepen.io/rachsmith/pen/LpZbmZ

  // Lab Raycaster 2.0
  // https://codepen.io/vcomics/pen/OZPayy

  if (1) {
    // Create lights
    let shadowLight = new THREE.DirectionalLight(0xffffff, 2);
    shadowLight.position.set(20, 0, 10);
    shadowLight.castShadow = true;
    shadowLight.shadowDarkness = 0.01;
    scene.add(shadowLight);

    let light = new THREE.DirectionalLight(0xffffff, 0.5);
    light.position.set(-20, 0, 20);
    scene.add(light);

    let backLight = new THREE.DirectionalLight(0xffffff, 0.8);
    backLight.position.set(0, 0, -20);
    scene.add(backLight);
  }

  if (0) {
    var light = new THREE.SpotLight(0xffffff, 3);
    light.position.set(5, 5, 2);
    light.castShadow = true;
    light.shadow.mapSize.width = 10000;
    light.shadow.mapSize.height = light.shadow.mapSize.width;
    light.penumbra = 0.5;

    var lightBack = new THREE.PointLight(0x0fffff, 1);
    lightBack.position.set(0, -3, -1);

    scene.add(light);
    scene.add(lightBack);

    var rectSize = 2;
    var intensity = 100;
    var rectLight = new THREE.RectAreaLight(
      0x0fffff,
      intensity,
      rectSize,
      rectSize
    );
    rectLight.position.set(0, 0, 1);
    rectLight.lookAt(0, 0, 0);
    scene.add(rectLight);
  }

  let canvas = document.createElement("canvas");
  let ww = (canvas.width = 160);
  let wh = (canvas.height = 40);

  let ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.font = "bold " + ww / 10 + "px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(text, ww / 2, wh / 2);

  let data = ctx.getImageData(0, 0, ww, wh).data;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.globalCompositeOperation = "screen";

  let n = 0;
  for (let i = 0; i < ww; i += 1) {
    for (let j = 0; j < wh; j += 1) {
      if (data[(i + j * ww) * 4 + 3] > 150) {
        {
          // let geometry = new THREE.BoxGeometry();
          // for (let i = 0; i < geometry.vertices.length; i++) {
          //   geometry.vertices[i].x += (-1 + Math.random() * 0.5) * 0.2;
          //   geometry.vertices[i].y += (-1 + Math.random() * 0.5) * 0.2;
          //   geometry.vertices[i].z += (-1 + Math.random() * 0.5) * 0.2;
          // }

          // let material = new THREE.MeshLambertMaterial({
          //   color: pallete[i % pallete.length],
          //   shading: THREE.FlatShading
          // });

          // let material = new THREE.MeshPhysicalMaterial({color:0xFFFFFF, side:THREE.DoubleSide});
          // let geometry = new THREE.CircleGeometry(1, 5);

          var material = new THREE.MeshStandardMaterial({
            shading: THREE.FlatShading,
            color: palette[n % palette.length],
            transparent: false,
            opacity: 1,
            wireframe: false,
          });
          var geometry = new THREE.IcosahedronGeometry(1);

          let mesh = new THREE.Mesh(geometry, material);
          const S = 5;
          mesh.position.set(i / S, -j / S, 0);
          mesh.scale.set(0.5 / S, 0.5 / S, 0.5 / S);
          scene.add(mesh);

          let clock = new THREE.Clock();
          const vx = Math.random();
          const vy = Math.random();
          mesh.onBeforeRender = () => {
            let delta = clock.getDelta();
            mesh.rotation.x += vx * delta;
            mesh.rotation.y += vy * delta;
          };

          if (1) {
            mesh.scale.set(0, 0, 0);
            const params = {
              scale: 0,
            };
            gsap.to(params, {
              scale: (0.5 + (Math.random() - 0.5) * 0.5) / S,
              duration: 5,
              ease: "elastic.out(1, 0.1)",
              onUpdate: () => {
                mesh.scale.set(params.scale, params.scale, params.scale);
              },
              delay: 2 + Math.random(),
            });
          }

          n++;
        }
      }
    }
  }
}

// createTextParticles();

function createRingAnimation() {
  const SEGMENT = 100;
  const RADIUS = 1;

  let geometry = new THREE.Geometry();
  for (let j = 0; j < 2 * Math.PI; j += (2 * Math.PI) / SEGMENT) {
    let v = new THREE.Vector3(Math.sin(j) * RADIUS, Math.cos(j) * RADIUS, 0);
    geometry.vertices.push(v);
  }

  let line = new MeshLine();

  line.setGeometry(geometry);

  const material = new MeshLineMaterial({
    lineWidth: 0.3,

    dashArray: 1,
    dashOffset: 0,
    dashRatio: 0.8, // The ratio between that is visible or not for each dash

    opacity: 1,
    transparent: true,
    color: "#ffffff",
    // TODO: don't hard code value here.
    resolution: new THREE.Vector2(WIDTH, HEIGHT),
    sizeAttenuation: !false, // Line width constant regardless distance
  });

  let mesh = new THREE.Mesh(line.geometry, material); // this syntax could definitely be improved!
  scene.add(mesh);

  mesh.position.z = -1;

  mesh.scale.set(4, 4, 4);

  // Animation
  if (1) {
    let vals = {
      start: 0,
      end: 0,
    };
    let tl = gsap.timeline({
      defaults: { duration: 1, ease: "power3.out" },
      onUpdate: () => {
        material.uniforms.dashOffset.value = vals.start;
        material.uniforms.dashRatio.value = 1 - (vals.end - vals.start);
      },
    });
    tl.to(vals, {
      end: 1,
      duration: 2,
    }).to(
      vals,
      {
        start: 1,
        duration: 2,
      },
      "<0.5"
    );
  }
}

// createRingAnimation();

function createCanvas({ width = 64, height = 64 } = {}) {
  let canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

function canvasDrawTriangle() {
  let canvas = createCanvas();
  var ctx = canvas.getContext("2d");

  // Filled triangle
  ctx.beginPath();
  ctx.moveTo(10, 25);
  ctx.lineTo(50, 60);
  ctx.lineTo(45, 5);
  ctx.fill();

  let data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  return data;
}

function createRect({ color = 0xffff00 } = {}) {
  var geometry = new THREE.PlaneGeometry(1, 1);
  var material = new THREE.MeshBasicMaterial({
    color: color,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 1.0,
  });
  var plane = new THREE.Mesh(geometry, material);
  // scene.add(plane);
  return plane;
}

import { SVGLoader } from "three/examples/jsm/loaders/SVGLoader";
function createLine3D({ color = 0xffffff, points = [], lineWidth = 0.1 } = {}) {
  if (points.length == 0) {
    points.push(new THREE.Vector3(-1.73, -1, 0));
    points.push(new THREE.Vector3(1.73, -1, 0));
    points.push(new THREE.Vector3(0, 2, 0));
    points.push(points[0]);
  }

  let lineColor = new THREE.Color(0xffffff);
  let style = SVGLoader.getStrokeStyle(lineWidth, lineColor.getStyle());
  // style.strokeLineJoin = "round";
  let geometry = SVGLoader.pointsToStroke(points, style);

  let material = new THREE.MeshBasicMaterial({
    color,
    side: THREE.DoubleSide,
    transparent: true,
  });

  let mesh = new THREE.Mesh(geometry, material);
  return mesh;
}

function createWipeAnimation(
  object3d,
  { direction3d = new THREE.Vector3(-1, 0, 0) } = {}
) {
  let localPlane = new THREE.Plane(direction3d, 0);
  const boundingBox = getBoundingBox(object3d);

  object3d.material.clippingPlanes = [localPlane];

  const tween = gsap.fromTo(
    localPlane,
    { constant: boundingBox.min.x * 1.1 },
    {
      constant: boundingBox.max.x * 1.1,
      duration: 0.6,
      ease: "expo.out",
    }
  );

  // object3d.material.clippingPlanes[0] = new THREE.Plane(new THREE.Vector3(-5, 0, 0), 0.8);
  return tween;
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
  if (type == "sphere") {
    geometry = new THREE.SphereGeometry(0.5, segments, segments);
  } else if (type == "circle") {
    geometry = new THREE.CircleGeometry(0.5, segments);
  } else if (type == "cone") {
    geometry = new THREE.ConeGeometry(0.5, 1.0, segments, segments);
  }

  let material;
  if (materialType == "phong") {
    material = new THREE.MeshPhongMaterial({
      color,
    });
  } else if (materialType == "physical") {
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

//// GLOW MESH

const dilateGeometry = function (geometry, length) {
  // gather vertexNormals from geometry.faces
  var vertexNormals = new Array(geometry.vertices.length);
  geometry.faces.forEach(function (face) {
    if (face instanceof THREE.Face4) {
      vertexNormals[face.a] = face.vertexNormals[0];
      vertexNormals[face.b] = face.vertexNormals[1];
      vertexNormals[face.c] = face.vertexNormals[2];
      vertexNormals[face.d] = face.vertexNormals[3];
    } else if (face instanceof THREE.Face3) {
      vertexNormals[face.a] = face.vertexNormals[0];
      vertexNormals[face.b] = face.vertexNormals[1];
      vertexNormals[face.c] = face.vertexNormals[2];
    } else console.assert(false);
  });
  // modify the vertices according to vertextNormal
  geometry.vertices.forEach(function (vertex, idx) {
    var vertexNormal = vertexNormals[idx];
    vertex.x += vertexNormal.x * length;
    vertex.y += vertexNormal.y * length;
    vertex.z += vertexNormal.z * length;
  });
};

const createAtmosphereMaterial = function () {
  var vertexShader = [
    "varying vec3	vVertexWorldPosition;",
    "varying vec3	vVertexNormal;",

    "varying vec4	vFragColor;",

    "void main(){",
    "	vVertexNormal	= normalize(normalMatrix * normal);",

    "	vVertexWorldPosition	= (modelMatrix * vec4(position, 1.0)).xyz;",

    "	// set gl_Position",
    "	gl_Position	= projectionMatrix * modelViewMatrix * vec4(position, 1.0);",
    "}",
  ].join("\n");
  var fragmentShader = [
    "uniform vec3	glowColor;",
    "uniform float	coeficient;",
    "uniform float	power;",

    "varying vec3	vVertexNormal;",
    "varying vec3	vVertexWorldPosition;",

    "varying vec4	vFragColor;",

    "void main(){",
    "	vec3 worldCameraToVertex= vVertexWorldPosition - cameraPosition;",
    "	vec3 viewCameraToVertex	= (viewMatrix * vec4(worldCameraToVertex, 0.0)).xyz;",
    "	viewCameraToVertex	= normalize(viewCameraToVertex);",
    "	float intensity		= pow(coeficient + dot(vVertexNormal, viewCameraToVertex), power);",
    "	gl_FragColor		= vec4(glowColor, intensity);",
    "}",
  ].join("\n");

  // create custom material from the shader code above
  //   that is within specially labeled script tags
  var material = new THREE.ShaderMaterial({
    uniforms: {
      coeficient: {
        type: "f",
        value: 1.0,
      },
      power: {
        type: "f",
        value: 2,
      },
      glowColor: {
        type: "c",
        value: new THREE.Color("pink"),
      },
    },
    vertexShader: vertexShader,
    fragmentShader: fragmentShader,
    //blending	: THREE.AdditiveBlending,
    transparent: true,
    depthWrite: false,
  });
  return material;
};

const GeometricGlowMesh = function (mesh, { color = "cyan" } = {}) {
  var object3d = new THREE.Object3D();

  var geometry = mesh.geometry.clone();
  dilateGeometry(geometry, 0.01);
  var material = createAtmosphereMaterial();
  material.uniforms.glowColor.value = new THREE.Color(color);
  material.uniforms.coeficient.value = 1.1;
  material.uniforms.power.value = 1.4;
  var insideMesh = new THREE.Mesh(geometry, material);
  object3d.add(insideMesh);

  var geometry = mesh.geometry.clone();
  dilateGeometry(geometry, 0.2);
  var material = createAtmosphereMaterial();
  material.uniforms.glowColor.value = new THREE.Color(color);
  material.uniforms.coeficient.value = 0.1;
  material.uniforms.power.value = 1.2;
  material.side = THREE.BackSide;
  var outsideMesh = new THREE.Mesh(geometry, material);
  object3d.add(outsideMesh);

  // expose a few variable
  this.object3d = object3d;
  this.insideMesh = insideMesh;
  this.outsideMesh = outsideMesh;
};

function addGlow(object3d) {
  object3d.add(new GeometricGlowMesh(circle).object3d);
}

///

function createRectMeshLine({ lineWidth = 0.1, color = 0x00ff00 } = {}) {
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

function createRectLine({ color = 0x00ff00 } = {}) {
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
  color = 0x00ff00,
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

function getAllMaterials(object3d) {
  const materials = new Set();
  const getMaterialsRecursive = (object3d) => {
    if (object3d.material != null) {
      materials.add(object3d.material);
    }
    object3d.children.forEach((child) => {
      getMaterialsRecursive(child);
    });
  };
  getMaterialsRecursive(object3d);
  return materials;
}

// TODO: Deprecated
function addFadeIn(
  object3d,
  { duration = 0.5, ease = "power1.out", opacity = 1.0 } = {}
) {
  const tl = gsap.timeline({ defaults: { duration, ease } });

  const materials = getAllMaterials(object3d);

  // console.log(materials);
  materials.forEach((material) => {
    material.transparent = true;

    // tl.fromTo(
    //   material,
    //   {
    //     transparent: false,
    //   },
    //   {
    //     transparent: true,
    //     duration: 0,
    //   },
    //   "<"
    // );

    tl.fromTo(
      material,
      {
        opacity: 0,
      },
      {
        opacity,
        duration,
      },
      "<"
    );
  });

  return tl;
}

function fadeIn(
  object3d,
  {
    duration = 0.5,
    ease = "power1.out",
    opacity = 1.0,
    t = "+=0",
    timeline = null,
  } = {}
) {
  const tl = gsap.timeline({ defaults: { duration, ease } });

  const materials = getAllMaterials(object3d);

  materials.forEach((material) => {
    material.transparent = true;
    tl.fromTo(
      material,
      {
        opacity: 0,
      },
      {
        opacity,
        duration,
      },
      "<"
    );
  });

  if (timeline != null) {
    timeline.add(tl, t);
  } else {
    mainTimeline.add(tl, t);
  }
}

function setOpacity(object3d, opacity = 1.0) {
  if (object3d.material != null) {
    object3d.material.transparent = true;
    object3d.material.opacity = opacity;
  }

  object3d.children.forEach((x) => {
    setOpacity(x, opacity);
  });
}

function addFadeOut(object3d) {
  return addFadeIn(object3d).reverse();
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
    addFadeIn(object3d, {
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

function createMoveToAnimation(
  object3d,
  {
    position = null,
    x = null,
    y = null,
    z = null,
    scale = null,
    dx = null,
    dy = null,
    rotX = null,
    rotY = null,
    rotZ = null,
    sx = null,
    sy = null,
    sz = null,
    duration = 0.5,
    ease = "power2.out",
    multiplyScale = null,
  } = {}
) {
  if (dx != null) x = object3d.position.x + dx;
  if (dy != null) y = object3d.position.y + dy;

  let tl = gsap.timeline({
    defaults: {
      duration,
      ease,
    },
  });

  if (position != null) {
    tl.to(
      object3d.position,
      { x: position.x, y: position.y, z: position.z },
      "<"
    );
  } else {
    if (x != null) tl.to(object3d.position, { x }, "<");
    if (y != null) tl.to(object3d.position, { y }, "<");
    if (z != null) tl.to(object3d.position, { z }, "<");
  }

  if (rotX != null) tl.to(object3d.rotation, { x: rotX }, "<");
  if (rotY != null) tl.to(object3d.rotation, { y: rotY }, "<");
  if (rotZ != null) tl.to(object3d.rotation, { z: rotZ }, "<");

  if (scale != null) {
    tl.to(
      object3d.scale,
      {
        x: scale,
        y: scale,
        z: scale,
      },
      "<"
    );
  } else if (multiplyScale != null) {
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
    if (sx != null) tl.to(object3d.scale, { x: sx }, "<");
    if (sy != null) tl.to(object3d.scale, { y: sy }, "<");
    if (sz != null) tl.to(object3d.scale, { z: sz }, "<");
  }

  return tl;
}

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

  if (beginScale != null) {
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

  tl.add(addFadeIn(object3d), "<");

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
  if (lightGroup == null) {
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

function addShake2D(
  object3d,
  { shakes = 20, duration = 0.01, strength = 0.5 } = {}
) {
  function R(max, min) {
    return Math.random() * (max - min) + min;
  }

  var tl = new gsap.timeline({ defaults: { ease: "none" } });
  tl.set(object3d, { x: "+=0" }); // this creates a full _gsTransform on object3d
  var transforms = object3d._gsTransform;

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

  return tl;
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
    duration = 1.5,
    rotationMin = 0,
    rotationMax = Math.PI * 8,
    radiusMin = 1,
    radiusMax = 8,
    stagger = 0,
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
    const r = radiusMin + (radiusMax - radiusMin) * rng();
    const theta = rng() * 2 * Math.PI;
    const x = r * 2.0 * Math.cos(theta);
    const y = r * Math.sin(theta);
    child.position.z += 0.01 * i; // z-fighting

    tl.fromTo(child.position, { x: 0, y: 0 }, { x, y }, delay);

    const rotation = rotationMin + rng() * (rotationMax - rotationMin);
    tl.fromTo(child.rotation, { z: 0 }, { z: rotation }, delay);

    const targetScale = child.scale.clone().multiplyScalar(rng() * 0.5 + 0.5);
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

function addExplosionAnimation(group, options, aniPos = "<") {
  yo.tl.add(mainTimeline.createExplosionAnimation(group, options), aniPos);
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

function addCollapseAnimation(objectGroup, { duration = 0.5 } = {}) {
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
  var box = null;
  object3D.traverse(function (obj3D) {
    var geometry = obj3D.geometry;
    if (geometry === undefined) return;
    geometry.computeBoundingBox();
    if (box === null) {
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

async function loadSVG(url, { color = null, isCCW = true } = {}) {
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
            color: color !== null ? color : path.color,
            side: THREE.DoubleSide,
            depthWrite: false,
          });

          const shapes = path.toShapes(isCCW);

          let geometry = new THREE.ShapeBufferGeometry(shapes);

          let mesh = new THREE.Mesh(geometry, material);

          const name = _getNodeName(path.userData.node);

          if (name) {
            let group = parentGroup.children.filter((x) => x.name == name)[0];
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
          group.children.forEach((subMesh) => {
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
  if (glitchPass != null) {
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

    tl.add(addFadeIn(letter, { duration }), "<");
  });

  return tl;
}

function addFlyInAnimation(obj, params) {
  commandList.push({ type: "animation", obj, params });
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

    fadeIn(obj, { duration, t: "<", timeline: tl });
  }

  mainTimeline.add(tl, t);
  // return tl;
}

const metaData = {
  cutPoints: [],
};

function setBloom(enabled) {
  if (enabled) {
    BLOOM_ENABLED = true;
    AA_METHOD = "fxaa";
  }
}

function newScene(initFunction) {
  (async () => {
    {
      let cut = getQueryString().cut;
      if (cut) {
        subClipDurations = cut.split("|").map((x) => parseFloat(x));
      }
    }

    setupScene({ width: WIDTH, height: HEIGHT });

    await initFunction();

    for (const cmd of commandList) {
      if (cmd.type == "add") {
        const mesh = await addAsync(cmd.obj, cmd.params);

        threeJsSceneObjects[cmd.id] = mesh;
      } else if (cmd.type == "animation") {
        groupFlyIn(
          threeJsSceneObjects[cmd.obj], // object GUID
          cmd.params
        );
      } else if (cmd.type == "addGroup") {
        const group = addThreeJsGroup();
        threeJsSceneObjects[cmd.id] = group;
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

    {
      // Grid helper
      const size = 20;
      const divisions = 20;
      const colorCenterLine = "#008800";
      const colorGrid = "#888888";

      gridHelper = new THREE.GridHelper(
        size,
        divisions,
        colorCenterLine,
        colorGrid
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

  if (0) {
    var geometry = new THREE.ConeBufferGeometry(
      lineWidth * 2,
      lineWidth * 2,
      32
    );
  }

  for (let i = 0; i < 2; i++) {
    if (i == 0 && !arrowStart) continue;
    if (i == 1 && !arrowEnd) continue;

    const geometry = new THREE.Geometry();
    geometry.vertices = [
      new THREE.Vector3(-lineWidth * 2, -lineWidth * 4, 0),
      new THREE.Vector3(lineWidth * 2, -lineWidth * 4, 0),
      new THREE.Vector3(0, 0, 0),
    ];
    geometry.faces.push(new THREE.Face3(0, 1, 2));

    const mesh = new THREE.Mesh(geometry, material);
    group.add(mesh);

    if (i == 0) {
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

function addObject() {}

function addText(
  text,
  {
    x = 0,
    y = 0,
    z = 0,
    aniEnter = "fade",
    aniExit = null,
    color = 0xffffff,
    font = "en",
    fontSize = 1.0,
  } = {}
) {
  const mesh = new TextMesh({
    text,
    font,
    size: 0.5,
    color,
    size: fontSize,
  });
  mesh.position.set(x, y, z);

  addAnimation(mesh, { aniEnter, aniExit });

  scene.add(mesh);

  return mesh;
}

async function loadTexture(url) {
  return new Promise((resolve, reject) => {
    new THREE.TextureLoader().load(url, (texture) => {
      resolve(texture);
    });
  });
}

function addAnimation(
  object3d,
  animation = "fadeIn",
  { aniPos = "+=0", aniHold = 1 } = {}
) {
  const tl = gsap.timeline();

  if (animation != null) {
    const animationList = animation.split("|");

    // Enter animation
    animationList.forEach((animation) => {
      if (animation == "fadeIn") {
        tl.add(addFadeIn(object3d), "<");
      } else if (animation == "jumpIn") {
        tl.add(addJumpIn(object3d), "<");
      } else if (animation == "spinIn") {
        tl.from(object3d.rotation, { y: Math.PI * 4, ease: "expo.out" }, "<");
      } else if (animation == "rotateIn") {
        tl.from(object3d.rotation, { z: -Math.PI * 2 }, "<");
      } else if (animation == "grow") {
        tl.from(
          object3d.scale,
          { x: 0.01, y: 0.01, z: 0.01, ease: "expo.out" },
          "<"
        );
      } else if (animation == "grow2") {
        tl.from(
          object3d.scale,
          { x: 0.01, y: 0.01, z: 0.01, ease: "elastic.out(1, 0.75)" },
          "<"
        );
      } else if (animation == "growX") {
        tl.from(object3d.scale, { x: 0.01, ease: "expo.out" }, "<");
      } else if (animation == "growY") {
        tl.from(object3d.scale, { y: 0.01, ease: "expo.out" }, "<");
      } else if (animation == "growX2") {
        tl.from(
          object3d.scale,
          { x: 0.01, ease: "elastic.out(1, 0.75)", duration: 1 },
          "<"
        );
      } else if (animation == "growY2") {
        tl.from(object3d.scale, { y: 0.01, ease: "elastic.out(1, 0.75)" }, "<");
      } else if (animation == "growX3") {
        tl.from(object3d.scale, { x: 0.01, ease: "back.out" }, "<");
      } else if (animation == "growY3") {
        tl.from(object3d.scale, { y: 0.01, ease: "back.out" }, "<");
      } else if (animation == "type" || animation == "fastType") {
        const speed = animation == "fastType" ? 0.005 : 0.01;
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
      } else if (animation == "wipe") {
        tl.add(createWipeAnimation(object3d, "<"));
      } else if (animation == "flyIn") {
        const duration = 0.5;
        const ease = "elastic.out";
        tl.from(object3d.position, {
          x: object3d.position.x + 20,
          duration,
          ease,
        });

        tl.add(
          addFadeIn(object3d, {
            duration,
          }),
          "<"
        );
      }
    });

    // Animation
    animationList.forEach((animation) => {
      if (animation == "rotation") {
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
      if (animation == "fadeOut") {
        tlExitAnimation.add(
          addFadeIn(object3d, { ease: "power1.in" }).reverse(),
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
    mainTimeline.add(tl, aniPos);
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
      v = c == "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function add(obj, params) {
  const guid = uuidv4();
  commandList.push({ type: "add", obj, params, id: guid });
  return guid;
}

async function addAsync(
  obj,
  {
    x = null,
    y = null,
    z = null,
    rotX = null,
    rotY = null,
    rotZ = null,
    position = null,
    animation = "fadeIn",
    color = null,
    opacity = 1.0,
    sx = null,
    sy = null,
    sz = null,
    scale = null,
    vertices = [],
    wireframe = false,
    outline = false,
    outlineWidth = 0.1,
    width = 1,
    height = 1,
    aniPos = "+=0",
    t = null,
    parent = null,
    lighting = false,
    ccw = true,
    font = null,
    fontSize = 1.0,
    arrowFrom = new THREE.Vector3(0, 0, 0),
    arrowTo = new THREE.Vector3(0, 1, 0),
    lineWidth = 0.1,
    gridSize = 10,
    centralAngle = Math.PI * 2,
    letterSpacing = 0.05,
  } = {}
) {
  let material;

  if (lighting) {
    addDefaultLights();
    material = new THREE.MeshPhongMaterial({
      color: color != null ? color : 0xffffff,
      // emissive: 0x072534,
      // side: THREE.DoubleSide,
      flatShading: true,
    });
  } else {
    material = new THREE.MeshBasicMaterial({
      side: THREE.DoubleSide,
      color: color != null ? color : 0xffffff,
      transparent: opacity < 1.0 ? true : false,
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
    });

    const geometry = new THREE.PlaneGeometry(1, 1, 1, 1);
    mesh = new THREE.Mesh(geometry, material);

    const ratio = texture.image.width / texture.image.height;
    if (ratio > 1) {
      mesh.scale.y /= ratio;
    } else {
      mesh.scale.x *= ratio;
    }
  } else if (obj == "triangle") {
    if (vertices.length == 0) {
      vertices = createTriangleVertices();
    }

    if (outline) {
      mesh = createLine3D({
        points: vertices.concat(vertices[0]),
        lineWidth: outlineWidth,
        color: color != null ? color : 0xffffff,
      });
    } else {
      const geometry = new THREE.Geometry();
      geometry.vertices.push(vertices[0], vertices[1], vertices[2]);
      geometry.faces.push(new THREE.Face3(0, 1, 2));

      mesh = new THREE.Mesh(geometry, material);
    }
  } else if (obj == "triangleOutline") {
    if (vertices.length == 0) {
      vertices = createTriangleVertices();
    }

    mesh = createLine3D({
      points: vertices.concat(vertices[0]),
      lineWidth,
      color,
    });
    // triangleStroke.scale.set(0.2, 0.2, 0.2);
    // scene.add(triangleStroke);
  } else if (obj == "rect" || obj == "rectangle") {
    const geometry = new THREE.PlaneGeometry(width, height);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj == "circle") {
    const geometry = new THREE.CircleGeometry(0.5, 32, 0, centralAngle);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj == "ring") {
    const geometry = new THREE.RingGeometry(0.85, 1, 64);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj == "sphere") {
    const geometry = new THREE.SphereGeometry(0.5, 32, 32);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj == "pyramid") {
    const geometry = new THREE.ConeGeometry(0.5, 1.0, 4, 32);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj == "arrow") {
    mesh = createArrow({
      from: arrowFrom,
      to: arrowTo,
      color: color != null ? color : 0xffffff,
      lineWidth,
    });
  } else if (obj == "grid") {
    const gridHelper = new THREE.GridHelper(1, gridSize, 0x00ff00, 0xc0c0c0);
    gridHelper.rotation.x = Math.PI / 2;
    gridHelper.position.z = 0.01;

    mesh = gridHelper;
  } else if (typeof obj == "string") {
    mesh = new TextMesh({
      text: obj,
      font,
      size: 0.5,
      color: color != null ? color : 0xffffff,
      size: fontSize,
      letterSpacing,
    });
  }

  if (scale != null) {
    mesh.scale.multiplyScalar(scale);
  } else {
    if (sx != null) {
      mesh.scale.x *= sx;
    }
    if (sy != null) {
      mesh.scale.y *= sy;
    }
    if (sz != null) {
      mesh.scale.z *= sz;
    }
  }

  // Position
  if (position != null) {
    mesh.position.set(position.x, position.y, position.z);
  } else {
    if (x != null) mesh.position.x = x;
    if (y != null) mesh.position.y = y;
    if (z != null) mesh.position.z = z;
  }

  // Rotation
  if (rotX != null) mesh.rotation.x = rotX;
  if (rotY != null) mesh.rotation.y = rotY;
  if (rotZ != null) mesh.rotation.z = rotZ;

  addAnimation(mesh, animation, { aniPos: t !== null ? t : aniPos });

  if (parent != null) {
    if (typeof parent === "string") {
      threeJsSceneObjects[parent].add(mesh);
    } else {
      parent.add(mesh);
    }
  } else {
    scene.add(mesh);
  }

  return mesh;
}

function addGroup(params) {
  const id = uuidv4();
  commandList.push({ type: "addGroup", id, params });
  return id;
}

function addThreeJsGroup(
  name,
  { x = 0, y = 0, z = 0, sx = 1, sy = 1, sz = 1 } = {}
) {
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

function getQueryString(url) {
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

function pause(t) {
  mainTimeline.set({}, {}, "+=" + t.toString());
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
    if (capturer !== null) {
      console.log("CutPoint: " + globalTimeline.time().toString());
      metaData["cutPoints"].push(globalTimeline.time());
    }
  });
}

function moveTo(object3d, { t = "+=0", ...options } = {}) {
  if (object3d instanceof Array) {
    for (let i = 0; i < object3d.length; i++) {
      mainTimeline.add(
        createMoveToAnimation(object3d[i], options),
        i == 0 ? t : "<"
      );
    }
  } else {
    mainTimeline.add(createMoveToAnimation(object3d, options), t);
  }
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

function setMotionBlur(v) {
  if (v === true) {
    MOTION_BLUR_SAMPLES = 16;
  } else {
    MOTION_BLUR_SAMPLES = v;
  }
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

export default {
  addCollapseAnimation,
  addExplosionAnimation,
  addFadeIn,
  fadeIn,
  addFadeOut,
  addGlitch,
  addJumpIn,
  addLights: addDefaultLights,
  addShake2D,
  addTextFlyInAnimation,
  addWipeAnimation: createWipeAnimation,
  camera,
  canvasDrawTriangle,
  createObject,
  createRect,
  createTriangle,
  flyIn,
  globalTimeline,
  jumpTo,
  loadSVG,
  moveCameraTo,
  createMoveToAnimation,
  newScene,
  palette,
  randomInt,
  scene,
  setOpacity,
  TextMesh,
  tl: globalTimeline,
  createArrow,
  addText,
  addAsync,
  addGroup,
  getBoundingBox,
  addFlash,
  getQueryString,
  addAnimation,
  createTriangleVertices,
  pause,
  createExplosionAnimation,
  createGroupFlyInAnimation,
  groupFlyIn,
  addFlyInAnimation,
  setSeed,
  getGridLayoutPositions,
  random,
  mainTimeline,
  addCut,
  moveTo,
  add3DSpinning,
  addPulse,
  setupOrthoCamera,
  addCustomAnimation,
  add2DSpinning,
  setBackgroundAlpha,
  setMotionBlur,
  setBloom,
  generateRandomString,
  setGlitch,
  setViewportSize,
  add,
};

export { THREE, gsap };
