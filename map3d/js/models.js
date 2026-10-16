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
    if (st.blank && (key === 'window' || key === 'windowArched')) return;
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
  // roof monitor along a flat roof (packing house)
  if (st.monitor && roofType === 'flat') { const p = P2(F, 0, 0); bk.add(wallKey, box(p[0], z0 + H + 0.9, -p[1], F.L * 0.7, 1.4, 2.4, Math.atan2(F.u[1], F.u[0]))); bk.add(roofKey, box(p[0], z0 + H + 1.65, -p[1], F.L * 0.7 + .4, .12, 3.0, Math.atan2(F.u[1], F.u[0]))); }
  // ridge ventilators (sheds)
  if (st.vents && roofType !== 'flat') for (let i = 0; i < st.vents; i++) {
    const t = (i + 0.5) / st.vents - 0.5, a = ridgeAlongU ? [F.L * t * .9, 0] : [0, F.W * t * .9], p = P2(F, a[0], a[1]);
    bk.add(wallKey, box(p[0], z0 + ridgeH + .35, -p[1], 1.1, .8, 1.1)); const g = new THREE.ConeGeometry(.95, .6, 4).toNonIndexed(); g.rotateY(Math.PI / 4 + Math.atan2(F.u[1], F.u[0])); g.translate(p[0], z0 + ridgeH + 1.05, -p[1]); bk.add(roofKey, g); }
  // stacked open galleries on one front (packing house)
  if (st.gallery) {
    const dir = DIRS[st.gallery.side] || [0, -1]; let fc = faces[0], best = -9; for (const x of faces) { const d = x.n[0] * dir[0] + x.n[1] * dir[1]; if (d > best) { best = d; fc = x; } }
    const s0 = P2(F, fc.a[0], fc.a[1]), s1 = P2(F, fc.b[0], fc.b[1]), fr = st.gallery.frac || .35, dep = st.gallery.depth || 2.2;
    const lv = st.gallery.levels || 3, lh = H / lv, ang = Math.atan2(s1[1] - s0[1], s1[0] - s0[0]);
    const ta = 0.5 - fr / 2, tb = 0.5 + fr / 2, A = [s0[0] + (s1[0] - s0[0]) * ta, s0[1] + (s1[1] - s0[1]) * ta], B = [s0[0] + (s1[0] - s0[0]) * tb, s0[1] + (s1[1] - s0[1]) * tb];
    const M = [(A[0] + B[0]) / 2 + fc.n[0] * dep / 2, (A[1] + B[1]) / 2 + fc.n[1] * dep / 2], len = fr * fc.len;
    for (let k = 1; k <= lv; k++) { bk.add('plank#8d8170', box(M[0], z0 + k * lh - .1, -M[1], len, .15, dep, ang)); bk.add(trimKey, box(M[0] + fc.n[0] * dep / 2, z0 + k * lh + .45, -(M[1] + fc.n[1] * dep / 2), len, .08, .06, ang)); }
    const np = Math.round(len / 2.5) + 1; for (let i = 0; i < np; i++) { const t = i / (np - 1), x = A[0] + (B[0] - A[0]) * t + fc.n[0] * (dep - .1), y = A[1] + (B[1] - A[1]) * t + fc.n[1] * (dep - .1); bk.add(trimKey, box(x, z0 + H / 2, -y, .16, H, .16)); }
    bk.add(roofKey, box(M[0], z0 + H + .1, -M[1], len + .3, .12, dep + .3, ang));
    for (let k = 0; k < lv; k++) put(fc, fc.len / 2 + (k % 2 ? 1.5 : -1.5), k * lh + .1, 1.0, 2.1, 'door');
  }
  // inclined cattle runway on trestle bents up to the killing floor (packing house; Huffman 1886, SHSND 00042-00074/-75)
  if (st.runway) {
    const d = DIRS[st.runway.end] || [-1, 0], sg = Math.sign(F.u[0] * d[0] + F.u[1] * d[1]) || -1, L = st.runway.len || 30, top = H * 0.8;
    const steps = 12, rot = Math.atan2(F.u[1], F.u[0]);
    for (let i = 0; i < steps; i++) {
      const a0 = sg * (F.L / 2 + L * i / steps), a1 = sg * (F.L / 2 + L * (i + 1) / steps), am = (a0 + a1) / 2, p = P2(F, am, -F.W * 0.25);
      const h = top * (1 - (i + 0.5) / steps), zg = ctxZ ? ctxZ(p[0], p[1]) : z0;
      const seg = box(p[0], zg + h + .9, -p[1], L / steps + .05, .2, 2.4, rot); seg.rotateZ ? 0 : 0; bk.add('plank#857a6a', seg);
      for (const s2 of [-1.25, 1.25]) bk.add('plank#857a6a', box(p[0] - F.v[0] * 0 , zg + h + 1.6, -p[1], L / steps, 1.3, .08, rot).translate(F.v[0] * s2, 0, -F.v[1] * s2));
      if (i % 2 === 0 && h > 0.5) for (const s2 of [-1.1, 1.1]) bk.add('plank#6f6455', box(p[0] + F.v[0] * s2, zg + (h + .8) / 2, -(p[1] + F.v[1] * s2), .25, h + .8, .25));
    }
  }
  // square tower with a pyramid-roofed cupola (ice house)
  if (st.tower) {
    const tw = (st.tower.w || 5), th = (st.tower.h || 4), p = P2(F, -F.L * 0.25, 0), rot = Math.atan2(F.u[1], F.u[0]);
    bk.add(wallKey, box(p[0], z0 + ridgeH + th / 2 - .5, -p[1], tw, th, tw, rot));
    const g = new THREE.ConeGeometry(tw * .78, 2.2, 4).toNonIndexed(); g.rotateY(Math.PI / 4 + rot); g.translate(p[0], z0 + ridgeH + th + .55, -p[1]); bk.add(roofKey, g);
    bk.add(wallKey, box(p[0], z0 + ridgeH + th + 2.1, -p[1], 1.4, 1.2, 1.4, rot)); const c = new THREE.ConeGeometry(1.2, 1.1, 4).toNonIndexed(); c.rotateY(Math.PI / 4 + rot); c.translate(p[0], z0 + ridgeH + th + 3.25, -p[1]); bk.add(roofKey, c);
  }
  // cupola (packing plant, ice house)
  if (st.cupola && !st.tower) { const p = P2(F, 0, 0); bk.add(wallKey, box(p[0], z0 + ridgeH + .6, -p[1], 2.2, 1.6, 2.2)); const g = new THREE.ConeGeometry(1.8, 1.4, 4).toNonIndexed(); g.rotateY(Math.PI / 4 + Math.atan2(F.u[1], F.u[0])); g.translate(p[0], z0 + ridgeH + 2.1, -p[1]); bk.add(roofKey, g); }
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
  const bk = new Bucket(); ctxZ = ctx.zAt;
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
  const place = (obj, s) => { const q = at(s); obj.position.set(q[0], q[2] + 0.35, -q[1]); obj.rotation.y = q[3]; grp.add(obj); };
  const s0 = cum[bi] + fwd * 22;                    // engine (its origin) about 22 m west of the depot
  const loco = locomotive(); place(loco.g, s0);
  let s = s0 - fwd * 9.4;                           // rear of the tender (tender ends 9.3 m behind the engine origin)
  for (const k of ['baggage', 'coach', 'coach', 'pullman']) { const c = car(k); s -= fwd * (c.length / 2 + 0.3); place(c.g, s); s -= fwd * (c.length / 2 + 0.3); }
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
