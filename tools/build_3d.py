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
for f in json.load(open(R('map', 'data', 'historic_features.geojson')))['features']:
    pr = f['properties']; g = _shape(f['geometry'])
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
    from shapely import distance as _dist, points as _pts
    d = _dist(gu, _pts(sx.ravel(), sy.ravel())).reshape(sx.shape)
    w = np.clip(1 - (d - 1.5) / 8.0, 0, 1)
    blk = Z[r0:r1, c0:c1]
    Z[r0:r1, c0:c1] = np.where(w > 0, blk * (1 - w) + pz * w, blk)
q = np.round((Z - meta['z0']) / meta['scale']).clip(0, 65535).astype('<u2')
q.tofile(R('map3d', 'data', 'terrain_pads.bin'))

out = {'origin': {'utm13n': ORIGIN[:2], 'z0': ORIGIN[2]}, 'features': []}
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
    out['features'].append(item)

riv = json.load(open(R('map', 'data', 'river_1883.geojson')))['features'][0]
_, pts = utm_geom(shape(riv['geometry']))
line = LineString(pts); dense = [line.interpolate(d) for d in np.arange(0, line.length, 6.0)]
out['river_1883'] = [loc(x, y) + [round(v - ORIGIN[2], 2)] for x, y, v in WATER83]
out['terrain'] = {'x0': meta['x0'] - ORIGIN[0], 'y1': meta['y1'] - ORIGIN[1], 'res': meta['res'], 'cols': meta['cols'], 'rows': meta['rows'],
                  'z0': meta['z0'] - ORIGIN[2], 'scale': meta['scale'], 'file': 'terrain_pads.bin'}

# ---------------------------------------------------------------- appearance (for the detailed 3D models)
# wall: clapboard | drop | brick | yellowbrick | boardbatten | log ;  roof: shingle | tin | sod
# front: compass side of the main door; ridge: 'long' (along the long axis) or 'front' (front-gabled)
# basis: what the look is based on. Anything not stated in a photo or source is a best guess.
STYLE = {
 'hotel-de-mores': dict(wall='brick', wall_color='#b46a4e', trim='#efe9dc', roof='shingle', front='W', ridge='long', stories=2, bays=11, gable_bays=3,
        arched=True, porch=[dict(side='W', depth=2.4), dict(side='S', depth=2.4)], chimneys=3, end_block=dict(end='E', len=7.6, extra=2.6),
        basis='SHSND 00042-00076/-00086 and Houghton 3013534/3013559 (brick, arched windows, taller end block); porches west and south from the Cow Boy, Feb-May 1885. No sign appears on the building in any of these photographs, so none is modelled',
        phases=[dict(until=1885.3, wall='clapboard', wall_color='#ece6d8', arched=False, porch=[], bays=9, end_block=None,
                     basis='SHSND 00042-00149 (1883: two-story frame hotel, about 9 bays, two ridge chimneys)')]),
 'roberts-hall': dict(wall='drop', wall_color='#e2dccd', trim='#f3efe6', roof='shingle', front='S', ridge='front', stories=2, bays=6, upper_bays=3, gable_bays=2,
        fanlight=True, outside_stair='E', chimneys=1, false_front=False,
        basis='Hagedorn 1919 (Houghton 3013539) and the courthouse panel photo: two-story front-gabled frame hall, fanlight in the gable, upper door; Cow Boy: drop siding, 24x75, 26 ft'),
 'metropolitan-hotel': dict(wall='drop', wall_color='#7c6a58', trim='#e8e2d4', roof='tin', front='W', ridge='flat', stories=2, bays=10, gable_bays=4,
        porch=[dict(side='W', depth=2.4)], chimneys=2, parapet=1.0,
        basis='SHSND 00042-00071/-00195 (dark, flat-roofed, two rows of windows); Cow Boy: drop siding, 35x80, long front porch planned. Colour and porch side are guesses'),
 'ferris-store': dict(wall='clapboard', wall_color='#eee6cf', trim='#ffffff', roof='shingle', front='W', ridge='front', stories=2, bays=5, gable_bays=2,
        storefront=True, porch=[dict(side='W', depth=2.6)], outside_stair='S', chimneys=1,
        basis='Houghton 3013537/3013655 and the Historic Medora panel (two-story front-gabled frame store, porch, side stair); today\'s 1963 rebuild'),
 'st-marys-church': dict(wall='yellowbrick', wall_color='#cdb48a', trim='#f2ede2', roof='shingle', front='W', ridge='front', stories=1, bays=4, gable_bays=1,
        arched=True, belfry=True, chimneys=0, basis='SHSND 00042-00077/-00124 and the standing church (front gable, belfry, arched windows); front side a guess'),
 'von-hoffman-house': dict(wall='brick', wall_color='#a95c43', trim='#efe9dc', roof='shingle', front='S', ridge='hip', stories=1.5, bays=4, gable_bays=3,
        porch=[dict(side='S', depth=2.4)], chimneys=2, basis='the standing house and SHSND 00042-00176/-00038 (brick, hip-gable roof, front porch)'),
 'courthouse-cottages': dict(wall='brick', wall_color='#ad6248', trim='#efe9dc', roof='shingle', front='W', ridge='hip', stories=1, bays=3, gable_bays=2,
        porch=[dict(side='W', depth=2.0)], chimneys=1, split=dict(n=2, gap=0.3),
        basis='SHSND 00042-00195 (two matching hipped one-story cottages) and the courthouse panel; brick from the Cow Boy'),
 'chateau-de-mores': dict(wall='clapboard', wall_color='#a3a29b', trim='#8b2e24', roof='shingle', roof_color='#7c3428', front='E', ridge='long', stories=2, bays=6, gable_bays=3,
        porch=[dict(side='E', depth=3.0), dict(side='S', depth=3.0)], chimneys=3,
        basis='Colours follow the building as the State Historical Society of North Dakota maintains it today (grey siding with red roof and trim; the 1974 National Register nomination describes "French grey" siding with a red roof and shutters). The Cow Boy of Nov. 26, 1885 described "green sides and red roof"; the 1883-86 photographs show light walls and a dark roof, which fits either. Form: two-story main block, lower rear wing, one-story veranda on the river (east) and south sides, simplified'),
 'company-store-offices': dict(wall='clapboard', wall_color='#f0ebdf', trim='#ffffff', roof='shingle', front='E', ridge='front', stories=1.5, bays=3, gable_bays=2,
        storefront=True, split=dict(n=3, gap=0.0), chimneys=1, basis='Houghton 3013533 (1883: three joined front-gabled frame buildings, white; no sign visible)'),
 'medora-depot': dict(wall='boardbatten', wall_color='#cbb68c', trim='#6b4a32', roof='shingle', front='S', ridge='long', stories=1.5, bays=5, gable_bays=2,
        bay_window=True, chimneys=1,
        signs=[dict(id='medora-depot', w_frac=0.36, aspect=0.15, at=2.55, out=0.98, photo='MHS 72461')],
        basis='Huffman 1886 (MHS 72461): board-and-batten, long side on the track, agent\'s bay window; colours are a guess (NP depots of the period were commonly painted buff with brown trim). Sign: the photograph shows a dark board with white letters across the bay window reading MEDORA, with ST. PAUL at the left end and PORTLAND at the right, each over a mileage figure; the figures are not legible in the available scan, so the model leaves them blank. A smaller board above the bay is also unreadable and is left out'),
 'lm-depot': dict(wall='boardbatten', wall_color='#bfae8a', trim='#6b4a32', roof='shingle', front='S', ridge='long', stories=1, bays=3, gable_bays=1,
        chimneys=1, basis='Haynes 1881 (SHSND 00119-00017): small board-and-batten depot along the track; colours a guess'),
 'pyramid-park-hotel': dict(wall='clapboard', wall_color='#e8e2d2', trim='#ffffff', roof='shingle', front='N', ridge='front', stories=2, bays=4, gable_bays=2,
        porch=[dict(side='N', depth=2.0)], chimneys=2, basis='Haynes 1881 (SHSND 00119-00017): two-story front-gabled frame hotel with a block behind; porch a guess. No sign is visible in the photograph'),
 'cowboy-office': dict(wall='boardbatten', wall_color='#e6e0d0', trim='#ffffff', roof='shingle', front='W', ridge='front', stories=1, bays=2, gable_bays=1,
        chimneys=1, basis='Houghton 3013536 (one-story front-gabled board building, chimney at rear). That photo shows two lines of lettering laid into the roof in light-coloured shingles, but the words cannot be read at the available resolution (and the print may date from after 1887), so no lettering is modelled'),
 'paddock-livery': dict(wall='boardbatten', wall_color='#8c7a62', trim='#5b4a3a', roof='shingle', front='S', ridge='long', stories=1.5, bays=4, gable_bays=1,
        barn=True, basis='Cow Boy 1885 (livery barn, drop siding); appearance a guess'),
 'freight-house': dict(wall='boardbatten', wall_color='#9b8a70', trim='#5b4a3a', roof='shingle', front='S', ridge='long', stories=1, bays=12, gable_bays=1,
        barn=True, basis='Cow Boy (240 x 42 freight house); appearance a guess'),
 'cantonment': dict(wall='log', wall_color='#8a7357', trim='#5b4a3a', roof='sod', front='S', ridge='long', stories=1, bays=4, gable_bays=1, chimneys=2,
        basis='Haynes 1880 (MHS 91738) and HM52: cedar-log army buildings; roof covering a guess'),
 'pp-foundation': dict(wall='boardbatten', wall_color='#9e9586', trim='#8a8173', roof='tin', roof_color='#77736c', front='S', ridge='flat', stories=3, bays=0, gable_bays=0,
        size=[46, 18], parapet=0.4, monitor=True, gallery=dict(side='S', levels=3, frac=0.35), runway=dict(end='W', len=34), chimneys=0, eave=9.0,
        basis='SHSND 00042-00074/-00075 (1885), the "1883" card 00042-00153 and Huffman 1886 (MHS 72460): a tall, nearly windowless block of unpainted vertical boards with a low roof and a long roof monitor, stacked galleries on one front, the chimney behind. Size widened from the 1957 foundation line to the proportions in the photos (a guess); height about 9 m from the photos. Sign: SHSND 00042-00180 and -00181 show a long banner on a blank wall of the closed plant, "This building with machinery will be furnished rent free to any responsible party who will start any industry therein." The photo is undated (after the plant shut in late 1886), so the model shows it only in the spring 1887 view; which wall it was on is a guess',
        signs=[dict(id='pp-rentfree', side='N', w=28, aspect=0.057, at=2.2, along=0.5, **{'from': 1887.0}, photo='SHSND 00042-00180')]),
 'pp-ice-house': dict(wall='boardbatten', wall_color='#a39a8a', trim='#8a8173', roof='shingle', roof_color='#5f5a54', front='S', ridge='long', stories=2, bays=0, gable_bays=0,
        cupola=True, tower=dict(w=5.5, h=4.0), chimneys=0, eave=7.0, barn=True,
        basis='SHSND 00042-00188 (ice house under construction, 1883) and 00042-00074/-00075: a long gabled block with a square tower and pyramid-roofed cupola; unpainted boards'),
 'pp-east-building': dict(wall='boardbatten', wall_color='#5e564c', trim='#4a443c', roof='shingle', roof_color='#4f4a44', front='S', ridge='long', stories=1, bays=0, gable_bays=0,
        size=[40, 14], vents=3, barn=True, chimneys=0, eave=4.2,
        basis='SHSND 00042-00075 and Huffman 72460: long, low, dark gabled sheds with roof ventilators east of the chimney; identity and size are guesses'),
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
    if it['id'] == 'chateau-de-mores':
        poly = SPoly(it['ring']).buffer(0)
        a, b = (-739.93, -228.55), (-715.55, -237.74)
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); px, py = -dy / L, dx / L
        q = lambda t, d: [round(a[0] + dx * t + px * d, 2), round(a[1] + dy * t + py * d, 2)]
        # main two-story block along the south front, and a rear block filling the rest of the footprint
        st['blocks'] = [[q(0, 0), q(1, 0), q(1, 9), q(0, 9)], [q(0.08, 9), q(0.92, 9), q(0.92, 15.5), q(0.08, 15.5)]]
    if 'size' in st and it.get('rect'):
        RR = it['rect']; cx = sum(p[0] for p in RR) / 4; cy = sum(p[1] for p in RR) / 4
        e0 = (RR[1][0] - RR[0][0], RR[1][1] - RR[0][1]); e1 = (RR[2][0] - RR[1][0], RR[2][1] - RR[1][1])
        u = e0 if math.hypot(*e0) >= math.hypot(*e1) else e1; ul = math.hypot(*u); u = (u[0] / ul, u[1] / ul); v = (-u[1], u[0])
        L, W = st['size']
        it['rect'] = [[round(cx + u[0] * a * L / 2 + v[0] * b * W / 2, 2), round(cy + u[1] * a * L / 2 + v[1] * b * W / 2, 2)] for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        it['ring'] = it['rect']; it['size_m'] = [L, W]
    if 'eave' in st:
        m = dict(it.get('massing') or {}); r = m.get('ridge', 0) - m.get('eave', 0)
        m['eave'] = st['eave']; m['src'] = 'estimated from the period photographs (see Appearance)'; m['ridge'] = st['eave'] + (max(r, 0.3) if st.get('ridge') == 'flat' else max(r, 2.5)); it['massing'] = m
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
            streets.append({'name': pr['name'], 'kind': 'street', 'width': 12 if pr['name'] in ('Main Street', '3rd Avenue') else 10, 'built': 1883.9, 'pts': drape(list(part.coords))})
TRAILS = [
 ('Road from Medora to the ford and Little Missouri', [(-103.5262, 46.9150), (-103.5285, 46.9160), (-103.5300, 46.91625), (-103.53085, 46.91629), (-103.5320, 46.9164), (-103.5328, 46.9163)], 1879.0),
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
# So the 3D view uses today's alignment (OpenStreetMap), clipped to the model area. See docs/modeling-approach.md.
from shapely.ops import linemerge, unary_union
rails = [shape(f['geometry']) for f in O['features'] if f['properties'].get('kind') == 'rail']
rl = linemerge(unary_union(rails))
rl = max(rl.geoms, key=lambda g: g.length) if hasattr(rl, 'geoms') else rl
pts = [T.transform(*c) for c in rl.coords]
box_ = SPoly([(meta['x0'] + 30, meta['y1'] - 30), (meta['x0'] + meta['cols'] * meta['res'] - 30, meta['y1'] - 30),
              (meta['x0'] + meta['cols'] * meta['res'] - 30, meta['y1'] - meta['rows'] * meta['res'] + 30), (meta['x0'] + 30, meta['y1'] - meta['rows'] * meta['res'] + 30)])
seg = LineString(pts).intersection(box_)
seg = max(seg.geoms, key=lambda g: g.length) if hasattr(seg, 'geoms') else seg
for it in out['features']:
    if it['id'] == 'np-railroad':
        it['line'] = drape(list(seg.coords), step=6.0, lift=0.4)
        it['notes'] = (it.get('notes') or '') + ' In the 3D view the track follows today\'s alignment through town, which the 1885-86 photos support (the depot and sheds stand beside it).'

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
    if rng.random() > math.exp(-(off - 17) / 35): continue
    trees.append([round(e, 1), round(n, 1), round(g - ORIGIN[2], 2), round(float(rng.uniform(9, 19)), 1), int(rng.integers(0, 1000))])
# a few trees in and around town (two large ones stand in the middle of town in SHSND 00042-00071 and -00195)
for lo, la in [(-103.52520, 46.91420), (-103.52450, 46.91432), (-103.52395, 46.91370), (-103.52300, 46.91470), (-103.52205, 46.91445)]:
    x, y = T.transform(lo, la); trees.append([round(x - ORIGIN[0], 1), round(y - ORIGIN[1], 1), round(zat(x, y) - ORIGIN[2], 2), 13.0, int(rng.integers(0, 1000))])
out['trees'] = trees
# sagebrush and grass tussocks on the valley floor within ~1 km of town
sage = []
cx0, cy0 = T.transform(-103.5260, 46.9145)
while len(sage) < 9000:
    e = rng.uniform(-1100, 900); n = rng.uniform(-900, 900)
    x, y = cx0 + e, cy0 + n; ee, nn = x - ORIGIN[0], y - ORIGIN[1]
    c = int((x - meta['x0']) / meta['res']); r = int((meta['y1'] - y) / meta['res'])
    if not (0 <= r < Z.shape[0] and 0 <= c < Z.shape[1]) or _slope[r, c] > 0.25: continue
    if _d83[r, c] < 30 or not _free(ee, nn): continue
    sage.append([round(ee, 1), round(nn, 1), round(zat(x, y) - ORIGIN[2], 2), round(float(rng.uniform(0.5, 1.3)), 2)])
out['sage'] = sage
# telegraph line along the railroad, poles every ~45 m on the north side
poles = []; rl_ = LineString([(p[0], p[1]) for p in _rail])
for d in np.arange(10, rl_.length, 45):
    q = rl_.interpolate(d); a = rl_.interpolate(max(0, d - 2)); b = rl_.interpolate(min(rl_.length, d + 2))
    tx, ty = b.x - a.x, b.y - a.y; L = math.hypot(tx, ty) or 1; nx, ny = -ty / L, tx / L
    if ny < 0: nx, ny = -nx, -ny
    e, n = q.x + nx * 11, q.y + ny * 11
    poles.append([round(e, 1), round(n, 1), round(zat(e + ORIGIN[0], n + ORIGIN[1]) - ORIGIN[2], 2)])
out['poles'] = poles

# street-level viewpoints: (title, lon, lat, look-at lon, look-at lat)
VIEWS = [
 ('Little Missouri depot, where Roosevelt stepped off the train (Sept. 1883)', -103.53262, 46.91652, -103.532968, 46.91594),
 ('Main Street outside the Hotel de Mores', -103.52628, 46.91378, -103.525635, 46.913867),
 ('Third Avenue by the Ferris store', -103.52540, 46.91482, -103.525759, 46.915065),
 ('St. Mary\'s Church and the Von Hoffman House', -103.52300, 46.91420, -103.52178, 46.914),
 ('Below the packing-plant chimney', -103.52725, 46.91580, -103.527793, 46.916084),
 ('The Chateau lawn, looking across to Medora', -103.53430, 46.91265, -103.5255, 46.9142),
]
out['viewpoints'] = []
for title, lo, la, tlo, tla in VIEWS:
    x, y = T.transform(lo, la); tx, ty = T.transform(tlo, tla)
    out['viewpoints'].append({'title': title, 'at': loc(x, y), 'heading': round(math.degrees(math.atan2(tx - x, ty - y)) % 360, 1)})
json.dump(out, open(R('map3d', 'data', 'scene.json'), 'w'))
print(len(out['features']), 'features written to map3d/data/scene.json')
