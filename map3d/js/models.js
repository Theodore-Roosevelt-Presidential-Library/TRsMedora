// Detailed (photo-informed) building models, streets and the train for the 3D view.
// Everything is procedural: canvas textures + simple geometry, merged per building and material.
import * as THREE from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';

// ---------------------------------------------------------------- textures
function canvasTex(w, h, draw, repeatM = [2, 2], srgb = true) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); draw(g, w, h);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.repeat.set(1 / repeatM[0], 1 / repeatM[1]);
  return t;
}
const rnd = (() => { let s = 1234567; return () => ((s = (s * 16807) % 2147483647) / 2147483647); })();
function noise(g, w, h, a = 18, n = 4000) {
  for (let i = 0; i < n; i++) { const v = (rnd() - 0.5) * a; g.fillStyle = `rgba(${v > 0 ? 255 : 0},${v > 0 ? 255 : 0},${v > 0 ? 255 : 0},${Math.abs(v) / 255})`; g.fillRect(rnd() * w, rnd() * h, 1 + rnd() * 2, 1 + rnd() * 2); }
}
// textures are drawn in mid-grey/white so the material colour tints them
const TEX = {};
export function makeTextures() {
  // clapboard / drop siding: 2 m tile, boards 0.12 m
  TEX.clapboard = canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = '#fff'; g.fillRect(0, 0, w, h);
    for (let y = 0; y < h; y += h / 16) { const grd = g.createLinearGradient(0, y, 0, y + h / 16); grd.addColorStop(0, '#d8d8d8'); grd.addColorStop(0.15, '#fff'); grd.addColorStop(1, '#ececec'); g.fillStyle = grd; g.fillRect(0, y, w, h / 16); }
    noise(g, w, h, 20, 3000);
  });
  TEX.drop = canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = '#fff'; g.fillRect(0, 0, w, h);
    for (let y = 0; y < h; y += h / 14) { g.fillStyle = '#cfcfcf'; g.fillRect(0, y, w, 3); g.fillStyle = '#f2f2f2'; g.fillRect(0, y + 3, w, 3); }
    noise(g, w, h, 18, 3000);
  });
  TEX.boardbatten = canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = '#f4f4f4'; g.fillRect(0, 0, w, h);
    for (let x = 0; x < w; x += w / 8) { g.fillStyle = '#d0d0d0'; g.fillRect(x, 0, 3, h); g.fillStyle = '#fff'; g.fillRect(x + 3, 0, 9, h); g.fillStyle = '#c4c4c4'; g.fillRect(x + 12, 0, 2, h); }
    noise(g, w, h, 26, 5000);
  });
  const brick = (base, mortar) => canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = mortar; g.fillRect(0, 0, w, h);
    const bh = h / 26, bw = w / 10;
    for (let r = 0; r < 26; r++) for (let c = -1; c < 11; c++) {
      const x = c * bw + (r % 2) * bw / 2, v = 0.85 + rnd() * 0.3;
      g.fillStyle = `rgb(${base[0] * v | 0},${base[1] * v | 0},${base[2] * v | 0})`; g.fillRect(x + 1, r * bh + 1, bw - 2, bh - 2);
    }
    noise(g, w, h, 20, 2000);
  });
  TEX.brick = brick([255, 255, 255], '#bdb6aa');
  TEX.yellowbrick = TEX.brick;
  TEX.log = canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = '#777'; g.fillRect(0, 0, w, h);
    for (let y = 0; y < h; y += h / 7) { const grd = g.createLinearGradient(0, y, 0, y + h / 7); grd.addColorStop(0, '#888'); grd.addColorStop(0.5, '#fff'); grd.addColorStop(1, '#7a7a7a'); g.fillStyle = grd; g.fillRect(0, y + 2, w, h / 7 - 4); }
    noise(g, w, h, 40, 6000);
  });
  TEX.shingle = canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = '#ddd'; g.fillRect(0, 0, w, h);
    const rh = h / 16;
    for (let r = 0; r < 16; r++) { let x = (r % 2) * 9 - 9; while (x < w) { const sw = 10 + rnd() * 14, v = 170 + rnd() * 70 | 0; g.fillStyle = `rgb(${v},${v},${v})`; g.fillRect(x, r * rh, sw - 1.5, rh - 2); g.fillStyle = 'rgba(0,0,0,.35)'; g.fillRect(x, r * rh + rh - 2, sw, 2); x += sw; } }
    noise(g, w, h, 25, 3000);
  });
  TEX.tin = canvasTex(256, 256, (g, w, h) => { g.fillStyle = '#ddd'; g.fillRect(0, 0, w, h); for (let x = 0; x < w; x += w / 10) { g.fillStyle = '#bbb'; g.fillRect(x, 0, 2, h); } noise(g, w, h, 18, 2000); });
  TEX.sod = canvasTex(256, 256, (g, w, h) => { g.fillStyle = '#8a8a6a'; g.fillRect(0, 0, w, h); noise(g, w, h, 60, 9000); });
  TEX.plank = canvasTex(256, 256, (g, w, h) => {
    for (let x = 0; x < w; x += w / 9) { const v = 150 + rnd() * 60 | 0; g.fillStyle = `rgb(${v},${v * .9 | 0},${v * .78 | 0})`; g.fillRect(x, 0, w / 9 - 2, h); }
    noise(g, w, h, 30, 4000);
  }, [2, 2]);
  TEX.dirt = canvasTex(512, 512, (g, w, h) => {
    g.fillStyle = '#b9a385'; g.fillRect(0, 0, w, h);
    noise(g, w, h, 50, 20000);
    // wheel ruts and hoof-trodden centre (u = across the road, 0..1 over the road width)
    for (const x of [0.33, 0.67]) { const grd = g.createLinearGradient((x - .06) * w, 0, (x + .06) * w, 0); grd.addColorStop(0, 'rgba(90,70,50,0)'); grd.addColorStop(.5, 'rgba(90,70,50,.35)'); grd.addColorStop(1, 'rgba(90,70,50,0)'); g.fillStyle = grd; g.fillRect((x - .06) * w, 0, .12 * w, h); }
    const e = g.createLinearGradient(0, 0, w, 0); e.addColorStop(0, 'rgba(150,160,110,.9)'); e.addColorStop(.12, 'rgba(150,160,110,0)'); e.addColorStop(.88, 'rgba(150,160,110,0)'); e.addColorStop(1, 'rgba(150,160,110,.9)'); g.fillStyle = e; g.fillRect(0, 0, w, h);
  }, [1, 12]);
  TEX.grass = canvasTex(512, 512, (g, w, h) => {
    g.fillStyle = '#c8c8c8'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 9000; i++) { const v = 150 + rnd() * 105 | 0; g.strokeStyle = `rgba(${v},${v},${v},.7)`; const x = rnd() * w, y = rnd() * h; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (rnd() - .5) * 4, y - 3 - rnd() * 5); g.stroke(); }
    for (let i = 0; i < 160; i++) { g.fillStyle = 'rgba(110,105,90,.35)'; g.beginPath(); g.arc(rnd() * w, rnd() * h, 3 + rnd() * 8, 0, 7); g.fill(); }   // sagebrush clumps
  }, [9, 9]);
  TEX.ballast = canvasTex(256, 256, (g, w, h) => { g.fillStyle = '#8c8578'; g.fillRect(0, 0, w, h); noise(g, w, h, 70, 9000); }, [2, 2]);
  // windows: 2-over-2 sash, white frame, dark glass with a little sky reflection
  const win = (arched) => canvasTex(128, 208, (g, w, h) => {
    g.fillStyle = '#f4f1e8'; g.fillRect(0, 0, w, h);
    const gx = 12, gy = arched ? 30 : 12, gw = w - 24, gh = h - gy - 14;
    const grd = g.createLinearGradient(0, gy, 0, gy + gh); grd.addColorStop(0, '#6f7c84'); grd.addColorStop(.45, '#2c3438'); grd.addColorStop(1, '#1d2326');
    g.fillStyle = grd;
    if (arched) { g.beginPath(); g.moveTo(gx, gy + 12); g.quadraticCurveTo(w / 2, gy - 22, gx + gw, gy + 12); g.lineTo(gx + gw, gy + gh); g.lineTo(gx, gy + gh); g.fill(); }
    else g.fillRect(gx, gy, gw, gh);
    g.fillStyle = '#f4f1e8'; g.fillRect(w / 2 - 3, gy, 6, gh); g.fillRect(gx, gy + gh / 2 - 4, gw, 8);
    g.fillStyle = 'rgba(0,0,0,.35)'; g.fillRect(0, h - 8, w, 8);
  }, [1, 1]);
  TEX.window = win(false); TEX.windowArched = win(true);
  TEX.window.repeat.set(1, 1); TEX.windowArched.repeat.set(1, 1);
  TEX.windowLancet = canvasTex(96, 320, (g, w, h) => {   // tall pointed (lancet) window, St. Mary's
    g.fillStyle = '#f1ece0'; g.fillRect(0, 0, w, h);
    const grd = g.createLinearGradient(0, 0, 0, h); grd.addColorStop(0, '#6f7c84'); grd.addColorStop(.4, '#2c3438'); grd.addColorStop(1, '#1d2326'); g.fillStyle = grd;
    g.beginPath(); g.moveTo(10, h - 12); g.lineTo(10, 70); g.quadraticCurveTo(12, 22, w / 2, 8); g.quadraticCurveTo(w - 12, 22, w - 10, 70); g.lineTo(w - 10, h - 12); g.fill();
    g.fillStyle = '#f1ece0'; g.fillRect(w / 2 - 2, 20, 4, h - 32); for (let y = 90; y < h - 20; y += 52) g.fillRect(10, y, w - 20, 3);
  }, [1, 1]); TEX.windowLancet.repeat.set(1, 1);
  TEX.blindArch = canvasTex(96, 128, (g, w, h) => {   // a pointed blind arch in the brickwork over a door (St. Mary's, 1886)
    g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h); g.strokeStyle = '#8f8a82'; g.lineWidth = 7;
    g.beginPath(); g.moveTo(8, h); g.lineTo(8, 60); g.quadraticCurveTo(10, 14, w / 2, 5); g.quadraticCurveTo(w - 10, 14, w - 8, 60); g.lineTo(w - 8, h); g.stroke();
  }, [1, 1]); TEX.blindArch.repeat.set(1, 1);
  TEX.vlog = canvasTex(256, 256, (g, w, h) => {   // vertical cedar logs, stockade style (Cantonment)
    g.fillStyle = '#6a6a6a'; g.fillRect(0, 0, w, h);
    for (let x = 0; x < w; x += w / 9) { const grd = g.createLinearGradient(x, 0, x + w / 9, 0); grd.addColorStop(0, '#777'); grd.addColorStop(.5, '#f2f2f2'); grd.addColorStop(1, '#7c7c7c'); g.fillStyle = grd; g.fillRect(x + 1, 0, w / 9 - 2, h); }
    noise(g, w, h, 45, 7000);
  });
  TEX.boards = canvasTex(256, 256, (g, w, h) => {   // roof of boards laid eave to ridge (Little Missouri depot, 1881)
    g.fillStyle = '#eee'; g.fillRect(0, 0, w, h);
    for (let x = 0; x < w; x += w / 10) { const v = 200 + rnd() * 50 | 0; g.fillStyle = `rgb(${v},${v},${v})`; g.fillRect(x, 0, w / 10 - 3, h); g.fillStyle = '#9a9a9a'; g.fillRect(x + w / 10 - 3, 0, 3, h); }
    noise(g, w, h, 25, 3000);
  });
  TEX.door = canvasTex(128, 256, (g, w, h) => {
    g.fillStyle = '#efece4'; g.fillRect(0, 0, w, h); g.fillStyle = '#5b4535'; g.fillRect(10, 10, w - 20, h - 10);
    g.fillStyle = '#3e2f25'; [[22, 26, 36, 70], [70, 26, 36, 70], [22, 120, 36, 110], [70, 120, 36, 110]].forEach(r => g.fillRect(...r));
    g.fillStyle = '#c9a54a'; g.fillRect(w - 30, 135, 6, 6);
  }, [1, 1]); TEX.door.repeat.set(1, 1);
  TEX.storefront = canvasTex(256, 192, (g, w, h) => {
    g.fillStyle = '#efece4'; g.fillRect(0, 0, w, h);
    const grd = g.createLinearGradient(0, 0, 0, h); grd.addColorStop(0, '#5f6c73'); grd.addColorStop(.5, '#262e32'); grd.addColorStop(1, '#1b2124'); g.fillStyle = grd;
    g.fillRect(10, 14, 90, 120); g.fillRect(156, 14, 90, 120);
    g.fillStyle = '#5b4535'; g.fillRect(108, 10, 40, h - 10);
    g.fillStyle = '#efece4'; [55, 201].forEach(x => g.fillRect(x - 2, 14, 4, 120));
    g.fillStyle = '#8a7a66'; g.fillRect(0, 140, w, h - 140);
  }, [1, 1]); TEX.storefront.repeat.set(1, 1);
  TEX.coach = canvasTex(512, 128, (g, w, h) => {
    g.fillStyle = '#5a3a26'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#c9a54a'; g.fillRect(0, 20, w, 3); g.fillRect(0, 92, w, 3);
    for (let x = 22; x < w - 20; x += 30) { g.fillStyle = '#20282b'; g.fillRect(x, 32, 18, 44); g.fillStyle = '#7a5a3a'; g.fillRect(x - 6, 32, 4, 44); }
    noise(g, w, h, 16, 1500);
  }, [1, 1]); TEX.coach.repeat.set(1, 1);
  return TEX;
}

// ---------------------------------------------------------------- geometry helpers (local metres; three: x=E, y=up, z=-N)
const V = (e, n, u) => new THREE.Vector3(e, u, -n);
function quad(a, b, c, d, uvA, uvB, uvC, uvD) {          // a-b-c-d counter-clockwise seen from outside
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute([a, b, c, a, c, d].flatMap(p => [p.x, p.y, p.z]), 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute([uvA, uvB, uvC, uvA, uvC, uvD].flat(), 2));
  g.computeVertexNormals(); return g;
}
function tri(a, b, c, uvA, uvB, uvC) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute([a, b, c].flatMap(p => [p.x, p.y, p.z]), 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute([uvA, uvB, uvC].flat(), 2));
  g.computeVertexNormals(); return g;
}
function box(cx, cy, cz, sx, sy, sz, rotY = 0) {           // centred box with uvs in metres
  const g = new THREE.BoxGeometry(sx, sy, sz).toNonIndexed();
  const uv = g.attributes.uv, pos = g.attributes.position, nrm = g.attributes.normal;
  for (let i = 0; i < uv.count; i++) {
    const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i), nx = Math.abs(nrm.getX(i)), ny = Math.abs(nrm.getY(i));
    if (ny > .5) uv.setXY(i, x, z); else if (nx > .5) uv.setXY(i, z, y); else uv.setXY(i, x, y);
  }
  g.rotateY(rotY); g.translate(cx, cy, cz); return g;
}
class Bucket {                                             // collects geometries per material, merges at the end
  constructor() { this.m = new Map(); }
  add(key, geo) { if (!this.m.has(key)) this.m.set(key, []); this.m.get(key).push(geo.index ? geo.toNonIndexed() : geo); }
  meshes(mats, opts = {}) {
    const out = [];
    for (const [k, gs] of this.m) {
      const geo = mergeGeometries(gs.map(g => { if (!g.attributes.uv) g.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(g.attributes.position.count * 2), 2)); return g; }), false);
      const mesh = new THREE.Mesh(geo, mats(k)); mesh.castShadow = opts.cast !== false; mesh.receiveShadow = true; out.push(mesh);
    }
    return out;
  }
}

// ---------------------------------------------------------------- materials (cached by key)
const MATS = new Map(); const SIGNS = {};
function signText(f) {
  const n = (f.name || '').replace(/\(.*?\)/g, '').replace(/["']/g, '').trim();
  // Guesses only. Buildings whose photographs show no sign (Hotel de Mores, the company store, the
  // Pyramid Park Hotel) or illegible lettering (the Cow Boy office roof) are left out on purpose.
  const map = [[/Ferris/i, 'J. A. FERRIS'], [/Metropolitan/i, 'METROPOLITAN HOTEL'], [/Malloy/i, 'MALLOY HOUSE'], [/roller rink/i, 'ROLLER RINK'],
    [/drug/i, 'DRUGS'], [/Fisher/i, 'J. C. FISHER'], [/Nelson/i, 'JOHN NELSON'], [/saloon/i, 'SALOON']];
  for (const [re, t] of map) if (re.test(n)) return t; return null;
}
// signs read off the period photographs
function signTex(sg) {
  const W = sg.aspect < 0.1 ? 4096 : 2048, Hh = Math.round(W * sg.aspect);
  return canvasTex(W, Hh, (g) => {
    if (sg.id === 'medora-depot') {
      // Huffman 1886 (MHS 72461): dark board, white letters, MEDORA with St. Paul and Portland mileboards at the ends
      g.fillStyle = '#1e1d1b'; g.fillRect(0, 0, W, Hh); g.strokeStyle = '#d9d4c6'; g.lineWidth = 10; g.strokeRect(10, 10, W - 20, Hh - 20);
      g.fillStyle = '#ece7da'; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.font = `bold ${Math.round(Hh * 0.62)}px Georgia`; g.fillText('M E D O R A', W / 2, Hh / 2 + 4);
      g.font = `bold ${Math.round(Hh * 0.24)}px Georgia`; g.fillText('ST. PAUL', W * 0.105, Hh * 0.36, W * 0.17); g.fillText('PORTLAND', W * 0.895, Hh * 0.36, W * 0.17);
      g.fillRect(W * 0.04, Hh * 0.62, W * 0.14, 6); g.fillRect(W * 0.82, Hh * 0.62, W * 0.14, 6);   // mileage figures: not legible in the scan
      g.fillRect(W * 0.205, 20, 6, Hh - 40); g.fillRect(W * 0.79, 20, 6, Hh - 40);
    } else if (sg.id === 'pp-rentfree') {
      // SHSND 00042-00180: long white banner, two lines, RENT FREE in large letters at the right
      g.fillStyle = '#e8e2d2'; g.fillRect(0, 0, W, Hh); g.fillStyle = '#1d1b19'; g.textBaseline = 'middle';
      g.font = `bold ${Math.round(Hh * 0.42)}px Arial`; g.textAlign = 'left';
      g.fillText('THIS BUILDING WITH MACHINERY  |  WILL BE FURNISHED', W * 0.01, Hh * 0.3, W * 0.8);
      g.font = `bold ${Math.round(Hh * 0.3)}px Arial`; g.fillText('TO ANY RESPONSIBLE PARTY WHO WILL START  |  ANY INDUSTRY THEREIN.', W * 0.01, Hh * 0.75, W * 0.8);
      g.font = `bold ${Math.round(Hh * 0.66)}px Arial`; g.textAlign = 'right'; g.fillText('RENT FREE', W * 0.995, Hh * 0.53, W * 0.17);
      g.fillRect(W * 0.82, 0, 4, Hh);
    } else {
      g.fillStyle = sg.bg || '#2e2a25'; g.fillRect(0, 0, W, Hh); g.fillStyle = sg.fg || '#efe6cf'; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.font = `bold ${Math.round(Hh * 0.6)}px Georgia`; g.fillText(sg.text || '', W / 2, Hh / 2);
    }
  }, [1, 1]);
}
function mat(key, grade) {
  const k = key + '|' + grade;
  if (MATS.has(k)) return MATS.get(k);
  const isSign = key.startsWith('sign:') || key.startsWith('signguess:');
  const [kind, color] = isSign ? ['sign', null] : key.split('#');
  const col = color ? new THREE.Color('#' + color) : new THREE.Color(0xffffff);
  const map = {wall_clapboard: TEX.clapboard, wall_drop: TEX.drop, wall_boardbatten: TEX.boardbatten, wall_brick: TEX.brick, wall_yellowbrick: TEX.yellowbrick, wall_log: TEX.log,
    roof_shingle: TEX.shingle, roof_tin: TEX.tin, roof_sod: TEX.sod, roof_boards: TEX.boards, wall_vlog: TEX.vlog, blindArch: TEX.blindArch, window: TEX.window, windowArched: TEX.windowArched, windowLancet: TEX.windowLancet, door: TEX.door, storefront: TEX.storefront,
    plank: TEX.plank, trim: null, stone: null, dark: null, coach: TEX.coach}[kind] || (isSign ? SIGNS[key] : undefined);
  const m = new THREE.MeshStandardMaterial({color: col, map: map || null, roughness: kind.startsWith('roof_tin') ? 0.55 : 0.92, metalness: kind === 'roof_tin' ? 0.3 : 0, side: THREE.DoubleSide});
  // confidence is shown by a marker above the building, not by transparency
  MATS.set(k, m); return m;
}

// ---------------------------------------------------------------- buildings
const DIRS = {N: [0, 1], S: [0, -1], E: [1, 0], W: [-1, 0]};
function rectFrame(R) {
  // R: 4 corners [e,n]; returns centre, long unit vector u, short unit vector v, length L, width W
  const c = R.reduce((s, p) => [s[0] + p[0] / 4, s[1] + p[1] / 4], [0, 0]);
  const e0 = [R[1][0] - R[0][0], R[1][1] - R[0][1]], e1 = [R[2][0] - R[1][0], R[2][1] - R[1][1]];
  const l0 = Math.hypot(...e0), l1 = Math.hypot(...e1);
  const [lv, ll, sv, sl] = l0 >= l1 ? [e0, l0, e1, l1] : [e1, l1, e0, l0];
  return {c, u: [lv[0] / ll, lv[1] / ll], v: [sv[0] / sl, sv[1] / sl], L: ll, W: sl};
}
const P2 = (f, a, b) => [f.c[0] + f.u[0] * a + f.v[0] * b, f.c[1] + f.u[1] * a + f.v[1] * b];   // local (along, across) -> e,n

let ctxZ = null;
// a straight timber between two points (three-space vectors), square section t
function beam(p, q, t) {
  const d = new THREE.Vector3().subVectors(q, p), L = d.length();
  const g = new THREE.BoxGeometry(t, t, L).toNonIndexed();
  const m = new THREE.Matrix4().lookAt(new THREE.Vector3(0, 0, 0), d, Math.abs(d.y) / L > 0.99 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0));
  g.applyMatrix4(m); const c = p.clone().add(q).multiplyScalar(0.5); g.translate(c.x, c.y, c.z); return g;
}
function buildFrame(bk, R, z0, fr, key) {
  // R: 4 corners; the frame's bents run across the short side, posts stand along both long sides
  const P = R.map(p => [p[0], p[1]]), d01 = Math.hypot(P[1][0] - P[0][0], P[1][1] - P[0][1]), d12 = Math.hypot(P[2][0] - P[1][0], P[2][1] - P[1][1]);
  const [A, B, C, D] = d01 >= d12 ? P : [P[1], P[2], P[3], P[0]];            // A-B and D-C are the long sides
  const lerp = (p, q, t) => [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t];
  const nA = Math.max(2, fr.posts_along || 6), nX = Math.max(2, fr.posts_across || 2), ph = fr.post_h || 6, t = fr.size || 0.22, sill = z0 + 0.15;
  const rise = fr.roof === 'rafters' ? (fr.rafter_rise || 2.5) : 0;
  for (let i = 0; i < nA; i++) {
    const u = i / (nA - 1), a = lerp(A, B, u), b = lerp(D, C, u);
    for (let j = 0; j < nX; j++) { const q = lerp(a, b, j / (nX - 1)); bk.add(key, beam(V(q[0], q[1], sill), V(q[0], q[1], sill + ph), t)); }
    bk.add(key, beam(V(a[0], a[1], sill + ph), V(b[0], b[1], sill + ph), t * 0.9));           // tie beam of the bent
    if (fr.mid_tie) bk.add(key, beam(V(a[0], a[1], sill + ph * 0.5), V(b[0], b[1], sill + ph * 0.5), t * 0.8));
    if (fr.braces !== false) {                                                                // knee braces at both posts
      const kb = Math.min(1.2, ph * 0.2), w = Math.hypot(b[0] - a[0], b[1] - a[1]), ua = [(b[0] - a[0]) / w, (b[1] - a[1]) / w];
      bk.add(key, beam(V(a[0], a[1], sill + ph - kb), V(a[0] + ua[0] * kb, a[1] + ua[1] * kb, sill + ph), t * 0.6));
      bk.add(key, beam(V(b[0], b[1], sill + ph - kb), V(b[0] - ua[0] * kb, b[1] - ua[1] * kb, sill + ph), t * 0.6));
    }
    if (rise > 0) { const m = lerp(a, b, 0.5); bk.add(key, beam(V(a[0], a[1], sill + ph), V(m[0], m[1], sill + ph + rise), t * 0.7)); bk.add(key, beam(V(b[0], b[1], sill + ph), V(m[0], m[1], sill + ph + rise), t * 0.7)); }
  }
  for (const [p, q] of [[A, B], [D, C]]) { bk.add(key, beam(V(p[0], p[1], sill), V(q[0], q[1], sill), t)); bk.add(key, beam(V(p[0], p[1], sill + ph), V(q[0], q[1], sill + ph), t)); }   // sills and plates
  for (const [p, q] of [[A, D], [B, C]]) bk.add(key, beam(V(p[0], p[1], sill), V(q[0], q[1], sill), t));
  if (rise > 0) { const m1 = lerp(A, D, 0.5), m2 = lerp(B, C, 0.5); bk.add(key, beam(V(m1[0], m1[1], sill + ph + rise), V(m2[0], m2[1], sill + ph + rise), t * 0.8)); }   // ridge piece
  if (fr.girts) for (const [p, q] of [[A, B], [D, C], [A, D], [B, C]]) bk.add(key, beam(V(p[0], p[1], sill + ph * 0.5), V(q[0], q[1], sill + ph * 0.5), t * 0.7));
}
// polygon (convex, ordered) as a triangle fan
function poly(pts, uvs) {
  const g = new THREE.BufferGeometry(), P = [], U = [];
  for (let i = 1; i < pts.length - 1; i++) { for (const k of [0, i, i + 1]) { P.push(pts[k].x, pts[k].y, pts[k].z); U.push(...uvs[k]); } }
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(U, 2)); g.computeVertexNormals(); return g;
}
function buildBlock(bk, f, st, z0, H, R, frontDir, grade, ridgeAbs) {
  // one rectangular building block: walls, gables, roof, windows, doors, porch, chimneys, extras
  const F = rectFrame(R), hl = F.L / 2, hw = F.W / 2;
  const wallKey = `wall_${st.wall}#${(st.wall_color || '#e9e3d6').slice(1)}`;
  const trimKey = `trim#${(st.trim || '#f3efe6').slice(1)}`;
  const roofKey = `roof_${st.roof || 'shingle'}#${(st.roof_color || (st.roof === 'tin' ? '#8d9296' : st.roof === 'sod' ? '#7d7a58' : st.roof === 'boards' ? '#b9b1a2' : '#6e655c')).slice(1)}`;
  const timberKey = `trim#${(st.timber || st.trim || '#6b5a48').slice(1)}`;
  // faces in local frame: +v side, -v side (long faces), +u end, -u end (short faces)
  const faces = [
    {name: '+v', a: [-hl, hw], b: [hl, hw], n: F.v, len: F.L, long: true},
    {name: '-v', a: [hl, -hw], b: [-hl, -hw], n: [-F.v[0], -F.v[1]], len: F.L, long: true},
    {name: '+u', a: [hl, hw], b: [hl, -hw], n: F.u, len: F.W, long: false},
    {name: '-u', a: [-hl, -hw], b: [-hl, hw], n: [-F.u[0], -F.u[1]], len: F.W, long: false},
  ];
  const toward = (d) => { let fc = faces[0], best = -9; for (const x of faces) { const dd = x.n[0] * d[0] + x.n[1] * d[1]; if (dd > best) { best = dd; fc = x; } } return fc; };
  const front = frontDir ? toward(frontDir) : faces[1];
  // ridge axis: 'long' runs along u; 'front' runs perpendicular to the front face
  let ridgeAlongU = true;
  if (st.ridge === 'front') ridgeAlongU = !front.long;
  if (st.ridge === 'cross') ridgeAlongU = front.long;
  const roofType = st.ridge === 'flat' ? 'flat' : st.ridge === 'hip' ? 'hip' : st.ridge === 'shed' ? 'shed' : 'gable';
  const span = ridgeAlongU ? F.W : F.L;
  const rise = st.rise ?? (ridgeAbs > H + 0.3 ? ridgeAbs - H : Math.min(span * 0.42, 4.5));
  const ridgeH = roofType === 'flat' ? H : H + (roofType === 'shed' ? Math.min(rise, span * 0.3) : rise);
  const L3 = (a, b, h) => { const p = P2(F, a, b); return V(p[0], p[1], z0 + h); };
  const rotU = Math.atan2(F.u[1], F.u[0]);
  // shed roof: which long/short face is the high side
  const shedHigh = roofType === 'shed' ? toward(DIRS[st.shed_high] || [-front.n[0], -front.n[1]]) : null;
  const shedH = (pt) => { // height of a shed roof at local point pt
    const hn = [shedHigh.n[0] * F.u[0] + shedHigh.n[1] * F.u[1], shedHigh.n[0] * F.v[0] + shedHigh.n[1] * F.v[1]];
    const ext = Math.abs(hn[0]) > .5 ? hl : hw, s = (pt[0] * hn[0] + pt[1] * hn[1]) / ext;   // -1 .. 1
    return H + (ridgeH - H) * (s + 1) / 2;
  };
  // jerkinhead (clipped) gable ends
  const jerk = new Set((st.jerkin || []).map(d => toward(DIRS[d]).name));
  const clip = st.jerkin_clip ?? 0.3;
  // with a deep overhang the roof plane passes above the wall plate at the wall line: carry the walls up to meet it
  // (closes the open wedge under the eaves and behind the gable rakes, through which the attic showed)
  const oW = st.overhang ?? 0.35, RBw = ridgeAlongU ? hw : hl, bEw = RBw + oW;
  const wallTop = (roofType === 'gable') ? Math.max(H, (H - 0.15) + (ridgeH - (H - 0.15)) * (1 - RBw / bEw)) : H;
  // walls (stone plinth below if asked)
  for (const fc of faces) {
    const A = fc.a, B = fc.b;
    if (roofType === 'shed') {
      const hA = shedH(A), hB = shedH(B);
      bk.add(wallKey, poly([L3(A[0], A[1], -0.4), L3(B[0], B[1], -0.4), L3(B[0], B[1], hB), L3(A[0], A[1], hA)], [[0, -0.4], [fc.len, -0.4], [fc.len, hB], [0, hA]]));
      continue;
    }
    const isGableEnd = roofType === 'gable' && ((ridgeAlongU && !fc.long) || (!ridgeAlongU && fc.long));
    const wt = (!isGableEnd && wallTop > H) ? wallTop : H;
    bk.add(wallKey, quad(L3(A[0], A[1], -0.4), L3(B[0], B[1], -0.4), L3(B[0], B[1], wt), L3(A[0], A[1], wt), [0, -0.4], [fc.len, -0.4], [fc.len, wt], [0, wt]));
    if (isGableEnd) {
      const m = [(A[0] + B[0]) / 2, (A[1] + B[1]) / 2];
      if (jerk.has(fc.name)) {
        const hc = ridgeH - clip * (ridgeH - H), k = clip;   // wall stops at hc; points on the rakes
        const pa = [A[0] + (m[0] - A[0]) * (1 - k), A[1] + (m[1] - A[1]) * (1 - k)], pb = [B[0] + (m[0] - B[0]) * (1 - k), B[1] + (m[1] - B[1]) * (1 - k)];
        bk.add(wallKey, poly([L3(A[0], A[1], H), L3(B[0], B[1], H), L3(pb[0], pb[1], hc), L3(pa[0], pa[1], hc)], [[0, H], [fc.len, H], [fc.len * (1 - (1 - k) / 2), hc], [fc.len * (1 - k) / 2, hc]]));
      } else if (wallTop > H + 0.02) {   // gable wall up to the underside of a deep-overhang roof
        const rh = (b) => (H - 0.15) + (ridgeH - (H - 0.15)) * (1 - Math.abs(b) / bEw), half = fc.len / 2;
        bk.add(wallKey, poly([L3(A[0], A[1], H), L3(B[0], B[1], H), L3(B[0], B[1], rh(half)), L3(m[0], m[1], ridgeH), L3(A[0], A[1], rh(half))], [[0, H], [fc.len, H], [fc.len, rh(half)], [half, ridgeH], [0, rh(half)]]));
      } else bk.add(wallKey, tri(L3(A[0], A[1], H), L3(B[0], B[1], H), L3(m[0], m[1], ridgeH), [0, H], [fc.len, H], [fc.len / 2, ridgeH]));
    }
  }
  if (st.plinth) {
    const ph = st.plinth.h || 0.9, key = `stone#${(st.plinth.color || '#a39882').slice(1)}`;
    for (const fc of faces) { const n = fc.n, o = .06, A = P2(F, ...fc.a), B = P2(F, ...fc.b);
      bk.add(key, quad(V(A[0] + n[0] * o, A[1] + n[1] * o, z0 - .4), V(B[0] + n[0] * o, B[1] + n[1] * o, z0 - .4), V(B[0] + n[0] * o, B[1] + n[1] * o, z0 + ph), V(A[0] + n[0] * o, A[1] + n[1] * o, z0 + ph), [0, 0], [1, 0], [1, 1], [0, 1])); }
  }
  // roof
  const o = st.overhang ?? 0.35, og = st.gable_overhang ?? o;
  const he = H - 0.15;
  if (roofType === 'flat') {
    bk.add(roofKey, quad(L3(-hl, -hw, H + .05), L3(hl, -hw, H + .05), L3(hl, hw, H + .05), L3(-hl, hw, H + .05), [-hl, -hw], [hl, -hw], [hl, hw], [-hl, hw]));
    const ph = st.parapet ?? 0.8;   // parapet / cornice all round
    if (ph > 0) for (const fc of faces) bk.add(wallKey, quad(L3(fc.a[0], fc.a[1], H), L3(fc.b[0], fc.b[1], H), L3(fc.b[0], fc.b[1], H + ph), L3(fc.a[0], fc.a[1], H + ph), [0, H], [fc.len, H], [fc.len, H + ph], [0, H + ph]));
    bk.add(trimKey, box(...(() => { const p = P2(F, 0, 0); return [p[0], z0 + H + ph, -p[1]]; })(), F.L + .3, .18, F.W + .3, rotU));
  } else if (roofType === 'shed') {
    const C = [[-hl - o, -hw - o], [hl + o, -hw - o], [hl + o, hw + o], [-hl - o, hw + o]];
    bk.add(roofKey, quad(...C.map(p => L3(p[0], p[1], shedH(p) + .05)), [0, 0], [F.L, 0], [F.L, F.W], [0, F.W]));
  } else if (roofType === 'hip') {
    let r0, r1; const k = Math.min(span / 2, (ridgeAlongU ? F.L : F.W) / 2 - 0.3);
    if (ridgeAlongU) { r0 = [-hl + k, 0]; r1 = [hl - k, 0]; } else { r0 = [0, -hw + k]; r1 = [0, hw - k]; }
    const C = [[-hl - o, -hw - o], [hl + o, -hw - o], [hl + o, hw + o], [-hl - o, hw + o]];
    const near = (p) => (Math.hypot(p[0] - r0[0], p[1] - r0[1]) < Math.hypot(p[0] - r1[0], p[1] - r1[1])) ? r0 : r1;
    for (let i = 0; i < 4; i++) {
      const p = C[i], q = C[(i + 1) % 4], np = near(p), nq = near(q);
      const run = Math.hypot(q[0] - p[0], q[1] - p[1]), slope = Math.hypot(span / 2 + o, ridgeH - he);
      if (np === nq) bk.add(roofKey, tri(L3(p[0], p[1], he), L3(q[0], q[1], he), L3(np[0], np[1], ridgeH), [0, 0], [run, 0], [run / 2, slope]));
      else bk.add(roofKey, quad(L3(p[0], p[1], he), L3(q[0], q[1], he), L3(nq[0], nq[1], ridgeH), L3(np[0], np[1], ridgeH), [0, 0], [run, 0], [run, slope], [0, slope]));
    }
    const rm = [(r0[0] + r1[0]) / 2, (r0[1] + r1[1]) / 2], rl = Math.hypot(r1[0] - r0[0], r1[1] - r0[1]);
    if (rl > 0.2) { const p = P2(F, rm[0], rm[1]); bk.add(roofKey, box(p[0], z0 + ridgeH + .03, -p[1], rl, .12, .3, ridgeAlongU ? rotU : Math.atan2(F.v[1], F.v[0]))); }
  } else {
    // gable roof as two planes, written in (a = along the ridge, b = across) and mapped to local (u, v)
    const RA = ridgeAlongU ? hl : hw, RB = ridgeAlongU ? hw : hl;
    const map = (a, b) => ridgeAlongU ? [a, b] : [b, a];
    const LL = (a, b, h) => L3(...map(a, b), h);
    // extensions past each gable end (roof_extend over an open platform)
    let ext = [og, og];
    const endFace = [toward(ridgeAlongU ? [-F.u[0], -F.u[1]] : [-F.v[0], -F.v[1]]), toward(ridgeAlongU ? F.u : F.v)];
    if (st.roof_extend) { const d = DIRS[st.roof_extend.end], s = (ridgeAlongU ? F.u : F.v); const sg = s[0] * d[0] + s[1] * d[1] > 0 ? 1 : 0; ext[sg] += st.roof_extend.len; }
    const bE = RB + o, slope = Math.hypot(bE, ridgeH - he);
    const hAt = (b) => he + (ridgeH - he) * (1 - Math.abs(b) / bE);
    for (const sgnB of [-1, 1]) {
      // plane outline from end 0 (a = -RA - ext0) to end 1
      const pts = [], uvs = [];
      const endPts = (e) => {   // e: 0 or 1 -> list of (a, b, h) for that end, going from eave to ridge
        const aE = e ? RA + ext[e] : -RA - ext[e];
        if (jerk.has(endFace[e].name)) {
          const hc = ridgeH - clip * (ridgeH - H), bc = bE * (ridgeH - hc) / (ridgeH - he), aR = aE - (e ? 1 : -1) * bc * 0.9;
          return [[aE, sgnB * bE, he], [aE, sgnB * bc, hc], [aR, 0, ridgeH]];
        }
        return [[aE, sgnB * bE, he], [aE, 0, ridgeH]];
      };
      const e0 = endPts(0), e1 = endPts(1);
      // order: eave end0 -> eave end1 -> (end1 up to ridge) -> ridge end0 -> (end0 down)
      const seq = [e0[0], e1[0], ...e1.slice(1), ...e0.slice(1).reverse()];
      for (const [a, b, h] of seq) { pts.push(LL(a, b, h)); uvs.push([a, (bE - Math.abs(b)) / bE * slope]); }
      bk.add(roofKey, poly(pts, uvs));
    }
    // hip triangles of clipped gables
    for (const e of [0, 1]) if (jerk.has(endFace[e].name)) {
      const aE = e ? RA + ext[e] : -RA - ext[e], hc = ridgeH - clip * (ridgeH - H), bc = bE * (ridgeH - hc) / (ridgeH - he), aR = aE - (e ? 1 : -1) * bc * 0.9;
      bk.add(roofKey, tri(LL(aE, -bc, hc), LL(aE, bc, hc), LL(aR, 0, ridgeH), [0, 0], [2 * bc, 0], [bc, bc]));
    }
    // ridge cap and fascia boards along the rakes
    const a0 = -RA - ext[0], a1 = RA + ext[1], pm = P2(F, ...map((a0 + a1) / 2, 0));
    bk.add(roofKey, box(pm[0], z0 + ridgeH + .03, -pm[1], a1 - a0, .12, .3, ridgeAlongU ? rotU : Math.atan2(F.v[1], F.v[0])));
    // posts and X-bracing under a roof extended past the end wall
    if (st.roof_extend) {
      const e = ext[1] > og + 0.01 ? 1 : 0, aw = e ? RA : -RA, aE = e ? RA + ext[e] - og : -RA - ext[e] + og, n = Math.max(2, Math.round(Math.abs(aE - aw) / 2.7) + 1);
      for (const sb of [-1, 1]) for (let i = 1; i < n; i++) {
        const a = aw + (aE - aw) * i / (n - 1), p = P2(F, ...map(a, sb * (RB - .1)));
        bk.add(timberKey, box(p[0], z0 + H / 2 - .1, -p[1], .22, H + .2, .22));
      }
      for (const sb of [-1, 1]) { // X-brace on each long side, and across the open end
        const p0 = LL(aw, sb * (RB - .1), 0.1), p1 = LL(aE, sb * (RB - .1), H - .2), p2 = LL(aw, sb * (RB - .1), H - .2), p3 = LL(aE, sb * (RB - .1), 0.1);
        bk.add(timberKey, beam(p0, p1, .12)); bk.add(timberKey, beam(p2, p3, .12));
      }
      const q0 = LL(aE, -RB + .1, .1), q1 = LL(aE, RB - .1, H - .2), q2 = LL(aE, -RB + .1, H - .2), q3 = LL(aE, RB - .1, .1);
      bk.add(timberKey, beam(q0, q1, .12)); bk.add(timberKey, beam(q2, q3, .12));
      bk.add(timberKey, beam(LL(aE, -RB + .1, H - .1), LL(aE, RB - .1, H - .1), .2));
      if (st.roof_extend.deck) { const pc = P2(F, ...map((aw + aE) / 2, 0)); bk.add('plank#8f7b60', box(pc[0], z0 + (st.roof_extend.deck_h ?? .5) / 2, -pc[1], ...(ridgeAlongU ? [Math.abs(aE - aw), st.roof_extend.deck_h ?? .5, 2 * RB] : [2 * RB, st.roof_extend.deck_h ?? .5, Math.abs(aE - aw)]), rotU)); }
    }
    // knee-brace brackets under deep eaves (Medora depot)
    if (st.brackets) {
      const sp = st.brackets.spacing || 2.7, drop = st.brackets.drop || 1.0, out = Math.max(0.3, o - 0.25);
      const aMin = -RA - (ext[0] - og), aMax = RA + (ext[1] - og);
      for (const sb of [-1, 1]) { const n = Math.max(2, Math.round((aMax - aMin) / sp) + 1);
        for (let i = 0; i < n; i++) { const a = aMin + (aMax - aMin) * i / (n - 1); bk.add(timberKey, beam(LL(a, sb * RB, H - drop), LL(a, sb * (RB + out), H - .12), .11)); } }
      for (const e of [0, 1]) if (ext[e] - og < 0.01) {   // the gable ends: brackets at the corners and a strut to the apex
        const aw = e ? RA : -RA, s = e ? 1 : -1;
        for (const sb of [-0.75, 0.75]) bk.add(timberKey, beam(LL(aw, sb * RB, H - drop), LL(aw + s * Math.max(.3, og - .2), sb * RB, H + (ridgeH - H) * (1 - Math.abs(sb)) - .1), .11));
        if (st.brackets.strut) bk.add(timberKey, beam(LL(aw + s * .05, -RB * 0.45, H - 0.6), LL(aw + s * .05, 0, ridgeH - .3), .12));
      }
    }
  }
  // trim: corner boards
  for (const fc of faces) { const p = P2(F, fc.a[0], fc.a[1]); bk.add(trimKey, box(p[0], z0 + H / 2 - .2, -p[1], .16, H + .4, .16)); }
  // windows and doors
  const stories = Math.max(1, Math.floor(st.stories || 1)), half = (st.stories || 1) % 1 > 0;
  const sh = Math.min(3.8, H / ((st.stories || 1) + (half ? 0.2 : 0)));
  const winKey = st.arched === 'lancet' ? 'windowLancet' : st.arched ? 'windowArched' : 'window';
  const winW = st.win_w || 0.9;
  const put = (fc, along, bottom, w, h, key, out = 0.04) => {
    const isWin = key.startsWith('window');
    if (st.blank && isWin) return;
    // along: 0..len from fc.a towards fc.b
    const t0 = along - w / 2, t1 = along + w / 2;
    const ax = fc.a[0] + (fc.b[0] - fc.a[0]) * t0 / fc.len, ay = fc.a[1] + (fc.b[1] - fc.a[1]) * t0 / fc.len;
    const bx = fc.a[0] + (fc.b[0] - fc.a[0]) * t1 / fc.len, by = fc.a[1] + (fc.b[1] - fc.a[1]) * t1 / fc.len;
    const pa = P2(F, ax, ay), pb = P2(F, bx, by), ox = fc.n[0] * out, oy = fc.n[1] * out;
    // lettering must read left-to-right for someone facing the wall from outside
    const flip = key.startsWith('sign') && ((pb[0] - pa[0]) * -fc.n[1] + (pb[1] - pa[1]) * fc.n[0]) < 0;
    const [u0, u1] = flip ? [1, 0] : [0, 1];
    bk.add(key, quad(V(pa[0] + ox, pa[1] + oy, z0 + bottom), V(pb[0] + ox, pb[1] + oy, z0 + bottom), V(pb[0] + ox, pb[1] + oy, z0 + bottom + h), V(pa[0] + ox, pa[1] + oy, z0 + bottom + h), [u0, 0], [u1, 0], [u1, 1], [u0, 1]));
    if (isWin && st.shutters) {   // board shutters either side
      const sk = `trim#${st.shutters.slice(1)}`, dx = (pb[0] - pa[0]) / w, dy = (pb[1] - pa[1]) / w;
      for (const s of [-1, 1]) { const c = [(pa[0] + pb[0]) / 2 + dx * s * (w / 2 + w * .27), (pa[1] + pb[1]) / 2 + dy * s * (w / 2 + w * .27)];
        bk.add(sk, box(c[0] + fc.n[0] * .06, z0 + bottom + h / 2, -(c[1] + fc.n[1] * .06), w * .5, h, .05, Math.atan2(dy, dx))); }
    }
  };
  const skipAt = (fc, along) => {   // leave part of a long wall blank (St. Mary's front quarter)
    if (!st.win_skip || !fc.long) return false;
    const d = DIRS[st.win_skip.from], A = P2(F, ...fc.a), B = P2(F, ...fc.b), towardB = (B[0] - A[0]) * d[0] + (B[1] - A[1]) * d[1] > 0;
    const t = along / fc.len; return towardB ? t > 1 - st.win_skip.frac : t < st.win_skip.frac;
  };
  const rear = toward([-front.n[0], -front.n[1]]);
  const compass = (fc) => Math.abs(fc.n[0]) > Math.abs(fc.n[1]) ? (fc.n[0] > 0 ? 'E' : 'W') : (fc.n[1] > 0 ? 'N' : 'S');
  // explicit openings for a face, read from a drone model or photographs: {S: {0: [[kind, t], ...], 1: [...]}}
  // t = centre as a fraction of the wall from the left, seen from outside. kinds: win, shut (closed shutters), door, double, hooddoor, archdoor
  const drawOpenings = (fc, spec) => {
    const A = P2(F, ...fc.a), B = P2(F, ...fc.b), l2r = ((B[0] - A[0]) * -fc.n[1] + (B[1] - A[1]) * fc.n[0]) > 0;
    for (const [fl, items] of Object.entries(spec)) for (const [kind, t] of items) {
      const al = (l2r ? t : 1 - t) * fc.len, s0 = +fl, base = s0 === 0 ? 0 : s0 * sh;
      if (kind === 'win' || kind === 'shut') {
        if (kind === 'shut') put(fc, al, base + (s0 === 0 ? .95 : .76), winW * 1.05, Math.min(1.6, sh * .5), `trim#${(st.shutters || '#6b5a48').slice(1)}`, .07);   // shutters closed over the window
        else if (st.arched === 'lancet') {     // tall pointed window with a stone sill
          const sill = base + (st.win_sill ?? 1.0), wh2 = st.win_h || 2.6;
          put(fc, al, sill, winW, wh2, winKey); put(fc, al, sill - .12, winW + .25, .12, trimKey, .08);
        } else put(fc, al, base + (s0 === 0 ? .95 : .76), winW, Math.min(1.6, sh * .5), winKey);
      } else {
        const w = kind === 'double' ? 1.6 : (st.door_w || 1.0), dh = st.door_h || 2.25; put(fc, al, base + .05, w, dh, 'door');
        if (kind === 'archdoor') put(fc, al, base + dh + .05, w + (st.arch_extra ?? .5), st.arch_h || 1.5, `blindArch#${(st.wall_color || '#e9e3d6').slice(1)}`, .03);
        if (kind === 'hooddoor') {   // small gabled hood over the door on brackets
          const c = [A[0] + (B[0] - A[0]) * al / fc.len, A[1] + (B[1] - A[1]) * al / fc.len], ux = (B[0] - A[0]) / fc.len, uy = (B[1] - A[1]) / fc.len, n = fc.n;
          const pt = (x, o, h) => V(c[0] + ux * x + n[0] * o, c[1] + uy * x + n[1] * o, z0 + base + h);
          for (const sg of [-1, 1]) bk.add(roofKey, quad(pt(sg * .9, 0, 2.45), pt(sg * .9, .95, 2.45), pt(0, .95, 2.95), pt(0, 0, 2.95), [0, 0], [1, 0], [1, 1], [0, 1]));
          bk.add(trimKey, tri(pt(-.9, .95, 2.45), pt(.9, .95, 2.45), pt(0, .95, 2.95), [0, 0], [1, 0], [.5, 1]));
          for (const sg of [-1, 1]) bk.add(trimKey, beam(pt(sg * .75, 0, 2.0), pt(sg * .75, .85, 2.42), .07));
        }
      }
    }
  };
  for (const fc of faces) {
    if (st.openings && st.openings[compass(fc)]) { drawOpenings(fc, st.openings[compass(fc)]); continue; }
    if (st.bay_window && fc === toward(DIRS[st.bay_window.side] || front.n) && st.bay_window.face_only) continue;
    const isFront = fc === front;
    let n = fc.long ? (st.bays ?? Math.round(fc.len / 3)) : (fc === rear && st.rear_bays != null ? st.rear_bays : (st.gable_bays ?? 1));
    if (n <= 0 && !isFront) continue;
    for (let s = 0; s < stories + (half && !fc.long && roofType === 'gable' ? 1 : 0); s++) {
      let nn = (s >= 1 && st.upper_bays && fc.long) ? st.upper_bays : n;
      if (s === stories) nn = Math.max(1, Math.min(2, n));   // half-story gable window(s)
      if (s === stories && fc === rear && st.rear_bays === 0) continue;
      const bottom = s * sh + 0.95 * (s === 0 ? 1 : 0.8), wh = st.win_h || Math.min(1.6, sh * 0.5);
      if (isFront && s === 0) continue;                      // ground floor of the front is done below
      if (st.barn && s === 0) continue;
      if (st.paired && fc.long) {
        const np = Math.max(1, Math.round(nn / 2));
        for (let i = 0; i < np; i++) { const c = fc.len * (i + 0.5) / np; if (skipAt(fc, c)) continue; for (const dd of [-0.6, 0.6]) put(fc, c + dd * winW * 1.2, bottom, winW, wh, winKey); }
      } else for (let i = 0; i < nn; i++) {
        const along = fc.len * (i + 0.5) / nn; if (skipAt(fc, along)) continue;
        put(fc, along, bottom, winW, st.arched === 'lancet' ? (st.win_h || 2.6) : wh, winKey);
      }
    }
    if (isFront && !st.no_front_door) {
      if (st.storefront) {
        const w = Math.min(fc.len - 0.6, 6.2); put(fc, fc.len / 2, 0.15, w, Math.min(3.0, sh - 0.4), 'storefront');
        for (let i = 0; i < Math.floor((fc.len - w) / 2.6); i++) { put(fc, 1.2 + i * 2.6, .95, winW, 1.6, winKey); put(fc, fc.len - 1.2 - i * 2.6, .95, winW, 1.6, winKey); }
      } else if (st.barn) {
        put(fc, fc.len / 2, 0.05, Math.min(3.6, fc.len * .4), Math.min(3.4, H - .4), 'door');
      } else if (st.front_openings) {
        // explicit ground-floor openings across the front: list of [kind, centre as fraction of the face from the left as seen from outside]
        const A = P2(F, ...fc.a), B = P2(F, ...fc.b), leftToRight = ((B[0] - A[0]) * -fc.n[1] + (B[1] - A[1]) * fc.n[0]) > 0;
        for (const [kind, t] of st.front_openings) { const al = (leftToRight ? t : 1 - t) * fc.len;
          if (kind === 'door') put(fc, al, 0.05, 1.0, 2.2, 'door'); else if (kind === 'double') put(fc, al, 0.05, 1.6, 2.4, 'door'); else put(fc, al, .95, winW, Math.min(1.6, sh * .5), winKey); }
      } else {
        const nn = Math.max(2, n); put(fc, fc.len / 2, 0.05, 1.05, 2.25, 'door');
        for (let i = 0; i < nn; i++) { const along = fc.len * (i + 0.5) / nn; if (Math.abs(along - fc.len / 2) > 1.1) put(fc, along, .95, winW, Math.min(1.6, sh * .5), winKey); }
      }
    }
  }
  // fanlight in the front gable (Roberts Hall)
  if (st.fanlight) put(front, front.len / 2, H + 0.4, 1.4, 1.0, 'windowArched');
  // upper front door with a small hood (Roberts Hall, 1919 photo)
  if (st.upper_door) { put(front, front.len / 2, sh + 0.1, 1.1, 2.3, 'door', .05); const c = P2(F, ...[(front.a[0] + front.b[0]) / 2, (front.a[1] + front.b[1]) / 2]); bk.add(trimKey, box(c[0] + front.n[0] * .25, z0 + sh + 2.55, -(c[1] + front.n[1] * .25), front.long ? 1.6 : .5, .12, front.long ? .5 : 1.6, rotU)); }
  // false front: a tall square facade hiding the gable
  if (st.false_front && roofType === 'gable' && !ridgeAlongU === front.long) {
    const p = front, top = ridgeH + (st.false_front_extra ?? .5);
    bk.add(wallKey, quad(L3(p.a[0], p.a[1], H), L3(p.b[0], p.b[1], H), L3(p.b[0], p.b[1], top), L3(p.a[0], p.a[1], top), [0, H], [p.len, H], [p.len, top], [0, top]));
    const c = P2(F, (p.a[0] + p.b[0]) / 2, (p.a[1] + p.b[1]) / 2);
    bk.add(trimKey, box(c[0] + p.n[0] * .12, z0 + top + .1, -(c[1] + p.n[1] * .12), p.long ? p.len + .3 : .35, .3, p.long ? .35 : p.len + .3, rotU));
  }
  // signs seen in the period photographs (st.signs, from build_3d.py); drawn as boards on a wall
  for (const sg of (st.signs || [])) {
    const fc = sg.side ? toward(DIRS[sg.side]) : front;
    const key = 'sign:' + sg.id; if (!SIGNS[key]) SIGNS[key] = signTex(sg);
    const w = Math.min(sg.w_frac ? fc.len * sg.w_frac : sg.w, fc.len - 0.4);
    let along = fc.len * (sg.along ?? 0.5);
    if (sg.on_bay && st.bay_window) along = bayAlong(fc);
    put(fc, along, sg.at, w, w * sg.aspect, key, sg.out ?? 0.08);
  }
  // a likely name board for a known business (not seen in any photograph; hidden unless the viewer asks for it)
  if (st.storefront && !f.id.startsWith('photo85') && signText(f)) {
    const key = 'signguess:' + signText(f); if (!SIGNS[key]) SIGNS[key] = letterTex(signText(f), 1024, 160, '#2e2a25', '#efe6cf', 'bold 84px Georgia');
    const w = Math.min(front.len - 0.8, 7.5); put(front, front.len / 2, Math.min(H - 1.0, (Math.max(1, Math.floor(st.stories || 1)) > 1 ? 3.5 : H - 0.9)), w, w * 0.16, key, 0.08);
  }
  // porches and platforms. pc: {side, depth, roof (default true), h (floor height), span [t0, t1] measured from the span_from end, rail}
  for (const pc of (st.porch || [])) {
    const fc = toward(DIRS[pc.side] || front.n);
    const d = pc.depth || 2.4, ph = pc.post_h || Math.min(3.0, sh - 0.2), fh = pc.h ?? 0.3;
    let s0 = P2(F, fc.a[0], fc.a[1]), s1 = P2(F, fc.b[0], fc.b[1]);
    if (pc.span) {
      let [t0, t1] = pc.span; const dd = DIRS[pc.span_from || 'W'] || [-1, 0];
      if ((s1[0] - s0[0]) * dd[0] + (s1[1] - s0[1]) * dd[1] > 0) [t0, t1] = [1 - t1, 1 - t0];
      const a = [s0[0] + (s1[0] - s0[0]) * t0, s0[1] + (s1[1] - s0[1]) * t0], b = [s0[0] + (s1[0] - s0[0]) * t1, s0[1] + (s1[1] - s0[1]) * t1]; s0 = a; s1 = b;
    }
    const len = Math.hypot(s1[0] - s0[0], s1[1] - s0[1]), rot = Math.atan2(s1[1] - s0[1], s1[0] - s0[0]);
    const pw = [(s0[0] + s1[0]) / 2 + fc.n[0] * d / 2, (s0[1] + s1[1]) / 2 + fc.n[1] * d / 2];
    const zg = ctxZ ? Math.min(z0, ctxZ(pw[0], pw[1])) : z0;
    bk.add('plank#9a8466', box(pw[0], (z0 + fh + zg - .2) / 2, -pw[1], len + (pc.extend || 0), z0 + fh - zg + .2, d, rot));
    if (pc.roof !== false) {
      const ox = (fc.n[0]) * (d + .25), oy = (fc.n[1]) * (d + .25), e0 = (pc.extend || 0) / 2;
      const ux = Math.cos(rot) * e0, uy = Math.sin(rot) * e0;
      bk.add(roofKey, quad(V(s1[0] + ox + ux, s1[1] + oy + uy, z0 + fh + ph), V(s0[0] + ox - ux, s0[1] + oy - uy, z0 + fh + ph), V(s0[0] - ux, s0[1] - uy, z0 + fh + ph + (pc.rise ?? .7)), V(s1[0] + ux, s1[1] + uy, z0 + fh + ph + (pc.rise ?? .7)), [0, 0], [len, 0], [len, d], [0, d]));
      const posts = Math.max(2, Math.round(len / (pc.post_spacing || 2.5)) + 1);
      let ts = Array.from({length: posts}, (_, i) => i / (posts - 1));
      if (pc.posts_t) { const dd = DIRS[pc.posts_from || 'W'] || [-1, 0], flip = (s1[0] - s0[0]) * dd[0] + (s1[1] - s0[1]) * dd[1] > 0; ts = pc.posts_t.map(t => flip ? 1 - t : t); }   // measured post positions
      for (const t of ts) { const x = s0[0] + (s1[0] - s0[0]) * t + fc.n[0] * (d - .15), y = s0[1] + (s1[1] - s0[1]) * t + fc.n[1] * (d - .15); bk.add(trimKey, box(x, z0 + fh + ph / 2, -y, .16, ph, .16)); }
    }
    if (pc.rail) { const ry = z0 + fh + .9; const a = [s0[0] + fc.n[0] * (d - .1), s0[1] + fc.n[1] * (d - .1)], b = [s1[0] + fc.n[0] * (d - .1), s1[1] + fc.n[1] * (d - .1)]; bk.add(trimKey, beam(V(a[0], a[1], ry), V(b[0], b[1], ry), .07)); }
  }
  // outside stair along a wall up to an upper door (Hotel de Mores east gable, Ferris store)
  if (st.outside_stair) {
    const os = typeof st.outside_stair === 'string' ? {side: st.outside_stair} : st.outside_stair;
    const fc = toward(DIRS[os.side]);
    const s0 = P2(F, fc.a[0], fc.a[1]), s1 = P2(F, fc.b[0], fc.b[1]), tl = Math.min(fc.len - 1.4, sh * 1.6), steps = 14;
    // the top landing is at the end of the face nearest os.top (compass) or at fc.b
    let topAtB = true; if (os.top) { const d = DIRS[os.top]; topAtB = (s1[0] - s0[0]) * d[0] + (s1[1] - s0[1]) * d[1] > 0; }
    const at = (dist) => { const t = topAtB ? (fc.len - 0.8 - dist) / fc.len : (0.8 + dist) / fc.len; return [s0[0] + (s1[0] - s0[0]) * t + fc.n[0] * .7, s0[1] + (s1[1] - s0[1]) * t + fc.n[1] * .7]; };
    for (let i = 0; i < steps; i++) { const p = at(tl * (1 - (i + 1) / steps)); bk.add('plank#8c7558', box(p[0], z0 + sh * (i + 1) / steps, -p[1], .9, .08, .9)); }
    const top = at(-0.3); bk.add('plank#8c7558', box(top[0], z0 + sh, -top[1], 1.2, .12, 1.2));
    put(fc, topAtB ? fc.len - 0.8 : 0.8, sh + .05, 1.0, 2.1, 'door', .05);
    const p0 = at(tl), p1 = at(0); bk.add(trimKey, beam(V(p0[0] + fc.n[0] * .45, p0[1] + fc.n[1] * .45, z0 + .9), V(p1[0] + fc.n[0] * .45, p1[1] + fc.n[1] * .45, z0 + sh + .9), .06));
  }
  // bay window: flat box, or canted three-sided bay with its own low hip roof (Medora depot)
  function bayAlong(fc) { const bw = st.bay_window; if (!bw.offset) return fc.len / 2; const d = DIRS[bw.offset_dir || 'E'], A = P2(F, ...fc.a), B = P2(F, ...fc.b), s = ((B[0] - A[0]) * d[0] + (B[1] - A[1]) * d[1]) > 0 ? 1 : -1; return fc.len / 2 + s * bw.offset; }
  if (st.bay_window) {
    const bw = st.bay_window === true ? {} : st.bay_window, fc = bw.side ? toward(DIRS[bw.side]) : front;
    const w = bw.w || 2.4, dp = bw.d || 0.8, eh = bw.eave || Math.min(3.0, H - .3), al = bayAlong(fc);
    const A = P2(F, ...fc.a), B = P2(F, ...fc.b), ux = (B[0] - A[0]) / fc.len, uy = (B[1] - A[1]) / fc.len, n = fc.n;
    const pt = (t, out, h) => V(A[0] + ux * (al + t) + n[0] * out, A[1] + uy * (al + t) + n[1] * out, z0 + h);
    const cw = bw.canted === false ? w : w - 2 * dp;   // width of the front face
    const outline = bw.canted === false ? [[-w / 2, 0], [-w / 2, dp], [w / 2, dp], [w / 2, 0]] : [[-w / 2, 0], [-cw / 2, dp], [cw / 2, dp], [w / 2, 0]];
    for (let i = 0; i < 3; i++) { const [t0, o0] = outline[i], [t1, o1] = outline[i + 1], L = Math.hypot(t1 - t0, o1 - o0);
      bk.add(wallKey, quad(pt(t0, o0, -.3), pt(t1, o1, -.3), pt(t1, o1, eh), pt(t0, o0, eh), [0, 0], [L, 0], [L, eh], [0, eh]));
      // a window in each face, over a 0.8 m board base
      const ww = Math.min(L - .25, i === 1 ? 0.95 : 0.6), mt = (t0 + t1) / 2, mo = (o0 + o1) / 2, ex = (t1 - t0) / L, eo = (o1 - o0) / L;
      const wp = (s, h) => pt(mt + ex * s, mo + eo * s + .03 * (i === 1 ? 1 : 0.7), h);
      bk.add('window', quad(wp(-ww / 2, .8), wp(ww / 2, .8), wp(ww / 2, Math.min(eh - .25, 2.7)), wp(-ww / 2, Math.min(eh - .25, 2.7)), [0, 0], [1, 0], [1, 1], [0, 1]));
    }
    // low hip roof: from the bay's outer eave up to the wall
    const ro = 0.25, rh = eh + 0.7, R2 = [[-w / 2 - ro, 0], [-cw / 2 - ro * .5, dp + ro], [cw / 2 + ro * .5, dp + ro], [w / 2 + ro, 0]];
    for (let i = 0; i < 3; i++) { const [t0, o0] = R2[i], [t1, o1] = R2[i + 1];
      bk.add(roofKey, poly([pt(t0, o0, eh), pt(t1, o1, eh), pt(Math.max(-w / 2, Math.min(w / 2, t1 * .6)), 0, rh), pt(Math.max(-w / 2, Math.min(w / 2, t0 * .6)), 0, rh)], [[0, 0], [1, 0], [1, 1], [0, 1]])); }
  }
  // chimneys on the ridge: chimney_at {from: compass end, at: [metres from that end]} or evenly spread
  const chimneyPts = [];
  if (st.chimney_at) {
    const d = DIRS[st.chimney_at.from], ax = ridgeAlongU ? F.u : F.v, s = (ax[0] * d[0] + ax[1] * d[1]) > 0 ? 1 : -1, ext = ridgeAlongU ? hl : hw;
    for (const m of st.chimney_at.at) { const a = s * (ext - m); chimneyPts.push(ridgeAlongU ? [a, st.chimney_at.off || 0] : [st.chimney_at.off || 0, a]); }
  } else { const nch = st.chimneys ?? 1;
    for (let i = 0; i < nch; i++) { const t = nch === 1 ? 0.25 : (i / (nch - 1) - 0.5) * 0.7; chimneyPts.push(ridgeAlongU ? [F.L * t, 0] : [0, F.W * t]); } }
  const chH = roofType === 'shed' ? (p) => shedH(p) : () => ridgeH;
  for (const a of chimneyPts) { const p = P2(F, a[0], a[1]); const top = chH(a) + (st.chimney_h || 1.1);
    bk.add('wall_brick#9c5a44', box(p[0], z0 + (top + ridgeH - 2.5) / 2, -p[1], .48, top - ridgeH + 2.5, .48));
    bk.add('wall_brick#8e5040', box(p[0], z0 + top - .1, -p[1], .62, .18, .62)); }   // corbelled cap
  // church belfry on the ridge just behind the front gable (St. Mary's: base 2.6 m, open stage 2.3 m, pyramid roof 1.8 m)
  if (st.belfry) {
    const bf = st.belfry === true ? {} : st.belfry, bwid = bf.w || 2.6, back = (bf.back ?? 0.5) + bwid / 2;
    const fm = [(front.a[0] + front.b[0]) / 2, (front.a[1] + front.b[1]) / 2], L0 = Math.hypot(...fm) || 1;
    const c = [fm[0] - fm[0] / L0 * back, fm[1] - fm[1] / L0 * back], p = P2(F, c[0], c[1]);
    const shingKey = bf.color ? `wall_clapboard#${bf.color.slice(1)}` : wallKey.replace(/^wall_[a-z]+/, 'wall_clapboard'), postKey = bf.color ? `trim#${bf.color.slice(1)}` : trimKey;
    bk.add(shingKey, box(p[0], z0 + ridgeH - .3 + (bf.base || .8) / 2, -p[1], bwid, (bf.base || .8) + .6, bwid, rotU));
    const sb = z0 + ridgeH + (bf.base || .8) - .3, stg = bf.stage || 2.3;
    for (const [dx, dy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) { const q = P2(F, c[0] + dx * (bwid / 2 - .15), c[1] + dy * (bwid / 2 - .15)); bk.add(postKey, box(q[0], sb + stg / 2, -q[1], .3, stg, .3)); }
    if (bf.mullion) for (const [dx, dy] of [[0, -1], [1, 0], [0, 1], [-1, 0]]) { const q = P2(F, c[0] + dx * (bwid / 2 - .1), c[1] + dy * (bwid / 2 - .1)); bk.add(postKey, box(q[0], sb + stg / 2, -q[1], .16, stg, .16)); }   // centre post: two openings a face
    if (bf.rail) bk.add(trimKey, box(p[0], sb + .45, -p[1], bwid - .1, .1, bwid - .1, rotU));
    bk.add('dark#2a2622', box(p[0], sb + stg / 2, -p[1], bwid * .55, stg * .8, bwid * .55, rotU));
    bk.add(postKey, box(p[0], sb + stg + .08, -p[1], bwid + .2, .16, bwid + .2, rotU));
    const g = new THREE.ConeGeometry((bwid + (bf.overhang ?? .5)) / Math.SQRT2, bf.roof || 1.8, 4).toNonIndexed(); g.rotateY(Math.PI / 4 + rotU); g.translate(p[0], sb + stg + .16 + (bf.roof || 1.8) / 2, -p[1]); bk.add(roofKey, g);
  }
  // roof monitor on a flat roof: monitor true or {len_frac, at (-0.5..0.5 along), w}
  if (st.monitor && roofType === 'flat') { const mo = st.monitor === true ? {} : st.monitor, lf = mo.len_frac ?? 0.7, at = mo.at ?? 0, mw = mo.w || 2.4, p = P2(F, F.L * at, 0);
    bk.add(wallKey, box(p[0], z0 + H + 0.9, -p[1], F.L * lf, 1.4, mw, rotU)); bk.add(roofKey, box(p[0], z0 + H + 1.65, -p[1], F.L * lf + .4, .12, mw + .6, rotU)); }
  // ridge ventilators (sheds)
  if (st.vents && roofType !== 'flat') for (let i = 0; i < st.vents; i++) {
    const t = (i + 0.5) / st.vents - 0.5, a = ridgeAlongU ? [F.L * t * .9, 0] : [0, F.W * t * .9], p = P2(F, a[0], a[1]);
    bk.add(wallKey, box(p[0], z0 + ridgeH + .35, -p[1], 1.1, .8, 1.1)); const g = new THREE.ConeGeometry(.95, .6, 4).toNonIndexed(); g.rotateY(Math.PI / 4 + rotU); g.translate(p[0], z0 + ridgeH + 1.05, -p[1]); bk.add(roofKey, g); }
  // galleries on one front (packing house): roofed porch at the ground, open framing above
  if (st.gallery) {
    const fc = toward(DIRS[st.gallery.side] || [0, -1]);
    const s0 = P2(F, fc.a[0], fc.a[1]), s1 = P2(F, fc.b[0], fc.b[1]), fr = st.gallery.frac || .35, dep = st.gallery.depth || 2.2;
    let ta = 0.5 - fr / 2, tb = 0.5 + fr / 2;
    if (st.gallery.end) { const d = DIRS[st.gallery.end], toB = (s1[0] - s0[0]) * d[0] + (s1[1] - s0[1]) * d[1] > 0; [ta, tb] = toB ? [1 - fr - .02, .98] : [.02, fr + .02]; }
    const lv = st.gallery.levels || 3, lh = H / lv, ang = Math.atan2(s1[1] - s0[1], s1[0] - s0[0]);
    const A = [s0[0] + (s1[0] - s0[0]) * ta, s0[1] + (s1[1] - s0[1]) * ta], B = [s0[0] + (s1[0] - s0[0]) * tb, s0[1] + (s1[1] - s0[1]) * tb];
    const M = [(A[0] + B[0]) / 2 + fc.n[0] * dep / 2, (A[1] + B[1]) / 2 + fc.n[1] * dep / 2], len = Math.hypot(B[0] - A[0], B[1] - A[1]);
    bk.add('plank#8d8170', box(M[0], z0 + .3, -M[1], len, .3, dep, ang));            // raised floor
    bk.add(roofKey, box(M[0], z0 + 3.2, -M[1], len + .3, .12, dep + .3, ang));        // porch roof at the ground level
    for (let k = 2; k <= lv; k++) bk.add(timberKey, box(M[0] + fc.n[0] * dep / 2, z0 + k * lh, -(M[1] + fc.n[1] * dep / 2), len, .16, .16, ang));   // open frame above
    const np = Math.round(len / 2.5) + 1; for (let i = 0; i < np; i++) { const t = i / (np - 1), x = A[0] + (B[0] - A[0]) * t + fc.n[0] * (dep - .1), y = A[1] + (B[1] - A[1]) * t + fc.n[1] * (dep - .1); bk.add(timberKey, box(x, z0 + H / 2, -y, .16, H, .16));
      if (i < np - 1) { const t2 = (i + 1) / (np - 1), x2 = A[0] + (B[0] - A[0]) * t2 + fc.n[0] * (dep - .1), y2 = A[1] + (B[1] - A[1]) * t2 + fc.n[1] * (dep - .1); bk.add(timberKey, beam(V(x, y, z0 + 3.4), V(x2, y2, z0 + H - .3), .1)); } }
    for (let k = 0; k < lv; k++) put(fc, fc.len * (ta + tb) / 2 + (k % 2 ? 1.5 : -1.5), k * lh + .1, 1.0, 2.1, 'door');
  }
  // horizontal enclosed runway from the top of the building out to a timber pier (packing house; Huffman 1886, SHSND 00042-00074/-75)
  if (st.runway) {
    const d = DIRS[st.runway.end] || [-1, 0], sg = Math.sign(F.u[0] * d[0] + F.u[1] * d[1]) || -1, L = st.runway.len || 24, top = st.runway.h ?? H + 1.0;
    const start = sg * (F.L / 2 - (st.runway.inset || 0)), c = P2(F, start + sg * L / 2, 0);
    if (st.runway.open) {     // roofed deck on an open timber truss (SHSND 00042-00074, MHS 72460)
      bk.add(timberKey, box(c[0], z0 + top - .3, -c[1], L, .7, 2.2, rotU));
      bk.add(wallKey, box(c[0], z0 + top + .45, -c[1], L, .9, 2.2, rotU));
      bk.add(roofKey, box(c[0], z0 + top + 1.0, -c[1], L + .3, .12, 2.8, rotU));
      const nb = Math.max(2, Math.round(L / 3.2)), dep = st.runway.truss || 2.2;
      for (let i = 0; i <= nb; i++) for (const side of [-1, 1]) {
        const a1 = start + sg * (L * i / nb), q1 = P2(F, a1, side * 1.0), a2 = start + sg * (L * Math.min(nb, i + 1) / nb), q2 = P2(F, a2, side * 1.0);
        bk.add(timberKey, beam(V(q1[0], q1[1], z0 + top - .65), V(q1[0], q1[1], z0 + top - .65 - dep), .16));                       // vertical
        if (i < nb) bk.add(timberKey, beam(V(q1[0], q1[1], z0 + top - .65 - dep), V(q2[0], q2[1], z0 + top - .65), .14));             // diagonal
        if (i < nb) bk.add(timberKey, beam(V(q1[0], q1[1], z0 + top - .65 - dep), V(q2[0], q2[1], z0 + top - .65 - dep), .16));       // bottom chord
      }
    } else {
      bk.add(wallKey, box(c[0], z0 + top, -c[1], L, 2.0, 2.2, rotU));
      bk.add(roofKey, box(c[0], z0 + top + 1.1, -c[1], L + .3, .12, 2.8, rotU));
    }
    // pier: tapered square timber tower at the far end
    const pc = P2(F, start + sg * (L - 2), 0), zg = ctxZ ? ctxZ(pc[0], pc[1]) : z0, ph = z0 + top - 1 - zg;
    const g = new THREE.CylinderGeometry(3 / Math.SQRT2, 4 / Math.SQRT2, ph, 4, 1).toNonIndexed(); g.rotateY(Math.PI / 4 + rotU); g.translate(pc[0], zg + ph / 2, -pc[1]); bk.add(timberKey, g);
  }
  // square tower with a pyramid-roofed cupola
  if (st.tower) {
    const tw = (st.tower.w || 5), th = (st.tower.h || 4), p = P2(F, -F.L * 0.25, 0);
    bk.add(wallKey, box(p[0], z0 + ridgeH + th / 2 - .5, -p[1], tw, th, tw, rotU));
    const g = new THREE.ConeGeometry(tw * .78, 2.2, 4).toNonIndexed(); g.rotateY(Math.PI / 4 + rotU); g.translate(p[0], z0 + ridgeH + th + .55, -p[1]); bk.add(roofKey, g);
  }
  // cupola on the ridge or hip apex (cooling house)
  if (st.cupola && !st.tower) { const cs = st.cupola === true ? {} : st.cupola, w = cs.w || 2.2, p = P2(F, 0, 0);
    bk.add(wallKey, box(p[0], z0 + ridgeH + (cs.h || 1.6) / 2 - .2, -p[1], w, (cs.h || 1.6) + .4, w, rotU));
    const g = new THREE.ConeGeometry(w * .82, cs.cap || 1.4, 4).toNonIndexed(); g.rotateY(Math.PI / 4 + rotU); g.translate(p[0], z0 + ridgeH + (cs.h || 1.6) + (cs.cap || 1.4) / 2 - .2, -p[1]); bk.add(roofKey, g); }
  return {ridgeH, F, front};
}

function splitRect(R, n, gap) {
  const F = rectFrame(R), out = [], seg = F.L / n, g = seg * gap;
  for (let i = 0; i < n; i++) {
    const a0 = -F.L / 2 + i * seg + (gap ? g / 2 : 0), a1 = a0 + seg - (gap ? g : 0);
    out.push([P2(F, a0, -F.W / 2), P2(F, a1, -F.W / 2), P2(F, a1, F.W / 2), P2(F, a0, F.W / 2)]);
  }
  return out;
}

// decks and platforms (st.decks: [{rect, h, rails: [[[e,n],[e,n],...], ...]}]) and fences (st.fences: [{pts, kind: 'rail'|'board'|'picket', h}])
function buildDecks(bk, st, zAt) {
  for (const dk of (st.decks || [])) {
    const R = dk.rect, c = R.reduce((s, p) => [s[0] + p[0] / 4, s[1] + p[1] / 4], [0, 0]), zt = (dk.z ?? Math.max(...R.map(p => zAt(p[0], p[1])))) + (dk.h ?? .5);
    bk.add('plank#94805f', poly(R.map(p => V(p[0], p[1], zt)), R.map(p => [p[0] - c[0], p[1] - c[1]])));
    for (let i = 0; i < 4; i++) { const a = R[i], b = R[(i + 1) % 4], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      bk.add('plank#7d6b52', quad(V(a[0], a[1], zt), V(b[0], b[1], zt), V(b[0], b[1], Math.min(zt - .2, zAt(b[0], b[1]) - .3)), V(a[0], a[1], Math.min(zt - .2, zAt(a[0], a[1]) - .3)), [0, 0], [L, 0], [L, 1], [0, 1])); }
    for (const line of (dk.rails || [])) railLine(bk, line, () => zt, 1.1, 2.4, 'trim#6f5e49');
  }
  for (const fe of (st.fences || [])) {
    const h = fe.h || 1.2;
    if (fe.kind === 'board') for (let i = 0; i < fe.pts.length - 1; i++) { const a = fe.pts[i], b = fe.pts[i + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]), za = zAt(a[0], a[1]), zb = zAt(b[0], b[1]);
      bk.add('plank#8a7a62', quad(V(a[0], a[1], za - .2), V(b[0], b[1], zb - .2), V(b[0], b[1], zb + h), V(a[0], a[1], za + h), [0, 0], [L, 0], [L, h], [0, h])); }
    else if (fe.kind === 'worm') {     // zigzag (worm) split-rail fence: rails stacked on alternate corners
      const key = 'trim#8a7c66', z = [];
      for (let i = 0; i < fe.pts.length - 1; i++) { const a = fe.pts[i], b = fe.pts[i + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.round(L / 3.2)), nx = -(b[1] - a[1]) / L, ny = (b[0] - a[0]) / L;
        for (let k = 0; k <= n; k++) { const t = k / n, sg = (k % 2 ? 1 : -1) * .45; z.push([a[0] + (b[0] - a[0]) * t + nx * sg, a[1] + (b[1] - a[1]) * t + ny * sg]); } }
      for (let i = 0; i < z.length - 1; i++) for (const hh of [.25, .5, .75, 1.0].filter(x => x < h + .05)) bk.add(key, beam(V(z[i][0], z[i][1], zAt(z[i][0], z[i][1]) + hh), V(z[i + 1][0], z[i + 1][1], zAt(z[i + 1][0], z[i + 1][1]) + hh + .08), .09));
    }
    else railLine(bk, fe.pts, zAt, h, 2.5, 'trim#7a6a55');
  }
}
function railLine(bk, pts, zf, h, sp, key) {
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i], b = pts[i + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.round(L / sp));
    for (let k = 0; k <= n; k++) { const t = k / n, x = a[0] + (b[0] - a[0]) * t, y = a[1] + (b[1] - a[1]) * t, z = zf(x, y); bk.add(key, box(x, z + h / 2 - .1, -y, .12, h + .2, .12)); }
    for (const hh of [h * .5, h - .05]) bk.add(key, beam(V(a[0], a[1], zf(a[0], a[1]) + hh), V(b[0], b[1], zf(b[0], b[1]) + hh), .07));
  }
}

export function buildDetailed(f, ctx) {
  // returns a THREE.Group, or null if the feature has no detailed style
  const st = f.style; if (!st || !f.rect) return null;
  const grade = ctx.grade(f), m = f.massing || {};
  const H = m.eave > 0 ? m.eave : (st.stories >= 2 ? 7 : st.stories >= 1.5 ? 4.5 : 3.2);
  const bk = new Bucket(); ctxZ = ctx.zAt;
  let frontDir = st.front ? DIRS[st.front] : ctx.streetDir(f);
  if (st.frame) {            // an open timber frame going up (posts, sills, plates, tie beams, rafters, knee braces)
    const z0 = Math.min(...f.rect.map(p => ctx.zAt(p[0], p[1])));
    buildFrame(bk, f.rect, z0, st.frame, `trim#${(st.timber || '#a08463').slice(1)}`);
  } else if (!st.skip_main) {
    let rects = st.blocks || (st.split ? splitRect(f.rect, st.split.n, st.split.gap) : [f.rect]);
    rects.forEach((R, i) => {
      const z0 = Math.min(...R.map(p => ctx.zAt(p[0], p[1])));
      const s2 = (st.blocks && i > 0) ? Object.assign({}, st, {stories: 1.5, porch: [], chimneys: 1}) : st;
      const H2 = (st.blocks && i > 0) ? H * 0.7 : H;
      buildBlock(bk, f, s2, z0, H2, R, frontDir, grade, m.ridge);
    });
  }
  // extra blocks: wings, lean-tos, annexes, towers. Each part: {rect, eave, ridge?, style: overrides}
  const ONE_OFF = ['parts', 'bridges', 'porch', 'signs', 'chimney_at', 'bay_window', 'outside_stair', 'gallery', 'runway', 'tower', 'belfry', 'monitor', 'roof_extend', 'brackets', 'decks', 'fences', 'upper_door', 'fanlight', 'front_openings', 'chimneys', 'cupola', 'vents', 'plinth', 'jerkin', 'skip_main', 'rise', 'false_front', 'storefront', 'win_skip', 'rear_bays', 'size', 'eave'];
  for (const p of (st.parts || [])) {
    const base = Object.fromEntries(Object.entries(st).filter(([k]) => !ONE_OFF.includes(k)));
    const s2 = Object.assign({chimneys: 0}, base, p.style || {});
    const z0 = p.z0 ?? Math.min(...p.rect.map(q => ctx.zAt(q[0], q[1])));
    buildBlock(bk, f, s2, z0, p.eave, p.rect, s2.front ? DIRS[s2.front] : frontDir, grade, p.ridge);
  }
  buildDecks(bk, st, ctx.zAt);
  for (const br of (st.bridges || [])) {     // elevated open walkway between buildings: two stringers, plank deck, rails
    const za = ctx.zAt(br.a[0], br.a[1]) + br.a[2], zb = ctx.zAt(br.b[0], br.b[1]) + br.b[2], w = br.w || 1.2, key = 'trim#7a6a58';
    const dx = br.b[0] - br.a[0], dy = br.b[1] - br.a[1], L = Math.hypot(dx, dy), nx = -dy / L * w / 2, ny = dx / L * w / 2;
    for (const sg of [-1, 1]) {
      bk.add(key, beam(V(br.a[0] + sg * nx, br.a[1] + sg * ny, za), V(br.b[0] + sg * nx, br.b[1] + sg * ny, zb), .2));
      bk.add(key, beam(V(br.a[0] + sg * nx, br.a[1] + sg * ny, za + 1), V(br.b[0] + sg * nx, br.b[1] + sg * ny, zb + 1), .08));
    }
    const np = Math.max(2, Math.round(L / 2.5));
    for (let i = 0; i <= np; i++) { const t = i / np, x = br.a[0] + dx * t, y = br.a[1] + dy * t, z = za + (zb - za) * t;
      bk.add(key, beam(V(x - nx, y - ny, z + .1), V(x + nx, y + ny, z + .1), .1));
      if (br.posts && i > 0 && i < np) for (const sg of [-1, 1]) bk.add(key, beam(V(x + sg * nx, y + sg * ny, ctx.zAt(x, y)), V(x + sg * nx, y + sg * ny, z), .18)); }
  }
  const grp = new THREE.Group();
  for (const [mesh, k] of bk.meshes(k => mat(k, grade)).map((m, i) => [m, [...bk.m.keys()][i]])) {
    mesh.userData = f; mesh.name = k;
    if (k.startsWith('sign:')) { const all = [...(st.signs || []), ...(st.parts || []).flatMap(p => (p.style && p.style.signs) || [])]; const sg = all.find(s => 'sign:' + s.id === k); mesh.signFrom = sg?.from ?? 0; mesh.signTo = sg?.to ?? 9999; }
    grp.add(mesh);
  }
  return grp;
}

// ---------------------------------------------------------------- streets
export function buildStreets(streets, t) {
  const grp = new THREE.Group();
  const matDirt = new THREE.MeshStandardMaterial({map: TEX.dirt, color: 0xffffff, roughness: 1, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2});
  const matTrail = matDirt.clone(); matTrail.opacity = 0.85;
  const matLane = matDirt.clone(); matLane.opacity = 0.6;   // side streets: worn wagon tracks in the 1885 photos, not graded roads
  const matPlank = new THREE.MeshStandardMaterial({map: TEX.plank, color: 0xa08a6a, roughness: .95});
  for (const s of streets) {
    const pts = s.pts, w = s.width, pos = [], uv = [], idx = []; let dist = 0;
    for (let i = 0; i < pts.length; i++) {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
      let dx = b[0] - a[0], dy = b[1] - a[1]; const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
      if (i) dist += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      const nx = -dy * w / 2, ny = dx * w / 2, u = pts[i][2];
      pos.push(pts[i][0] + nx, u, -(pts[i][1] + ny), pts[i][0] - nx, u, -(pts[i][1] - ny));
      uv.push(0, dist / 12, 1, dist / 12);
      if (i) { const k = i * 2; idx.push(k - 2, k - 1, k, k - 1, k + 1, k); }
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals();
    let m;
    if (s.kind === 'sidewalk') { for (let i = 0; i < uv.length; i += 2) { uv[i] *= w / 2; } g.setAttribute('uv', new THREE.Float32BufferAttribute(uv.map((v, i) => i % 2 ? v * 6 : v), 2)); m = matPlank; }
    else m = s.kind === 'trail' ? matTrail : s.kind === 'lane' ? matLane : matDirt;
    const mesh = new THREE.Mesh(g, m); mesh.receiveShadow = true; mesh.userData = {street: s}; grp.add(mesh);
  }
  return grp;
}

// ---------------------------------------------------------------- railroad track and train
export function buildTrack(line) {
  const grp = new THREE.Group();
  // ballast bed
  const pos = [], uv = [], idx = []; let dist = 0;
  // a 4th element of 1 marks an open-deck point (on a trestle): no ballast bed there
  const dense = [], open = []; for (let i = 0; i < line.length - 1; i++) { const a = line[i], b = line[i + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.ceil(L / 2)); for (let k = 0; k < n; k++) { const t = k / n; dense.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]); open.push(a[3] === 1 && (k === 0 || b[3] === 1)); } } dense.push(line[line.length - 1].slice(0, 3)); open.push(line[line.length - 1][3] === 1);
  dense.forEach((p, i) => {
    const a = dense[Math.max(0, i - 1)], b = dense[Math.min(dense.length - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1]; const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
    if (i) dist += Math.hypot(p[0] - dense[i - 1][0], p[1] - dense[i - 1][1]);
    const nx = -dy * 1.9, ny = dx * 1.9;
    pos.push(p[0] + nx, p[2] - .1, -(p[1] + ny), p[0] - nx, p[2] - .1, -(p[1] - ny)); uv.push(0, dist / 2, 2, dist / 2);
    if (i && !(open[i] && open[i - 1])) { const k = i * 2; idx.push(k - 2, k - 1, k, k - 1, k + 1, k); }
  });
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals();
  const bed = new THREE.Mesh(g, new THREE.MeshStandardMaterial({map: TEX.ballast, roughness: 1, polygonOffset: true, polygonOffsetFactor: -3})); bed.receiveShadow = true; grp.add(bed);
  // ties (instanced) and two rails
  const tieGeo = new THREE.BoxGeometry(2.6, .15, .22), tieMat = new THREE.MeshStandardMaterial({color: 0x5a4a3c, roughness: 1});
  const ties = []; let acc = 0;
  for (let i = 1; i < dense.length; i++) { const a = dense[i - 1], b = dense[i], L = Math.hypot(b[0] - a[0], b[1] - a[1]); for (let s = (0.6 - acc) % 0.6; s < L; s += 0.6) { const t = s / L; ties.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t, Math.atan2(b[1] - a[1], b[0] - a[0])]); } acc = (acc + L) % 0.6; }
  const inst = new THREE.InstancedMesh(tieGeo, tieMat, ties.length), M = new THREE.Matrix4(), q = new THREE.Quaternion();
  ties.forEach((t, i) => { q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), t[3] + Math.PI / 2); M.compose(new THREE.Vector3(t[0], t[2] + .02, -t[1]), q, new THREE.Vector3(1, 1, 1)); inst.setMatrixAt(i, M); });
  inst.receiveShadow = true; grp.add(inst);
  const railMat = new THREE.MeshStandardMaterial({color: 0x6a6460, metalness: .6, roughness: .45});
  for (const off of [-0.72, 0.72]) {
    const rg = [];
    for (let i = 1; i < dense.length; i++) {
      const a = dense[i - 1], b = dense[i], L = Math.hypot(b[0] - a[0], b[1] - a[1]); if (L < .01) continue;
      const nx = -(b[1] - a[1]) / L * off, ny = (b[0] - a[0]) / L * off, mx = (a[0] + b[0]) / 2 + nx, my = (a[1] + b[1]) / 2 + ny;
      rg.push(box(mx, (a[2] + b[2]) / 2 + .17, -my, L + .02, .12, .08, Math.atan2(b[1] - a[1], b[0] - a[0])));
    }
    const rail = new THREE.Mesh(mergeGeometries(rg), railMat); rail.castShadow = true; grp.add(rail);
  }
  return {grp, dense};
}

function letterTex(text, w, h, bg, fg, font) {
  const t = canvasTex(w, h, (g) => { g.fillStyle = bg; g.fillRect(0, 0, w, h); g.fillStyle = fg; g.font = font; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, w / 2, h / 2 + 2); }, [1, 1]);
  t.repeat.set(1, 1); return t;
}
function spokedWheel(r, mat, hubMat, spokes = 12, counterweight = null) {
  // a cast wheel: tyre, rim, spokes, hub, optional counterweight; axis along z
  const g = new THREE.Group();
  const tyre = new THREE.Mesh(new THREE.TorusGeometry(r - .05, .07, 8, 32), mat); g.add(tyre);
  const flange = new THREE.Mesh(new THREE.CylinderGeometry(r + .04, r + .04, .03, 32), mat); flange.rotation.x = Math.PI / 2; flange.position.z = -.06; g.add(flange);
  for (let i = 0; i < spokes; i++) { const sp = new THREE.Mesh(new THREE.BoxGeometry(.045, r - .12, .05), mat); const a = i / spokes * Math.PI * 2; sp.position.set(Math.sin(a) * (r - .12) / 2, Math.cos(a) * (r - .12) / 2, 0); sp.rotation.z = -a; g.add(sp); }
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(r * .2, r * .2, .14, 16), hubMat); hub.rotation.x = Math.PI / 2; g.add(hub);
  if (counterweight) { const cw = new THREE.Mesh(new THREE.CylinderGeometry(r * .78, r * .78, .06, 24, 1, false, -.9, 1.8), counterweight); cw.rotation.x = Math.PI / 2; g.add(cw); }
  return g;
}
function truck(x, wheelR, gauge, mat, frameMat) {
  const g = new THREE.Group(); g.position.x = x;
  for (const dx of [-0.85, 0.85]) for (const z of [-gauge / 2, gauge / 2]) { const w = spokedWheel(wheelR, mat, mat, 0); w.position.set(dx, wheelR, z); g.add(w);
    const disc = new THREE.Mesh(new THREE.CylinderGeometry(wheelR - .06, wheelR - .06, .08, 20), mat); disc.rotation.x = Math.PI / 2; disc.position.set(dx, wheelR, z); g.add(disc); }
  for (const z of [-gauge / 2 - .12, gauge / 2 + .12]) { const side = new THREE.Mesh(new THREE.BoxGeometry(2.6, .28, .1), frameMat); side.position.set(0, wheelR + .05, z); g.add(side);
    const spring = new THREE.Mesh(new THREE.BoxGeometry(.5, .25, .12), frameMat); spring.position.set(0, wheelR + .32, z); g.add(spring); }
  const bol = new THREE.Mesh(new THREE.BoxGeometry(.4, .25, gauge + .5), frameMat); bol.position.set(0, wheelR + .3, 0); g.add(bol);
  return g;
}
function locomotive() {
  // Northern Pacific 4-4-0 "American" of 1882-83, after the Portland Co. builder's photo of NP No. 225 (March 1883)
  // and contemporary Baldwin/Hinkley engines: 5 ft drivers, wagon-top boiler, balloon spark-arresting stack,
  // square box headlamp, sand and steam domes, wooden cab, slatted pilot, 8-wheel tender. Built along +x, rail top at y=0.
  const g = new THREE.Group();
  const M = (c, o = {}) => new THREE.MeshStandardMaterial(Object.assign({color: c, roughness: .5, metalness: .2}, o));
  const russia = M(0x56646d, {metalness: .55, roughness: .35}), black = M(0x161616, {roughness: .7}), brass = M(0xc8a24a, {metalness: .85, roughness: .25});
  const red = M(0x8a2a1c, {metalness: .05}), wood = M(0x6e4528, {metalness: 0, roughness: .6}), steel = M(0x8c8c8c, {metalness: .8, roughness: .3}), green = M(0x2f4a35, {metalness: .1});
  const add = (geo, m, x, y, z, rx = 0, ry = 0, rz = 0, parent = g) => { const k = new THREE.Mesh(geo, m); k.position.set(x, y, z); k.rotation.set(rx, ry, rz); parent.add(k); return k; };
  const G = 1.435, DR = 0.79;   // gauge, driver radius
  // frame and running boards
  add(new THREE.BoxGeometry(7.4, .3, .9), black, .6, 1.05, 0);
  for (const z of [-1.05, 1.05]) add(new THREE.BoxGeometry(5.2, .05, .45), black, .9, 1.62, z);
  // boiler: barrel, wagon-top course and firebox, with brass bands
  add(new THREE.CylinderGeometry(.66, .66, 4.0, 32), russia, 2.2, 2.25, 0, 0, 0, Math.PI / 2);
  add(new THREE.CylinderGeometry(.74, .66, .6, 32), russia, .0, 2.33, 0, 0, 0, Math.PI / 2);
  add(new THREE.CylinderGeometry(.74, .74, 1.4, 32), russia, -.9, 2.33, 0, 0, 0, Math.PI / 2);
  add(new THREE.BoxGeometry(1.5, 1.1, 1.3), russia, -1.0, 1.6, 0);   // firebox between frames
  for (const x of [0.4, 1.4, 2.4, 3.4, -0.3, -1.5]) add(new THREE.TorusGeometry(x < 0 ? .745 : .665, .025, 6, 32), brass, x, x < 0 ? 2.33 : 2.25, 0, 0, Math.PI / 2, 0);
  // smokebox, front door, stack
  add(new THREE.CylinderGeometry(.7, .7, 1.1, 32), black, 4.7, 2.25, 0, 0, 0, Math.PI / 2);
  add(new THREE.CylinderGeometry(.62, .62, .06, 32), black, 5.27, 2.25, 0, 0, 0, Math.PI / 2);
  add(new THREE.CylinderGeometry(.08, .08, .06, 12), brass, 5.31, 2.25, 0, 0, 0, Math.PI / 2);
  add(new THREE.CylinderGeometry(.2, .24, 1.0, 16), black, 4.7, 3.35, 0);
  add(new THREE.CylinderGeometry(.62, .2, .9, 24), black, 4.7, 4.25, 0);        // balloon
  add(new THREE.CylinderGeometry(.64, .64, .12, 24), black, 4.7, 4.72, 0);
  add(new THREE.CylinderGeometry(.52, .62, .18, 24), black, 4.7, 4.86, 0);       // spark-arrestor cap
  // headlamp on a bracket with number boards
  add(new THREE.BoxGeometry(.5, .3, .5), black, 5.05, 3.05, 0);
  const lamp = add(new THREE.BoxGeometry(.75, .8, .7), black, 5.1, 3.6, 0);
  add(new THREE.CylinderGeometry(.3, .3, .05, 20), M(0xfff3c4, {emissive: 0x6b5a2a, metalness: .9, roughness: .1}), 5.48, 3.6, 0, 0, 0, Math.PI / 2);
  add(new THREE.BoxGeometry(.03, .4, .22), brass, 5.48, 3.6, .38); add(new THREE.BoxGeometry(.03, .4, .22), brass, 5.48, 3.6, -.38);
  add(new THREE.ConeGeometry(.45, .3, 4), black, 5.1, 4.15, 0, 0, Math.PI / 4);
  // domes, bell, whistle, sand pipes, handrails
  add(new THREE.CylinderGeometry(.3, .36, .55, 24), brass, 3.2, 3.15, 0); add(new THREE.SphereGeometry(.3, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), brass, 3.2, 3.42, 0);
  add(new THREE.CylinderGeometry(.33, .4, .65, 24), brass, 1.2, 3.2, 0); add(new THREE.SphereGeometry(.33, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), brass, 1.2, 3.52, 0);
  add(new THREE.BoxGeometry(.12, .3, .5), black, 2.2, 3.0, 0); const bell = add(new THREE.CylinderGeometry(.13, .25, .32, 16), brass, 2.2, 3.35, 0);
  add(new THREE.CylinderGeometry(.06, .08, .45, 12), brass, .1, 3.3, 0);
  for (const z of [-.4, .4]) add(new THREE.CylinderGeometry(.025, .025, 1.6, 6), brass, 3.0, 2.3, z, 0, 0, .4);
  for (const z of [-.72, .72]) add(new THREE.CylinderGeometry(.022, .022, 4.6, 6), brass, 2.3, 2.62, z, 0, 0, Math.PI / 2);
  // cylinders, steam chests, crossheads, guides
  for (const z of [-1.0, 1.0]) {
    add(new THREE.CylinderGeometry(.34, .34, 1.1, 24), russia, 4.0, 1.55, z, 0, 0, Math.PI / 2);
    for (const x of [3.45, 4.55]) add(new THREE.TorusGeometry(.34, .03, 6, 24), brass, x, 1.55, z, 0, Math.PI / 2, 0);
    add(new THREE.BoxGeometry(1.0, .4, .4), russia, 4.0, 2.05, z * .92);
    add(new THREE.BoxGeometry(1.6, .06, .08), steel, 2.75, 1.68, z); add(new THREE.BoxGeometry(1.6, .06, .08), steel, 2.75, 1.42, z);
    add(new THREE.BoxGeometry(.3, .3, .14), steel, 3.1, 1.55, z);
  }
  // drivers with counterweights, main and side rods, splashers
  const drivers = [0.15, -1.55];
  for (const x of drivers) for (const z of [-G / 2 - .02, G / 2 + .02]) {
    const w = spokedWheel(DR, red, steel, 16, red); w.position.set(x, DR, z); g.add(w);
    add(new THREE.CylinderGeometry(DR + .05, DR + .05, .3, 32, 1, true, Math.PI / 2 - .9, 1.8), black, x, DR + .02, z + (z > 0 ? .1 : -.1), Math.PI / 2, 0, 0);  // splasher
  }
  for (const z of [-G / 2 - .14, G / 2 + .14]) {
    add(new THREE.BoxGeometry(1.75, .1, .05), steel, -.7, DR - .3, z);                                  // side (coupling) rod
    const mr = add(new THREE.BoxGeometry(2.95, .12, .05), steel, 1.65, (DR - .3 + 1.55) / 2, z); mr.rotation.z = Math.atan2(1.55 - (DR - .3), 3.1 - .15);   // main rod
  }
  // pilot (engine) truck and slatted pilot
  for (const x of [3.6, 4.6]) for (const z of [-G / 2, G / 2]) { const w = spokedWheel(.42, black, steel, 10); w.position.set(x, .42, z); g.add(w); }
  for (let i = 0; i < 9; i++) { const zz = -.85 + i * .2125; const sl = add(new THREE.BoxGeometry(1.25, .05, .06), red, 5.75, .55, zz); sl.rotation.z = -.62; }
  add(new THREE.BoxGeometry(.12, .22, 2.0), red, 5.25, 1.0, 0); add(new THREE.BoxGeometry(.1, .1, 2.0), black, 6.2, .2, 0);
  add(new THREE.BoxGeometry(.25, .25, .3), black, 5.35, 1.0, 0);   // coupler
  // cab: varnished wood, arched windows, roof with overhang, number on the side
  const num = letterTex('No. 225', 256, 96, '#6e4528', '#e2c06a', 'bold 44px Georgia');
  add(new THREE.BoxGeometry(2.0, 1.5, 2.6), wood, -2.45, 2.05, 0);
  add(new THREE.BoxGeometry(2.0, 1.0, .1), wood, -2.45, 3.3, 1.25); add(new THREE.BoxGeometry(2.0, 1.0, .1), wood, -2.45, 3.3, -1.25);
  add(new THREE.BoxGeometry(.1, 1.0, 2.6), wood, -1.5, 3.3, 0);
  for (const z of [-1.31, 1.31]) { add(new THREE.PlaneGeometry(1.6, .5), new THREE.MeshStandardMaterial({map: num}), -2.45, 2.1, z, 0, z > 0 ? 0 : Math.PI, 0);
    for (const x of [-2.9, -2.0]) add(new THREE.BoxGeometry(.6, .7, .02), M(0x1b2226, {roughness: .1, metalness: .3}), x, 3.35, z * 1.0); }
  add(new THREE.BoxGeometry(2.6, .1, 3.0), wood, -2.45, 3.86, 0); add(new THREE.BoxGeometry(2.4, .12, 1.0), wood, -2.45, 3.97, 0);
  // tender: tank with flared coal space, two trucks, lettering
  const t = new THREE.Group(); g.add(t);
  const letters = letterTex('NORTHERN PACIFIC', 1024, 128, '#161616', '#d9b65a', 'bold 64px Georgia');
  add(new THREE.BoxGeometry(5.4, .25, 2.7), black, -6.45, 1.22, 0, 0, 0, 0, t);
  add(new THREE.BoxGeometry(5.0, 1.45, 2.6), black, -6.6, 2.05, 0, 0, 0, 0, t);
  for (const z of [-1.31, 1.31]) add(new THREE.PlaneGeometry(4.4, .55), new THREE.MeshStandardMaterial({map: letters}), -6.6, 2.15, z, 0, z > 0 ? 0 : Math.PI, 0, t);
  add(new THREE.BoxGeometry(2.6, .45, 2.9), black, -5.0, 2.95, 0, 0, 0, 0, t);           // flared coal board
  add(new THREE.BoxGeometry(2.3, .55, 2.3), M(0x1a1a1a, {roughness: 1}), -5.0, 3.0, 0, 0, 0, 0, t);
  add(new THREE.CylinderGeometry(.25, .25, .15, 16), black, -7.8, 2.85, 0, 0, 0, 0, t);  // water hatch
  for (const z of [-1.3, 1.3]) add(new THREE.BoxGeometry(5.0, .04, .04), brass, -6.6, 2.75, z, 0, 0, 0, t);
  t.add(truck(-5.1, .42, G, black, black)); t.add(truck(-8.0, .42, G, black, black));
  g.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return {g, length: 15.4};
}
function car(kind) {
  // wooden passenger equipment of the early 1880s: clerestory ("monitor") roof with duckbill ends, open end platforms
  // with railings and steps, truss rods and queen posts under the floor, two four-wheel trucks; along +x, rail top y=0.
  const len = kind === 'pullman' ? 17.5 : kind === 'baggage' ? 14 : 15.2, W = 2.9, g = new THREE.Group();
  const M = (c, o = {}) => new THREE.MeshStandardMaterial(Object.assign({color: c, roughness: .6, metalness: .05}, o));
  const body = kind === 'baggage' ? M(0x5b3a24, {map: TEX.boardbatten}) : M(0xffffff, {map: TEX.coach});
  const dark = M(0x2a2420), black = M(0x161616), brass = M(0xc8a24a, {metalness: .8, roughness: .3}), roof = M(0x3a3632, {roughness: .9});
  const add = (geo, m, x, y, z, rx = 0, ry = 0, rz = 0) => { const k = new THREE.Mesh(geo, m); k.position.set(x, y, z); k.rotation.set(rx, ry, rz); g.add(k); return k; };
  const label = kind === 'pullman' ? 'PULLMAN' : kind === 'baggage' ? 'BAGGAGE  NORTHERN PACIFIC  EXPRESS' : 'NORTHERN PACIFIC';
  const lt = letterTex(label, 1024, 64, kind === 'baggage' ? '#5b3a24' : '#5a3a26', '#e1bf63', 'bold 36px Georgia');
  add(new THREE.BoxGeometry(len, .3, W + .1), dark, 0, 1.25, 0);                                   // floor sill
  add(new THREE.BoxGeometry(len, 2.45, W), body, 0, 2.62, 0);
  if (kind === 'baggage') { for (const z of [-1, 1]) add(new THREE.BoxGeometry(1.5, 2.0, .05), M(0x47301e), 0, 2.45, z * (W / 2 + .03)); }
  for (const z of [-1, 1]) add(new THREE.PlaneGeometry(len * .7, .3), new THREE.MeshStandardMaterial({map: lt}), 0, 3.6, z * (W / 2 + .03), 0, z > 0 ? 0 : Math.PI, 0);
  add(new THREE.BoxGeometry(len + .1, .14, W + .5), roof, 0, 3.92, 0);                             // lower roof deck
  if (kind !== 'baggage' || true) {
    add(new THREE.BoxGeometry(len - 1.6, .45, 1.5), M(0x2e2924), 0, 4.2, 0);                       // clerestory with small windows
    for (let x = -len / 2 + 1.4; x < len / 2 - 1.2; x += .9) for (const z of [-.76, .76]) add(new THREE.BoxGeometry(.5, .22, .02), M(0x7a8a8f, {roughness: .2}), x, 4.2, z);
    add(new THREE.BoxGeometry(len - 1.4, .1, 1.9), roof, 0, 4.47, 0);
    for (const s of [-1, 1]) { const d = add(new THREE.CylinderGeometry(.95, .95, .55, 16, 1, false, 0, Math.PI), roof, s * (len / 2 - .55), 4.12, 0, 0, s > 0 ? -Math.PI / 2 : Math.PI / 2, Math.PI / 2); d.scale.set(1, 1, .5); }   // duckbill ends
  }
  // end platforms: deck, railings, steps, couplers
  for (const s of [-1, 1]) {
    const x = s * (len / 2 + .55);
    add(new THREE.BoxGeometry(1.1, .12, W - .2), dark, x, 1.2, 0);
    for (const z of [-1, 1]) { add(new THREE.BoxGeometry(.05, 1.0, .05), brass, s * (len / 2 + 1.05), 1.75, z * (W / 2 - .2)); add(new THREE.BoxGeometry(1.05, .05, .05), brass, x, 2.25, z * (W / 2 - .15));
      for (let k = 0; k < 2; k++) add(new THREE.BoxGeometry(.4, .04, .55), dark, s * (len / 2 + 1.0), .95 - k * .3, z * (W / 2 - .05)); }
    add(new THREE.BoxGeometry(.05, .7, 1.4), brass, s * (len / 2 + 1.07), 1.65, 0);
    add(new THREE.BoxGeometry(.4, .22, .3), black, s * (len / 2 + 1.2), 1.0, 0);
  }
  // truss rods and queen posts
  for (const z of [-.7, .7]) { add(new THREE.BoxGeometry(len * .5, .04, .04), black, 0, .82, z);
    for (const s of [-1, 1]) { const r = add(new THREE.BoxGeometry(len * .28, .04, .04), black, s * len * .37, .98, z); r.rotation.z = s * .07; add(new THREE.BoxGeometry(.08, .35, .08), black, s * len * .22, .95, z); } }
  add(new THREE.BoxGeometry(.8, .5, .5), black, len * .12, .85, 0);   // brake cylinder / box
  for (const s of [-1, 1]) g.add(truck(s * (len / 2 - 2.0), .45, 1.435, black, black));
  g.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return {g, length: len + 2.2};
}
export function buildTrestle(bents, zAt) {
  // open-deck timber pile trestle: bents = [[e, n, rail z], ...] one per bent, in order. Each bent has four round piles
  // down to the ground (or the river bed) under a 12x12 in cap; X-bracing on the taller bents; four stringers under the
  // ties and a guard timber each side. Rail level is the track's z (models.js buildTrack lays the ties and rails).
  const grp = new THREE.Group(), B = new Bucket();
  const PILES = [-1.9, -0.65, 0.65, 1.9], capTop = -0.505, capD = 0.35, capL = 4.8;
  for (let i = 0; i < bents.length; i++) {
    const [e, n, z] = bents[i], a = bents[Math.max(0, i - 1)], b = bents[Math.min(bents.length - 1, i + 1)];
    const ang = Math.atan2(b[1] - a[1], b[0] - a[0]), ux = Math.cos(ang), uy = Math.sin(ang), px = -uy, py = ux;
    const capZ = z + capTop - capD / 2;
    B.add('cap', box(e, capZ, -n, 0.32, capD, capL, ang));       // box x along the track (rotY = ang), z across
    let low = Infinity; const feet = [];
    for (const o of PILES) {
      const pe = e + px * o, pn = n + py * o, g = zAt(pe, pn) - 0.6, top = capZ - capD / 2;
      if (top - g < 0.2) continue;
      const c = new THREE.CylinderGeometry(0.15, 0.17, top - g, 8); c.translate(pe, (top + g) / 2, -pn); B.add('pile', c);
      low = Math.min(low, g + 0.6); feet.push([pe, pn, o]);
    }
    const top = capZ - capD / 2, h = top - low;
    if (h > 2.5) {          // sway bracing: two planks crossing between the outer piles, over the upper 4 m at most
      const zb = top - Math.min(h - 0.5, 4.0), w = 3.8, len = Math.hypot(w, top - zb), tilt = Math.atan2(top - zb, w);
      for (const sgn of [1, -1]) {
        const g = new THREE.BoxGeometry(len, 0.25, 0.08); g.rotateZ(sgn * tilt); g.rotateY(ang + Math.PI / 2);
        g.translate(e + ux * 0.2 * sgn, (top + zb) / 2, -(n + uy * 0.2 * sgn)); B.add('brace', g);
      }
    }
    if (i < bents.length - 1) {     // stringers and guard timbers to the next bent
      const L = Math.hypot(b[0] - e, b[1] - n), me = (e + b[0]) / 2, mn = (n + b[1]) / 2, mz = (z + b[2]) / 2;
      for (const o of [-0.95, -0.45, 0.45, 0.95]) B.add('stringer', box(me + px * o, mz - 0.28, -(mn + py * o), L + 0.3, 0.45, 0.22, ang));
      for (const o of [-1.35, 1.35]) B.add('stringer', box(me + px * o, mz + 0.12, -(mn + py * o), L + 0.05, 0.2, 0.2, ang));
    }
  }
  const mats = k => new THREE.MeshStandardMaterial({color: k === 'pile' ? 0x5b4c3d : k === 'brace' ? 0x6a5a48 : 0x56483a, roughness: 1});
  for (const m of B.meshes(mats)) grp.add(m);
  return grp;
}
export function buildTrain(dense, atE, atN) {
  // standing just west of the depot with the engine pointing west (the westbound Pacific Express)
  let bi = 0, bd = 1e9; dense.forEach((p, i) => { const d = Math.hypot(p[0] - atE, p[1] - atN); if (d < bd) { bd = d; bi = i; } });
  const cum = [0]; for (let i = 1; i < dense.length; i++) cum.push(cum[i - 1] + Math.hypot(dense[i][0] - dense[i - 1][0], dense[i][1] - dense[i - 1][1]));
  const fwd = dense[0][0] < dense[dense.length - 1][0] ? -1 : 1;     // direction of travel (west) in terms of s
  const at = (s) => {
    s = Math.max(0, Math.min(cum[cum.length - 1], s)); let i = 1; while (i < cum.length - 1 && cum[i] < s) i++;
    const a = dense[i - 1], b = dense[i], t = (s - cum[i - 1]) / ((cum[i] - cum[i - 1]) || 1);
    let h = Math.atan2(b[1] - a[1], b[0] - a[0]); if (fwd < 0) h += Math.PI;
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t, h];
  };
  const grp = new THREE.Group();
  const place = (obj, s) => { const q = at(s); obj.position.set(q[0], q[2] + 0.35, -q[1]); obj.rotation.y = q[3]; grp.add(obj); };
  // pulled up short of the station: the last car stops about 12 m west of the depot, so the depot stays in view
  const cars = ['baggage', 'coach', 'coach', 'pullman'].map(k => car(k));
  const len = 9.4 + cars.reduce((t, c) => t + c.length + 0.6, 0);
  const s0 = cum[bi] + fwd * (12 + len);            // engine origin
  const loco = locomotive(); place(loco.g, s0);
  let s = s0 - fwd * 9.4;                           // rear of the tender (tender ends 9.3 m behind the engine origin)
  for (const c of cars) { s -= fwd * (c.length / 2 + 0.3); place(c.g, s); s -= fwd * (c.length / 2 + 0.3); }
  grp.traverse(o => { if (o.isMesh) o.castShadow = true; });
  return grp;
}

// ---------------------------------------------------------------- confidence markers
const GRADE_LOOK = {A: ['#2f5d3a', 'A', 'Documented'], B: ['#3e6e86', 'B', 'Supported'], C: ['#b07a1c', 'C', 'Inferred'], D: ['#8a2a1c', 'D', 'Conjectural']};
const MARK_TEX = {};
export function gradeMarker(grade) {
  if (!MARK_TEX[grade]) {
    const [col, letter] = GRADE_LOOK[grade] || GRADE_LOOK.D;
    const c = document.createElement('canvas'); c.width = 128; c.height = 160; const g = c.getContext('2d');
    g.fillStyle = col; g.strokeStyle = '#f3efe6'; g.lineWidth = 8;
    g.beginPath(); g.moveTo(64, 156); g.lineTo(24, 96); g.arc(64, 64, 52, Math.PI * 0.8, Math.PI * 0.2); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#f3efe6'; g.font = 'bold 64px Georgia'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(letter, 64, 66);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; MARK_TEX[grade] = t;
  }
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({map: MARK_TEX[grade], depthTest: true, transparent: true}));
  sp.center.set(0.5, 0); sp.renderOrder = 10; sp.userData.isMarker = true;
  return sp;
}

// front face of a detailed building, for placing details in front of / behind it
export function frontInfo(f, ctx) {
  const st = f.style || {}, Fr = rectFrame(f.rect);
  const dir = st.front ? DIRS[st.front] : ctx.streetDir(f);
  const cands = [[Fr.v, Fr.L, Fr.W], [[-Fr.v[0], -Fr.v[1]], Fr.L, Fr.W], [Fr.u, Fr.W, Fr.L], [[-Fr.u[0], -Fr.u[1]], Fr.W, Fr.L]];
  let best = cands[0], bd = -9; for (const c of cands) { const d = c[0][0] * dir[0] + c[0][1] * dir[1]; if (d > bd) { bd = d; best = c; } }
  return {c: Fr.c, front: best[0], len: best[1], depth: best[2]};
}
