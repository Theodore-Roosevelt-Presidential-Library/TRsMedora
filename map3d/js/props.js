// Vegetation, the telegraph line and small town details (hitching rails, privies, wagons, stock fences).
import * as THREE from 'three';
import {mergeGeometries} from 'three/addons/utils/BufferGeometryUtils.js';

const R = (seed) => { let s = seed * 9301 + 49297; return () => ((s = (s * 9301 + 49297) % 233280) / 233280); };

function crownGeometry(seed) {
  // an irregular cottonwood crown: a few squashed, jittered icospheres
  const r = R(seed), parts = [];
  for (let i = 0; i < 4; i++) {
    const g = new THREE.IcosahedronGeometry(1, 1);
    const p = g.attributes.position;
    for (let k = 0; k < p.count; k++) { const j = 0.82 + r() * 0.36; p.setXYZ(k, p.getX(k) * j, p.getY(k) * j, p.getZ(k) * j); }
    g.scale(0.55 + r() * 0.3, 0.45 + r() * 0.25, 0.55 + r() * 0.3);
    g.translate((r() - .5) * .7, 0.15 + r() * .35, (r() - .5) * .7);
    parts.push(g.toNonIndexed());
  }
  const m = mergeGeometries(parts); m.computeVertexNormals(); return m;
}

export function buildVegetation(scene0, season) {
  const grp = new THREE.Group();
  const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), S = new THREE.Vector3(), P = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  // ---- trees: instanced trunks and three crown variants
  const trees = scene0.trees || [];
  const leaf = season === 'winter' ? null : new THREE.MeshStandardMaterial({color: 0x6b7f45, roughness: .95, flatShading: true});
  const leaf2 = season === 'winter' ? null : new THREE.MeshStandardMaterial({color: 0x7f8f52, roughness: .95, flatShading: true});
  const bark = new THREE.MeshStandardMaterial({color: 0x6d6255, roughness: 1});
  const trunkGeo = new THREE.CylinderGeometry(.18, .32, 1, 7); trunkGeo.translate(0, .5, 0);
  const trunks = new THREE.InstancedMesh(trunkGeo, bark, trees.length); trunks.castShadow = true;
  const crowns = [0, 1, 2].map(k => { const g = crownGeometry(k + 3); const im = new THREE.InstancedMesh(g, k === 1 ? (leaf2 || bark) : (leaf || bark), trees.length); im.castShadow = true; im.receiveShadow = true; im.count = 0; return im; });
  // winter: bare branch "crowns" drawn as sparse dark clumps
  trees.forEach((t, i) => {
    const [e, n, z, h, s] = t, r = R(s);
    const lean = (r() - .5) * .12, rot = r() * Math.PI * 2;
    Q.setFromEuler(new THREE.Euler(lean, rot, (r() - .5) * .12));
    S.set(h / 9, h * .45, h / 9); P.set(e, z - .2, -n); M.compose(P, Q, S); trunks.setMatrixAt(i, M);
    const cw = h * (0.42 + r() * 0.15), ch = h * (0.45 + r() * 0.1);
    const im = crowns[s % 3];
    S.set(cw, ch * (season === 'winter' ? .8 : 1), cw); P.set(e, z + h * .55, -n); Q.setFromAxisAngle(up, rot); M.compose(P, Q, S);
    im.setMatrixAt(im.count++, M);
  });
  if (season === 'winter') crowns.forEach(c => { c.material = new THREE.MeshStandardMaterial({color: 0x5a524a, roughness: 1, transparent: true, opacity: .55, flatShading: true}); });
  grp.add(trunks, ...crowns);
  grp.userData.trees = [trunks, ...crowns];
  // ---- sagebrush and grass tussocks
  const sage = scene0.sage || [];
  const sg = new THREE.IcosahedronGeometry(.55, 1); sg.scale(1, .6, 1); sg.translate(0, .22, 0);
  const sm = new THREE.MeshStandardMaterial({color: season === 'winter' ? 0x8f9088 : 0x8f9a7f, roughness: 1, flatShading: true});
  const sim = new THREE.InstancedMesh(sg, sm, sage.length); sim.receiveShadow = true;
  sage.forEach((p, i) => { const r = R(i + 7); Q.setFromAxisAngle(up, r() * 6.28); S.set(p[3] * (0.8 + r() * .5), p[3], p[3] * (0.8 + r() * .5)); P.set(p[0], p[2] - .05, -p[1]); M.compose(P, Q, S); sim.setMatrixAt(i, M); });
  grp.add(sim);
  return grp;
}

export function buildTelegraph(poles) {
  const grp = new THREE.Group();
  const wood = new THREE.MeshStandardMaterial({color: 0x6e5d4a, roughness: 1});
  const parts = [], tops = [];
  for (let i = 0; i < poles.length; i++) {
    const [e, n, z] = poles[i];
    const a = poles[Math.max(0, i - 1)], b = poles[Math.min(poles.length - 1, i + 1)], ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
    const p = new THREE.CylinderGeometry(.11, .15, 7.5, 6); p.translate(e, z + 3.75, -n); parts.push(p);
    const x = new THREE.BoxGeometry(.12, .12, 1.6); x.rotateY(ang); x.translate(e, z + 7.1, -n); parts.push(x);
    tops.push([e, z, n, ang]);
  }
  const mesh = new THREE.Mesh(mergeGeometries(parts), wood); mesh.castShadow = true; grp.add(mesh);
  // two wires with a little sag
  for (const off of [-.65, .65]) {
    const pts = [];
    for (let i = 0; i < tops.length - 1; i++) {
      const [e0, z0, n0, a0] = tops[i], [e1, z1, n1, a1] = tops[i + 1];
      const ox0 = -Math.sin(a0) * off, oy0 = Math.cos(a0) * off, ox1 = -Math.sin(a1) * off, oy1 = Math.cos(a1) * off;
      for (let k = 0; k <= 8; k++) { const t = k / 8, sag = Math.sin(t * Math.PI) * .45;
        pts.push(new THREE.Vector3(e0 + ox0 + (e1 + ox1 - e0 - ox0) * t, z0 + 7.2 + (z1 - z0) * t - sag, -(n0 + oy0 + (n1 + oy1 - n0 - oy0) * t))); }
    }
    grp.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({color: 0x2a2a2a})));
  }
  return grp;
}

// small details attached to a building: called with the building's frame (centre, long axis, front normal)
export function buildingDetails(f, info, zAt, kind) {
  const parts = {wood: [], dark: [], white: []};
  const {c, front, len, depth} = info;           // c=[e,n], front=[nx,ny] unit, len along the front, depth of building
  const tx = -front[1], ty = front[0];            // along the front
  const at = (a, b) => [c[0] + front[0] * a + tx * b, c[1] + front[1] * a + ty * b];
  const r = R([...f.id].reduce((s, ch) => s + ch.charCodeAt(0), 0));
  const ang = Math.atan2(ty, tx);
  const box = (key, p, sx, sy, sz, h, rot = ang) => { const g = new THREE.BoxGeometry(sx, sy, sz); g.rotateY(rot); g.translate(p[0], zAt(p[0], p[1]) + h, -p[1]); parts[key].push(g); };
  if (kind === 'commercial') {
    // hitching rail along the street, 3 m in front of the porch line
    const p0 = at(depth / 2 + 4.2, 0); const L = Math.min(len * .8, 10);
    box('wood', p0, L, .12, .12, 1.0);
    for (let i = 0; i <= 3; i++) box('wood', at(depth / 2 + 4.2, -L / 2 + L * i / 3), .14, 1.05, .14, .52);
    // a water barrel by the door
    const bp = at(depth / 2 + 1.0, len / 2 - .8); const g = new THREE.CylinderGeometry(.32, .3, .9, 10); g.translate(bp[0], zAt(bp[0], bp[1]) + .45, -bp[1]); parts.dark.push(g);
  }
  if (kind === 'dwelling' || kind === 'commercial') {
    // privy behind the building
    const pp = at(-depth / 2 - 6 - r() * 4, (r() - .5) * len * .6);
    box('wood', pp, 1.2, 2.2, 1.2, 1.1, ang + r());
    const roof = new THREE.BoxGeometry(1.45, .08, 1.45); roof.rotateY(ang + .3); roof.rotateX(.25); roof.translate(pp[0], zAt(pp[0], pp[1]) + 2.25, -pp[1]); parts.dark.push(roof);
    // woodpile
    const wp = at(-depth / 2 - 1.2, len / 2 - 1.5); box('wood', wp, 2.2, .7, .9, .35);
  }
  if (kind === 'dwelling' && f.style && !(f.style.fences && f.style.fences.length) && /residence|dwelling|house/i.test(f.use || '')) {   // not when the building has its own measured fences
    // picket fence across the front yard
    const fy = depth / 2 + 5, half = len / 2 + 2;
    for (let b = -half; b <= half; b += .35) box('white', at(fy, b), .05, 1.0, .07, .5);
    box('white', at(fy, 0), .05, .06, len + 4, .8, ang + Math.PI / 2);
  }
  const out = new THREE.Group();
  const mats = {wood: new THREE.MeshStandardMaterial({color: 0x7a6650, roughness: 1}), dark: new THREE.MeshStandardMaterial({color: 0x4b4038, roughness: 1}), white: new THREE.MeshStandardMaterial({color: 0xeeeae0, roughness: .9})};
  for (const k in parts) if (parts[k].length) { const m = new THREE.Mesh(mergeGeometries(parts[k].map(g => g.toNonIndexed())), mats[k]); m.castShadow = true; m.receiveShadow = true; out.add(m); }
  return out;
}

export function buildWagons(spots, zAt) {
  // farm and freight wagons standing at the stores (simple: box, wheels, tongue)
  const grp = new THREE.Group(), wood = new THREE.MeshStandardMaterial({color: 0x6b5236, roughness: .9}), dark = new THREE.MeshStandardMaterial({color: 0x2a2420});
  for (const [e, n, ang] of spots) {
    const g = new THREE.Group(), z = zAt(e, n);
    const bed = new THREE.Mesh(new THREE.BoxGeometry(3.4, .55, 1.25), wood); bed.position.y = 1.15; g.add(bed);
    const sides = new THREE.Mesh(new THREE.BoxGeometry(3.4, .35, 1.32), wood); sides.position.y = 1.55; g.add(sides);
    for (const [x, rr] of [[-1.1, .62], [1.1, .52]]) for (const zz of [-.72, .72]) { const w = new THREE.Mesh(new THREE.TorusGeometry(rr, .05, 6, 18), dark); w.position.set(x, rr, zz); g.add(w);
      for (let k = 0; k < 6; k++) { const sp = new THREE.Mesh(new THREE.BoxGeometry(.03, rr * 2, .03), wood); sp.position.set(x, rr, zz); sp.rotation.z = k * Math.PI / 6; g.add(sp); } }
    const tongue = new THREE.Mesh(new THREE.BoxGeometry(2.6, .08, .08), wood); tongue.position.set(2.9, .7, 0); tongue.rotation.z = -.25; g.add(tongue);
    g.position.set(e, z, -n); g.rotation.y = ang; g.traverse(o => { if (o.isMesh) o.castShadow = true; }); grp.add(g);
  }
  return grp;
}

export function buildRailFence(ring, zAt, posts = 3.0) {
  // split-rail / board stock fence around a polygon (stock yards, corrals)
  const parts = [];
  for (let i = 0; i < ring.length; i++) {
    const a = ring[i], b = ring[(i + 1) % ring.length], L = Math.hypot(b[0] - a[0], b[1] - a[1]), ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
    for (let s = 0; s < L; s += posts) { const t = s / L, x = a[0] + (b[0] - a[0]) * t, y = a[1] + (b[1] - a[1]) * t, z = zAt(x, y);
      const p = new THREE.BoxGeometry(.16, 1.8, .16); p.translate(x, z + .9, -y); parts.push(p); }
    for (const h of [.5, 1.0, 1.5]) { const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], z = (zAt(a[0], a[1]) + zAt(b[0], b[1])) / 2;
      const r = new THREE.BoxGeometry(L, .14, .05); r.rotateY(ang); r.translate(m[0], z + h, -m[1]); parts.push(r); }
  }
  const mesh = new THREE.Mesh(mergeGeometries(parts.map(g => g.toNonIndexed())), new THREE.MeshStandardMaterial({color: 0x786a58, roughness: 1}));
  mesh.castShadow = true; return mesh;
}

// ---------------------------------------------------------------- people and horses (representative, not documented individuals)
const CLOTH = [0x2b2a2c, 0x3b332c, 0x4a3f33, 0x262f3a, 0x5a4a3a, 0x3d3a36];
const COATS = [0x7b5a3c, 0x4e3a28, 0x8a8174, 0x2e2622, 0x6b4a2e];
function horse(rng) {
  const g = new THREE.Group(), col = COATS[Math.floor(rng() * COATS.length)], m = new THREE.MeshStandardMaterial({color: col, roughness: .85}), dk = new THREE.MeshStandardMaterial({color: 0x1d1814, roughness: .9});
  const add = (geo, mat, x, y, z, rz = 0) => { const o = new THREE.Mesh(geo, mat); o.position.set(x, y, z); o.rotation.z = rz; o.castShadow = true; g.add(o); return o; };
  add(new THREE.CapsuleGeometry(.32, 1.15, 4, 10).rotateZ(Math.PI / 2), m, 0, 1.25, 0);                // barrel
  add(new THREE.CapsuleGeometry(.16, .55, 4, 8), m, .78, 1.62, 0, -.75);                                 // neck
  add(new THREE.CapsuleGeometry(.12, .38, 4, 8), m, 1.08, 1.78, 0, -1.9);                                // head
  add(new THREE.BoxGeometry(.05, .28, .05), dk, .62, 1.9, 0, -.6);                                        // mane
  for (const [x, z] of [[.55, .16], [.55, -.16], [-.55, .16], [-.55, -.16]]) add(new THREE.CylinderGeometry(.06, .05, 1.05, 6), m, x, .53, z);
  add(new THREE.CylinderGeometry(.05, .02, .7, 6), dk, -.86, 1.0, 0, .35);                                // tail
  return g;
}
function person(rng, woman) {
  const g = new THREE.Group(), cl = new THREE.MeshStandardMaterial({color: CLOTH[Math.floor(rng() * CLOTH.length)], roughness: .95});
  const skin = new THREE.MeshStandardMaterial({color: 0xc9a487, roughness: .8}), hat = new THREE.MeshStandardMaterial({color: rng() < .5 ? 0x2a2420 : 0x8c7a62, roughness: .9});
  const add = (geo, mat, x, y, z) => { const o = new THREE.Mesh(geo, mat); o.position.set(x, y, z); o.castShadow = true; g.add(o); return o; };
  if (woman) add(new THREE.ConeGeometry(.34, 1.0, 10), cl, 0, .5, 0);
  else for (const z of [-.09, .09]) add(new THREE.CylinderGeometry(.075, .07, .85, 6), cl, 0, .43, z);
  add(new THREE.CapsuleGeometry(.17, .42, 4, 8), cl, 0, 1.18, 0);
  add(new THREE.SphereGeometry(.11, 10, 8), skin, 0, 1.6, 0);
  add(new THREE.CylinderGeometry(woman ? .14 : .2, woman ? .14 : .2, .02, 12), hat, 0, 1.69, 0);
  add(new THREE.CylinderGeometry(.09, .1, .13, 10), hat, 0, 1.75, 0);
  return g;
}
export function buildFigures(spots, zAt) {
  // spots: [e, n, heading (radians, three's y rotation), kind: 'man' | 'woman' | 'horse']
  const grp = new THREE.Group(); let s = 7;
  const rng = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  for (const [e, n, ang, kind, z] of spots) {
    const o = kind === 'horse' ? horse(rng) : person(rng, kind === 'woman');
    o.position.set(e, (z ?? zAt(e, n)), -n); o.rotation.y = ang; grp.add(o);
  }
  return grp;
}
