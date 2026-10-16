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
const MATS = new Map();
function mat(key, grade) {
  const k = key + '|' + grade;
  if (MATS.has(k)) return MATS.get(k);
  const [kind, color] = key.split('#');
  const col = color ? new THREE.Color('#' + color) : new THREE.Color(0xffffff);
  const map = {wall_clapboard: TEX.clapboard, wall_drop: TEX.drop, wall_boardbatten: TEX.boardbatten, wall_brick: TEX.brick, wall_yellowbrick: TEX.yellowbrick, wall_log: TEX.log,
    roof_shingle: TEX.shingle, roof_tin: TEX.tin, roof_sod: TEX.sod, window: TEX.window, windowArched: TEX.windowArched, door: TEX.door, storefront: TEX.storefront,
    plank: TEX.plank, trim: null, stone: null, dark: null, coach: TEX.coach}[kind];
  const m = new THREE.MeshStandardMaterial({color: col, map: map || null, roughness: kind.startsWith('roof_tin') ? 0.55 : 0.92, metalness: kind === 'roof_tin' ? 0.3 : 0, side: THREE.DoubleSide});
  if (grade === 'C') { m.transparent = true; m.opacity = 0.8; }
  if (grade === 'D') { m.transparent = true; m.opacity = 0.45; m.depthWrite = false; }
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

function buildBlock(bk, f, st, z0, H, R, frontDir, grade) {
  // one rectangular building block: walls, gables, roof, windows, doors, porch, chimneys, extras
  const F = rectFrame(R), hl = F.L / 2, hw = F.W / 2;
  const wallKey = `wall_${st.wall}#${(st.wall_color || '#e9e3d6').slice(1)}`;
  const trimKey = `trim#${(st.trim || '#f3efe6').slice(1)}`;
  const roofKey = `roof_${st.roof || 'shingle'}#${(st.roof_color || (st.roof === 'tin' ? '#8d9296' : st.roof === 'sod' ? '#7d7a58' : '#6e655c')).slice(1)}`;
  // faces in local frame: +v side, -v side (long faces), +u end, -u end (short faces)
  const faces = [
    {name: '+v', a: [-hl, hw], b: [hl, hw], n: F.v, len: F.L, long: true},
    {name: '-v', a: [hl, -hw], b: [-hl, -hw], n: [-F.v[0], -F.v[1]], len: F.L, long: true},
    {name: '+u', a: [hl, hw], b: [hl, -hw], n: F.u, len: F.W, long: false},
    {name: '-u', a: [-hl, -hw], b: [-hl, hw], n: [-F.u[0], -F.u[1]], len: F.W, long: false},
  ];
  // which face is the front
  let front = faces[1];
  if (frontDir) { let best = -9; for (const fc of faces) { const d = fc.n[0] * frontDir[0] + fc.n[1] * frontDir[1]; if (d > best) { best = d; front = fc; } } }
  // ridge axis: 'long' runs along u; 'front' runs perpendicular to the front face
  let ridgeAlongU = true;
  if (st.ridge === 'front') ridgeAlongU = !front.long;
  const roofType = st.ridge === 'flat' ? 'flat' : (st.ridge === 'hip' ? 'hip' : 'gable');
  const span = ridgeAlongU ? F.W : F.L;
  const ridgeH = roofType === 'flat' ? H : H + Math.min(span * 0.42, 4.5);
  const L3 = (a, b, h) => { const p = P2(F, a, b); return V(p[0], p[1], z0 + h); };
  // walls
  for (const fc of faces) {
    const A = fc.a, B = fc.b;
    bk.add(wallKey, quad(L3(A[0], A[1], -0.4), L3(B[0], B[1], -0.4), L3(B[0], B[1], H), L3(A[0], A[1], H), [0, -0.4], [fc.len, -0.4], [fc.len, H], [0, H]));
    // gable triangles on the ends the ridge points at
    const isGableEnd = roofType === 'gable' && ((ridgeAlongU && !fc.long) || (!ridgeAlongU && fc.long));
    if (isGableEnd) {
      const m = [(A[0] + B[0]) / 2, (A[1] + B[1]) / 2];
      bk.add(wallKey, tri(L3(A[0], A[1], H), L3(B[0], B[1], H), L3(m[0], m[1], ridgeH), [0, H], [fc.len, H], [fc.len / 2, ridgeH]));
    }
  }
  // roof
  const o = 0.35;   // overhang
  if (roofType === 'flat') {
    bk.add(roofKey, quad(L3(-hl, -hw, H + .05), L3(hl, -hw, H + .05), L3(hl, hw, H + .05), L3(-hl, hw, H + .05), [-hl, -hw], [hl, -hw], [hl, hw], [-hl, hw]));
    const ph = st.parapet || 0.8;   // parapet / cornice all round
    for (const fc of faces) bk.add(wallKey, quad(L3(fc.a[0], fc.a[1], H), L3(fc.b[0], fc.b[1], H), L3(fc.b[0], fc.b[1], H + ph), L3(fc.a[0], fc.a[1], H + ph), [0, H], [fc.len, H], [fc.len, H + ph], [0, H + ph]));
    bk.add(trimKey, box(...(() => { const p = P2(F, 0, 0); return [p[0], z0 + H + ph, -p[1]]; })(), F.L + .3, .18, F.W + .3, Math.atan2(F.u[1], F.u[0])));
  } else {
    // ridge endpoints in (along, across)
    let r0, r1;
    if (ridgeAlongU) { r0 = [-hl - o, 0]; r1 = [hl + o, 0]; } else { r0 = [0, -hw - o]; r1 = [0, hw + o]; }
    if (roofType === 'hip') { const k = Math.min(span / 2, (ridgeAlongU ? F.L : F.W) / 2 - 0.3); if (ridgeAlongU) { r0 = [-hl + k, 0]; r1 = [hl - k, 0]; } else { r0 = [0, -hw + k]; r1 = [0, hw - k]; } }
    const C = [[-hl - o, -hw - o], [hl + o, -hw - o], [hl + o, hw + o], [-hl - o, hw + o]];
    const he = H - 0.15;
    const near = (p) => (Math.hypot(p[0] - r0[0], p[1] - r0[1]) < Math.hypot(p[0] - r1[0], p[1] - r1[1])) ? r0 : r1;
    for (let i = 0; i < 4; i++) {
      const p = C[i], q = C[(i + 1) % 4], np = near(p), nq = near(q);
      const run = Math.hypot(q[0] - p[0], q[1] - p[1]), slope = Math.hypot(span / 2 + o, ridgeH - he);
      if (np === nq) {
        if (roofType === 'gable') continue;               // gable end: no roof face
        bk.add(roofKey, tri(L3(p[0], p[1], he), L3(q[0], q[1], he), L3(np[0], np[1], ridgeH), [0, 0], [run, 0], [run / 2, slope]));
      } else {
        bk.add(roofKey, quad(L3(p[0], p[1], he), L3(q[0], q[1], he), L3(nq[0], nq[1], ridgeH), L3(np[0], np[1], ridgeH), [0, 0], [run, 0], [run, slope], [0, slope]));
      }
    }
    // ridge cap
    const rm = [(r0[0] + r1[0]) / 2, (r0[1] + r1[1]) / 2], rl = Math.hypot(r1[0] - r0[0], r1[1] - r0[1]);
    if (rl > 0.2) { const p = P2(F, rm[0], rm[1]); const ang = ridgeAlongU ? Math.atan2(F.u[1], F.u[0]) : Math.atan2(F.v[1], F.v[0]); bk.add(roofKey, box(p[0], z0 + ridgeH + .03, -p[1], rl, .12, .3, ang)); }
  }
  // trim: corner boards and a fascia band at the eaves
  for (const fc of faces) { const p = P2(F, fc.a[0], fc.a[1]); bk.add(trimKey, box(p[0], z0 + H / 2 - .2, -p[1], .16, H + .4, .16)); }
  // windows and doors
  const stories = Math.max(1, Math.floor(st.stories || 1)), half = (st.stories || 1) % 1 > 0;
  const sh = Math.min(3.8, H / ((st.stories || 1) + (half ? 0.2 : 0)));
  const arched = !!st.arched, winKey = arched ? 'windowArched' : 'window';
  const put = (fc, along, bottom, w, h, key, out = 0.04) => {
    // along: 0..len from fc.a towards fc.b
    const t0 = along - w / 2, t1 = along + w / 2;
    const ax = fc.a[0] + (fc.b[0] - fc.a[0]) * t0 / fc.len, ay = fc.a[1] + (fc.b[1] - fc.a[1]) * t0 / fc.len;
    const bx = fc.a[0] + (fc.b[0] - fc.a[0]) * t1 / fc.len, by = fc.a[1] + (fc.b[1] - fc.a[1]) * t1 / fc.len;
    const pa = P2(F, ax, ay), pb = P2(F, bx, by), ox = fc.n[0] * out, oy = fc.n[1] * out;
    bk.add(key, quad(V(pa[0] + ox, pa[1] + oy, z0 + bottom), V(pb[0] + ox, pb[1] + oy, z0 + bottom), V(pb[0] + ox, pb[1] + oy, z0 + bottom + h), V(pa[0] + ox, pa[1] + oy, z0 + bottom + h), [0, 0], [1, 0], [1, 1], [0, 1]));
  };
  for (const fc of faces) {
    const isFront = fc === front;
    let n = fc.long ? (st.bays ?? Math.round(fc.len / 3)) : (st.gable_bays ?? 1);
    if (n <= 0 && !isFront) continue;
    for (let s = 0; s < stories + (half && !fc.long && roofType === 'gable' ? 1 : 0); s++) {
      let nn = (s >= 1 && st.upper_bays && fc.long) ? st.upper_bays : n;
      if (s === stories) nn = Math.max(1, Math.min(2, n));   // half-story gable window(s)
      const bottom = s * sh + 0.95 * (s === 0 ? 1 : 0.8);
      for (let i = 0; i < nn; i++) {
        const along = fc.len * (i + 0.5) / nn;
        if (isFront && s === 0) continue;                    // ground floor of the front is done below
        if (st.barn && s === 0) continue;
        put(fc, along, bottom, 0.9, Math.min(1.6, sh * 0.5), winKey);
      }
    }
    if (isFront) {
      if (st.storefront) {
        const w = Math.min(fc.len - 0.6, 6.2); put(fc, fc.len / 2, 0.15, w, Math.min(3.0, sh - 0.4), 'storefront');
        for (let i = 0; i < Math.floor((fc.len - w) / 2.6); i++) { put(fc, 1.2 + i * 2.6, .95, .9, 1.6, winKey); put(fc, fc.len - 1.2 - i * 2.6, .95, .9, 1.6, winKey); }
      } else if (st.barn) {
        put(fc, fc.len / 2, 0.05, Math.min(3.6, fc.len * .4), Math.min(3.4, H - .4), 'door');
      } else {
        const nn = Math.max(2, n); put(fc, fc.len / 2, 0.05, 1.05, 2.25, 'door');
        for (let i = 0; i < nn; i++) { const along = fc.len * (i + 0.5) / nn; if (Math.abs(along - fc.len / 2) > 1.1) put(fc, along, .95, .9, Math.min(1.6, sh * .5), winKey); }
      }
    }
  }
  // fanlight in the front gable (Roberts Hall)
  if (st.fanlight) put(front, front.len / 2, H + 0.4, 1.4, 1.0, 'windowArched');
  // false front: a tall square facade hiding the gable
  if (st.false_front && roofType === 'gable' && !ridgeAlongU === front.long) {
    const p = front; bk.add(wallKey, quad(L3(p.a[0], p.a[1], H), L3(p.b[0], p.b[1], H), L3(p.b[0], p.b[1], ridgeH + .5), L3(p.a[0], p.a[1], ridgeH + .5), [0, H], [p.len, H], [p.len, ridgeH + .5], [0, ridgeH + .5]));
    const q = [(p.a[0] + p.b[0]) / 2 + p.n[0] * 0.08 * 0, (p.a[1] + p.b[1]) / 2];
  }
  // porches
  for (const pc of (st.porch || [])) {
    const dir = DIRS[pc.side] || [front.n[0], front.n[1]];
    let fc = faces[0], best = -9; for (const x of faces) { const d = x.n[0] * dir[0] + x.n[1] * dir[1]; if (d > best) { best = d; fc = x; } }
    const d = pc.depth || 2.4, ph = Math.min(3.0, sh - 0.2);
    const mid = [(fc.a[0] + fc.b[0]) / 2, (fc.a[1] + fc.b[1]) / 2];
    const nl = [fc.n[0] * F.u[0] + fc.n[1] * F.u[1], fc.n[0] * F.v[0] + fc.n[1] * F.v[1]];   // normal in local frame
    const out = [mid[0] + nl[0] * d / 2, mid[1] + nl[1] * d / 2], pw = P2(F, out[0], out[1]);
    const ang = -Math.atan2(fc.b[1] - fc.a[1], fc.b[0] - fc.a[0]) - Math.atan2(F.u[1], F.u[0]);
    const rot = Math.atan2(...(() => { const t = P2(F, fc.b[0], fc.b[1]), s = P2(F, fc.a[0], fc.a[1]); return [t[1] - s[1], t[0] - s[0]]; })());
    bk.add('plank#9a8466', box(pw[0], z0 + 0.25, -pw[1], fc.len, 0.3, d, rot));
    const roofP = [mid[0] + nl[0] * (d + .2), mid[1] + nl[1] * (d + .2)];
    // sloping porch roof
    const s0 = P2(F, fc.a[0], fc.a[1]), s1 = P2(F, fc.b[0], fc.b[1]);
    const ox = (fc.n[0]) * (d + .25), oy = (fc.n[1]) * (d + .25);
    bk.add(roofKey, quad(V(s1[0] + ox, s1[1] + oy, z0 + ph), V(s0[0] + ox, s0[1] + oy, z0 + ph), V(s0[0], s0[1], z0 + ph + .7), V(s1[0], s1[1], z0 + ph + .7), [0, 0], [fc.len, 0], [fc.len, d], [0, d]));
    const posts = Math.max(2, Math.round(fc.len / 2.6) + 1);
    for (let i = 0; i < posts; i++) { const t = i / (posts - 1); const x = s0[0] + (s1[0] - s0[0]) * t + fc.n[0] * (d - .15), y = s0[1] + (s1[1] - s0[1]) * t + fc.n[1] * (d - .15); bk.add(trimKey, box(x, z0 + ph / 2 + .2, -y, .14, ph - .2, .14)); }
  }
  // outside stair (Ferris store, Roberts Hall)
  if (st.outside_stair) {
    const dir = DIRS[st.outside_stair]; let fc = faces[0], best = -9; for (const x of faces) { const d = x.n[0] * dir[0] + x.n[1] * dir[1]; if (d > best) { best = d; fc = x; } }
    const s0 = P2(F, fc.a[0], fc.a[1]), s1 = P2(F, fc.b[0], fc.b[1]), tl = Math.min(fc.len - 1, sh * 1.6);
    const steps = 14;
    for (let i = 0; i < steps; i++) { const t = (fc.len - 0.8 - tl * (i / steps)) / fc.len; const x = s0[0] + (s1[0] - s0[0]) * t + fc.n[0] * .7, y = s0[1] + (s1[1] - s0[1]) * t + fc.n[1] * .7; bk.add('plank#8c7558', box(x, z0 + sh * (i + 1) / steps, -y, .9, .08, .9)); }
  }
  // depot bay window
  if (st.bay_window) { const m = [(front.a[0] + front.b[0]) / 2, (front.a[1] + front.b[1]) / 2], p = P2(F, m[0], m[1]); bk.add(wallKey, box(p[0] + front.n[0] * .45, z0 + 1.4, -(p[1] + front.n[1] * .45), 2.4, 2.8, .9, Math.atan2(F.u[1], F.u[0]))); }
  // chimneys on the ridge
  const nch = st.chimneys ?? 1;
  for (let i = 0; i < nch; i++) {
    const t = nch === 1 ? 0.25 : (i / (nch - 1) - 0.5) * 0.7;
    const a = ridgeAlongU ? [F.L * t, 0] : [0, F.W * t], p = P2(F, a[0], a[1]);
    bk.add('wall_brick#9c5a44', box(p[0], z0 + ridgeH + 0.3, -p[1], .55, 1.8, .55));
  }
  // church belfry over the front gable
  if (st.belfry) {
    const m = [(front.a[0] + front.b[0]) / 2 * .85, (front.a[1] + front.b[1]) / 2 * .85], p = P2(F, m[0], m[1]);
    bk.add(wallKey.replace(/^wall_[a-z]+/, 'wall_clapboard').replace(/#.*/, '#efe9dc'), box(p[0], z0 + ridgeH + 1.0, -p[1], 1.8, 2.6, 1.8));
    const g = new THREE.ConeGeometry(1.5, 2.4, 4).toNonIndexed(); g.rotateY(Math.PI / 4 + Math.atan2(F.u[1], F.u[0])); g.translate(p[0], z0 + ridgeH + 3.5, -p[1]); bk.add(roofKey, g);
  }
  // cupola (packing plant, ice house)
  if (st.cupola) { const p = P2(F, 0, 0); bk.add(wallKey, box(p[0], z0 + ridgeH + .6, -p[1], 2.2, 1.6, 2.2)); const g = new THREE.ConeGeometry(1.8, 1.4, 4).toNonIndexed(); g.rotateY(Math.PI / 4 + Math.atan2(F.u[1], F.u[0])); g.translate(p[0], z0 + ridgeH + 2.1, -p[1]); bk.add(roofKey, g); }
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

export function buildDetailed(f, ctx) {
  // returns a THREE.Group, or null if the feature has no detailed style
  const st = f.style; if (!st || !f.rect) return null;
  const grade = ctx.grade(f), m = f.massing || {};
  const H = m.eave > 0 ? m.eave : (st.stories >= 2 ? 7 : st.stories >= 1.5 ? 4.5 : 3.2);
  const bk = new Bucket();
  let frontDir = st.front ? DIRS[st.front] : ctx.streetDir(f);
  let rects = st.blocks || (st.split ? splitRect(f.rect, st.split.n, st.split.gap) : [f.rect]);
  rects.forEach((R, i) => {
    const z0 = Math.min(...R.map(p => ctx.zAt(p[0], p[1])));
    const s2 = (st.blocks && i > 0) ? Object.assign({}, st, {stories: 1.5, porch: [], chimneys: 1}) : st;
    const H2 = (st.blocks && i > 0) ? H * 0.7 : H;
    buildBlock(bk, f, s2, z0, H2, R, frontDir, grade);
  });
  // the hotel's taller end block
  if (st.end_block) {
    const F = rectFrame(f.rect), d = DIRS[st.end_block.end], sgn = Math.sign(F.u[0] * d[0] + F.u[1] * d[1]) || 1, L = st.end_block.len;
    const a0 = sgn > 0 ? F.L / 2 - L : -F.L / 2, a1 = a0 + L;
    const R = [P2(F, a0, -F.W / 2 - .2), P2(F, a1, -F.W / 2 - .2), P2(F, a1, F.W / 2 + .2), P2(F, a0, F.W / 2 + .2)];
    const z0 = Math.min(...R.map(p => ctx.zAt(p[0], p[1])));
    buildBlock(bk, f, Object.assign({}, st, {ridge: 'front', porch: [], chimneys: 1, bays: 2, gable_bays: 3, stories: 2.5}), z0, H + st.end_block.extra, R, d, grade);
  }
  const grp = new THREE.Group();
  for (const mesh of bk.meshes(k => mat(k, grade))) { mesh.userData = f; grp.add(mesh); }
  return grp;
}

// ---------------------------------------------------------------- streets
export function buildStreets(streets, t) {
  const grp = new THREE.Group();
  const matDirt = new THREE.MeshStandardMaterial({map: TEX.dirt, color: 0xffffff, roughness: 1, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2});
  const matTrail = matDirt.clone(); matTrail.opacity = 0.85;
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
    else m = s.kind === 'trail' ? matTrail : matDirt;
    const mesh = new THREE.Mesh(g, m); mesh.receiveShadow = true; mesh.userData = {street: s}; grp.add(mesh);
  }
  return grp;
}

// ---------------------------------------------------------------- railroad track and train
export function buildTrack(line) {
  const grp = new THREE.Group();
  // ballast bed
  const pos = [], uv = [], idx = []; let dist = 0;
  const dense = []; for (let i = 0; i < line.length - 1; i++) { const a = line[i], b = line[i + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.ceil(L / 2)); for (let k = 0; k < n; k++) { const t = k / n; dense.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]); } } dense.push(line[line.length - 1]);
  dense.forEach((p, i) => {
    const a = dense[Math.max(0, i - 1)], b = dense[Math.min(dense.length - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1]; const L = Math.hypot(dx, dy) || 1; dx /= L; dy /= L;
    if (i) dist += Math.hypot(p[0] - dense[i - 1][0], p[1] - dense[i - 1][1]);
    const nx = -dy * 1.9, ny = dx * 1.9;
    pos.push(p[0] + nx, p[2] - .1, -(p[1] + ny), p[0] - nx, p[2] - .1, -(p[1] - ny)); uv.push(0, dist / 2, 2, dist / 2);
    if (i) { const k = i * 2; idx.push(k - 2, k - 1, k, k - 1, k + 1, k); }
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

function locomotive() {
  // Northern Pacific 4-4-0 "American" of the early 1880s: balloon spark-arresting stack, Russia-iron boiler,
  // brass bands and dome, wooden cab, cowcatcher, four drivers and a four-wheel truck; 8-wheel tender.
  // Built along +x (forward), track centre at y=0 (railhead), metres.
  const g = new THREE.Group();
  const M = (c, o = {}) => new THREE.MeshStandardMaterial(Object.assign({color: c, roughness: .55, metalness: .25}, o));
  const iron = M(0x46525a, {metalness: .5, roughness: .4}), black = M(0x1c1c1c), brass = M(0xc9a54a, {metalness: .8, roughness: .3}), red = M(0x7e2a1e, {metalness: 0}), wood = M(0x6b4a32, {metalness: 0});
  const add = (geo, m, x, y, z, rx = 0, ry = 0, rz = 0) => { const k = new THREE.Mesh(geo, m); k.position.set(x, y, z); k.rotation.set(rx, ry, rz); k.castShadow = true; g.add(k); return k; };
  add(new THREE.CylinderGeometry(.68, .68, 6.2, 24), iron, 1.4, 2.25, 0, 0, 0, Math.PI / 2);               // boiler
  add(new THREE.CylinderGeometry(.74, .74, .5, 24), black, 4.4, 2.25, 0, 0, 0, Math.PI / 2);               // smokebox front
  add(new THREE.CylinderGeometry(.18, .18, 1.0, 12), black, 4.3, 3.2, 0);                                    // stack pipe
  add(new THREE.CylinderGeometry(.55, .2, 1.0, 16), black, 4.3, 4.1, 0);                                     // balloon stack
  add(new THREE.CylinderGeometry(.3, .32, .55, 16), brass, 2.3, 3.1, 0);                                     // sand dome
  add(new THREE.CylinderGeometry(.32, .35, .65, 16), brass, 0.6, 3.15, 0);                                   // steam dome
  add(new THREE.SphereGeometry(.3, 12, 8), brass, 0.6, 3.5, 0);
  add(new THREE.CylinderGeometry(.22, .22, .55, 12), black, 4.6, 3.2, 0, 0, 0, Math.PI / 2);                // headlight base
  add(new THREE.BoxGeometry(.7, .75, .7), black, 4.75, 3.55, 0);                                            // big box headlamp
  add(new THREE.BoxGeometry(.06, .45, .45), brass, 5.12, 3.55, 0);
  [-1.1, 1.1].forEach(z => add(new THREE.CylinderGeometry(.4, .4, 1.1, 16), iron, 3.6, 1.55, z * .8, 0, 0, Math.PI / 2));   // cylinders
  for (const x of [-1.0, 0.9]) for (const z of [-.78, .78]) { add(new THREE.CylinderGeometry(.85, .85, .14, 24), red, x, .87, z, Math.PI / 2); add(new THREE.CylinderGeometry(.2, .2, .2, 12), black, x, .87, z, Math.PI / 2); }   // drivers (red wheel centres)
  for (const x of [3.0, 4.2]) for (const z of [-.78, .78]) add(new THREE.CylinderGeometry(.42, .42, .12, 16), black, x, .45, z, Math.PI / 2);   // pilot truck
  add(new THREE.BoxGeometry(6.8, .35, 1.9), black, 0.8, 1.15, 0);                                            // frame / running board
  add(new THREE.CylinderGeometry(.05, .05, 3.6, 8), brass, 0.0, 1.6, .7, 0, 0, Math.PI / 2);                 // brass handrail
  // cowcatcher: slatted wedge
  const cc = new THREE.Shape([new THREE.Vector2(0, 0), new THREE.Vector2(1.2, .05), new THREE.Vector2(0, .95)]);
  const ccg = new THREE.ExtrudeGeometry(cc, {depth: 1.8, bevelEnabled: false}); ccg.translate(0, 0, -.9); add(ccg, red, 4.9, .15, 0);
  // cab (varnished wood) with roof and windows
  add(new THREE.BoxGeometry(2.0, 2.3, 2.4), wood, -2.4, 2.65, 0);
  add(new THREE.BoxGeometry(2.4, .14, 2.7), black, -2.4, 3.86, 0);
  [-1.21, 1.21].forEach(z => add(new THREE.BoxGeometry(.9, .7, .02), M(0x1f282b), -2.2, 3.0, z));
  add(new THREE.CylinderGeometry(.25, .25, .25, 12), brass, -0.8, 3.35, 0);                                  // whistle/bell
  // tender
  const t = new THREE.Group(); g.add(t);
  const tb = new THREE.Mesh(new THREE.BoxGeometry(5.0, 1.6, 2.6), black); tb.position.set(-6.4, 2.0, 0); tb.castShadow = true; t.add(tb);
  const coal = new THREE.Mesh(new THREE.BoxGeometry(3.0, .4, 2.2), M(0x222222, {roughness: 1})); coal.position.set(-5.6, 2.9, 0); t.add(coal);
  for (const x of [-4.6, -5.4, -7.4, -8.2]) for (const z of [-.78, .78]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(.42, .42, .12, 16), black); w.rotation.x = Math.PI / 2; w.position.set(x, .45, z); t.add(w); }
  const lettering = new THREE.Mesh(new THREE.BoxGeometry(3.4, .12, .02), brass); lettering.position.set(-6.4, 2.2, 1.31); t.add(lettering);
  return {g, length: 13.5, front: 5.6};
}
function car(kind) {
  // wooden passenger, baggage or stock car of the period, about 15-18 m, with clerestory roof; along +x
  const len = kind === 'pullman' ? 18 : kind === 'stock' ? 10.5 : 15, g = new THREE.Group();
  const body = new THREE.MeshStandardMaterial({color: kind === 'stock' ? 0x7a3a26 : 0xffffff, map: kind === 'stock' ? TEX.boardbatten : TEX.coach, roughness: .6});
  if (kind === 'baggage') { body.map = TEX.boardbatten; body.color.set(0x6a4028); }
  const b = new THREE.Mesh(new THREE.BoxGeometry(len, 2.7, 3.0), [body, body, new THREE.MeshStandardMaterial({color: 0x3a3a38}), body, body, body]); b.position.set(0, 2.55, 0); b.castShadow = true; g.add(b);
  if (kind !== 'stock') { const cl = new THREE.Mesh(new THREE.BoxGeometry(len - 2, .5, 1.6), new THREE.MeshStandardMaterial({color: 0x2e2a26})); cl.position.set(0, 4.15, 0); g.add(cl); }
  const roof = new THREE.Mesh(new THREE.BoxGeometry(len + .4, .18, 3.3), new THREE.MeshStandardMaterial({color: 0x3a3634})); roof.position.set(0, 3.95, 0); g.add(roof);
  for (const end of [-1, 1]) { const pl = new THREE.Mesh(new THREE.BoxGeometry(.9, .2, 2.6), new THREE.MeshStandardMaterial({color: 0x2a2a2a})); pl.position.set(end * (len / 2 + .45), 1.2, 0); g.add(pl); }
  for (const x of [-len / 2 + 2, -len / 2 + 3.4, len / 2 - 3.4, len / 2 - 2]) for (const z of [-.78, .78]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(.45, .45, .12, 16), new THREE.MeshStandardMaterial({color: 0x1c1c1c})); w.rotation.x = Math.PI / 2; w.position.set(x, .45, z); g.add(w); }
  return {g, length: len + 1};
}
export function buildTrain(dense, atE, atN) {
  // parked at the depot with the engine pointing west (the westbound Pacific Express)
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
  const place = (obj, s) => { const q = at(s); obj.position.set(q[0], q[2] + 0.3, -q[1]); obj.rotation.y = q[3]; grp.add(obj); };
  const s0 = cum[bi] + fwd * 22;                    // engine (its origin) about 22 m west of the depot
  const loco = locomotive(); place(loco.g, s0);
  let s = s0 - fwd * 9.4;                           // rear of the tender
  for (const k of ['baggage', 'coach', 'coach', 'pullman']) { const c = car(k); s -= fwd * (c.length / 2 + 0.3); place(c.g, s); s -= fwd * (c.length / 2 + 0.3); }
  grp.traverse(o => { if (o.isMesh) o.castShadow = true; });
  return grp;
}
