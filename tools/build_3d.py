"""Build the data for the 3D view (map3d/) from the gazetteer and the lidar terrain.

Run after tools/build_features.py:
    python3 tools/build_3d.py

Reads  map/data/historic_features.geojson, map/data/river_1883.geojson, map3d/data/terrain.{bin,json}
Writes map3d/data/scene.json  (local metres: x = east, y = north, z = up; origin ORIGIN below)
"""
import json, math, os
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, Polygon, LineString, Point

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
R = lambda *p: os.path.join(ROOT, *p)
ORIGIN = (612300.0, 5196700.0, 690.0)   # UTM 13N easting, northing, elevation (m)
T = Transformer.from_crs(4326, 26913, always_xy=True)

meta = json.load(open(R('map3d', 'data', 'terrain.json')))
Z = np.fromfile(R('map3d', 'data', 'terrain.bin'), dtype='<u2').reshape(meta['rows'], meta['cols']) * meta['scale'] + meta['z0']

def zat(x, y):
    """Bilinear terrain elevation at UTM x, y (m)."""
    c = (x - meta['x0']) / meta['res'] - 0.5; r = (meta['y1'] - y) / meta['res'] - 0.5
    c0 = int(np.clip(math.floor(c), 0, meta['cols'] - 2)); r0 = int(np.clip(math.floor(r), 0, meta['rows'] - 2))
    fc, fr = min(max(c - c0, 0), 1), min(max(r - r0, 0), 1)
    a = Z[r0:r0 + 2, c0:c0 + 2]
    return float(a[0, 0] * (1 - fc) * (1 - fr) + a[0, 1] * fc * (1 - fr) + a[1, 0] * (1 - fc) * fr + a[1, 1] * fc * fr)

def loc(x, y):
    return [round(x - ORIGIN[0], 2), round(y - ORIGIN[1], 2)]

def utm_geom(g):
    if g.geom_type == 'Point':
        x, y = T.transform(g.x, g.y); return ('point', [(x, y)])
    if g.geom_type in ('LineString',):
        return ('line', [T.transform(*c) for c in g.coords])
    if g.geom_type == 'MultiLineString':
        return ('line', [T.transform(*c) for l in g.geoms for c in l.coords])
    if g.geom_type == 'MultiPolygon':
        g = max(g.geoms, key=lambda p: p.area)
    return ('poly', [T.transform(*c) for c in g.exterior.coords])

# ---------------------------------------------------------------- 1880s ground surface (approximate)
# The 2021 lidar shows today's earthworks: the railroad grade, Pacific Avenue (old US 10) and its bridge
# approaches, I-94 cuts, gravel pits on the Cantonment flats, and today's river channel. On the valley floor
# (below 704 m and gently sloping) small features are smoothed away; the 1883 river channel is cut in and today's
# channel west of it filled where the two differ. Buttes and badland slopes are left as measured.
from scipy.ndimage import gaussian_filter, maximum_filter, distance_transform_edt
from shapely.geometry import LineString as _LS, Point as _Pt
_Zm = Z.copy()
_smooth = gaussian_filter(Z, 6)                         # 18 m
_slope = np.hypot(*np.gradient(gaussian_filter(Z, 3), meta['res']))
_floor = (_smooth < 704) & (_slope < 0.12)
_w = gaussian_filter(_floor.astype(float), 3)
Z = Z * (1 - _w) + _smooth * _w
_osm = json.load(open(R('data', 'reference', 'osm_medora.geojson')))
_xc = meta['x0'] + (np.arange(meta['cols']) + 0.5) * meta['res']; _yc = meta['y1'] - (np.arange(meta['rows']) + 0.5) * meta['res']
def _dist_to(line_utm):
    """distance (m) from every grid cell to a polyline, via a rasterised mask + EDT"""
    m = np.zeros(Z.shape, bool)
    L = _LS(line_utm)
    for d in np.arange(0, L.length, meta['res'] / 2):
        q = L.interpolate(d); c = int((q.x - meta['x0']) / meta['res']); r = int((meta['y1'] - q.y) / meta['res'])
        if 0 <= r < Z.shape[0] and 0 <= c < Z.shape[1]: m[r, c] = True
    return distance_transform_edt(~m) * meta['res']
_riv83 = [T.transform(*c) for c in json.load(open(R('map', 'data', 'river_1883.geojson')))['features'][0]['geometry']['coordinates']]
# 1880-86 reach at the railroad crossing (photo reconciliation of MHS 72459, SHSND 00119-00017 and the 1880s town views):
# the plat trace runs the river straight under the grade; the photos put it in a loop south of the grade (a channel
# along the south side of the track) that turns north under the west end of the trestle. Local metres, upstream (south)
# first; it replaces the plat trace between (-458,-76) and (-136,391) and joins it again at (-464,-325) and (-89,476).
RIVER_1880_86 = [(-430, -160), (-410, -80), (-372, -12), (-350, 22), (-400, 55), (-455, 78), (-505, 100), (-540, 118), (-548, 145),
                 (-527, 170), (-500, 205), (-469, 255), (-400, 305), (-339, 348), (-245, 398), (-140, 458)]
def _splice_river(pts):
    lp = [(x - ORIGIN[0], y - ORIGIN[1]) for x, y in pts]
    near = lambda q: min(range(len(lp)), key=lambda i: math.dist(lp[i], q))
    i0, i1 = near((-89, 476)), near((-464, -325))          # kept: the plat trace runs north (index 0) to south
    assert i0 < i1
    new = [(x + ORIGIN[0], y + ORIGIN[1]) for x, y in reversed(RIVER_1880_86)]
    return pts[:i0 + 1] + new + pts[i1:]
_riv83 = _splice_river(_riv83)
def _chaikin(pts, n=3):
    for _ in range(n):
        q = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]): q += [(0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]), (0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1])]
        pts = q + [pts[-1]]
    return pts
_riv83 = _chaikin(_riv83)   # the plat/survey trace is a polyline; a river bends smoothly
_d83 = _dist_to(_riv83)
_modern = []
for f in _osm['features']:
    if f['properties'].get('name') == 'Little Missouri River' and f['geometry']['type'] == 'LineString':
        _modern += [T.transform(*c) for c in f['geometry']['coordinates']]
_dmod = _dist_to(_modern) if _modern else np.full(Z.shape, 1e9)
# fill today's channel where it is away from the 1883 one: raise to the surrounding floodplain
_fp = gaussian_filter(maximum_filter(Z, size=15), 5) - 1.0
_fill = np.clip(1 - (_dmod - 22) / 12, 0, 1) * np.clip((_d83 - 40) / 25, 0, 1)
Z = np.maximum(Z, Z * (1 - _fill) + _fp * _fill)
# cut the 1883 channel: water about 1.6 m below the floodplain, banks over 15-28 m from the centreline
_fp83 = gaussian_filter(Z, 8)
_bed = _fp83 - 2.6
_cut = np.clip(1 - (_d83 - 12) / 14, 0, 1)
Z = np.minimum(Z, Z * (1 - _cut) + _bed * _cut)
# water surface along the 1883 channel, falling downstream (the river flows north)
_rline = _LS(_riv83); _wl = []
for d in np.arange(0, _rline.length, 6.0):
    q = _rline.interpolate(d); c = int((q.x - meta['x0']) / meta['res']); r = int((meta['y1'] - q.y) / meta['res'])
    _wl.append((q.x, q.y, float(_fp83[min(max(r, 0), Z.shape[0] - 1), min(max(c, 0), Z.shape[1] - 1)]) - 1.6))
_vals = np.array([w[2] for w in _wl])
_vals = np.convolve(np.pad(_vals, 15, mode='edge'), np.ones(31) / 31, mode='valid')
WATER83 = [(x, y, float(v)) for (x, y, _), v in zip(_wl, _vals)]
# a narrow, shallow slough along the north side of the grade east of the crossing (low confidence: read from the
# dark strip beside the grade in the 1880s views; width and depth are guesses)
SLOUGH = [(-484.1, 162.5), (-449.9, 141.7), (-416.2, 120.2), (-364.5, 89.6), (-294.9, 50.0), (-225.8, 9.6), (-161.0, -37.6), (-111.5, -71.6)]
_sl = _chaikin([(x + ORIGIN[0], y + ORIGIN[1]) for x, y in SLOUGH])
_dsl = _dist_to(_sl)
_fsl = gaussian_filter(Z, 3)                            # 9 m: the slough follows the local ground
_slcut = np.clip(1 - (_dsl - 2.5) / 4.0, 0, 1)
Z = np.minimum(Z, Z * (1 - _slcut) + (_fsl - 1.1) * _slcut)
_sline = _LS(_sl); _swl = []
for d in list(np.arange(0, _sline.length, 6.0)) + [_sline.length]:
    q = _sline.interpolate(d); c = int((q.x - meta['x0']) / meta['res']); r = int((meta['y1'] - q.y) / meta['res'])
    _swl.append((q.x, q.y, float(_fsl[min(max(r, 0), Z.shape[0] - 1), min(max(c, 0), Z.shape[1] - 1)]) - 0.55))
_sv = np.array([w[2] for w in _swl]); _sv = np.convolve(np.pad(_sv, 4, mode='edge'), np.ones(9) / 9, mode='valid')
WATER_SLOUGH = [(x, y, float(v)) for (x, y, _), v in zip(_swl, _sv)]

# ---------------------------------------------------------------- photo-audit footprints and extra buildings (tools/geom3d.py)
import sys as _sys; _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom3d import overrides as _overrides
_HF = json.load(open(R('map', 'data', 'historic_features.geojson')))['features']
def _orig_rect(fid, point=False):
    for f in _HF:
        if f['properties']['id'] != fid: continue
        g = shape(f['geometry'])
        if point:
            c = g.centroid; x, y = T.transform(c.x, c.y); return [x - ORIGIN[0], y - ORIGIN[1]]
        if g.geom_type == 'MultiPolygon': g = max(g.geoms, key=lambda q: q.area)
        pu = Polygon([T.transform(*c) for c in g.exterior.coords]).minimum_rotated_rectangle
        return [[x - ORIGIN[0], y - ORIGIN[1]] for x, y in list(pu.exterior.coords)[:4]]
    raise KeyError(fid)
GEOM3D, EXTRA3D, STYLE_ADD, PROPS3D = _overrides(_osm, T, ORIGIN, _orig_rect, [f['properties'] for f in _HF])
def _utm_poly(rect): return Polygon([(x + ORIGIN[0], y + ORIGIN[1]) for x, y in rect])

# ---------------------------------------------------------------- building pads
# The 3 m bare-earth terrain is too coarse for buildings on slopes (the Chateau sits on a bluff edge), so each
# building gets a level pad: the ground inside its footprint (plus 1.5 m) is set to one height, and the ground
# within the next 8 m blends back to the natural surface. The pad height is the median ground around the building
# (the lidar ground class at the Chateau gives 709.9 m, which this reproduces).
from shapely.geometry import shape as _shape
from matplotlib.path import Path as _Path
_cols, _rows, _res = meta['cols'], meta['rows'], meta['res']
_xc = meta['x0'] + (np.arange(_cols) + 0.5) * _res; _yc = meta['y1'] - (np.arange(_rows) + 0.5) * _res
_XX, _YY = np.meshgrid(_xc, _yc)
_Zorig = Z.copy()
# pad heights fixed from photo solves (local metres): the Pyramid Park Hotel's floor in Haynes 1881 sits about 1.1 m above
# the depot's; today's flood plain there is lower than in 1881
PAD_Z = {'pyramid-park-hotel': 3.5, 'lm-depot': 4.25}  # LM depot platform level with the raised 1880s grade (rail ~4.5)
_padsrc = [(f['properties'], _shape(f['geometry'])) for f in _HF] + [({'id': x['id'], 'kind': 'building', 'massing': {}}, None) for x in EXTRA3D]
for pr, g in _padsrc:
    if pr['id'] in GEOM3D or g is None:
        gu = _utm_poly(GEOM3D[pr['id']] if pr['id'] in GEOM3D else [x for x in EXTRA3D if x['id'] == pr['id']][0]['rect'])
    else:
        if g.geom_type not in ('Polygon', 'MultiPolygon') or pr['kind'] in ('landmark', 'railroad', 'bridge'): continue
        if (pr.get('massing') or {}).get('roof') in ('none',): continue
        if g.geom_type == 'MultiPolygon': g = max(g.geoms, key=lambda q: q.area)
        gu = Polygon([T.transform(*c) for c in g.exterior.coords])
    if gu.area > 4000: continue
    x0, y0, x1, y1 = gu.buffer(10).bounds
    c0, c1 = int((x0 - meta['x0']) / _res), int((x1 - meta['x0']) / _res) + 1
    r0, r1 = int((meta['y1'] - y1) / _res), int((meta['y1'] - y0) / _res) + 1
    if c0 < 0 or r0 < 0 or c1 > _cols or r1 > _rows: continue
    sx, sy = _XX[r0:r1, c0:c1], _YY[r0:r1, c0:c1]
    ring = gu.buffer(4).exterior
    pz = float(np.median([zat(*ring.interpolate(d).coords[0]) for d in np.linspace(0, ring.length, 40)]))
    # inside the footprint use the median of the natural ground there if the surrounding ring is far off (cut into slope)
    inner = _Path(np.array(gu.buffer(1.5).exterior.coords)).contains_points(np.c_[sx.ravel(), sy.ravel()]).reshape(sx.shape)
    if inner.any():
        pz = float(np.median(_Zorig[r0:r1, c0:c1][inner])) if pr['id'] != 'chateau-de-mores' else 709.9
    if pr['id'] in PAD_Z: pz = ORIGIN[2] + PAD_Z[pr['id']]
    from shapely import distance as _dist, points as _pts
    d = _dist(gu, _pts(sx.ravel(), sy.ravel())).reshape(sx.shape)
    w = np.clip(1 - (d - 1.5) / 8.0, 0, 1)
    blk = Z[r0:r1, c0:c1]
    Z[r0:r1, c0:c1] = np.where(w > 0, blk * (1 - w) + pz * w, blk)

# ---------------------------------------------------------------- railroad grade, trestle and sidings
# The 3D view uses today's alignment (OpenStreetMap), clipped to the model area (see below). Chainage ('ch') runs
# east from its west end. The 1880s grade (photo reconciliation of MHS 72459, SHSND 00119-00017 and the town views):
# rail about +4.5..5.0 m (local) past Little Missouri, level at +4.5 across a timber pile trestle from ch 320 to 530
# (about 210 m, bents every 4.6 m), easing down to +3.5 by ch 600 and to today's lidar grade by ch 760, which it
# follows past the Medora depot. Where the rail is above the ground the grade is built up on fill (side slopes 1.5:1).
from shapely.geometry import Polygon as _SP
_O = _osm
_rails = [shape(f['geometry']) for f in _O['features'] if f['properties'].get('kind') == 'rail']
from shapely.ops import linemerge as _lm, unary_union as _uu
_rl = _lm(_uu(_rails)); _rl = max(_rl.geoms, key=lambda g: g.length) if hasattr(_rl, 'geoms') else _rl
_box = _SP([(meta['x0'] + 30, meta['y1'] - 30), (meta['x0'] + meta['cols'] * meta['res'] - 30, meta['y1'] - 30),
            (meta['x0'] + meta['cols'] * meta['res'] - 30, meta['y1'] - meta['rows'] * meta['res'] + 30), (meta['x0'] + 30, meta['y1'] - meta['rows'] * meta['res'] + 30)])
RAIL_SEG = LineString([T.transform(*c) for c in _rl.coords]).intersection(_box)
RAIL_SEG = max(RAIL_SEG.geoms, key=lambda g: g.length) if hasattr(RAIL_SEG, 'geoms') else RAIL_SEG
if RAIL_SEG.coords[0][0] > RAIL_SEG.coords[-1][0]: RAIL_SEG = LineString(list(RAIL_SEG.coords)[::-1])   # chainage from the west
TRESTLE = (320.0, 530.0); TRESTLE_Z = 4.5; BENT = 4.6
def _ch_pt(d, off=0.0):
    """local (e, n) at chainage d, offset off m to the left (north-east side); negative = south"""
    q = RAIL_SEG.interpolate(d); a = RAIL_SEG.interpolate(max(0, d - 2)); b = RAIL_SEG.interpolate(min(RAIL_SEG.length, d + 2))
    tx, ty = b.x - a.x, b.y - a.y; L = math.hypot(tx, ty) or 1
    return (q.x - ty / L * off - ORIGIN[0], q.y + tx / L * off - ORIGIN[1])
def _drape_ch(d):
    e, n = _ch_pt(d); return zat(e + ORIGIN[0], n + ORIGIN[1]) - ORIGIN[2] + 0.4
_sm = lambda t: t * t * (3 - 2 * t)
_CH = np.arange(0, RAIL_SEG.length, 2.0)
_raw = np.array([_drape_ch(d) for d in _CH]); _des = _raw.copy()
_z760 = float(np.interp(760, _CH, _raw))
for i, d in enumerate(_CH):
    if 200 <= d < 320: _des[i] = min(max(_raw[i], 4.5), 5.0)
    elif TRESTLE[0] <= d <= TRESTLE[1]: _des[i] = TRESTLE_Z
    elif TRESTLE[1] < d <= 600: _des[i] = TRESTLE_Z + (3.5 - TRESTLE_Z) * (d - TRESTLE[1]) / (600 - TRESTLE[1])
    elif 600 < d <= 760: _des[i] = max(_raw[i], 3.5 + (_z760 - 3.5) * (d - 600) / 160)
_k = np.ones(15) / 15                                    # 30 m running mean rounds off the breaks of grade
_smz = np.convolve(np.pad(_des, 7, mode='edge'), _k, mode='valid')
_w = np.clip((_CH - 170) / 30, 0, 1) * np.clip((790 - _CH) / 30, 0, 1)   # only between ch 170 and 790; drape elsewhere
RAIL_Z = _des * (1 - _w) + _smz * _w
RAIL_Z[(_CH >= TRESTLE[0] - 1) & (_CH <= TRESTLE[1] + 1)] = TRESTLE_Z
rail_z = lambda d: float(np.interp(d, _CH, RAIL_Z))
# sidings at Little Missouri (offset in m, negative = south of the main; chainage 'ch'): three tracks in Haynes 1881
# (SHSND 00119-00017). Both sidings end west of the trestle. After the Little Missouri depot closed (1884.5) only the
# inner siding is kept (MHS 72459, 1886).
def _sid_inner(d):
    if d < 40 or d > 305: return None
    return -4.6 * (_sm((d - 40) / 30) if d < 70 else 1.0 if d <= 268 else 1 - _sm((d - 268) / 37))
def _sid_outer(d):        # leaves the inner siding at ch 80 and rejoins it by ch 285
    if d < 80 or d > 285: return None
    return -4.6 - 4.6 * (_sm((d - 80) / 40) if d < 120 else 1.0 if d <= 240 else 1 - _sm((d - 240) / 45))
SIDINGS = [dict(name='Siding at Little Missouri (Haynes 1881; kept after 1884)', built=1880.5, removed=None, f=_sid_inner, ch=(40, 305)),
           dict(name='Second siding at Little Missouri (Haynes 1881)', built=1880.5, removed=1884.5, f=_sid_outer, ch=(80, 285))]
def _south_width(d):
    o = [s['f'](d) for s in SIDINGS]; o = [x for x in o if x is not None]
    return -min(o) if o else 0.0
# grade the terrain: fill under the formation (rail level - 0.4 m), 2.5 m either side of the outermost track, 1.5:1
# side slopes, a fill cone under each end of the trestle; and a shallow cut where today's ground stands above it
_gx0, _gy0, _gx1, _gy1 = LineString([(_ch_pt(d)[0] + ORIGIN[0], _ch_pt(d)[1] + ORIGIN[1]) for d in np.arange(0, 800, 10)]).buffer(40).bounds
_c0, _c1 = int((_gx0 - meta['x0']) / _res), int((_gx1 - meta['x0']) / _res) + 1
_ra, _rb = int((meta['y1'] - _gy1) / _res), int((meta['y1'] - _gy0) / _res) + 1
from shapely import points as _pts2, line_locate_point as _llp
_cells = _pts2(_XX[_ra:_rb, _c0:_c1].ravel(), _YY[_ra:_rb, _c0:_c1].ravel())
_chs = _llp(RAIL_SEG, _cells)
from shapely import distance as _sdist
_near = _sdist(RAIL_SEG, _cells) < 40
_blk = Z[_ra:_rb, _c0:_c1].ravel().copy()
# under the trestle the lidar still shows today's embankment: take the ground there down to the flood plain either
# side (the lower of the ground 18 m north and south of the centreline)
def _zcell(e, n):
    c = int((e + ORIGIN[0] - meta['x0']) / _res); r = int((meta['y1'] - n - ORIGIN[1]) / _res)
    return float(Z[min(max(r, 0), _rows - 1), min(max(c, 0), _cols - 1)])
_flood = {round(d): min(_zcell(*_ch_pt(d, 18)), _zcell(*_ch_pt(d, -18))) for d in np.arange(TRESTLE[0], TRESTLE[1] + 1, 1.0)}
for i, (p, d) in enumerate(zip(_cells, _chs)):
    if not _near[i] or d <= 0.5 or d > 790: continue
    a = RAIL_SEG.interpolate(d - 1); b = RAIL_SEG.interpolate(d + 1); tx, ty = b.x - a.x, b.y - a.y; L = math.hypot(tx, ty) or 1
    s = ((p.x - a.x) * -ty + (p.y - a.y) * tx) / L      # signed offset, + = north-east (left)
    if abs(s) > 40: continue
    fz = rail_z(d) - 0.4 + ORIGIN[2]
    sw = _south_width(d)
    dd = max(0.0, s - 2.5) if s >= 0 else max(0.0, -s - 2.5 - sw)
    if TRESTLE[0] < d < TRESTLE[1]:
        w = min(1.0, max(0.0, (16 - abs(s)) / 6)) * min(1.0, max(0.0, (d - TRESTLE[0] - 15) / 10), max(0.0, (TRESTLE[1] - 12 - d) / 10))
        if w > 0: _blk[i] = min(_blk[i], _blk[i] * (1 - w) + _flood[round(d)] * w)
        de = min(d - TRESTLE[0], TRESTLE[1] - d)
        fill = fz - (dd + de) / 1.5
    else:
        fill = fz - dd / 1.5
        if d < 760:
            cut = fz + max(0.0, dd - 0.5) / 1.0
            if _blk[i] > cut: _blk[i] = cut
    if _blk[i] < fill: _blk[i] = fill
Z[_ra:_rb, _c0:_c1] = _blk.reshape(Z[_ra:_rb, _c0:_c1].shape)
q = np.round((Z - meta['z0']) / meta['scale']).clip(0, 65535).astype('<u2')
q.tofile(R('map3d', 'data', 'terrain_pads.bin'))

out = {'origin': {'utm13n': ORIGIN[:2], 'z0': ORIGIN[2]}, 'features': []}
def _set_rect(item, rect):
    rect = [[round(a, 2), round(b, 2)] for a, b in rect]
    item['rect'] = rect; item['ring'] = rect
    item['ground'] = round(min(zat(x + ORIGIN[0], y + ORIGIN[1]) for x, y in rect) - ORIGIN[2], 2)
    e0 = math.dist(rect[0], rect[1]); e1 = math.dist(rect[1], rect[2])
    if e0 >= e1: a = ((rect[1][0] + rect[2][0]) / 2, (rect[1][1] + rect[2][1]) / 2); b = ((rect[3][0] + rect[0][0]) / 2, (rect[3][1] + rect[0][1]) / 2)
    else: a = ((rect[0][0] + rect[1][0]) / 2, (rect[0][1] + rect[1][1]) / 2); b = ((rect[2][0] + rect[3][0]) / 2, (rect[2][1] + rect[3][1]) / 2)
    item['ridge_line'] = [[round(a[0], 2), round(a[1], 2)], [round(b[0], 2), round(b[1], 2)]]
    item['size_m'] = [round(max(e0, e1), 1), round(min(e0, e1), 1)]
H = json.load(open(R('map', 'data', 'historic_features.geojson')))
for f in H['features']:
    p = f['properties']; kind, pts = utm_geom(shape(f['geometry']))
    m = p.get('massing') or {}
    item = {k: p.get(k) for k in ('id', 'name', 'town', 'kind', 'built', 'removed', 'built_text', 'removed_text', 'loc', 'form', 'use',
                                    'material', 'stories', 'footprint_ft', 'evidence', 'sources', 'photos', 'notes', 'model')}
    item['massing'] = m; item['geom'] = kind
    if kind == 'poly':
        poly = Polygon(pts)
        if not poly.is_valid: poly = poly.buffer(0)
        item['ring'] = [loc(x, y) for x, y in list(poly.exterior.coords)[:-1]]
        item['ground'] = round(min(zat(x, y) for x, y in poly.exterior.coords) - ORIGIN[2], 2)
        mr = poly.minimum_rotated_rectangle; cs = list(mr.exterior.coords)[:4]
        e0 = math.dist(cs[0], cs[1]); e1 = math.dist(cs[1], cs[2])
        # ridge runs along the long side, through the middle of the rectangle
        if e0 >= e1: a = ((cs[1][0] + cs[2][0]) / 2, (cs[1][1] + cs[2][1]) / 2); b = ((cs[3][0] + cs[0][0]) / 2, (cs[3][1] + cs[0][1]) / 2)
        else: a = ((cs[0][0] + cs[1][0]) / 2, (cs[0][1] + cs[1][1]) / 2); b = ((cs[2][0] + cs[3][0]) / 2, (cs[2][1] + cs[3][1]) / 2)
        item['rect'] = [loc(x, y) for x, y in cs]
        item['ridge_line'] = [loc(*a), loc(*b)]
        item['size_m'] = [round(max(e0, e1), 1), round(min(e0, e1), 1)]
    elif kind == 'line':
        item['line'] = [loc(x, y) + [round(zat(x, y) - ORIGIN[2] + 0.4, 2)] for x, y in pts]
    else:
        x, y = pts[0]; item['point'] = loc(x, y); item['ground'] = round(zat(x, y) - ORIGIN[2], 2)
    if item['id'] in GEOM3D and kind == 'poly': _set_rect(item, GEOM3D[item['id']])
    for k, v in PROPS3D.get(item['id'], {}).items():
        if k == 'notes_add': item['notes'] = ((item.get('notes') or '') + ' ' + v).strip()
        else: item[k] = v
    out['features'].append(item)
for x in EXTRA3D:
    item = {k: x.get(k) for k in ('id', 'name', 'town', 'kind', 'built', 'removed', 'built_text', 'removed_text', 'loc', 'form', 'use',
                                    'material', 'stories', 'footprint_ft', 'evidence', 'sources', 'photos', 'notes', 'model')}
    item['massing'] = dict(eave=x['eave'], ridge=x['ridge'], roof='gable', src='estimated from the period photographs (see Appearance)'); item['geom'] = 'poly'
    _set_rect(item, x['rect']); out['features'].append(item)

riv = json.load(open(R('map', 'data', 'river_1883.geojson')))['features'][0]
_, pts = utm_geom(shape(riv['geometry']))
line = LineString(pts); dense = [line.interpolate(d) for d in np.arange(0, line.length, 6.0)]
out['river_1883'] = [loc(x, y) + [round(v - ORIGIN[2], 2)] for x, y, v in WATER83]
out['slough'] = [loc(x, y) + [round(v - ORIGIN[2], 2)] for x, y, v in WATER_SLOUGH]   # low confidence (see SLOUGH)
out['terrain'] = {'x0': meta['x0'] - ORIGIN[0], 'y1': meta['y1'] - ORIGIN[1], 'res': meta['res'], 'cols': meta['cols'], 'rows': meta['rows'],
                  'z0': meta['z0'] - ORIGIN[2], 'scale': meta['scale'], 'file': 'terrain_pads.bin'}

# ---------------------------------------------------------------- appearance (for the detailed 3D models)
# wall: clapboard | drop | brick | yellowbrick | boardbatten | log ;  roof: shingle | tin | sod
# front: compass side of the main door; ridge: 'long' (along the long axis) or 'front' (front-gabled)
# basis: what the look is based on. Anything not stated in a photo or source is a best guess.
STYLE = {
 # ---- Medora, Main Street
 'hotel-de-mores': dict(wall='yellowbrick', wall_color='#ddd3bd', trim='#f3efe6', roof='shingle', front='W', ridge='long', stories=2, bays=11, upper_bays=11, gable_bays=2,
        arched=True, chimneys=2, chimney_at=dict(**{'from': 'E'}, at=[9.8, 24.5]), outside_stair=dict(side='E', top='S', at=2.6), eave=7.6, rise=3.0,
        openings=dict(E={0: [['win', 0.7]], 1: [['win', 0.7]]}),   # east gable: one window per floor offset north of the stair landing (t from the south end, the viewer's left standing east; 00042-00195)
        porch=[dict(side='W', depth=2.4, roof=False, h=0.45), dict(side='S', depth=2.4, roof=False, h=0.45)],
        part_styles=[dict(wall='clapboard', wall_color='#ece6d8', front='E', ridge='long', stories=1, bays=2, gable_bays=1, chimneys=1, arched=False, porch=[])],
        basis='Form from the 1885-86 overviews (SHSND 00042-00071, -00195, -00194): a light-toned two-storey building of one eave height with a plain gable at the east end, an outside stair up the east gable to an upper door, and a lower wing on the north side near the east end (the Cow Boy\'s 1885 kitchen and laundry). Height: eave about 7.5-8 m (00042-00195: 41-44 px at 570 m; the 1883 photo gives eave = length/4.0 = 7.6 m for the 100-ft length, ridge/eave 1.40). Walls: the Cow Boy says the hotel was brick-veneered in spring 1885, and the building reads light in every 1885-86 print, so a pale (cream) brick is used, like St. Mary\'s of the same year. Windows: narrow 2/2 sash under segmental brick arches, as in the 1890s photos of the brick hotel (SHSND 00042-00076/-00086, Houghton 3013534/3013559); those photos date from the 1890s (dress, wires), so the taller cross-gabled block they show is not modelled for 1885-87. Front platforms unroofed (the photos show a raised plank walk, no porch roof). No sign appears in any photo',
        phases=[dict(until=1885.3, wall='clapboard', wall_color='#ece6d8', arched=False, porch=[dict(side='W', depth=1.6, roof=False, h=0.25)], bays=10, upper_bays=8, gable_bays=2,
                     outside_stair=None, openings={}, parts=[], chimneys=2, front_openings=[['win', 0.25], ['double', 0.5], ['win', 0.75]],
                     basis='SHSND 00042-00149 (1883): two-storey clapboard hotel, light paint, gable roof of about 40 degrees with cornice returns, 6/6 windows with flat heads (10 openings below, 8 windows above on the long side), window-double door-window on the gable end with two windows above, two ridge chimneys, a low plank walk; eave 7.6 m and ridge 10.6 m from the camera solve against the 100 x 25 ft footprint; chimneys 9.8 and 24.5 m from the east end')]),
 'roberts-hall': dict(wall='drop', wall_color='#e2dccd', trim='#f3efe6', roof='shingle', front='S', ridge='front', stories=2, bays=10, upper_bays=10, paired=True, gable_bays=2,
        fanlight=True, upper_door=True, chimneys=1, false_front=False, storefront=True,
        basis='Houghton 3013539 (Hagedorn 1919, context): two-storey front-gabled frame hall, drop siding, sunburst/fan in the gable, central upper door with a small hood between two windows, a storefront below (recessed central double door between two large display windows, boarded by 1919; the same front in the Historic Medora courthouse panel photo), narrow side windows in pairs; SHSND 00042-00195 (1885) shows paired upper windows on the east side and an arched opening in the south gable. Cow Boy: 24x75, 26 ft. The outside stair once modelled on the east side is not confirmed in any photo and has been removed'),
 'metropolitan-hotel': dict(wall='drop', wall_color='#7c6a58', trim='#e8e2d4', roof='shingle', front='S', ridge='hip', stories=2, bays=10, upper_bays=10, paired=True, gable_bays=4,
        porch=[], chimneys=2, rise=1.0, overhang=0.6, front_openings=[['win', 0.07], ['win', 0.15], ['win', 0.27], ['win', 0.35], ['door', 0.5], ['win', 0.65], ['win', 0.73], ['win', 0.85], ['win', 0.93]],
        basis='SHSND 00042-00071, -00195 and -00194 (1885-86): a dark two-storey building with its long side east-west, about 22 x 10 m, a low hipped roof (seen from above in 00042-00071) with a projecting cornice, windows in pairs on both floors (about five pairs on the south face). In the c.1905 postcard (00259-00003) the same building is white. Cow Boy: drop siding, 35x80, long front porch planned. The front on Third Avenue (south) is inferred; no porch is modelled for 1885-87 because 00042-00195 shows the south face plain to the ground with the lower windows clear (the Cow Boy only says one was planned). Roof: a very low hip (rise 1.0 over 10 m) under a wide cornice, as 00042-00071 (near-flat from above), the 1900s panel photo and the replica show'),
 'ferris-store': dict(wall='clapboard', wall_color='#eee6cf', trim='#ffffff', roof='shingle', front='W', ridge='front', stories=2, bays=5, gable_bays=2,
        storefront=True, false_front=False, porch=[dict(side='W', depth=2.0, h=0.5, post_spacing=2.6, rise=0.5)], outside_stair=dict(side='S', top='E', at=10.5, len=6.0),
        chimney_at=dict(**{'from': 'W'}, at=[2.5, 12.0]),
        openings=dict(S={0: [['win', 0.08], ['win', 0.62], ['win', 0.8]], 1: [['win', 0.08], ['win', 0.52], ['win', 0.7], ['win', 0.88]]}),   # t from the west (front) end; the stair lands at t about 0.4
        basis='Hagedorn 1921 plate n436 ("Joe Ferris\'s Store", archive.org rooseveltinbadla00hage), the 1963 rebuild and the c.1900s photo on the Historic Medora panel all show the same building: a two-storey GABLE-FRONTED clapboard store with a boxed cornice and returns (returns not modelled), two upper windows in the gable, a shallow shed-roofed porch across the front on a raised plank platform, display windows either side of a recessed door, and a long shallow outside stair on the south side rising from about 1 m behind the front corner to a landing and upper door about 7 m back; two ridge chimneys (about 2.5 m behind the gable and two-thirds back). The false-fronted store in Houghton 3013537/3013655 is the neighbour at the left of Hagedorn\'s plate, not Ferris\'s (architectural review, Oct 20, 2026)'),
 'company-store-offices': dict(wall='clapboard', wall_color='#f0ebdf', trim='#ffffff', roof='shingle', front='E', ridge='front', stories=1, bays=2, gable_bays=1,
        part_styles=[dict(front_openings=[['win', 0.2], ['door', 0.5], ['win', 0.8]], chimney_at=dict(**{'from': 'E'}, at=[1.0])),
                     dict(front_openings=[['win', 0.2], ['double', 0.5], ['win', 0.8]], chimney_at=dict(**{'from': 'E'}, at=[2.0], off=-1.6), chimney_kind='pipe', chimney_h=1.2),   # stovepipe near the front, on the slope by the valley with the south block
                     dict(front_openings=[['door', 0.32], ['win', 0.72]], chimneys=0)] * 2,   # the same looks for the 1883-84 and the 1885 parts (geom3d.py builds both, dated)
        basis='Two dated states (joint solve of the 1883-84 close-up and the 1885 overview, Oct 20, 2026; docs/photo-audit.md). Houghton 3013533 (winter 1883-84; camera fitted at 1.4 percent of the group width, nearly square-on from about 27 m): three joined one-storey front-gabled white frame buildings, south to north about 7.9, 7.0 and 4.0 m wide (19 m of frontage), the ridges stepping down 5.8, 5.4, 4.3 m (eaves 3.5, 3.1, 2.7), the small north block standing about 1.5 m forward of the others (its south side wall shows), floors raised about 0.5 m with a flight of steps at each door and no continuous platform; a brick chimney on the south block\'s ridge close behind its gable and a thin stovepipe at the valley between the south and middle blocks near the front; no sign. SHSND 00042-00071 (summer 1885; camera held fixed, group re-measured): the same three gables but 7.9, 8.4 and 6.9 m wide (23.2 m), all at one height (eave about 3.8, ridge about 6.7 m), so the north block was rebuilt bigger between the photographs (the 1884-85 stage line, post office and NPRC offices); dated 1885.0. The old 27.4 m footprint was a 90 ft placeholder, not a measurement; 00042-00195 shows nothing of the group (it stands behind the Hotel de Mores). Depth 9.2 m unmeasured'),
 'cowboy-office': dict(wall='boardbatten', wall_color='#e6e0d0', trim='#ffffff', roof='shingle', front='E', ridge='front', stories=1, bays=2, gable_bays=0, rear_bays=0, eave=2.1, rise=1.8,
        no_front_door=True, chimney_at=dict(**{'from': 'W'}, at=[0.8]), plinth=dict(h=0.5, color='#8a7c68'),
        part_styles=[dict(wall='boardbatten', wall_color='#9a8c78', ridge='shed', shed_high='W', front='E', bays=0, gable_bays=0, rear_bays=0, front_openings=[['door', 0.5]], chimneys=0, no_front_door=False)],
        basis='Houghton 3013536 (summer, 1884-86), camera fitted to the building (worst point under 1% of its width): a long one-storey board-and-batten building about 2.5 times as long as wide (about 12 x 5 m, scaled from the man at the door, so possibly 20% larger), eave about 2.1 m and a roof of about 37 degrees, floor raised about 0.5 m; an unpainted board entry vestibule with a shed roof on the Main Street (east) gable, just south of centre; two windows on the long south side; capped brick chimney at the rear (west) of the ridge. Two lines of lettering are laid into the roof in light shingles but cannot be read, so none is modelled. Two lines of lettering are laid into the roof in light shingles but cannot be read, so none is modelled'),
 'paddock-livery': dict(wall='boardbatten', wall_color='#8c7a62', trim='#5b4a3a', roof='shingle', front='E', ridge='front', stories=1.5, bays=4, gable_bays=1,
        barn=True, basis='SHSND 00042-00071 (1885): a gable-fronted barn facing east with a big central wagon door and lean-tos; Cow Boy 1885 (livery barn, drop siding)'),
 'freight-house': dict(wall='boardbatten', wall_color='#9b8a70', trim='#5b4a3a', roof='shingle', front='S', ridge='long', stories=1, bays=12, gable_bays=1,
        barn=True, basis='Cow Boy (240 x 42 freight house); appearance a guess. The 1885-86 overviews show open ground at this spot, so its position is unconfirmed'),
 # ---- Medora, churches and houses
 'st-marys-church': dict(wall='yellowbrick', wall_color='#c8baa0', trim='#d9cfbd', door_w=1.4, door_h=2.65, arch_h=1.3, arch_extra=0.15, roof='shingle', front='W', ridge='front', stories=1, bays=5, gable_bays=1, rear_bays=0,
        arched='lancet', win_w=1.0, win_h=2.7, win_sill=1.1, plinth=dict(h=0.35, color='#a89a84'),
        openings=dict(W={0: [['archdoor', 0.5]]}, S={0: [['win', t] for t in (0.21, 0.41, 0.61, 0.80)]}, N={0: [['win', t] for t in (0.20, 0.39, 0.59, 0.79)]}, E={}),
        belfry=dict(w=2.0, base=0.35, skirt=0.35, stage=1.9, roof=1.7, back=-0.1, overhang=0.7, color='#4d443b', core=False), chimneys=0,   # open stage: sky shows through in 00042-00077 (no bell until 1946)
        basis='SHSND 00042-00077 (c.1886) and the standing church: buff brick, mid-toned in the prints (not white); west front with a broad central door (about 1.4 x 2.65 m) directly under a pointed blind arch in the brickwork, a low stone step in front and no other openings (today the same door and arch, with round-headed side windows that replaced the pointed ones); four tall pointed (lancet) windows of two lights, about 1 m wide and 2.7 m tall on stone sills about 1.1 m up, spaced about 3.4 m from about a fifth of the way along the side walls; blank east gable; a low stone foundation course; small square open belfry on the ridge just behind the west gable, all dark wood: shingled base, open stage on corner posts, steep pyramid roof with broad eaves; a zigzag split-rail fence runs behind the church, about 2 m wide. The 1886 roof is steeper than the lidar values (eave about 4.1 m, ridge about 8.1 m, fitted to the photo)'),
 'von-hoffman-house': dict(wall='brick', wall_color='#9a6a50', trim='#efe9dc', roof='shingle', front='S', ridge='long', stories=1.5, bays=5, gable_bays=2, arched=True,
        jerkin=['S', 'N'], jerkin_clip=0.3, front_openings=[['win', 0.25], ['door', 0.5], ['win', 0.75]],
        win_h=1.7, attic_sill=0.6, attic_win_h=1.4, attic_pair_gap=1.3,   # tall 2/2 sash; the close pair of gable windows sits above the porch roof (00042-00176, -00182, -00195)
        openings=dict(E={0: [['win', 0.14], ['win', 0.34], ['win', 0.52], ['win', 0.68], ['door', 0.86]]}),   # t from the south end (viewer's left standing east): four windows and the east door near the north end (00042-00195, -00071; NRHP)
        porch=[dict(side='S', depth=2.3, h=0.35, post_h=2.1, rise=1.05, posts_t=[0.0, 0.158, 0.364, 0.502, 0.705, 0.888, 1.0], posts_from='W', rail=False)], chimneys=2,
        basis='SHSND 00042-00176, -00182, -00071, -00195 and the standing house: brick, long north-south ridge with a clipped (jerkinhead) south gable over a full-width porch on square chamfered posts, a close pair of attic windows in the gable, two ridge chimneys, four windows and a door on the east side, a post-and-rail fenced yard to the west and north. The 1977 National Register nomination: common-bond brick, "hip-gabled" wood-shingle roof, 2/2 windows under segmental brick arches, the original one-storey front porch, about 38 x 48 ft. The north end is shown clipped too (probable). The wall colour is not recorded; a red-brown common brick is used (the 1885 prints read mid-tone). No porch rail: 00042-00182 and -00195 show the porch open between the posts (architectural review, Oct 20, 2026)'),
 'courthouse-cottages': dict(wall='brick', wall_color='#e9e4d8', trim='#efe9dc', roof='shingle', front='E', ridge='hip', stories=1, bays=2, gable_bays=1, eave=2.8, rise=2.0,
        chimneys=1, chimney_at=dict(**{'from': 'N'}, at=[4.0]), split=dict(n=2, gap=0.256),   # the stack at the apex of each pyramid (courthouse panel photo); gap: see basis
        basis='SHSND 00042-00195 and -00194: two separate identical one-storey cottages with near-pyramidal dark hipped roofs and a gap of about 2.75 m as built here (the split takes 2.75 m out of a 21.5 m rect; the photos were read as 5-6 m, but the pair was fitted to the solved overviews at this spacing, so the rect is kept and the figure corrected), walls bright white (brick per the Cow Boy, so whitewashed or painted), each about 8 m square with a door and two windows on the east'),
 # ---- the Chateau (colours as the State Historical Society keeps it today)
 'chateau-de-mores': dict(wall='clapboard', wall_color='#a3a29b', trim='#8b2e24', roof='shingle', roof_color='#7c3428', front='E', ridge='long', stories=2, bays=6, gable_bays=3,
        eave=6.3, rise=3.1,
        shutters='#8b2e24', chimney_at=dict(**{'from': 'W'}, at=[2.6, 15.5, 20.5]),
        openings=dict(S={0: [['win', 0.06], ['win', 0.15], ['hooddoor', 0.25], ['win', 0.5], ['door', 0.62], ['win', 0.75], ['win', 0.9]],
                         1: [['win', 0.06], ['win', 0.14], ['shut', 0.37], ['shut', 0.54], ['shut', 0.82]]},
                      N={1: [['win', 0.38], ['shut', 0.46], ['win', 0.60], ['win', 0.76], ['win', 0.92]]},   # t from the east (viewer's left standing north); none above the wing (00042-00191)
                      E={0: [['win', 0.22], ['door', 0.5], ['win', 0.78]], 1: [['win', 0.22], ['win', 0.5], ['win', 0.78]]},
                      W={0: [['win', 0.3], ['win', 0.7]], 1: [['win', 0.5]]}),
        porch=[dict(side='E', depth=3.0, h=0.5, post_spacing=2.4, rail=True, rise=1.1), dict(side='S', depth=3.0, h=0.5, post_spacing=2.4, rail=True, span=[0.42, 1.0], span_from='W', extend=3.0, rise=1.1)],
        basis='Height: the 2021 lidar ridge (9.4 m) with a two-storey eave of about 6.3 m (the lidar eave of 3.8 m is the veranda roof). Colours follow the building as the State Historical Society of North Dakota maintains it today (grey siding with red roof and trim; the 1974 National Register nomination describes "French grey" siding with a red roof and shutters). The Cow Boy of Nov. 26, 1885 described "green sides and red roof"; the 1883-86 photographs show light walls and a dark roof, which fits either. Doors and windows of the main block follow the 2023 drone photogrammetry model of the building (Sketchfab, ajkclark) and the 1975 National Register nomination (the veranda runs along the east side and "partway down the south side"). The north side follows the 1883-86 photographs, not today\'s hipped ell: a front-gabled service wing (ridge north-south, gable to the north) at the north-east corner with a stove pipe near the house (00042-00158, -00191, -00197, MHS 72389; the same wing in the 1969 NRHP photographs), a low shed lean-to against its north gable, a shed-roofed lean-to with large windows along the north wall west of it, and no upper windows on the north wall above the wing (00042-00191). Chimneys for 1883-86: two on the ridge (about 2.6 and 15.5 m from the west, 00042-00152) and the big stack at the wing junction (00042-00191, -00197); the east-end ridge chimney first appears in the 1920s photographs and is left out. A west door the nomination says was later made a window is not modelled as a door. Form from SHSND 00042-00152/-00157/-00196/-00197 and MHS 72389/72403: two-storey side-gabled main block, no dormers, board shutters; a one-storey rear wing with its ridge running north-south; a one-storey veranda with open rafters along the whole east end, wrapping the south-east corner and covering about the eastern half of the south front; chimneys near the west end and about a third from the east end, and a stove pipe on the wing'),
 # ---- railroad
 'medora-depot': dict(wall='boardbatten', front='S', ridge='front', stories=1,
        part_styles=[dict(wall='boardbatten', wall_color='#6f5d4a', trim='#c9bfa8', timber='#5d4c3a', roof='shingle', front='S', ridge='front', stories=1,
                          overhang=1.6, gable_overhang=1.5, brackets=dict(spacing=2.7, drop=1.0, strut=True), bays=3, gable_bays=0, rear_bays=0,
                          front_openings=[['transomdoor', 0.223]], door_h=2.1, transom_h=0.45, bay_window=dict(w=2.4, d=0.7, eave=3.0, win_top=2.1, offset=0.8, offset_dir='E'),
                          openings=dict(E={0: [['door', 0.1], ['win', 0.45], ['win', 0.8]]}),   # east side: a door in the first bay from the track (barrel beside it in MHS 72461), windows further back
                          chimney_at=dict(**{'from': 'S'}, at=[2.5, 8.0]), chimney_h=0.8, roof_extend=dict(end='N', len=2.3, deck=True, deck_h=0.45),
                          signs=[dict(id='medora-depot', w=3.4, aspect=0.15, at=2.18, out=0.76, on_bay=True, photo='MHS 72461')])],   # the board (2.18-2.7 m in the fitted camera) sits on the bay's face under its eave, the window heads just below it
        basis='Huffman 1886 (MHS 72461), measured with the door (2.1 m) as scale: a one-storey board-and-batten depot whose gable end faces the track, about 4-5 m from it, standing at the back of a plank platform at rail height. The roof is about 30 degrees with very deep eaves (about 1.7 m at the sides, 1.2 m at the gable) on diagonal knee braces, and runs on one X-braced bay (about 2.3 m) past the north end wall over open posts (camera fitted to the building: eave about 3.5 m, ridge 5.6 m). The gable end has a door with a transom west of a canted three-sided bay window with its own low hip roof; two corbelled brick chimneys; railings on the platform either side. 5.6 m across the track face, about 13.5 m of enclosed walls. The walls read mid-dark in the print; the actual colour is unknown. Sign: a dark board with white letters across the bay head reading MEDORA, with ST. PAUL and PORTLAND mileboards at its ends; the mileage figures are not reliably legible in the scan, so the model leaves them blank'),
 'lm-depot': dict(wall='boardbatten', front='S', ridge='long', stories=1,
        part_styles=[dict(wall='boardbatten', wall_color='#e6dfcf', trim='#ffffff', roof='boards', front='S', ridge='long', stories=1, bays=2, gable_bays=1,
                          front_openings=[['win', 0.2], ['door', 0.5], ['win', 0.8]], chimney_at=dict(**{'from': 'W'}, at=[1.0], off=1.0), chimney_kind='pipe', chimney_h=1.0),   # one thin stovepipe on the rear (north) slope near the west end
                     dict(wall='drop', wall_color='#e9e4d8', trim='#ffffff', roof='shingle', front='S', ridge='long', stories=1, bays=0, gable_bays=0,
                          front_openings=[['door', 0.45]], chimneys=0)],
        basis='Haynes 1881 (SHSND 00119-00017 = MHS 108837): two attached one-storey gabled blocks along the track, ridges parallel to it. West block: very light board-and-batten, a roof of boards laid eave to ridge, window-door-window on the track side, a stovepipe; east block: deeper and higher, smooth light walls, shingle roof, a single door with a small plaque, no flue. A plank walk along the track, no raised platform. Colours from the light tones of the print'),
 'pyramid-park-hotel': dict(wall='drop', front='S', ridge='long', stories=1.5,
        # main front (Haynes 1881, left to right): door, window, window, [window, window, door under the cross gable]; stovepipes, no brick
        part_styles=[dict(wall='drop', wall_color='#7d6f60', trim='#d8d0c0', roof='shingle', front='S', ridge='long', stories=1.5, bays=4, gable_bays=1,
                          front_openings=[['door', 0.065], ['win', 0.21], ['win', 0.37]], chimneys=3, chimney_kind='pipe', chimney_h=1.2),
                     dict(wall='drop', wall_color='#7d6f60', trim='#d8d0c0', roof='shingle', front='S', ridge='front', stories=1.5, bays=0, gable_bays=2, rear_bays=0,
                          front_openings=[['win', 0.22], ['win', 0.5], ['door', 0.85]], chimneys=0),
                     dict(wall='clapboard', wall_color='#ece6d6', trim='#ffffff', roof='shingle', front='S', ridge='front', stories=1.5, bays=1, gable_bays=1, rear_bays=0,
                          front_openings=[['win', 0.5]], chimneys=0),
                     dict(wall='clapboard', wall_color='#e6dfcf', trim='#ffffff', roof='shingle', front='W', ridge='front', stories=1.5, bays=1, gable_bays=1, chimneys=1, chimney_kind='pipe')],
        basis='Haynes 1881 (SHSND 00119-00017): a main block with its ridge along the track and its front to the south, one tall storey with a loft under a steep roof (Hagedorn\'s "loft with 14 beds"), a front-facing cross gable with two upper windows at the east end, its apex at the main ridge (one continuous ridge, no gable at the back); a light front-gabled block at the west end, flush with the front, its gable to the south; and a light rear wing behind it shows its gable to the west; a very small shack stands to the north-west. The ground between the depot and the hotel is level and open, with no road. Along the front, left to right: door, four windows, and a door at the far east end under the cross gable; no upper windows on the front. Dark weathered horizontal siding on the main block, new light boards on the west block, three thin stovepipes (no brick chimneys); no porch roof, only a plank walk. No sign is visible'),
 'cantonment': dict(wall='vlog', wall_color='#b9b3a6', trim='#5b4a3a', roof='shingle', roof_color='#8f877a', front='N', ridge='long', stories=1, bays=6, gable_bays=0, chimneys=0, eave=1.9, rise=1.9,
        door_h=1.75, win_w=0.7, win_h=0.8,   # low doors under the 1.9 m eave; small square windows
        # about 13 openings along the front with four full-height doors at roughly 0.30, 0.45, 0.57 and 0.80 of the length from the west (MHS 91738); t here runs from the east (the viewer's left standing north of it)
        openings=dict(N={0: [[k, round(1 - t, 2)] for k, t in (('win', 0.08), ('win', 0.15), ('win', 0.22), ('door', 0.30), ('win', 0.38), ('door', 0.45), ('win', 0.51), ('door', 0.57), ('win', 0.64), ('win', 0.71), ('door', 0.80), ('win', 0.87), ('win', 0.94))]}, E={}, W={}),
        basis='Haynes 1880 (MHS 91738): long one-storey barracks of vertical cedar logs, stockade style, weathered grey, with a shingle or board gable roof (not sod), evenly spaced doors and windows along the long side; the photographed building measures about 29.5 x 6.8 m with an eave of about 1.9 m (camera fitted to the butte skyline). The barracks were 200 x 22 ft (HM52); the buildings here are the plat\'s schematic symbols, so their sizes are placeholders'),
 # ---- Little Missouri: the saloon, the store and the shacks (no photographs except Maunders's hut; architectural review, Oct 20, 2026)
 'lm-roberts-saloon': dict(wall='boardbatten', wall_color='#d2c3a5', trim='#e8e2d4', roof='shingle', front='N', ridge='front', stories=1, bays=3, gable_bays=1,
        storefront=False, false_front=True, false_front_extra=0.4, front_openings=[['win', 0.25], ['door', 0.5], ['win', 0.75]], chimneys=1, chimney_kind='pipe', eave=2.8, rise=2.0,
        basis='No photograph. Hagedorn: one-storey "palace of sin" beside the hotel; a plain false-fronted frame saloon with a stovepipe, facing the hotel yard, is assumed'),
 'nelson-store': dict(wall='boardbatten', wall_color='#a89a86', trim='#e8e2d4', roof='shingle', front='N', ridge='front', stories=1, bays=3, gable_bays=1,
        storefront=True, false_front=True, chimneys=1, chimney_kind='pipe', eave=3.0, rise=2.2,
        basis='No photograph. Hagedorn: south of the track; Cow Boy 1884: Ferris\'s dry-goods store in Nelson\'s building, enlarged June 1884. Generic false-fronted store facing the track, stovepipe'),
 'mcgeeney-boarding-house': dict(wall='boardbatten', wall_color='#a89a86', trim='#b9ad98', roof='shingle', front='N', ridge='long', stories=1, bays=3, gable_bays=1, chimneys=1, chimney_kind='pipe', eave=2.5, rise=1.8,
        basis='No photograph. Lang: "three or four rough shacks" south of the track at the foot of Graveyard Butte. Low board shack facing the track, stovepipe'),
 'fitzgerald-shack': dict(wall='log', wall_color='#9a8a74', trim='#7a6a55', roof='shingle', front='N', ridge='long', stories=1, bays=2, gable_bays=0, chimneys=1, chimney_kind='pipe', eave=2.2, rise=1.6,
        basis='No photograph. Section foreman\'s shack "on the brink of the river" (Hagedorn); low log shack with a stovepipe assumed'),
 'maunders-shack': dict(wall='boardbatten', wall_color='#d8cfbd', trim='#b9ad98', roof='shingle', front='S', ridge='long', stories=1, bays=1, gable_bays=0, chimneys=1, chimney_kind='pipe', eave=2.0, rise=1.2,
        basis='Haynes 1881 (SHSND 00119-00017): a very small hut north-west of the hotel; size from the back-projection, height assumed; stovepipe'),
 # ---- packing plant
 'pp-foundation': dict(wall='drop', front='S', ridge='flat', stories=3,
        part_styles=[dict(wall='drop', wall_color='#9e9586', trim='#8a8173', timber='#6e6558', roof='tin', roof_color='#77736c', front='S', ridge='flat', parapet=0.4, stories=3,
                          bays=0, gable_bays=0, blank=True, no_front_door=True, plinth=dict(h=0.9, color='#a39882'), monitor=dict(len_frac=0.2, at=-0.1, w=3.0),
                          runway=dict(end='W', len=27.5, h=10.9, h2=12.3, depth=2.1, off=-0.6,
                                      struts=[[[24.0, 8.6], [22.4, None]], [[15.6, 8.5], [18.4, None]], [[15.6, 8.5], [12.8, None]]]), chimneys=0,
                          signs=[dict(id='pp-rentfree', side='S', w=22, aspect=0.057, at=2.2, along=0.45, **{'from': 1887.0}, photo='SHSND 00042-00180')]),
                     dict(wall='drop', wall_color='#a39a8c', trim='#8a8173', roof='tin', roof_color='#77736c', front='S', stories=3,
                          bays=6, gable_bays=2, ridge='shed', shed_high='E', rise=1.0, chimneys=0,   # no no_front_door: it would suppress front_openings
                          front_openings=[['win', 0.08], ['win', 0.25], ['win', 0.42], ['win', 0.58], ['win', 0.75], ['win', 0.92]],   # three rows on the south face (00042-00074, MHS 72460)
                          monitor=dict(len_frac=0.6, w=2.2, h=1.3)),   # louvred monitor along the high (east) edge of the annex roof (00042-00075, 00042-00074)
                     dict(wall='drop', wall_color='#958c7d', trim='#8a8173', timber='#6e6558', roof='tin', roof_color='#77736c', front='S', stories=1,
                          bays=0, gable_bays=0, blank=True, no_front_door=True, ridge='shed', shed_high='N', rise=0.6, chimneys=0,
                          gallery=dict(side='S', span=[-2.1, 9.6], **{'from': 'W'}, levels=3, depth=2.4, h=9.3, porch=4.3, until=1886.0, doors=False))],   # doors=False: the generator's upper door would float above the 4.5 m wing eave   # in the 1885 photo; gone in the 1886 and 1887 ones
        basis='SHSND 00042-00074 (= 00042-00153 and 0039_00001, the same 1885 exposure; the "1883" on the card is wrong), 00042-00075 (from the north), Huffman 1886 (MHS 72460) and 00042-00180: three parts: a tall nearly windowless block (32.6 m long, eave about 10 m; its long axis runs ENE-WSW at about 76 degrees, not due east: placed by a joint solve of the two plant photos and the town overviews 00042-00071 and -00195 about the surviving chimney) of horizontal siding on a stone foundation course, with a short box ventilator on its low roof; a lower annex at the west end with three rows of small windows and a louvred monitor (its roof slopes down to the west, eave about 8.4 m there and 9.4 m at the block); and a low one-storey east wing (eave about 4.5 m) between the block and the tower, fronted in 1885 by three levels of galleries (a roofed porch below, open framing above, up to about 9 m) that run from just west of the block\'s south-east corner to the tower (00042-00074; gone by 1886 in MHS 72460 and 00042-00180). An enclosed, roofed runway slopes from the top of the tall block (roof about 10.9 m) up to a timber pier about 25 m west-south-west of the block (roof about 12.3 m), with only a few struts beneath it near the ends: a knee brace at the pier and a V-strut standing on the annex\'s west end (MHS 72460, 00042-00074, -00075); an open walkway rises from the block\'s east end (about 8 m) to the tower (about 9 m); a small log hut with a shed roof stands in front of the east building; a raised loading platform runs along the north side. Depth not measurable in the photos; 8.2 m (assumed) meets the cooling house (the foundation note gives 14-24 ft). Sign: the undated "rent free" banner (00042-00180) is on the south wall; shown only in the spring 1887 view'),
 'pp-ice-house': dict(wall='diagonal', wall_color='#5e564c', trim='#4a443c', roof='shingle', roof_color='#4f4a44', front='S', ridge='long', stories=2, bays=0, gable_bays=0,
        vents=2, vent_w=2.0, vent_h=1.4, chimneys=0, eave=5.0, rise=3.0, barn=True,
        basis='MHS 72460 (left) and SHSND 00042-00075 (right): a long dark gabled shed of diagonal boards (laid at about 45 degrees; the wall texture follows them), ridge east-west, two LARGE louvred ridge ventilators (about 2 m square, hip-capped) and, on the north side at the west end, a cross-gabled wing as high as the main ridge (00042-00075; the south face is plain in 72460); eave about 5 m; located from Huffman\'s view (its south-west corner; its east end hidden behind the runway pier), 00042-00075 from the north (in front of the pier) and the dark gable left of the pier in 00042-00071. Dated from the Cow Boy (Dec. 1884, 4,000 tons of ice); the large boarded building going up right of the timber frame in 00042-00188 (1883) is NOT this one but stands near the plant (perhaps the first ice house the NRHP says adjoined it) and is not modelled. The tower and cupola once modelled here belong to the cooling house'),
 'pp-cooling-house': dict(wall='clapboard', wall_color='#d9d3c4', trim='#bdb5a5', roof='shingle', roof_color='#5f5a54', front='N', ridge='hip', stories=3, bays=2, gable_bays=2, no_front_door=True,
        openings=dict(N={0: [['double', 0.35], ['win', 0.65]], 2: [['win', 0.8]]}, S={}, E={}, W={}),   # nearly blank walls: the loading door and a tall window at the north platform (00150), one small window high on the north face (00188)
        cupola=[dict(w=1.8, h=1.6, cap=1.5, until=1885.0), dict(w=3.2, h=2.3, cap=2.1, from_date=1885.0)], chimneys=0, rise=3.0,
        basis='SHSND 00042-00150 and -00188 (1883), seen behind the plant in 00042-00074/-00075 and MHS 72460: a near-cubic block of painted clapboard, eave about 9 m (scaled from the refrigerator car beside it), a hipped roof with a square louvred cupola, a loading platform on trestle legs at car-floor height. The walls are nearly blank in 00188, 00150 and 00075 (one or two openings a face, not a window grid). Cupola: small in 1883 (00188: about 1.8 m wide, 1.6 m body, 1.5 m cap), much larger in 1885-87 (00074 against the chimney, 00075 against the building: about 3.2 m square, 2.3 m louvred body, 2.1 m steep cap with a finial), so enlarged or rebuilt between 1883 and 1885; the model dates the two sizes at 1885.0'),
 'pp-east-building': dict(wall='diagonal', wall_color='#5e564c', trim='#4a443c', roof='shingle', roof_color='#4f4a44', front='S', ridge='long', stories=1, bays=0, gable_bays=0,
        vents=2, barn=True, chimneys=0, eave=6.0, rise=3.0,
        basis='SHSND 00042-00074 (= 0039_00001), MHS 72460, 00042-00071, DMC 25741: a dark gabled building sheathed in diagonal boards (00074, 00075, 72460; the wall texture follows them) with its ridge east-west and its gable end to the east, two ridge ventilators, eave about 6 m (00074 gives about 6.5, 72460 about 5.6), about 17.5 x 11 m (its east gable at x 1622 in 00074 and its east end in the panorama DMC 25741); located from the plant photos and the overviews, its south-west corner at the tower; identity unknown'),
 'pp-east-tower': dict(wall='boardbatten', wall_color='#4f483f', trim='#4a443c', roof='shingle', roof_color='#4a453f', front='S', ridge='hip', stories=3, bays=0, gable_bays=0,
        blank=True, no_front_door=True, chimneys=0, rise=1.1, basis='SHSND 00042-00074, MHS 72460: a tall narrow dark tower (about 2.7 m square) with a pyramid cap (eave about 10.3 m, peak about 11.4 m in both photos), standing on a lower front-gabled board base about 3.6 m wide (eave about 5.3 m, gable to the south with a long ladder on it in MHS 72460)'),
 'pp-north-frame': dict(frame=dict(posts_along=9, posts_across=2, post_h=5.0, braces=True, girts=True, roof='none'), timber='#a08463',
        basis='SHSND 00042-00188 (1883): an open timber frame of posts at about 2 m, wall plates about 5 m up and tie joists, with diagonal and X braces'),
 'pp-north-barn': dict(wall='boardbatten', wall_color='#5e564c', trim='#4a443c', roof='shingle', roof_color='#4f4a44', front='N', ridge='front', stories=1.5, bays=0, gable_bays=0, chimneys=0, barn=True,
        basis='The 1883 frame closed in; dark boards. SHSND 00042-00075 (1885) shows its gable end to the north (ridge north-south) and its ridge well below the cooling-house eave (about 6-6.5 m, eave about 3-4 m); low confidence either way'),
 'pp-log-hut': dict(wall='log', wall_color='#7a6a58', trim='#5b4a3a', roof='boards', roof_color='#b8b0a0', front='S', ridge='shed', shed_high='N', rise=0.7, stories=1, bays=1, gable_bays=0, chimneys=0,
        basis='SHSND 00042-00074 and MHS 72460: a small log hut (about 6 x 3.6 m, eave about 2.2 m) with a light board shed roof in front of the east building'),
 # ---- Chateau outbuildings, and buildings added from the overviews
 'chateau-outbuilding-east': dict(wall='clapboard', wall_color='#e6e1d6', trim='#ffffff', roof='shingle', front='S', ridge='long', stories=1, bays=1, gable_bays=1, chimneys=1,
        basis='SHSND 00042-00152 (1883): small light gabled one-storey building east of the house'),
 'chateau-stable': dict(wall='boardbatten', wall_color='#6a5d4e', trim='#4a443c', roof='shingle', front='S', ridge='long', stories=1, bays=3, gable_bays=1, chimneys=0, barn=True,
        basis='SHSND 00042-00157 (1884): long, low, dark gabled building with wagons in front; place provisional'),
 'photo85-x1': dict(wall='clapboard', wall_color='#ece8de', trim='#ffffff', roof='shingle', front='S', ridge='long', stories=1, bays=2, gable_bays=1, chimney_at=dict(**{'from': 'W'}, at=[0.3]),
        basis='SHSND 00042-00195/-00194/-00193: white one-storey side-gabled cottage, chimney at the west gable'),
 'photo85-x2': dict(wall='clapboard', wall_color='#ece8de', trim='#ffffff', roof='shingle', front='S', ridge='long', stories=1, bays=2, gable_bays=1, chimneys=1,
        front_openings=[['win', 0.25], ['door', 0.5], ['win', 0.75]], basis='SHSND 00042-00194/-00193: white side-gabled house, door and two windows facing south, chimney'),
 'photo85-x2b': dict(wall='boardbatten', wall_color='#6a5e50', trim='#4a443c', roof='shingle', front='S', ridge='long', stories=1, bays=1, gable_bays=0, chimneys=0,
        basis='SHSND 00042-00194: a darker building (log or unpainted boards) against the white house'),
 'von-hoffman-outbuilding': dict(wall='boardbatten', wall_color='#bfb3a0', trim='#efe9dc', roof='shingle', roof_color='#8c8378', front='S', ridge='long', stories=1, bays=1, gable_bays=1, chimneys=0, barn=True,
        basis='SHSND 00042-00071/-00193: low gabled outbuilding with a light roof inside the fenced yard'),
 # ---- unidentified buildings placed from the 1885-86 photos (descriptions from the photo audit)
 'photo85-g': dict(wall='drop', wall_color='#6e6458', trim='#5b5248', roof='tin', ridge='flat', parapet=0.3, front='', stories=1, bays=2, gable_bays=1, chimneys=0, eave=3.0,
        basis='SHSND 00042-00195/-00194/-00071: low dark building of horizontal boards against the east end of Roberts Hall, flat or very low shed roof, about 3 m tall'),
 'photo85-c': dict(wall='boardbatten', wall_color='#6f6253', trim='#5b4a3a', roof='shingle', front='E', ridge='front', stories=1, bays=2, gable_bays=1, barn=True, chimneys=0, eave=3.0, rise=2.5,
        basis='SHSND 00042-00071/-00195/-00194: unpainted dark front-gabled board building facing east, steep roof, large dark opening like a barn or stable'),
 'photo85-f': dict(wall='boardbatten', wall_color='#6f6253', trim='#5b5248', roof='shingle', roof_color='#9a917f', front='E', ridge='front', stories=1, bays=1, gable_bays=1, chimneys=1,
        basis='SHSND 00042-00071/-00195: small one-storey gabled building of dark unpainted boards, gable and door facing east, light new-shingle roof'),
 'photo85-m': dict(wall='clapboard', wall_color='#ece8de', trim='#ffffff', roof='shingle', front='', ridge='long', stories=1, bays=2, gable_bays=1, chimneys=1, eave=3.0,
        basis='SHSND 00042-00195: white one-storey side-gabled cottage (00042-00193 shows the spot empty; may be the same house as u09)'),
 'photo85-o': dict(wall='boardbatten', wall_color='#8a7c68', trim='#e8e2d4', roof='shingle', front='', ridge='long', stories=1, bays=1, gable_bays=1, chimneys=1, eave=2.6, rise=1.0,
        basis='SHSND 00042-00195: a low one-storey building behind a tall board fence'),
 'photo85-u01': dict(wall='boardbatten', wall_color='#ece8de', trim='#ffffff', roof='shingle', roof_color='#a8a090', front='', ridge='long', stories=1, bays=1, gable_bays=0, chimneys=0, eave=2.5, rise=1.3,
        basis='SHSND 00042-00071: small white shed with a light low gable roof, ridge parallel to the track'),
 'photo85-u02': dict(wall='clapboard', wall_color='#e6e0d2', trim='#ffffff', roof='shingle', front='E', ridge='front', stories=1.5, bays=1, gable_bays=1, chimneys=1, eave=2.8,
        basis='SHSND 00042-00071: small light house, gable to the east with a gable window, dark lean-to on the south'),
 'photo85-u03': dict(wall='clapboard', wall_color='#f0ece2', trim='#ffffff', roof='shingle', front='E', ridge='long', stories=1, bays=2, gable_bays=1, chimneys=1,
        basis='SHSND 00042-00071: white one-storey L-plan house, side-gabled main roof with a chimney at mid-ridge and a front-gabled wing at the south end facing east'),
 'photo85-u04': dict(wall='clapboard', wall_color='#e9e4d8', trim='#ffffff', roof='shingle', roof_color='#a8a090', front='E', ridge='front', stories=1, bays=3, gable_bays=1, chimneys=0, eave=3.0, barn=True,
        basis='SHSND 00042-00071/-00193: one light front-gabled barn-like building with its gable and a wide dark opening to the east, ridge east-west, a lower light shed west of it (u05) (low confidence)'),
 'photo85-u05': dict(wall='clapboard', wall_color='#ece8de', trim='#ffffff', roof='shingle', front='', ridge='shed', shed_high='E', stories=1, bays=1, gable_bays=1, chimneys=0, eave=2.5, rise=0.6,
        basis='SHSND 00042-00071: the low light shed west of u04\'s barn-like building (low confidence)'),
 'photo85-u07': dict(wall='boardbatten', wall_color='#d9d2c2', trim='#ffffff', roof='shingle', roof_color='#a8a090', front='', ridge='long', stories=1, bays=2, gable_bays=1, chimneys=1, eave=2.8, rise=1.5,
        basis='SHSND 00042-00193: long low light-roofed gabled building, long axis about NNE-SSW'),
 'photo85-u08': dict(wall='clapboard', wall_color='#ece8de', trim='#ffffff', roof='shingle', front='S', ridge='front', stories=1, bays=1, gable_bays=1, chimneys=1, eave=3.0,
        front_openings=[['door', 0.5], ['win', 0.8]], basis='SHSND 00042-00195: white one-storey front-gabled building, central door and small window, gable to the south'),
 'photo85-u09': dict(wall='clapboard', wall_color='#f0ece2', trim='#ffffff', roof='shingle', front='E', ridge='front', stories=1.5, bays=2, gable_bays=1, chimneys=1,
        bay_window=dict(side='E', w=2.4, d=0.7, eave=2.6, offset=1.0, offset_dir='S'), porch=[dict(side='S', depth=1.8)],
        basis='SHSND 00042-00071/-00193: white one-and-a-half-storey house, front gable to the east with a bay window, porch in the angle on the south'),
 'photo85-u11': dict(wall='boardbatten', wall_color='#6e6458', trim='#5b5248', roof='shingle', front='', ridge='long', stories=1, bays=1, gable_bays=0, chimneys=0, eave=2.5,
        basis='SHSND 00042-00195/-00193: small dark low shed'),
}
COMMERCIAL = ('store', 'saloon', 'drug', 'hotel', 'restaurant', 'office', 'rink', 'billiard', 'shop', 'bar')
PALETTE = ['#efe9dc', '#e6dcc6', '#d8cfbd', '#c9bfae', '#a89a86', '#e9e2cf', '#d2c3a5']
def default_style(f):
    u = (f.get('use') or '').lower(); st = (f.get('stories') or '').strip()
    h = sum(map(ord, f['id']))
    stories = 2 if st.startswith('2') else (1.5 if (st.startswith('1 1/2') or st.startswith('1.5')) else 1)
    commercial = any(k in u for k in COMMERCIAL) and 'dwelling' not in u
    long = (f.get('size_m') or [9, 6])[0]
    return dict(wall=['clapboard', 'clapboard', 'boardbatten', 'drop'][h % 4], wall_color=PALETTE[h % len(PALETTE)], trim='#f3efe6',
                roof='shingle', front='', ridge='front' if commercial else 'long', stories=stories, bays=max(1, round(long / 3.2)), gable_bays=1,
                storefront=commercial, false_front=commercial, chimneys=1, porch=[], basis='best guess: typical Dakota frame building of the 1880s')

# styles, period phases and sub-blocks
from shapely.geometry import Polygon as SPoly
from shapely import affinity
def rect_of(poly):
    mr = poly.minimum_rotated_rectangle; cs = list(mr.exterior.coords)[:4]
    return [loc(*c) if False else [round(c[0], 2), round(c[1], 2)] for c in cs]
new = []
for it in out['features']:
    st = STYLE.get(it['id'])
    if it['geom'] != 'poly' or (it.get('massing') or {}).get('roof') in ('none', 'chimney') or it['kind'] in ('landmark',):
        new.append(it); continue
    if st is None: st = default_style(it)
    st = dict(st); phases = st.pop('phases', [])
    for k, v in STYLE_ADD.get(it['id'], {}).items():
        if k == 'parts':   # rects from geom3d, looks from the STYLE entry's part_styles (same order)
            ps = st.pop('part_styles', [{}] * len(v))
            st['parts'] = [dict(p, style=dict({a: b for a, b in (p.get('style') or {}).items() if not a.startswith('_')}, **(ps[i] if i < len(ps) else {}))) for i, p in enumerate(v)]
        else: st[k] = v
    st.pop('part_styles', None)
    if it['id'] == 'chateau-de-mores':
        poly = SPoly(it['ring']).buffer(0)
        a, b = (-739.93, -228.55), (-715.55, -237.74)
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); px, py = -dy / L, dx / L
        q = lambda t, d: [round(a[0] + dx * t + px * d, 2), round(a[1] + dy * t + py * d, 2)]
        # main two-story block along the south front, and a rear block filling the rest of the footprint
        st['blocks'] = [[q(0, 0), q(1, 0), q(1, 9), q(0, 9)]]
        # one-storey service wing as the 1883-86 photographs show it (SHSND 00042-00158, -00191, -00197; MHS 72389; the same form in
        # the 1969 NRHP photographs): a front-gabled wing (ridge north-south, gable to the north) at the north-east corner, its east
        # wall about 1.5 m inside the main east wall, running about 10.5 m north, stove pipe near its south end; a low shed lean-to
        # against its north gable (shuttered window, stove pipe: 00042-00191, 72389); and a shed-roofed lean-to with large windows
        # along the rest of the north wall west of the wing (00042-00191). Today's long hipped ell is later (architectural review, Oct 20, 2026).
        st['parts'] = [dict(rect=[q(0.69, 9.0), q(0.94, 9.0), q(0.94, 19.5), q(0.69, 19.5)], eave=2.9, ridge=5.2,
                            style=dict(front='N', ridge='front', stories=1, bays=2, gable_bays=1, porch=[], chimneys=1, shutters='#8b2e24',
                                       chimney_kind='pipe', chimney_h=1.3, chimney_at=dict(**{'from': 'S'}, at=[2.0]),
                                       attic_sill=0.45, attic_win_h=0.9,   # the small window in the north gable sits above the lean-to roof (00042-00191)
                                       openings=dict(E={0: [['win', 0.3], ['door', 0.78]]}, W={0: [['win', 0.3], ['win', 0.7]]}, N={'a': [['win', 0.5]]}))),
                       dict(rect=[q(0.69, 19.5), q(0.94, 19.5), q(0.94, 21.8), q(0.69, 21.8)], eave=2.2, ridge=3.1,
                            style=dict(front='N', ridge='shed', shed_high='S', rise=0.9, stories=1, bays=1, gable_bays=0, porch=[], chimneys=1,
                                       chimney_kind='pipe', chimney_h=1.0, shutters='#8b2e24', openings=dict(N={0: [['shut', 0.5]]}))),
                       dict(rect=[q(0.03, 9.0), q(0.69, 9.0), q(0.69, 13.5), q(0.03, 13.5)], eave=2.4, ridge=3.8,
                            style=dict(front='N', ridge='shed', shed_high='S', rise=1.4, stories=1, bays=4, gable_bays=0, porch=[], chimneys=0,
                                       shutters='#8b2e24', openings=dict(N={0: [['win', 0.12], ['win', 0.35], ['door', 0.55], ['win', 0.8]]})))]
    if 'size' in st and it.get('rect'):
        RR = it['rect']; cx = sum(p[0] for p in RR) / 4; cy = sum(p[1] for p in RR) / 4
        e0 = (RR[1][0] - RR[0][0], RR[1][1] - RR[0][1]); e1 = (RR[2][0] - RR[1][0], RR[2][1] - RR[1][1])
        u = e0 if math.hypot(*e0) >= math.hypot(*e1) else e1; ul = math.hypot(*u); u = (u[0] / ul, u[1] / ul); v = (-u[1], u[0])
        L, W = st['size']
        it['rect'] = [[round(cx + u[0] * a * L / 2 + v[0] * b * W / 2, 2), round(cy + u[1] * a * L / 2 + v[1] * b * W / 2, 2)] for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        it['ring'] = it['rect']; it['size_m'] = [L, W]
    if 'eave' in st:
        m = dict(it.get('massing') or {}); r = m.get('ridge', 0) - m.get('eave', 0)
        m['eave'] = st['eave']; m['src'] = 'estimated from the period photographs (see Appearance)'; m['ridge'] = st['eave'] + (st['rise'] if 'rise' in st else (max(r, 0.3) if st.get('ridge') == 'flat' else max(r, 2.5))); it['massing'] = m
    it['style'] = st
    if phases:
        for ph in phases:
            frm = dict(it); s2 = dict(st); s2.update({k: v for k, v in ph.items() if k != 'until'})
            frm['style'] = s2; frm['removed'] = ph['until']; frm['id'] = it['id'] + '@before-' + str(ph['until'])
            new.append(frm)
        it = dict(it); it['built'] = max(phases[-1]['until'], it['built'] or 0)
    new.append(it)
out['features'] = new

# streets of the 1883 plat (north grid, as in the 1885 photos) and the trails out of town
O = json.load(open(R('data', 'reference', 'osm_medora.geojson')))
TOWN = SPoly([T.transform(lo, la) for lo, la in [(-103.5272, 46.9128), (-103.5200, 46.9128), (-103.5200, 46.9168), (-103.5272, 46.9168)]])
GRID = {'Main Street', '3rd Avenue', '2nd Avenue', '3rd Street', '4th Street', '5th Street', 'Broadway'}
def drape(pts, step=4.0, lift=0.15):
    line = LineString(pts); res = []
    for d in list(np.arange(0, line.length, step)) + [line.length]:
        q = line.interpolate(d); res.append(loc(q.x, q.y) + [round(zat(q.x, q.y) - ORIGIN[2] + lift, 2)])
    return res
streets = []
for f in O['features']:
    pr = f['properties']
    if pr.get('kind') != 'road' or pr.get('name') not in GRID: continue
    g = shape(f['geometry'])
    pts = [T.transform(*c) for c in (g.coords if g.geom_type == 'LineString' else [c for l in g.geoms for c in l.coords])]
    clip = LineString(pts).intersection(TOWN)
    for part in (clip.geoms if hasattr(clip, 'geoms') else [clip]):
        if part.length > 20:
            streets.append({'name': pr['name'], 'kind': 'street' if pr['name'] in ('Main Street', '3rd Avenue') else 'lane', 'width': 10 if pr['name'] in ('Main Street', '3rd Avenue') else 6, 'built': 1883.9, 'pts': drape(list(part.coords))})
TRAILS = [
 ('Road from Medora to the ford and Little Missouri', [(-103.5262, 46.9150), (-103.52767, 46.915625), (-103.528692, 46.915728), (-103.528973, 46.916001), (-103.5300, 46.91625), (-103.53085, 46.91629), (-103.531328, 46.916329)], 1879.0),   # ends east of the Pyramid Park Hotel: Haynes 1881 shows no road between the depot and the hotel
 ('Road to the Chateau', [(-103.5326, 46.9160), (-103.5330, 46.9150), (-103.5334, 46.9138), (-103.5340, 46.9130), (-103.5345, 46.9127)], 1883.6),
 ('Deadwood trail south along the river', [(-103.5262, 46.9132), (-103.5262, 46.9110), (-103.5265, 46.9070), (-103.5265, 46.9040)], 1884.8),
]
for name, ll, built in TRAILS:
    streets.append({'name': name, 'kind': 'trail', 'width': 5, 'built': built, 'pts': drape([T.transform(*c) for c in ll], lift=0.12)})
# plank sidewalks along Main Street in the business block (Cow Boy 1885-02-05)
for lo0, la0, lo1, la1 in [(-103.52589, 46.91385, -103.52589, 46.91510), (-103.52610, 46.91430, -103.52610, 46.91510)]:   # both sides of Main St (centre -103.52599)
    a = T.transform(lo0, la0); b = T.transform(lo1, la1)
    streets.append({'name': 'Plank sidewalk, Main Street', 'kind': 'sidewalk', 'width': 2.4, 'built': 1885.1, 'pts': drape([a, b], lift=0.35)})
out['streets'] = streets

# Railroad for the 3D view: the 1885-86 photos put the depot, loading sheds and freight buildings beside today's
# track through town, not beside the 1883 plat's line (which runs about 40-100 m south east of the river).
# So the 3D view uses today's alignment (OpenStreetMap), clipped to the model area (RAIL_SEG), on the 1880s grade
# profile RAIL_Z worked out above. See docs/modeling-approach.md.
_onbr = lambda d: TRESTLE[0] - 0.01 <= d <= TRESTLE[1] + 0.01
_chs_main = sorted(set([round(float(d), 2) for d in np.arange(0, RAIL_SEG.length, 4.0)] + [RAIL_SEG.length, *TRESTLE]))
def _rail_line(ds, off=lambda d: 0.0):
    res = []
    for d in ds:
        o = off(d); e, n = _ch_pt(d, o if o is not None else 0.0); pt = [round(e, 2), round(n, 2), round(rail_z(d), 2)]
        if _onbr(d): pt.append(1)                        # open deck: no ballast (models.js buildTrack)
        res.append(pt)
    return res
for it in out['features']:
    if it['id'] == 'np-railroad':
        it['line'] = _rail_line(_chs_main)
        it['notes'] = (it.get('notes') or '') + ' In the 3D view the track follows today\'s alignment through town, which the 1885-86 photos support (the depot and sheds stand beside it). West of town it runs on a raised grade (rail about 4.5-5 m above the 690 m datum) and crosses the river and its flood channel on a timber pile trestle about 210 m long; the grade height, the trestle and the river\'s course at the crossing are reconstructed from MHS 72459 (1886), SHSND 00119-00017 (Haynes 1881) and the town views, not measured.'
    if it['id'] == 'np-bridge':
        it['line'] = _rail_line([TRESTLE[0] + BENT * k for k in range(int(round((TRESTLE[1] - TRESTLE[0]) / BENT)) + 1)])
        it['line'] = [p[:3] for p in it['line']]
        it['trestle'] = dict(bent=BENT, ch=list(TRESTLE), rail=TRESTLE_Z)
        it['built'] = min(it.get('built') or 1880.5, 1880.5)
        it['notes'] = ((it.get('notes') or '') + ' 3D view: a timber pile trestle (open deck, bents of four piles every 4.6 m, about 210 m) at rail level +4.5 m, spanning the river where it turns north under the grade and the flood channel east of it. Length, bent spacing and pile layout are reconstructed (photo reconciliation of MHS 72459 and SHSND 00119-00017), not documented.').strip()
_tl = LineString([(x - ORIGIN[0], y - ORIGIN[1]) for x, y in RAIL_SEG.coords])
# the ford, "a hundred yards north of the trestle" (HAG): on the reconstructed channel, 91 m downstream (north) of
# where the trestle crosses it. The 2D map's ford stays on the plat trace; this one goes with the 3D river.
_rl = [(x - ORIGIN[0], y - ORIGIN[1]) for x, y in _riv83]
_tr_mid = LineString(_rl).interpolate(LineString(_rl).project(Point(_ch_pt((TRESTLE[0] + TRESTLE[1]) / 2))))
_ford = None
_rl_n = list(reversed(_rl))             # now south (upstream) to north (downstream)
_Lr = LineString(_rl_n); _ford = _Lr.interpolate(_Lr.project(_tr_mid) + 91.4)
for it in out['features']:
    if it['id'] == 'ford':
        it['point'] = [round(_ford.x, 2), round(_ford.y, 2)]
        it['ground'] = round(zat(_ford.x + ORIGIN[0], _ford.y + ORIGIN[1]) - ORIGIN[2], 2) if 'ground' in it else it.get('ground')
        it['notes'] = ((it.get('notes') or '') + ' 3D view: placed 100 yd downstream of the trestle on the reconstructed 1880-86 channel.').strip()
# the reconstructed channel for the 2D map, in lon/lat, with the ford
_inv = Transformer.from_crs(26913, 4326, always_xy=True)
json.dump({'type': 'FeatureCollection', 'features': [
    {'type': 'Feature', 'properties': {'name': 'Little Missouri River at the crossing, 1880-86 (reconstructed from MHS 72459, Haynes 1881 and the town views; low confidence)'},
     'geometry': {'type': 'LineString', 'coordinates': [list(_inv.transform(x, y)) for x, y in _riv83]}},
    {'type': 'Feature', 'properties': {'name': 'Ford, 100 yards north of the trestle (HAG), on the reconstructed channel'},
     'geometry': {'type': 'Point', 'coordinates': list(_inv.transform(_ford.x + ORIGIN[0], _ford.y + ORIGIN[1]))}}]},
    open(R('map', 'data', 'river_1880s_photos.geojson'), 'w'))
out['sidings'] = []
for sd in SIDINGS:
    ds = list(np.arange(sd['ch'][0], sd['ch'][1], 4.0)) + [sd['ch'][1]]
    out['sidings'].append({'name': sd['name'], 'built': sd['built'], 'removed': sd['removed'], 'pts': [p[:3] for p in _rail_line(ds, sd['f'])]})

# ---------------------------------------------------------------- vegetation and poles (deterministic)
rng = np.random.default_rng(1883)
from shapely.strtree import STRtree
_bpolys = [SPoly(it['ring']).buffer(6) for it in out['features'] if it.get('ring') and it['kind'] not in ('landmark',)]
_spolys = [LineString([(p[0], p[1]) for p in st_['pts']]).buffer(st_['width'] / 2 + 2) for st_ in out['streets']]
_rail = [it for it in out['features'] if it['id'] == 'np-railroad'][0]['line']
_spolys.append(LineString([(p[0], p[1]) for p in _rail]).buffer(6))
_avoid = STRtree(_bpolys + _spolys)
def _free(e, n): return len(_avoid.query(Point(e, n), predicate='intersects')) == 0
_r83 = LineString([(x - ORIGIN[0], y - ORIGIN[1]) for x, y, _ in WATER83])
trees = []
# cottonwoods and box elder along the 1883 channel (the photos show a belt of trees on the banks and bars)
for _ in range(2600):
    d = rng.uniform(0, _r83.length); q = _r83.interpolate(d)
    i = min(int(d / 6.0), len(WATER83) - 1); wl = WATER83[i][2]
    side = rng.choice([-1, 1]); off = rng.uniform(17, 85)
    a = _r83.interpolate(max(0, d - 3)); b = _r83.interpolate(min(_r83.length, d + 3)); tx, ty = b.x - a.x, b.y - a.y; L = math.hypot(tx, ty) or 1
    e, n = q.x - ty / L * off * side, q.y + tx / L * off * side
    g = zat(e + ORIGIN[0], n + ORIGIN[1])
    if g - wl > 4.5 or not _free(e, n): continue
    if rng.random() > 0.55 * math.exp(-(off - 17) / 35): continue   # sparser than a modern grove (photo audit: the 1885 river grove is thin)
    trees.append([round(e, 1), round(n, 1), round(g - ORIGIN[2], 2), round(float(rng.uniform(9, 19)), 1), int(rng.integers(0, 1000))])
# a few trees in and around town (two large ones stand in the middle of town in SHSND 00042-00071 and -00195)
for lo, la in [(-103.52520, 46.91420), (-103.52450, 46.91432), (-103.52395, 46.91370), (-103.52300, 46.91470), (-103.52205, 46.91445)]:
    x, y = T.transform(lo, la)
    if min(math.dist((x - ORIGIN[0], y - ORIGIN[1]), c) for c in ((190.5, 30.0), (261.8, -32.2))) < 45: continue   # none beside St. Mary's or the Von Hoffman House in 1885
    trees.append([round(x - ORIGIN[0], 1), round(y - ORIGIN[1], 1), round(zat(x, y) - ORIGIN[2], 2), 13.0, int(rng.integers(0, 1000))])
# no tree in the near foreground of a fitted photo view: none shows in those photographs, and one would block the comparison
_pv = [(v['e'], v['n'], math.radians(v['yaw'])) for v in json.load(open(R('data', 'photo_views.json')))]
def _blocks(t):
    for e, n, y in _pv:
        de, dn = t[0] - e, t[1] - n; along = de * math.sin(y) + dn * math.cos(y)
        if 0 < along < 120 and abs(de * math.cos(y) - dn * math.sin(y)) < 0.35 * along + 8: return True
    return False
trees = [t for t in trees if not _blocks(t)]
out['trees'] = trees
# sagebrush and grass tussocks on the valley floor within ~1 km of town
sage = []
cx0, cy0 = T.transform(-103.5260, 46.9145)
while len(sage) < 9000:
    e = rng.uniform(-1100, 900); n = rng.uniform(-900, 900)
    x, y = cx0 + e, cy0 + n; ee, nn = x - ORIGIN[0], y - ORIGIN[1]
    c = int((x - meta['x0']) / meta['res']); r = int((meta['y1'] - y) / meta['res'])
    if not (0 <= r < Z.shape[0] and 0 <= c < Z.shape[1]) or _slope[r, c] > 0.25: continue
    if _d83[r, c] < 30 or _dsl[r, c] < 6 or not _free(ee, nn): continue
    sage.append([round(ee, 1), round(nn, 1), round(zat(x, y) - ORIGIN[2], 2), round(float(rng.uniform(0.5, 1.3)), 2)])
out['sage'] = sage
# telegraph line along the railroad: poles about 50 m apart on the south side, 11.5 m from the main (clear of the
# second siding at Little Missouri); across the trestle they stand on the ends of the bent caps, 2.2 m from the centre
_PV = json.load(open(R('data', 'photo_views.json')))
poles = []
for d in np.arange(10, RAIL_SEG.length, 50.0):
    if TRESTLE[0] - 8 < d < TRESTLE[1] + 8:
        d = TRESTLE[0] + BENT * round((d - TRESTLE[0]) / BENT); d = min(max(d, TRESTLE[0] + BENT), TRESTLE[1] - BENT)
        e, n = _ch_pt(d, -2.2); poles.append([round(e, 1), round(n, 1), round(TRESTLE_Z - 0.5, 2)]); continue
    for dd_ in (0, -5, 5, -10, 10, -15, 15, -20, 20):     # step along the line to keep the pole out of the river, the slough and the photo cameras
        e, n = _ch_pt(d + dd_, -11.5); c = int((e + ORIGIN[0] - meta['x0']) / _res); r = int((meta['y1'] - n - ORIGIN[1]) / _res)
        if _d83[r, c] > 22 and _dsl[r, c] > 5 and all(math.hypot(e - v['e'], n - v['n']) > 15 for v in _PV): break
    poles.append([round(e, 1), round(n, 1), round(zat(e + ORIGIN[0], n + ORIGIN[1]) - ORIGIN[2], 2)])
out['poles'] = poles

# single-building period photos with a camera fitted to the surviving or modelled buildings in them, for the photo gallery
import csv as _csv
_cat = {r['image']: r['url'] for r in _csv.DictReader(open(R('data', 'photo_catalog_1880s.csv')))}
out['photo_views'] = []
for v in json.load(open(R('data', 'photo_views.json'))):
    key = v['ref'].replace('SHSND ', 'shsnd:').replace('MHS ', 'mhs:')
    g = zat(v['e'] + ORIGIN[0], v['n'] + ORIGIN[1])
    f = (v['H'] / 2) / math.tan(math.radians(v['vfov'] / 2))
    out['photo_views'].append(dict(id=v['id'], ref=v['ref'], title=v['title'], date=v['date'], url=v['img'], thumb=v['thumb'], page=_cat.get(key, v['page']),
                                   credit=v['credit'], fit=v.get('fit', 'points'), rms=v.get('rms'), W=v['W'], H=v['H'], C=[v['e'] + ORIGIN[0], v['n'] + ORIGIN[1], g + v['h']],
                                   yaw=v['yaw'], pitch=v['pitch'], roll=v.get('roll', 0), f=round(f, 1), cx=v.get('cx', v['W'] / 2), cy=v.get('cy', v['H'] / 2), slice=v.get('slice'), t=v.get('t')))

# street-level viewpoints: (title, lon, lat, look-at lon, look-at lat)
# (title, stand-at e,n in local metres, look-at e,n, date slice to open on or None)
VIEWS = [
 ('Little Missouri depot, where Roosevelt stepped off the train (Sept. 1883)', (-596.0, 206.5), (-560.0, 222.0), 0),   # on the track side, the depot front at right and the Pyramid Park Hotel beyond
 ('Main Street outside the Hotel de Mores', (-80.3, -63.0), (-37.6, -54.0), None),
 ('Third Avenue by the Ferris store', (-15.5, 53.8), (-43.1, 80.9), None),
 ('St. Mary\'s Church and the Von Hoffman House', (120.0, -70.0), (215.0, 0.0), None),    # both in one 60-degree view
 ('Below the packing-plant chimney', (-150.0, 125.0), (-200.3, 190.9), None),              # 80 m back, the chimney and the south front
 ('The Chateau lawn, looking across to Medora', (-688.6, -200.0), (-30.0, -20.0), None),
]
out['viewpoints'] = []
for title, (x, y), (tx, ty), sl in VIEWS:
    out['viewpoints'].append({'title': title, 'at': [x, y], 'heading': round(math.degrees(math.atan2(tx - x, ty - y)) % 360, 1), 'slice': sl})
json.dump(out, open(R('map3d', 'data', 'scene.json'), 'w'))
print(len(out['features']), 'features written to map3d/data/scene.json')
