import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { FXAAShader } from "three/examples/jsm/shaders/FXAAShader.js";
import { GlitchPass } from "./utils/GlitchPass";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { ShaderPass } from "three/examples/jsm/postprocessing/ShaderPass";
import { SMAAPass } from "three/examples/jsm/postprocessing/SMAAPass.js";
import { SSAARenderPass } from "three/examples/jsm/postprocessing/SSAARenderPass.js";
import { SVGLoader } from "three/examples/jsm/loaders/SVGLoader";
import { TAARenderPass } from "three/examples/jsm/postprocessing/TAARenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { WaterPass } from "./utils/WaterPass";
import * as dat from "dat.gui";
import * as THREE from "three";
import gsap from "gsap";
import Stats from "three/examples/jsm/libs/stats.module.js";
import TextMesh from "./objects/TextMesh";

declare class CCapture {
  constructor(params: any);
}

gsap.ticker.remove(gsap.updateRoot);

let glitchPassEnabled = false;
let screenWidth = 1920;
let screenHeight = 1080;
let antiAliasMethod = "msaa";
let motionBlurSamples = 1;
let bloomEnabled = false;
let captureStatus: HTMLDivElement;
let globalTimeline = gsap.timeline({ onComplete: stopCapture });
const mainTimeline = gsap.timeline();
let stats: Stats = undefined;
let capturer: CCapture = undefined;
let renderer: THREE.WebGLRenderer = undefined;
let composer: EffectComposer = undefined;
let scene: THREE.Scene = undefined;
let camera: THREE.Camera = undefined;
let lightGroup: THREE.Group = undefined;
let cameraControls: OrbitControls = undefined;
let glitchPass: any;
let gridHelper: THREE.GridHelper;
let backgroundAlpha = 1.0;
var animationCallbacks: Function[] = [];

var lastTimestamp: number = undefined;
var timeElapsed = 0;
var animTimeElapsed = 0;

globalTimeline.add(mainTimeline, "0");

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

var gui = new dat.GUI();
gui.add(options, "format", ["webm", "png"]);
gui.add(options, "framerate", [10, 25, 30, 60, 120]);
gui.add(options, "start");
gui.add(options, "stop");

function startCapture({ resetTiming = true, name = document.title } = {}) {
  if (gridHelper !== undefined) {
    gridHelper.visible = false;
  }

  if (resetTiming) {
    // Reset gsap
    gsap.ticker.remove(gsap.updateRoot);

    lastTimestamp = undefined;
  }

  capturer = new CCapture({
    verbose: true,
    display: false,
    framerate: options.framerate,
    motionBlurFrames: motionBlurSamples,
    quality: 100,
    format: options.format,
    workersPath: "dist/src/",
    timeLimit: 0,
    frameLimit: 0,
    autoSaveTime: 0,
    name,
  });

  (capturer as any).start();

  captureStatus.innerText = "capturing";
}

function stopCapture() {
  if (capturer !== undefined) {
    (capturer as any).stop();
    (capturer as any).save();
    capturer = undefined;
    captureStatus.innerText = "stopped";
  }
}

function setupOrthoCamera() {
  if (camera === undefined) {
    const aspect = screenWidth / screenHeight;
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
}

function setupPespectiveCamera() {
  if (camera === undefined) {
    // This will ensure the size of 10 in the vertical direction.
    camera = new THREE.PerspectiveCamera(
      60,
      screenWidth / screenHeight,
      0.1,
      5000
    );
    camera.position.set(0, 0, 8.66);
    camera.lookAt(new THREE.Vector3(0, 0, 0));
  }
}

function setupScene() {
  renderer = new THREE.WebGLRenderer({
    alpha: true,
    antialias: antiAliasMethod === "msaa",
  });
  renderer.localClippingEnabled = true;

  renderer.setSize(screenWidth, screenHeight);
  document.body.appendChild(renderer.domElement);

  {
    stats = Stats();
    // stats.showPanel(1); // 0: fps, 1: ms, 2: mb, 3+: custom
    document.body.appendChild(stats.dom);
  }

  renderer.setClearColor(0x000000, backgroundAlpha);
  scene.background = new THREE.Color(0);

  setupPespectiveCamera();

  cameraControls = new OrbitControls(camera, renderer.domElement);

  scene.add(new THREE.AmbientLight(0x000000));

  let renderScene = new RenderPass(scene, camera);

  composer = new EffectComposer(renderer);
  composer.setSize(screenWidth, screenHeight);
  composer.addPass(renderScene);

  if (bloomEnabled) {
    // Bloom pass
    let bloomPass = new UnrealBloomPass(
      new THREE.Vector2(screenWidth, screenHeight),
      0.5, // Strength
      0.4, // radius
      0.85 // threshold
    );
    composer.addPass(bloomPass);
  }

  // if (0) {
  //   // Water pass
  //   const waterPass = new WaterPass();
  //   waterPass.factor = 0.1;
  //   composer.addPass(waterPass);
  // }

  if (antiAliasMethod === "fxaa") {
    const fxaaPass = new ShaderPass(FXAAShader);

    let pixelRatio = renderer.getPixelRatio();
    (fxaaPass as any).uniforms["resolution"].value.x =
      1 / (screenWidth * pixelRatio);
    (fxaaPass as any).uniforms["resolution"].value.y =
      1 / (screenHeight * pixelRatio);

    composer.addPass(fxaaPass);
  } else if (antiAliasMethod === "ssaa") {
    let ssaaRenderPass = new SSAARenderPass(scene, camera, 0, 0);
    ssaaRenderPass.unbiased = true;
    composer.addPass(ssaaRenderPass);
  } else if (antiAliasMethod === "smaa") {
    let pixelRatio = renderer.getPixelRatio();
    let smaaPass = new SMAAPass(
      screenWidth * pixelRatio,
      screenHeight * pixelRatio
    );
    composer.addPass(smaaPass);
  } else if (antiAliasMethod === "taa") {
    let taaRenderPass = new TAARenderPass(scene, camera, 0, 0);
    taaRenderPass.unbiased = false;
    taaRenderPass.sampleLevel = 4;
    composer.addPass(taaRenderPass);
  }

  if (glitchPassEnabled) {
    glitchPass = new GlitchPass();
    composer.addPass(glitchPass);
  }
}

function animate() {
  // time /* `time` parameter is buggy in `ccapture`. Do not use! */
  const nowInSecs = Date.now() / 1000;

  requestAnimationFrame(animate);

  let delta: number;
  {
    // Compute `timeElapsed`. This works for both animation preview and capture.
    if (lastTimestamp === undefined) {
      delta = 0.000001;
      lastTimestamp = nowInSecs;
      globalTimeline.seek(0, false);
      animTimeElapsed = 0;
    } else {
      delta = nowInSecs - lastTimestamp;
      lastTimestamp = nowInSecs;
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

  if (capturer) (capturer as any).capture(renderer.domElement);
}

interface MoveCameraParameters extends Transform, AnimationParameters {}
function moveCamera({ x = 0, y = 0, z = 10, t }: MoveCameraParameters = {}) {
  commandQueue.push(() => {
    const tl = gsap.to(camera.position, {
      x,
      y,
      z,
      onUpdate: () => {
        camera.lookAt(new THREE.Vector3(0, 0, 0));
      },
      duration: 0.5,
      ease: "expo.out",
    });
    mainTimeline.add(tl, t);
  });
}

scene = new THREE.Scene();

function generateRandomString(length: number) {
  var result = "";
  var characters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  var charactersLength = characters.length;
  for (var i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
}

function randomInt(min: number, max: number) {
  return Math.floor(random() * (max - min + 1)) + min;
}

function createLine3D({
  color = new THREE.Color(0xffffff),
  points = [],
  lineWidth = 0.1,
}: {
  color: THREE.Color;
  points: THREE.Vector3[];
  lineWidth: number;
}) {
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
    color: new THREE.Color(color),
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

function getAllMaterials(object3d: THREE.Object3D): THREE.Material[] {
  const materials = new Set<THREE.Material>();

  const getMaterialsRecursive = (object3d: THREE.Object3D) => {
    const mesh = object3d as THREE.Mesh;
    if (mesh && mesh.material) {
      materials.add(mesh.material as THREE.Material);
    }

    if (object3d.children) {
      object3d.children.forEach((child) => {
        getMaterialsRecursive(child);
      });
    }
  };

  getMaterialsRecursive(object3d);
  return Array.from(materials);
}

function createFadeInAnimation(
  object3d: THREE.Object3D,
  { duration = 0.25, ease = "linear" }: AnimationParameters = {}
) {
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

function createFadeOutAnimation(
  obj: THREE.Object3D,
  { duration = 0.25, ease = "linear" }: AnimationParameters = {}
): gsap.core.Timeline {
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

function createJumpInAnimation(
  object3d: THREE.Object3D,
  { ease = "elastic.out(1, 0.2)" } = {}
) {
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

// TODO: remove
function flyIn(
  object3d: THREE.Object3D,
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

function addDefaultLights() {
  if (lightGroup === undefined) {
    const group = new THREE.Group();

    const lightGroup = new THREE.Group();
    scene.add(group);

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

function createExplosionAnimation(
  objectGroup: THREE.Object3D,
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
  objectGroup: THREE.Object3D,
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

function createImplodeAnimation(
  objectGroup: THREE.Object3D,
  { duration = 0.5 } = {}
) {
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

function getCompoundBoundingBox(object3D: THREE.Object3D) {
  let box: THREE.Box3;
  object3D.traverse(function (obj3D) {
    const geometry: THREE.Geometry = (obj3D as any).geometry;
    if (geometry === undefined) {
      return;
    }
    geometry.computeBoundingBox();
    if (box === undefined) {
      box = geometry.boundingBox;
    } else {
      box.union(geometry.boundingBox);
    }
  });
  return box;
}

function _getNodeName(node: any): any {
  if (!node) return "";
  if (node.id) {
    return _getNodeName(node.parentNode) + "/" + node.id;
  } else {
    return _getNodeName(node.parentNode);
  }
}

async function loadSVG(
  url: string,
  { color, ccw = true }: { color?: THREE.Color; ccw: boolean }
): Promise<THREE.Object3D> {
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
            color: color === undefined ? (path as any).color : color,
            side: THREE.DoubleSide,
            // depthWrite: false,
          });

          const shapes = path.toShapes(ccw);

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

function addGlitch({ duration = 0.2, t }: AnimationParameters = {}) {
  glitchPassEnabled = true;
  antiAliasMethod = "fxaa";

  commandQueue.push(() => {
    const tl = gsap.timeline();
    tl.set(glitchPass, { factor: 1 });
    tl.set(glitchPass, { factor: 0 }, `<${duration}`);
    mainTimeline.add(tl, t);
  });
}

function run() {
  (async () => {
    setupScene();

    for (const cmd of commandQueue) {
      if (typeof cmd === "function") {
        const ret = cmd();
        if (ret instanceof Promise) {
          await ret;
        }
      } else {
        throw `invalid command`;
      }
    }

    // _addMarkerToTimeline();

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
      const labels: any = {};
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
  color = new THREE.Color(0xffffff),
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

async function loadTexture(url: string): Promise<THREE.Texture> {
  return new Promise((resolve, reject) => {
    new THREE.TextureLoader().load(url, (texture) => {
      resolve(texture);
    });
  });
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

var commandQueue: Function[] = [];

interface AnimationParameters {
  t?: number | string;
  duration?: number;
  ease?: string;
}

interface MoveObjectParameters extends Transform, AnimationParameters {}

interface Shake2DParameters extends AnimationParameters {
  shakes?: number;
  strength?: number;
}

class SceneObject {
  _threeObject3d: THREE.Object3D;

  move({
    t,
    position,
    x,
    y,
    z,
    rx,
    ry,
    rz,
    sx,
    sy,
    sz,
    scale,
    duration = 0.5,
    ease = "power2.out",
  }: MoveObjectParameters = {}) {
    commandQueue.push(() => {
      let tl = gsap.timeline({
        defaults: {
          duration,
          ease,
        },
      });

      if (position !== undefined) {
        tl.to(
          this._threeObject3d.position,
          { x: position[0], y: position[1], z: position[2] },
          "<"
        );
      } else {
        if (x !== undefined) tl.to(this._threeObject3d.position, { x }, "<");
        if (y !== undefined) tl.to(this._threeObject3d.position, { y }, "<");
        if (z !== undefined) tl.to(this._threeObject3d.position, { z }, "<");
      }

      if (rx !== undefined) tl.to(this._threeObject3d.rotation, { x: rx }, "<");
      if (ry !== undefined) tl.to(this._threeObject3d.rotation, { y: ry }, "<");
      if (rz !== undefined) tl.to(this._threeObject3d.rotation, { z: rz }, "<");

      if (scale !== undefined) {
        tl.to(
          this._threeObject3d.scale,
          {
            x: scale,
            y: scale,
            z: scale,
          },
          "<"
        );
      } else {
        if (sx !== undefined) tl.to(this._threeObject3d.scale, { x: sx }, "<");
        if (sy !== undefined) tl.to(this._threeObject3d.scale, { y: sy }, "<");
        if (sz !== undefined) tl.to(this._threeObject3d.scale, { z: sz }, "<");
      }

      mainTimeline.add(tl, t);
    });
  }

  fadeIn({ duration = 0.25, ease = "linear", t }: AnimationParameters = {}) {
    commandQueue.push(() => {
      const tl = gsap.timeline({ defaults: { duration, ease } });

      const materials = getAllMaterials(this._threeObject3d);
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

      mainTimeline.add(tl, t);
    });
  }

  fadeOut({ duration = 0.25, ease = "linear", t }: AnimationParameters = {}) {
    commandQueue.push(() => {
      const tl = gsap.timeline({ defaults: { duration, ease } });

      const materials = getAllMaterials(this._threeObject3d);
      for (const material of materials) {
        material.transparent = true;
        tl.to(
          material,
          {
            opacity: 0,
          },
          "<"
        );
      }

      mainTimeline.add(tl, t);
    });
  }

  rotateIn({ t }: AnimationParameters = {}) {
    commandQueue.push(() => {
      const tl = gsap.timeline({ defaults: { duration: 0.5 } });

      tl.from(
        this._threeObject3d.rotation,
        { z: Math.PI * 4, ease: "power.in", duration: 0.5 },
        "<"
      );
      tl.from(
        this._threeObject3d.scale,
        {
          x: Number.EPSILON,
          y: Number.EPSILON,
          z: Number.EPSILON,
          ease: "power.in",
          duration: 0.5,
        },
        "<"
      );

      mainTimeline.add(tl, t);
    });
  }

  grow({ t }: AnimationParameters = {}) {
    commandQueue.push(() => {
      mainTimeline.from(
        this._threeObject3d.scale,
        { x: 0.01, y: 0.01, z: 0.01, ease: "expo.out" },
        t
      );
    });
  }

  grow2({ t }: AnimationParameters = {}) {
    commandQueue.push(() => {
      mainTimeline.from(
        this._threeObject3d.scale,
        { x: 0.01, y: 0.01, z: 0.01, ease: "elastic.out(1, 0.75)" },
        t
      );
    });
  }

  grow3({ t }: AnimationParameters = {}) {
    commandQueue.push(() => {
      mainTimeline.from(
        this._threeObject3d.scale,
        {
          x: 0.01,
          y: 0.01,
          z: 0.01,
          ease: "elastic.out(1, 0.2)",
          duration: 1.0,
        },
        t
      );
    });
  }

  flying({ t = undefined, duration = 5 }: AnimationParameters = {}) {
    const WIDTH = 30;
    const HEIGHT = 15;

    commandQueue.push(() => {
      const tl = gsap.timeline();

      this._threeObject3d.children.forEach((x) => {
        tl.fromTo(
          x.position,
          {
            x: rng() * WIDTH - WIDTH / 2,
            y: rng() * HEIGHT - HEIGHT / 2,
          },
          {
            x: rng() * screenWidth - screenWidth / 2,
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

  reveal({ dir = "up", t }: { dir?: string; t?: number | string }) {
    commandQueue.push(() => {
      const object3d = this._threeObject3d;

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

  shake2D({
    shakes = 20,
    duration = 0.2,
    strength = 0.5,
    t,
  }: Shake2DParameters = {}) {
    function R(max: number, min: number) {
      return rng() * (max - min) + min;
    }

    commandQueue.push(() => {
      const object3d = this._threeObject3d;

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
        tl.to(object3d.position, duration / shakes, {
          x: initProps.x + offset,
          y: initProps.y - offset,
          // rotation: initProps.rotation + R(-5, 5)
        });
      }
      //return to pre-shake values
      tl.to(object3d.position, duration / shakes, {
        x: initProps.x,
        y: initProps.y,
        // scale: initProps.scale,
        // rotation: initProps.rotation
      });

      mainTimeline.add(tl, t);
    });
  }
}

interface ExplodeParameters extends AnimationParameters {
  minRotation?: number;
  maxRotation?: number;
  minRadius?: number;
  maxRadius?: number;
  minScale?: number;
  maxScale?: number;
  stagger?: number;
}

class GroupObject extends SceneObject {
  explode({
    t,
    ease = "expo.out",
    duration = 2,
    minRotation = -2 * Math.PI,
    maxRotation = 2 * Math.PI,
    minRadius = 1,
    maxRadius = 4,
    minScale = 1,
    maxScale = 1,
    stagger = 0.03,
  }: ExplodeParameters = {}) {
    commandQueue.push(() => {
      const tl = createExplosionAnimation(this._threeObject3d, {
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

  implode({ t = undefined, duration = 0.5 }: AnimationParameters = {}) {
    commandQueue.push(() => {
      const tl = createImplodeAnimation(this._threeObject3d, { duration });
      mainTimeline.add(tl, t);
    });
  }
}

function toThreeColor(color: string | number): THREE.Color {
  return color === undefined
    ? new THREE.Color(0xffffff)
    : new THREE.Color(color);
}

function add(val: string, params: AddObjectParameters): SceneObject {
  const obj = new SceneObject();

  commandQueue.push(async () => {
    let {
      color,
      opacity = 1.0,
      vertices = [],
      wireframe = false,
      width = 1,
      height = 1,
      parent,
      ccw = false,
      font,
      fontSize = 1.0,
      start = { x: 0, y: 0 },
      end = { x: 0, y: 1 },
      lineWidth = 0.1,
      gridSize = 10,
      centralAngle = Math.PI * 2,
      letterSpacing = 0.05,
    } = params;

    // if (lighting) {
    //   addDefaultLights();
    //   material = new THREE.MeshPhongMaterial({
    //     color: color !== undefined ? color : 0xffffff,
    //     // emissive: 0x072534,
    //     // side: THREE.DoubleSide,
    //     flatShading: true,
    //   });
    // } else {
    //   material = new THREE.MeshBasicMaterial({
    //     side: THREE.DoubleSide,
    //     color: color !== undefined ? color : 0xffffff,
    //     transparent,
    //     opacity,
    //     wireframe,
    //   });
    // }

    let mesh: THREE.Object3D;
    if (val.endsWith(".svg")) {
      mesh = await loadSVG(val, {
        ccw,
        color: color === undefined ? undefined : toThreeColor(color),
      });
      scene.add(mesh);
    } else if (val.endsWith(".png") || val.endsWith(".jpg")) {
      const texture = await loadTexture(val);
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
    } else if (val === "triangle") {
      if (vertices.length === 0) {
        vertices = createTriangleVertices();
      }

      const geometry = new THREE.Geometry();
      geometry.vertices.push(vertices[0], vertices[1], vertices[2]);
      geometry.faces.push(new THREE.Face3(0, 1, 2));

      mesh = new THREE.Mesh(geometry, createBasicMaterial(params));
    } else if (val === "triangleOutline") {
      if (vertices.length === 0) {
        vertices = createTriangleVertices();
      }

      mesh = createLine3D({
        points: vertices.concat(vertices[0]),
        lineWidth,
        color:
          color !== undefined
            ? new THREE.Color(color)
            : new THREE.Color(0xffffff),
      });
    } else if (val === "rect" || val === "rectangle") {
      const geometry = new THREE.PlaneGeometry(width, height);
      mesh = new THREE.Mesh(geometry, createBasicMaterial(params));
    } else if (val === "circle") {
      const geometry = new THREE.CircleGeometry(0.5, 32, 0, centralAngle);
      mesh = new THREE.Mesh(geometry, createBasicMaterial(params));
    } else if (val === "ring") {
      const geometry = new THREE.RingGeometry(0.85, 1, 64);
      mesh = new THREE.Mesh(geometry, createBasicMaterial(params));
    } else if (val === "sphere") {
      const geometry = new THREE.SphereGeometry(0.5, 32, 32);
      mesh = new THREE.Mesh(geometry, createBasicMaterial(params));
    } else if (val === "pyramid") {
      const geometry = new THREE.ConeGeometry(0.5, 1.0, 4, 32);
      mesh = new THREE.Mesh(geometry, createBasicMaterial(params));
    } else if (val === "arrow") {
      mesh = createArrow({
        from: toThreeVector3(start),
        to: toThreeVector3(end),
        color:
          color !== undefined
            ? new THREE.Color(color)
            : new THREE.Color(0xffffff),
        lineWidth,
      });
    } else if (val === "line") {
      mesh = createArrow({
        from: toThreeVector3(start),
        to: toThreeVector3(end),
        arrowStart: false,
        arrowEnd: false,
        color:
          color !== undefined
            ? new THREE.Color(color)
            : new THREE.Color(0xffffff),
        lineWidth,
      });
    } else if (val === "grid") {
      const gridHelper = new THREE.GridHelper(1, gridSize, 0x00ff00, 0xc0c0c0);
      gridHelper.rotation.x = Math.PI / 2;
      gridHelper.position.z = 0.01;

      mesh = gridHelper;
    } else if (typeof val === "string") {
      mesh = new TextMesh({
        text: val,
        font,
        color:
          color !== undefined
            ? new THREE.Color(color)
            : new THREE.Color(0xffffff),
        size: fontSize,
        letterSpacing,
      });
    }

    updateTransform(mesh, params);

    if (parent !== undefined) {
      parent._threeObject3d.add(mesh);
    } else {
      scene.add(mesh);
    }

    obj._threeObject3d = mesh;
  });

  return obj;
}

function toThreeVector3(v: any) {
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
  scale?: number;
}

interface AddObjectParameters extends Transform, BasicMaterial {
  vertices?: any;
  wireframe?: any;
  outline?: any;
  outlineWidth?: any;
  width?: any;
  height?: any;
  t?: number | string;
  parent?: SceneObject;
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

interface BasicMaterial {
  color?: string | number;
  opacity?: number;
}

function createBasicMaterial(basicMaterial: BasicMaterial) {
  const opacity =
    basicMaterial.opacity === undefined ? 1.0 : basicMaterial.opacity;

  return new THREE.MeshBasicMaterial({
    side: THREE.DoubleSide,
    color: new THREE.Color(
      basicMaterial.color === undefined ? 0xffffff : basicMaterial.color
    ),
    transparent: opacity < 1.0 ? true : false,
    opacity,
  });
}

function updateTransform(mesh: THREE.Object3D, transform: Transform) {
  // Scale
  if (transform.scale !== undefined) {
    mesh.scale.setScalar(transform.scale);
  } else {
    if (transform.sx !== undefined) {
      mesh.scale.x = transform.sx;
    }
    if (transform.sy !== undefined) {
      mesh.scale.y = transform.sy;
    }
    if (transform.sz !== undefined) {
      mesh.scale.z = transform.sz;
    }
  }

  // Position
  if (transform.position !== undefined) {
    mesh.position.set(
      transform.position[0],
      transform.position[1],
      transform.position[2]
    );
  } else {
    if (transform.x !== undefined) mesh.position.x = transform.x;
    if (transform.y !== undefined) mesh.position.y = transform.y;
    if (transform.z !== undefined) mesh.position.z = transform.z;
  }

  // Rotation
  if (transform.rx !== undefined) mesh.rotation.x = transform.rx;
  if (transform.ry !== undefined) mesh.rotation.y = transform.ry;
  if (transform.rz !== undefined) mesh.rotation.z = transform.rz;
}

interface AddGroupParameters extends Transform {
  parent?: SceneObject;
}

function addGroup(params: AddGroupParameters = {}) {
  const groupObject = new GroupObject();

  commandQueue.push(() => {
    groupObject._threeObject3d = new THREE.Group();

    updateTransform(groupObject._threeObject3d, params);

    if (params.parent) {
      params.parent._threeObject3d.add(groupObject._threeObject3d);
    } else {
      scene.add(groupObject._threeObject3d);
    }
  });

  return groupObject;
}

function getBoundingBox(object3D: THREE.Object3D): THREE.Box3 {
  return new THREE.Box3().setFromObject(object3D);
}

function getQueryString(url: string = undefined) {
  // get query string from url (optional) or window
  var queryString = url ? url.split("?")[1] : window.location.search.slice(1);

  // we'll store the parameters here
  var obj: any = {};

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

function setSeed(val: any) {
  rng = seedrandom(val);
}

function random() {
  return rng();
}

function getGridPosition({ rows = 1, cols = 1, width = 25, height = 14 } = {}) {
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

function enableMotionBlur({ motionBlurSamples = 16 } = {}) {
  motionBlurSamples = motionBlurSamples;
  antiAliasMethod = "fxaa";
}

function setResolution(w: number, h: number) {
  screenWidth = w;
  screenHeight = h;
}

function setBackgroundColor(color: number | string) {
  commandQueue.push(() => {
    scene.background = toThreeColor(color);
  });
}

function fadeOutAll({ t }: AnimationParameters = {}) {
  commandQueue.push(() => {
    const tl = gsap.timeline();
    for (const object3d of scene.children) {
      tl.add(createFadeOutAnimation(object3d), "<");
    }
    mainTimeline.add(tl, t);
  });
}

export default {
  run,
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
  pause: (duration: number) => {
    commandQueue.push(() => {
      mainTimeline.set({}, {}, "+=" + duration.toString());
    });
  },
  addEmptyAnimation: (t: number | string) => {
    commandQueue.push(() => {
      mainTimeline.set({}, {}, t);
    });
  },
  fadeOutAll,
  setBackgroundColor,
  enableBloom: () => {
    bloomEnabled = true;
    antiAliasMethod = "fxaa";
  },
  addGlitch,
  setResolution,
};
