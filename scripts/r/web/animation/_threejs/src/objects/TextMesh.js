import {
  Object3D,
  ShapeGeometry,
  MeshBasicMaterial,
  Mesh,
  FontLoader,
  ShapeBufferGeometry,
  Group,
  Color,
  DoubleSide,
  Geometry,
  Vector3,
  Vector2,
  BufferGeometry
} from "three";

import { SVGLoader } from "three/examples/jsm/loaders/SVGLoader";

import fontFile from "../fonts/sourceHanBold3000";
import gsap from "gsap";
import { MeshLine, MeshLineMaterial } from "three.meshline";
import * as THREE from "three";
// import font2 from '../utils/cn.json'

const fontLoader = new FontLoader();
// const font = fontLoader.load('fonts/cn.json');

function createLitMaterial() {
  const material = new THREE.MeshStandardMaterial({
    shading: THREE.FlatShading,
    color: 0x00ff00,
    transparent: false,
    opacity: 1,
    wireframe: false
  });
  return material;
}

export default class TextMesh extends Object3D {
  constructor({
    text = "",
    size = 1.0,
    letterSpacing = 0.05,
    color = "#ffffff",
    opacity = 1,
    wireframe = false,
    font = "en",
    material = null
  } = {}) {
    super();

    this.basePosition = 0;
    this.size = size;
    this.color = color;
    this.letterSpacing = letterSpacing;

    if (font == "zh") {
      this.font = fontLoader.parse(require("../fonts/sourceHanBold3000"));
    } else {
      this.font = fontLoader.parse(require("../fonts/muliBold").default);
    }

    if (material) {
      this.material = material;
    } else {
      this.material = null;
    }

    this.text = text;

    // Text outlines
    // make line shape ( N.B. edge view remains visible )
    if (0) {
      // Hole shapes contains all the holes in text glyphs
      let holeShapes = [];

      for (let i = 0; i < shapes.length; i++) {
        let shape = shapes[i];
        if (shape.holes && shape.holes.length > 0) {
          for (let j = 0; j < shape.holes.length; j++) {
            let hole = shape.holes[j];
            holeShapes.push(hole);
          }
        }
      }

      let lineColor = new Color(color);
      let matDark = new MeshBasicMaterial({
        color: color,
        side: DoubleSide
      });

      shapes.push.apply(shapes, holeShapes);

      let style = SVGLoader.getStrokeStyle(0.05, lineColor.getStyle());
      let strokeText = new Group();

      for (let i = 0; i < shapes.length; i++) {
        let shape = shapes[i];
        let points = shape.getPoints();

        if (0) {
          let points3D = points.map(p => new Vector3(p.x, p.y, 0));
          let geometry = new Geometry();
          points3D.forEach(p => geometry.vertices.push(p));
          geometry.translate(xMid, 0, 0);

          let line = new MeshLine();
          line.setGeometry(geometry);

          const dashArray = 2;
          // Start to 0 and will be decremented to show the dashed line
          const dashOffset = 0.5;
          // The ratio between that is visible and other
          const dashRatio = 0.5;

          const material = new MeshLineMaterial({
            useMap: false,
            lineWidth: 0.05,
            dashArray,
            dashOffset,
            dashRatio, // The ratio between that is visible or not for each dash
            opacity,
            transparent: true,
            depthWrite: false,
            color: "#000000",
            // TODO: don't hard code value here.
            resolution: new Vector2(1920, 1080),
            sizeAttenuation: !false // Line width constant regardless distance
          });

          // new BufferGeometry().fromGeometry(line.geometry);
          let mesh = new Mesh(line.geometry, material); // this syntax could definitely be improved!
          this.add(mesh);

          // Text outline animation
          if (1) {
            const vals = { svg: 0 };
            gsap.to(vals, 5, {
              svg: 1,
              onUpdate: x => {
                material.uniforms.dashOffset.value = vals.svg;
              }
            });
          }

          continue;
        }

        let geometry = SVGLoader.pointsToStroke(points, style);

        geometry.translate(xMid, 0, 0);

        let strokeMesh = new Mesh(geometry, matDark);
        strokeText.add(strokeMesh);
      }
      this.add(strokeText);
    }
  }

  set text(text) {
    this.children.length = 0;

    if (1) {
      let totalWidth = 0;
      const letters = [...text];
      const letterSize = [];
      let minY = 999,
        maxY = -999;
      letters.forEach(letter => {
        if (letter === " ") {
          totalWidth += this.size * 0.5;
        } else {
          const geom = new THREE.ShapeBufferGeometry(
            this.font.generateShapes(letter, this.size, 1)
          );
          geom.computeBoundingBox();
          const mat = new MeshBasicMaterial({
            color: this.color
            // wireframe,
          });
          const mesh = new Mesh(geom, mat);

          // mesh.position.x = basePosition;
          letterSize.push(totalWidth);
          totalWidth += geom.boundingBox.max.x + this.letterSpacing;

          minY = Math.min(minY, geom.boundingBox.min.y);
          maxY = Math.max(maxY, geom.boundingBox.max.y);
          // minX

          this.add(mesh);
        }
      });

      this.children.forEach((letter, i) => {
        letter.position.set(
          -0.5 * totalWidth + letterSize[i],
          -0.5 * (maxY - minY),
          0
        );
      });
    } else {
      // Generate text shapes
      const shapes = this.font.generateShapes(text, this.size);

      // Compute xMid
      const geometry = new ShapeBufferGeometry(shapes);
      geometry.computeBoundingBox();
      const xMid =
        -0.5 * (geometry.boundingBox.max.x - geometry.boundingBox.min.x);
      const yMid =
        -0.5 * (geometry.boundingBox.max.y - geometry.boundingBox.min.y);

      // Text shapes
      shapes.forEach((shape, i) => {
        let geometry;

        if (1) {
          geometry = new ShapeBufferGeometry(shape);
        } else {
          // Geometry reshape
          const extrudeSettings = {
            steps: 2,
            depth: 0.1,

            bevelEnabled: false,
            bevelThickness: 1,
            bevelSize: 1,
            bevelOffset: 0,
            bevelSegments: 1
          };

          geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
        }

        // Shift letter to position whole text into center
        geometry.translate(xMid, yMid, 0);

        // Separate material for animation
        const material = new MeshBasicMaterial({
          color: this.color,
          transparent: true
        });

        const mesh = new Mesh(geometry, material);

        // mesh.position.x = this.basePosition;
        // this.basePosition += geometry.boundingBox.max.x + letterSpacing;
        this.add(mesh);
      });
    }
  }
}
