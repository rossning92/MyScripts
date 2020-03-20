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

const ENABLE_GLITCH_PASS = false;
const RENDER_TARGET_SCALE = 1;
const WIDTH = 1920 * RENDER_TARGET_SCALE;
const HEIGHT = 1080 * RENDER_TARGET_SCALE;
const AA_METHOD = "msaa";
const ENABLE_MOTION_BLUR_PASS = false;
const MOTION_BLUR_SAMPLES = 1;

var captureStatus;
var globalTimeline = gsap.timeline({ onComplete: stopCapture });
let stats;
let capturer = null;
let renderer;
let composer;
let scene;
let camera;
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
  "#f7fff7"
];

var glitchPass;
var gridHelper;

let options = {
  /* Recording options */
  format: "png",
  framerate: "25FPS",
  start: function() {
    startCapture();
  },
  stop: function() {
    stopCapture();
  }
};

var gui = new dat.gui.GUI();
gui.add(options, "format", ["gif", "webm-mediarecorder", "webm", "png"]);
gui.add(options, "framerate", ["10FPS", "25FPS", "30FPS", "60FPS", "120FPS"]);
gui.add(options, "start");
gui.add(options, "stop");

function initCapture() {
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
    autoSaveTime: 0
  });
}

function startCapture() {
  if (gridHelper != null) {
    gridHelper.visible = false;
  }

  start = null;
  gsap.ticker.remove(gsap.updateRoot);
  gsap.updateRoot(0);

  initCapture();
  capturer.start();
  globalTimeline.seek(0);
  captureStatus.innerText = "capturing";
}

window.startCapture = startCapture;

function stopCapture() {
  if (capturer !== null) {
    capturer.stop();
    capturer.save();
    capturer = null;
    captureStatus.innerText = "stopped";
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

function setupScene(width, height) {
  let options = {
    // antialias: true,
  };
  if (AA_METHOD == "msaa") {
    options.antialias = true;
  }

  renderer = new THREE.WebGLRenderer(options);
  renderer.setSize(width, height);
  document.body.appendChild(renderer.domElement);

  {
    stats = new Stats();
    // stats.showPanel(1); // 0: fps, 1: ms, 2: mb, 3+: custom
    document.body.appendChild(stats.dom);
  }

  scene = new THREE.Scene();
  scene.background = 0;

  if (1) {
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 5000);
    camera.position.set(0, 0, 10);
    camera.lookAt(new Vector3(0, 0, 0));
  } else {
    const aspect = width / height;
    const frustumSize = 1;
    camera = new THREE.OrthographicCamera(
      (frustumSize * aspect) / -2,
      (frustumSize * aspect) / 2,
      frustumSize / 2,
      frustumSize / -2,
      0,
      1000
    );
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
      renderCameraBlur: true
    };
    let motionPass = new MotionBlurPass(scene, camera, options);
    composer.addPass(motionPass);

    motionPass.debug.display = 0;
    // motionPass.renderToScreen = true;
  }

  if (0) {
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

  if (ENABLE_GLITCH_PASS) {
    glitchPass = new GlitchPass();
    composer.addPass(glitchPass);
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
}

var start;
function animate(time) {
  if (!start) {
    start = time;
  }
  let timestamp = time - start;

  gsap.updateRoot(timestamp / 1000);

  /* Loop this function */
  requestAnimationFrame(animate);

  cameraControls.update();

  render();

  stats.update();

  /* Record Video */
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
    ease: "expo.out"
  });
}

setupScene(WIDTH, HEIGHT);
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
  var random = Math.floor(Math.random() * (max - min + 1)) + min;
  return random;
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
import { Vector3 } from "three";
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
    "#71b9f2"
  ].map(col => new THREE.Color(col));
  const STATIC_PROPS = {
    nbrOfPoints: 4,
    speed: 0.03,
    turbulence: new THREE.Vector3(1, 0.8, 1),
    orientation: new THREE.Vector3(1, 0, 0),
    transformLineMethod: p => {
      const a = (0.5 - Math.abs(0.5 - p)) * 3;
      return a;
    }
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
        color: getRandomItem(COLORS)
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
          color: getRandomItem(COLORS)
        });
        line.rotation.x = getRandomFloat(0, Math.PI * 2);
      }
    }
  }
  var lineGenerator = new CustomLineGenerator(
    {
      frequency: 0.1
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
            wireframe: false
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
              scale: 0
            };
            gsap.to(params, {
              scale: (0.5 + (Math.random() - 0.5) * 0.5) / S,
              duration: 5,
              ease: "elastic.out(1, 0.1)",
              onUpdate: () => {
                mesh.scale.set(params.scale, params.scale, params.scale);
              },
              delay: 2 + Math.random()
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
    sizeAttenuation: !false // Line width constant regardless distance
  });

  let mesh = new THREE.Mesh(line.geometry, material); // this syntax could definitely be improved!
  scene.add(mesh);

  mesh.position.z = -1;

  mesh.scale.set(4, 4, 4);

  // Animation
  if (1) {
    let vals = {
      start: 0,
      end: 0
    };
    let tl = gsap.timeline({
      defaults: { duration: 1, ease: "power3.out" },
      onUpdate: () => {
        material.uniforms.dashOffset.value = vals.start;
        material.uniforms.dashRatio.value = 1 - (vals.end - vals.start);
      }
    });
    tl.to(vals, {
      end: 1,
      duration: 2
    }).to(
      vals,
      {
        start: 1,
        duration: 2
      },
      "<0.5"
    );
  }
}

// createRingAnimation();

function addAnimation(object3d) {
  gsap.from(object3d.position, {
    x: 0,
    duration: 0.5,
    delay: 0.5,
    ease: "power3.out"
  });

  let material;
  if (object3d.children.length > 0) {
    material = object3d.children[0].material;
  } else {
    material = object3d.material;
  }

  gsap.fromTo(
    material,
    { opacity: 0 },
    { opacity: 1, duration: 1, ease: "power.out", delay: 0.5 }
  );
}

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
    opacity: 1.0
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
  style.strokeLineJoin = "round";
  let geometry = SVGLoader.pointsToStroke(points, style);

  let material = new THREE.MeshBasicMaterial({
    color,
    side: THREE.DoubleSide,
    transparent: true
  });

  let mesh = new THREE.Mesh(geometry, material);
  return mesh;
}

function addWipeAnimation(
  object3d,
  { direction3d = new THREE.Vector3(-1, 0, 0), distance = 5.0 } = {}
) {
  let localPlane = new THREE.Plane(direction3d, 0);
  object3d.material.clippingPlanes = [localPlane];
  renderer.localClippingEnabled = true;

  const tween = gsap.fromTo(
    localPlane,
    { constant: -distance },
    {
      constant: distance,
      duration: 0.6,
      ease: "power3.out"
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
    opacity: 1.0
  });

  let circle = new THREE.Mesh(geometry, material);
  scene.add(circle);
  return circle;
}

function createObject({
  type = "sphere",
  materialType = "basic",
  segments = 32,
  color = 0xffffff
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
      color
    });
  } else if (materialType == "physical") {
    material = new THREE.MeshPhysicalMaterial({
      clearcoat: 1.0,
      clearcoatRoughness: 0.1,
      metalness: 0.9,
      roughness: 0.5,
      color,
      normalScale: new THREE.Vector2(0.15, 0.15)
    });
  } else {
    material = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 1.0
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
      ease: "power2.in"
      // repeatDelay: 0.4,
    }
  );
}

//// GLOW MESH

const dilateGeometry = function(geometry, length) {
  // gather vertexNormals from geometry.faces
  var vertexNormals = new Array(geometry.vertices.length);
  geometry.faces.forEach(function(face) {
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
  geometry.vertices.forEach(function(vertex, idx) {
    var vertexNormal = vertexNormals[idx];
    vertex.x += vertexNormal.x * length;
    vertex.y += vertexNormal.y * length;
    vertex.z += vertexNormal.z * length;
  });
};

const createAtmosphereMaterial = function() {
  var vertexShader = [
    "varying vec3	vVertexWorldPosition;",
    "varying vec3	vVertexNormal;",

    "varying vec4	vFragColor;",

    "void main(){",
    "	vVertexNormal	= normalize(normalMatrix * normal);",

    "	vVertexWorldPosition	= (modelMatrix * vec4(position, 1.0)).xyz;",

    "	// set gl_Position",
    "	gl_Position	= projectionMatrix * modelViewMatrix * vec4(position, 1.0);",
    "}"
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
    "}"
  ].join("\n");

  // create custom material from the shader code above
  //   that is within specially labeled script tags
  var material = new THREE.ShaderMaterial({
    uniforms: {
      coeficient: {
        type: "f",
        value: 1.0
      },
      power: {
        type: "f",
        value: 2
      },
      glowColor: {
        type: "c",
        value: new THREE.Color("pink")
      }
    },
    vertexShader: vertexShader,
    fragmentShader: fragmentShader,
    //blending	: THREE.AdditiveBlending,
    transparent: true,
    depthWrite: false
  });
  return material;
};

const GeometricGlowMesh = function(mesh, { color = "cyan" } = {}) {
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
      new THREE.Vector3(-0.5, -0.5, 0)
    ],
    lineWidth,
    color
  });
  return mesh;
}

function createRectLine({ color = 0x00ff00 } = {}) {
  var material = new THREE.LineBasicMaterial({
    color
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
  color = 0x00ff00
} = {}) {
  const group = new THREE.Group();
  for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
      let cellObject;
      if (useMeshLine) {
        cellObject = createRectMeshLine({
          lineWidth,
          color
        });
      } else {
        cellObject = createRectLine({
          color
        });
      }

      cellObject.position.set(-0.5 * cols + j, -0.5 * rows + i, 0);
      group.add(cellObject);
    }
  }
  return group;
}

function addFadeIn(
  object3d,
  { duration = 0.5, ease = "power1.out", opacity = 1.0 } = {}
) {
  const tl = gsap.timeline({ defaults: { duration, ease } });

  const materials = new Set();
  const getMaterialsRecursive = object3d => {
    if (object3d.material != null) {
      materials.add(object3d.material);
    }
    object3d.children.forEach(child => {
      getMaterialsRecursive(child);
    });
  };

  getMaterialsRecursive(object3d);

  // console.log(materials);
  materials.forEach(material => {
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
        opacity: 0
      },
      {
        opacity,
        duration
      },
      "<"
    );
  });

  return tl;
}

function setOpacity(object3d, opacity = 1.0) {
  if (object3d.material != null) {
    object3d.material.transparent = true;
    object3d.material.opacity = opacity;
  }

  object3d.children.forEach(x => {
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
    duration
  });

  tl.add(
    addFadeIn(object3d, {
      duration
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
    duration: 0.5
  });

  tl.from(
    object3d.material,
    {
      opacity: 0,
      duration: 0.5
    },
    "<"
  );

  return tl;
}

function createMoveToAnimation(
  object3d,
  {
    x = null,
    y = null,
    scale = 1.0,
    dx = null,
    dy = null,
    rotX = null,
    rotY = null,
    rotZ = null
  } = {}
) {
  if (x == null) x = object3d.position.x;
  if (y == null) y = object3d.position.y;

  if (dx != null) x = object3d.position.x + dx;
  if (dy != null) y = object3d.position.y + dy;

  let tl = gsap.timeline({
    defaults: {
      duration: 0.5,
      ease: "expo.out"
    }
  });
  tl.to(object3d.position, { x, y });

  if (rotX != null) tl.to(object3d.rotation, { x: rotX }, "<");
  if (rotY != null) tl.to(object3d.rotation, { y: rotY }, "<");
  if (rotZ != null) tl.to(object3d.rotation, { z: rotZ }, "<");

  tl.to(
    object3d.scale,
    {
      x: object3d.scale.x * scale,
      y: object3d.scale.y * scale,
      z: object3d.scale.z * scale
    },
    "<"
  );
  return tl;
}

function flyIn(
  object3d,
  {
    dx = 0.0,
    dy = 0.0,
    duration = 0.5,
    deltaRotation = -Math.PI * 4,
    beginScale = 0.01,
    ease = "power2.out"
  } = {}
) {
  let tl = gsap.timeline({
    defaults: {
      duration,
      ease
    }
  });

  tl.from(object3d.position, {
    x: object3d.position.x + dx,
    y: object3d.position.y + dy
  });

  tl.from(
    object3d.rotation,
    {
      z: object3d.rotation.z + deltaRotation
    },
    "<"
  );

  tl.from(
    object3d.scale,
    {
      x: beginScale,
      y: beginScale,
      z: beginScale
    },
    "<"
  );

  tl.add(addFadeIn(object3d), "<");

  return tl;
}

function addFlash(object3d, { repeat = 5, position = "+=0" } = {}) {
  const tl = gsap.timeline();
  for (let i = 0; i < repeat; i++) {
    tl.add(addFadeIn(object3d));
    tl.add(addFadeIn(object3d).reverse());
  }
  globalTimeline.add(tl, position);
  return tl;
}

function addLights() {
  const light0 = new THREE.PointLight(0xffffff, 1, 0);
  light0.position.set(0, 200, 0);
  scene.add(light0);

  const light1 = new THREE.PointLight(0xffffff, 1, 0);
  light1.position.set(100, 200, 100);
  scene.add(light1);

  const light2 = new THREE.PointLight(0xffffff, 1, 0);
  light2.position.set(-100, -200, -100);
  scene.add(light2);

  // const light0 = new THREE.DirectionalLight( 0xffffff, 1.0 );
  // light0.position.set(-1,1,1);
  // scene.add( light0 );

  // const light1 = new THREE.DirectionalLight( 0xffffff, 1.0 );
  // light1.position.set(1,1,1);
  // scene.add( light1 );
}

function createTriangle({
  vertices = [
    new THREE.Vector3(-1.732, -1, 0),
    new THREE.Vector3(1.732, -1, 0),
    new THREE.Vector3(0, 2, 0)
  ],
  color = 0xffffff,
  opacity = 1.0
} = {}) {
  let geometry = new THREE.Geometry();

  geometry.vertices.push(vertices[0], vertices[1], vertices[2]);

  geometry.faces.push(new THREE.Face3(0, 1, 2));

  let material = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity
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
    rotation: object3d.position.z
  };

  //shake a bunch of times
  for (var i = 0; i < shakes; i++) {
    const offset = R(-strength, strength);
    tl.to(object3d.position, duration, {
      x: initProps.x + offset,
      y: initProps.y - offset
      // rotation: initProps.rotation + R(-5, 5)
    });
  }
  //return to pre-shake values
  tl.to(object3d.position, duration, {
    x: initProps.x,
    y: initProps.y
    // scale: initProps.scale,
    // rotation: initProps.rotation
  });

  return tl;
}

function createTriangleOutline({ color = "0xffffff" } = {}) {
  const VERTICES = [
    new THREE.Vector3(-1.732, -1, 0),
    new THREE.Vector3(1.732, -1, 0),
    new THREE.Vector3(0, 2, 0)
  ];

  const triangleStroke = createLine3D({
    points: VERTICES.concat(VERTICES[0]),
    lineWidth: 0.3,
    color
  });
  triangleStroke.position.set(-6.4, -6.4, 0.02);
  // triangleStroke.scale.set(0.2, 0.2, 0.2);
  // scene.add(triangleStroke);
  return triangleStroke;
}

function addExplosionAnimation(
  objectGroup,
  { ease = "expo.out", duration = 1.5 } = {}
) {
  const tl = gsap.timeline({
    defaults: {
      duration,
      ease: ease
    }
  });

  tl.from(
    objectGroup.children.map(x => x.position),
    {
      x: 0,
      y: 0
    },
    0
  );
  tl.from(
    objectGroup.children.map(x => x.scale),
    {
      x: 0.001,
      y: 0.001
    },
    0
  );
  tl.from(
    objectGroup.children.map(x => x.rotation),
    {
      z: 0
    },
    0
  );
  return tl;
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
    stagger = 0
  } = {}
) {
  const tl = gsap.timeline({
    defaults: {
      duration,
      ease: ease
    }
  });

  let delay = 0;
  objectGroup.children.forEach(child => {
    const r = radiusMin + (radiusMax - radiusMin) * rng();
    const theta = rng() * 2 * Math.PI;
    const x = r * Math.cos(theta);
    const y = r * Math.sin(theta);

    tl.fromTo(child.position, { x: 0, y: 0 }, { x, y }, delay);

    const rotation = rotationMin + rng() * (rotationMax - rotationMin);
    tl.fromTo(child.rotation, { z: 0 }, { z: rotation }, delay);

    const targetScale = rng() * 0.5 + 0.5;
    tl.fromTo(
      child.scale,
      { x: 0.001, y: 0.001, z: 0.001 },
      { x: targetScale, y: targetScale, z: targetScale },
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
      ease: "expo.out"
    }
  });
  tl.to(
    objectGroup.children.map(x => x.position),
    {
      x: 0,
      y: 0
    },
    0
  );
  tl.to(
    objectGroup.children.map(x => x.scale),
    {
      x: 0.001,
      y: 0.001
    },
    0
  );
  return tl;
}

function getCompoundBoundingBox(object3D) {
  var box = null;
  object3D.traverse(function(obj3D) {
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
      function(data) {
        let paths = data.paths;

        let parentGroup = new THREE.Group();

        const unnamedGroup = new THREE.Group();
        parentGroup.add(unnamedGroup);

        for (let i = 0; i < paths.length; i++) {
          let path = paths[i];

          let material = new THREE.MeshBasicMaterial({
            color: color !== null ? color : path.color,
            side: THREE.DoubleSide,
            depthWrite: false
          });

          const shapes = path.toShapes(isCCW);

          let geometry = new THREE.ShapeBufferGeometry(shapes);

          let mesh = new THREE.Mesh(geometry, material);

          const name = _getNodeName(path.userData.node);

          if (name) {
            let group = parentGroup.children.filter(x => x.name == name)[0];
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

        parentGroup.children.forEach(group => {
          group.children.forEach(subMesh => {
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
      function(xhr) {
        // console.log((xhr.loaded / xhr.total * 100) + '% loaded');
      },
      // called when loading has errors
      function(error) {
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
    tl.set(glitchPass, { factor: 0 }, `+=${duration}`);
    return tl;
  } else {
    return gsap.timeline();
  }
}

function addTextFlyInAnimation(textMesh, { duration = 0.5 } = {}) {
  const tl = gsap.timeline();

  // Animation
  textMesh.children.forEach((letter, i) => {
    const vals = {
      position: -textMesh.size * 2,
      rotation: -Math.PI / 2
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
        }
      },
      `-=${duration - 0.03}`
    );

    tl.add(addFadeIn(letter, { duration }), "<");
  });

  return tl;
}

function newScene(initFunction) {
  (async () => {
    await initFunction();

    {
      // Create timeline GUI

      options.timeline = 0;
      gui
        .add(options, "timeline", 0, globalTimeline.totalDuration())
        .onChange(val => {
          globalTimeline.seek(val);
        });

      Object.keys(globalTimeline.labels).forEach(key => {
        console.log(`${key} ${globalTimeline.labels[key]}`);
      });

      const folder = gui.addFolder("Timeline Labels");
      var labels = new Object();
      Object.keys(globalTimeline.labels).forEach(key => {
        const label = key;
        const time = globalTimeline.labels[key];

        console.log(this);
        labels[label] = () => {
          globalTimeline.seek(time);
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
  color = 0xffff00
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
      new THREE.Vector3(0, 0, 0)
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
    fontSize = 1.0
  } = {}
) {
  const mesh = new TextMesh({
    text,
    font,
    size: 0.5,
    color,
    size: fontSize
  });
  mesh.position.set(x, y, z);

  addAnime(mesh, { aniEnter, aniExit });

  scene.add(mesh);

  return mesh;
}

async function loadTexture(url) {
  return new Promise((resolve, reject) => {
    new THREE.TextureLoader().load(url, texture => {
      resolve(texture);
    });
  });
}

function addAnime(
  object3d,
  { aniPos = "+=0", aniHold = 1, animation = "fadeIn" } = {}
) {
  const tl = gsap.timeline();

  if (animation) {
    const animationList = animation.split("|");

    // Enter animation
    animationList.forEach(animation => {
      if (animation == "fadeIn") {
        tl.add(addFadeIn(object3d));
      } else if (animation == "jumpIn") {
        tl.add(addJumpIn(object3d));
      } else if (animation == "spinIn") {
        tl.from(object3d.rotation, { y: Math.PI * 4 }, "<");
      } else if (animation == "grow") {
        tl.from(
          object3d.scale,
          { x: 0.01, y: 0.01, z: 0.01, ease: "expo.out" },
          "<"
        );
      } else if (animation == "grow2") {
        tl.from(
          object3d.scale,
          { x: 0.01, y: 0.01, z: 0.01, ease: "elastic.out" },
          "<"
        );
      } else if (animation == "type") {
        object3d.children.forEach(x => {
          tl.fromTo(
            x,
            {
              visible: false
            },
            {
              visible: true,
              ease: "steps(1)",
              duration: 0.1
            },
            ">"
          );
        });
      } else if (animation == "fastType") {
        object3d.children.forEach(x => {
          tl.fromTo(
            x,
            {
              visible: false
            },
            {
              visible: true,
              ease: "steps(1)",
              duration: 0.02
            },
            ">"
          );
        });
        tl.set({}, {}, ">+0.5");
      }
    });

    // Animation
    animationList.forEach(animation => {
      if (animation == "rotation") {
        tl.to(
          object3d.rotation,
          {
            y: object3d.rotation.y + Math.PI * 2 * 4,
            duration: 2,
            ease: "none"
          },
          ">"
        );
      }
    });

    // Exit animation
    const tlExitAnimation = gsap.timeline();
    animationList.forEach(animation => {
      if (animation == "fadeOut") {
        tlExitAnimation.add(
          addFadeIn(object3d, { ease: "power1.in" }).reverse(),
          "<"
        );
      }
    });

    if (tlExitAnimation.duration() > 0) {
      tl.add(tlExitAnimation, ">" + aniHold.toString());
    }
  }

  if (tl.duration() > 0) {
    globalTimeline.add(tl, aniPos);
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
    color = 0xffffff,
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
    parent = null,
    lighting = false,
    ccw = true,
    font = "en",
    fontSize = 1.0,
    arrowFrom = new THREE.Vector3(0, 0, 0),
    arrowTo = new THREE.Vector3(0, 1, 0)
  } = {}
) {
  let material;

  if (lighting) {
    material = new THREE.MeshPhongMaterial({
      color,
      // emissive: 0x072534,
      // side: THREE.DoubleSide,
      flatShading: true
      // transparent:
    });
  } else {
    material = new THREE.MeshBasicMaterial({
      side: THREE.DoubleSide,
      color,
      transparent: opacity < 1.0 ? true : false,
      opacity,
      wireframe
    });
  }

  let mesh;
  if (obj.endsWith(".svg")) {
    mesh = await loadSVG(obj, { isCCW: ccw });
    scene.add(mesh);
  } else if (obj.endsWith(".png")) {
    const texture = await loadTexture(obj);
    texture.anisotropy = renderer.getMaxAnisotropy();
    const material = new THREE.MeshBasicMaterial({
      map: texture,
      side: THREE.DoubleSide
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
        color
      });
    } else {
      const geometry = new THREE.Geometry();
      geometry.vertices.push(vertices[0], vertices[1], vertices[2]);
      geometry.faces.push(new THREE.Face3(0, 1, 2));

      mesh = new THREE.Mesh(geometry, material);
    }
  } else if (obj == "rect" || obj == "rectangle") {
    const geometry = new THREE.PlaneGeometry(width, height);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj == "circle") {
    const geometry = new THREE.CircleGeometry(0.5, 32);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj == "sphere") {
    const geometry = new THREE.SphereGeometry(0.5, 32, 32);
    mesh = new THREE.Mesh(geometry, material);
  } else if (obj == "arrow") {
    mesh = createArrow({
      from: arrowFrom,
      to: arrowTo,
      color
    });
  } else if (typeof obj == "string") {
    mesh = new TextMesh({
      text: obj,
      font,
      size: 0.5,
      color,
      size: fontSize
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

  addAnime(mesh, { aniPos, animation });

  if (parent != null) {
    parent.add(mesh);
  } else {
    scene.add(mesh);
  }

  return mesh;
}

function addGroup() {
  const group = new THREE.Group();
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
  globalTimeline.set({}, {}, "+=" + t.toString());
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
  height = 14
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

export default {
  addCollapseAnimation,
  addExplosionAnimation,
  addFadeIn,
  addFadeOut,
  addGlitch,
  addJumpIn,
  addLights,
  addShake2D,
  addTextFlyInAnimation,
  addWipeAnimation,
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
  addAnime: addAnime,
  createTriangleVertices,
  pause,
  createExplosionAnimation,
  setSeed,
  getGridLayoutPositions,
  random
};

export { THREE, gsap };
