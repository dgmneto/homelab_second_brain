// Renders out/assembly.glb (written by build_case.py) to out/*.png.
// Headless Chromium via Playwright + three.js loaded from jsDelivr (needs network).
//   node render.mjs
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const OUT = join(dirname(fileURLToPath(import.meta.url)), "out");

const COMPONENTS = ["drive0", "drive1", "drive2", "drive3", "psu", "zimaboard", "hba", "fan120", "fan80"];
const SHELVES = ["board_shelf", "hba_shelf"];
// dir = camera position relative to the target (Z up; front panel faces -Y, west is -X)
const VIEWS = [
  { file: "open.png", show: ["tray", ...SHELVES, ...COMPONENTS], dir: [-0.7, -1.2, 1.1] },
  { file: "open_rear.png", show: ["tray", ...SHELVES, ...COMPONENTS], dir: [0.7, 1.2, 1.0] },
  { file: "top.png", show: ["tray", ...SHELVES, ...COMPONENTS], dir: [0, -0.0001, 1] },
  { file: "column_section.png", show: ["tray", ...SHELVES, "psu", "zimaboard", "hba", "fan80"], dir: [-1, 0.15, 0.25],
    clipX: 3.0 },
  { file: "cage_section.png", show: ["tray", "lid", ...COMPONENTS], dir: [0, -1, 0.15], clipY: 100 },
  { file: "closed_front.png", show: ["tray", "lid"], dir: [-0.6, -1.3, 0.55] },
  { file: "closed_rear.png", show: ["tray", "lid"], dir: [0.6, 1.3, 0.6] },
  { file: "tray_only.png", show: ["tray"], dir: [0.6, -1.0, 1.3] },
  { file: "shelves.png", show: SHELVES, dir: [-1, -1, 1.2] },
  { file: "lid.png", show: ["lid_print"], dir: [-1, -1, 1.2] },
];

const html = `<!doctype html><html><body style="margin:0;background:#fff">
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
window.setup = async (b64) => {
  const buf = Uint8Array.from(atob(b64), c => c.charCodeAt(0)).buffer;
  const gltf = await new GLTFLoader().parseAsync(buf, "");
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xffffff);
  scene.add(gltf.scene);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x666666, 1.6));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6);
  scene.add(sun);
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setSize(1400, 1000);
  renderer.localClippingEnabled = true;
  document.body.appendChild(renderer.domElement);
  const parts = {};
  gltf.scene.traverse(o => {
    if (o.isMesh) {
      o.material = o.material.clone();
      o.material.side = THREE.DoubleSide;
      o.material.metalness = 0; o.material.roughness = 0.8;
      let n = o; while (n && !n.name) n = n.parent;
      parts[n.name] = o;
    }
  });
  window.view = (v) => {
    const box = new THREE.Box3();
    const planes = [];
    if (v.clipX !== undefined) planes.push(new THREE.Plane(new THREE.Vector3(1, 0, 0), -v.clipX));
    if (v.clipY !== undefined) planes.push(new THREE.Plane(new THREE.Vector3(0, 1, 0), -v.clipY));
    for (const [n, o] of Object.entries(parts)) {
      o.visible = v.show.includes(n);
      o.material.clippingPlanes = planes;
      if (o.visible) box.expandByObject(o);
    }
    const c = box.getCenter(new THREE.Vector3());
    const r = box.getSize(new THREE.Vector3()).length() / 2;
    const d = new THREE.Vector3(...v.dir).normalize();
    const asp = 1.4;
    const cam = new THREE.OrthographicCamera(-r * 1.05 * asp, r * 1.05 * asp, r * 1.05, -r * 1.05, 0.1, 10 * r);
    cam.up.set(0, 0, 1);
    cam.position.copy(c).addScaledVector(d, 4 * r);
    cam.lookAt(c);
    sun.position.copy(cam.position).add(new THREE.Vector3(-r, -r, 3 * r));
    renderer.render(scene, cam);
    return Object.keys(parts);
  };
  return Object.keys(parts);
};
window.ready = true;
</script></body></html>`;

const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
await page.setContent(html);
await page.waitForFunction(() => window.ready === true);
const names = await page.evaluate((b64) => window.setup(b64), readFileSync(join(OUT, "assembly.glb")).toString("base64"));
console.log("nodes:", names.join(", "));
for (const v of VIEWS) {
  await page.evaluate((v) => window.view(v), v);
  await page.locator("canvas").screenshot({ path: join(OUT, v.file) });
  console.log("wrote", v.file);
}
await browser.close();
