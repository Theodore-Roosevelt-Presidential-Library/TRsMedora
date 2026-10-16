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
GEOM3D, EXTRA3D, STYLE_ADD, PROPS3D = _overrides(_osm, T, ORIGIN, _orig_rect)
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
    from shapely import distance as _dist, points as _pts
    d = _dist(gu, _pts(sx.ravel(), sy.ravel())).reshape(sx.shape)
    w = np.clip(1 - (d - 1.5) / 8.0, 0, 1)
    blk = Z[r0:r1, c0:c1]
    Z[r0:r1, c0:c1] = np.where(w > 0, blk * (1 - w) + pz * w, blk)
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
out['terrain'] = {'x0': meta['x0'] - ORIGIN[0], 'y1': meta['y1'] - ORIGIN[1], 'res': meta['res'], 'cols': meta['cols'], 'rows': meta['rows'],
                  'z0': meta['z0'] - ORIGIN[2], 'scale': meta['scale'], 'file': 'terrain_pads.bin'}

# ---------------------------------------------------------------- appearance (for the detailed 3D models)
# wall: clapboard | drop | brick | yellowbrick | boardbatten | log ;  roof: shingle | tin | sod
# front: compass side of the main door; ridge: 'long' (along the long axis) or 'front' (front-gabled)
# basis: what the look is based on. Anything not stated in a photo or source is a best guess.
STYLE = {
 # ---- Medora, Main Street
 'hotel-de-mores': dict(wall='yellowbrick', wall_color='#ddd3bd', trim='#f3efe6', roof='shingle', front='W', ridge='long', stories=2, bays=11, upper_bays=11, gable_bays=2,
        arched=True, chimneys=2, outside_stair=dict(side='E', top='S'), eave=6.8,
        porch=[dict(side='W', depth=2.4, roof=False, h=0.45), dict(side='S', depth=2.4, roof=False, h=0.45)],
        part_styles=[dict(wall='clapboard', wall_color='#ece6d8', front='E', ridge='long', stories=1, bays=2, gable_bays=1, chimneys=1, arched=False, porch=[])],
        basis='Form from the 1885-86 overviews (SHSND 00042-00071, -00195, -00194): a light-toned two-storey building of one eave height with a plain gable at the east end, an outside stair up the east gable to an upper door, and a lower wing on the north side near the east end (the Cow Boy\'s 1885 kitchen and laundry). Height scaled from those photos (eave about 6.5-7 m). Walls: the Cow Boy says the hotel was brick-veneered in spring 1885, and the building reads light in every 1885-86 print, so a pale (cream) brick is used, like St. Mary\'s of the same year. Windows: narrow 2/2 sash under segmental brick arches, as in the 1890s photos of the brick hotel (SHSND 00042-00076/-00086, Houghton 3013534/3013559); those photos date from the 1890s (dress, wires), so the taller cross-gabled block they show is not modelled for 1885-87. Front platforms unroofed (the photos show a raised plank walk, no porch roof). No sign appears in any photo',
        phases=[dict(until=1885.3, wall='clapboard', wall_color='#ece6d8', arched=False, porch=[dict(side='W', depth=1.6, roof=False, h=0.25)], bays=10, upper_bays=8, gable_bays=2,
                     outside_stair=None, parts=[], chimneys=2, front_openings=[['win', 0.25], ['double', 0.5], ['win', 0.75]],
                     basis='SHSND 00042-00149 (1883): two-storey clapboard hotel, light paint, gable roof of about 40 degrees with cornice returns, 6/6 windows with flat heads (10 openings below, 8 windows above on the long side), window-double door-window on the gable end with two windows above, two ridge chimneys, a low plank walk; eave scaled at about 6-7 m')]),
 'roberts-hall': dict(wall='drop', wall_color='#e2dccd', trim='#f3efe6', roof='shingle', front='S', ridge='front', stories=2, bays=10, upper_bays=10, paired=True, gable_bays=2,
        fanlight=True, upper_door=True, chimneys=1, false_front=False,
        basis='Houghton 3013539 (Hagedorn 1919, context): two-storey front-gabled frame hall, drop siding, sunburst/fan in the gable, central upper door with a small hood between two windows, narrow side windows in pairs; SHSND 00042-00195 (1885) shows paired upper windows on the east side and an arched opening in the south gable. Cow Boy: 24x75, 26 ft. The outside stair once modelled on the east side is not confirmed in any photo and has been removed'),
 'metropolitan-hotel': dict(wall='drop', wall_color='#7c6a58', trim='#e8e2d4', roof='tin', front='W', ridge='flat', stories=2, bays=10, upper_bays=10, paired=True, gable_bays=4,
        porch=[dict(side='W', depth=2.4)], chimneys=2, parapet=1.0,
        basis='SHSND 00042-00071/-00195: dark, flat or very low roof, two storeys, windows in pairs on both floors (about five pairs on the visible long side), a chimney near the front. Cow Boy: drop siding, 35x80, long front porch planned. Colour and porch side are guesses'),
 'ferris-store': dict(wall='clapboard', wall_color='#eee6cf', trim='#ffffff', roof='shingle', front='W', ridge='front', stories=2, bays=5, gable_bays=2,
        storefront=True, false_front=True, false_front_extra=0.8, porch=[dict(side='W', depth=2.0, h=0.5, post_spacing=2.6)], outside_stair='S', chimneys=1,
        basis='Houghton 3013537/3013655 (both after 1887): two-storey store with a square false front and cornice, two upper windows, display windows either side of a recessed double door, a bracketed shed-roof porch on a raised plank platform; the Historic Medora panel (side stair); today\'s 1963 rebuild'),
 'company-store-offices': dict(wall='clapboard', wall_color='#f0ebdf', trim='#ffffff', roof='shingle', front='E', ridge='front', stories=1, bays=2, gable_bays=1,
        part_styles=[dict(front_openings=[['win', 0.2], ['door', 0.5], ['win', 0.8]], chimney_at=dict(**{'from': 'E'}, at=[1.0])),
                     dict(front_openings=[['win', 0.2], ['double', 0.5], ['win', 0.8]], chimney_at=dict(**{'from': 'W'}, at=[1.5])),
                     dict(front_openings=[['door', 0.32], ['win', 0.72]], chimneys=0)],
        basis='Houghton 3013533 (1883): three joined one-storey front-gabled white frame buildings of unequal width (about 7.3, 6.0 and 4.3 m, south to north), floor raised about 0.5 m, eave about 3.2 m, two chimneys; no sign. The photo suggests a frontage of about 18-19 m against the 27 m footprint, which fits the 1885 overview; the footprint is kept and the three blocks are scaled to it'),
 'cowboy-office': dict(wall='boardbatten', wall_color='#e6e0d0', trim='#ffffff', roof='shingle', front='W', ridge='front', stories=1, bays=2, gable_bays=0, rear_bays=0, eave=2.7, rise=1.7,
        no_front_door=True, chimney_at=dict(**{'from': 'E'}, at=[0.8]),
        part_styles=[dict(wall='boardbatten', wall_color='#9a8c78', ridge='shed', shed_high='E', front='W', bays=0, gable_bays=0, rear_bays=0, front_openings=[['door', 0.5]], chimneys=0, no_front_door=False)],
        basis='Houghton 3013536 (date uncertain): one-storey board-and-batten building, gable roof of about 40 degrees, an unpainted board entry vestibule with a shed roof on the gable end right of centre, two small high windows on the long side, capped brick chimney at the rear of the ridge; eave about 2.7 m. Two lines of lettering are laid into the roof in light shingles but cannot be read, so none is modelled'),
 'paddock-livery': dict(wall='boardbatten', wall_color='#8c7a62', trim='#5b4a3a', roof='shingle', front='E', ridge='front', stories=1.5, bays=4, gable_bays=1,
        barn=True, basis='SHSND 00042-00071 (1885): a gable-fronted barn facing east with a big central wagon door and lean-tos; Cow Boy 1885 (livery barn, drop siding)'),
 'freight-house': dict(wall='boardbatten', wall_color='#9b8a70', trim='#5b4a3a', roof='shingle', front='S', ridge='long', stories=1, bays=12, gable_bays=1,
        barn=True, basis='Cow Boy (240 x 42 freight house); appearance a guess. The 1885-86 overviews show open ground at this spot, so its position is unconfirmed'),
 # ---- Medora, churches and houses
 'st-marys-church': dict(wall='yellowbrick', wall_color='#e8e1d1', trim='#f2ede2', roof='shingle', front='W', ridge='front', stories=1, bays=5, gable_bays=1, rear_bays=0,
        arched='lancet', win_w=0.7, win_h=2.8, win_skip=dict(**{'from': 'W'}, frac=0.22), front_openings=[['double', 0.5]],
        belfry=dict(w=2.0, base=0.4, stage=1.6, roof=1.5, back=0.3), chimneys=0,
        basis='SHSND 00042-00077 (c.1886) and the standing church: pale brick that reads near-white in the prints; west front with a central double door under a pointed hood and no other openings; four tall pointed (lancet) windows on the rear three-quarters of the side walls, the front quarter blank; blank east gable; small square open belfry on the ridge just behind the west gable (shingled base, open stage with arched openings, pyramid roof), about 2 m wide'),
 'von-hoffman-house': dict(wall='brick', wall_color='#a95c43', trim='#efe9dc', roof='shingle', front='S', ridge='long', stories=1.5, bays=5, gable_bays=2, arched=True,
        jerkin=['S', 'N'], jerkin_clip=0.3, front_openings=[['win', 0.25], ['door', 0.5], ['win', 0.75]],
        porch=[dict(side='S', depth=2.4, h=0.35, post_spacing=2.6, rail=True)], chimneys=2,
        basis='SHSND 00042-00176, -00182, -00071, -00195 and the standing house: brick, long north-south ridge with a clipped (jerkinhead) south gable over a full-width porch on square chamfered posts, a close pair of attic windows in the gable, two ridge chimneys, four windows and a door on the east side, a post-and-rail fenced yard to the west and north. The 1977 National Register nomination: common-bond brick, "hip-gabled" wood-shingle roof, 2/2 windows under segmental brick arches, the original one-storey front porch, about 38 x 48 ft. The north end is shown clipped too (probable). The wall colour is not recorded; the 1885 prints read paler than this red, so check it against the standing house'),
 'courthouse-cottages': dict(wall='brick', wall_color='#e9e4d8', trim='#efe9dc', roof='shingle', front='E', ridge='hip', stories=1, bays=2, gable_bays=1, eave=2.8, rise=2.0,
        chimneys=1, split=dict(n=2, gap=0.256),
        basis='SHSND 00042-00195 and -00194: two separate identical one-storey cottages with near-pyramidal dark hipped roofs and a gap of about 5-6 m, walls bright white (brick per the Cow Boy, so whitewashed or painted), each about 8 m square with a door and two windows on the east'),
 # ---- the Chateau (colours as the State Historical Society keeps it today)
 'chateau-de-mores': dict(wall='clapboard', wall_color='#a3a29b', trim='#8b2e24', roof='shingle', roof_color='#7c3428', front='E', ridge='long', stories=2, bays=6, gable_bays=3,
        eave=6.3, rise=3.1,
        shutters='#8b2e24', chimney_at=dict(**{'from': 'W'}, at=[2.0, 17.4]),
        porch=[dict(side='E', depth=3.0, h=0.5, post_spacing=2.4, rail=True), dict(side='S', depth=3.0, h=0.5, post_spacing=2.4, rail=True, span=[0.5, 1.0], span_from='W', extend=3.0)],
        basis='Height: the 2021 lidar ridge (9.4 m) with a two-storey eave of about 6.3 m (the lidar eave of 3.8 m is the veranda roof). Colours follow the building as the State Historical Society of North Dakota maintains it today (grey siding with red roof and trim; the 1974 National Register nomination describes "French grey" siding with a red roof and shutters). The Cow Boy of Nov. 26, 1885 described "green sides and red roof"; the 1883-86 photographs show light walls and a dark roof, which fits either. Form from SHSND 00042-00152/-00157/-00196/-00197 and MHS 72389/72403: two-storey side-gabled main block, no dormers, board shutters; a one-storey rear wing with its ridge running north-south; a one-storey veranda with open rafters along the whole east end, wrapping the south-east corner and covering about the eastern half of the south front; chimneys near the west end and about a third from the east end, and one on the wing'),
 # ---- railroad
 'medora-depot': dict(wall='boardbatten', front='S', ridge='front', stories=1,
        part_styles=[dict(wall='boardbatten', wall_color='#6f5d4a', trim='#c9bfa8', timber='#5d4c3a', roof='shingle', front='S', ridge='front', stories=1,
                          overhang=1.7, gable_overhang=1.2, brackets=dict(spacing=2.7, drop=1.0, strut=True), bays=3, gable_bays=0, rear_bays=0,
                          front_openings=[['door', 0.223]], bay_window=dict(w=2.4, d=0.7, eave=3.0, offset=0.8, offset_dir='E'),
                          chimney_at=dict(**{'from': 'S'}, at=[2.5, 8.0]), chimney_h=0.8, roof_extend=dict(end='N', len=8.0, deck=True, deck_h=0.45),
                          signs=[dict(id='medora-depot', w=3.4, aspect=0.15, at=2.62, out=0.76, on_bay=True, photo='MHS 72461')])],
        basis='Huffman 1886 (MHS 72461), measured with the door (2.1 m) as scale: a one-storey board-and-batten depot whose gable end faces the track, about 4-5 m from it, standing at the back of a plank platform at rail height. The roof is about 30 degrees with very deep eaves (about 1.7 m at the sides, 1.2 m at the gable) on diagonal knee braces, and runs on past the north end wall over open X-braced posts. The gable end has a door with a transom west of a canted three-sided bay window with its own low hip roof; two corbelled brick chimneys; railings on the platform either side. 5.6 m across the track face, about 13.5 m of enclosed walls. The walls read mid-dark in the print; the actual colour is unknown. Sign: a dark board with white letters across the bay head reading MEDORA, with ST. PAUL and PORTLAND mileboards at its ends; the mileage figures are not reliably legible in the scan, so the model leaves them blank'),
 'lm-depot': dict(wall='boardbatten', front='S', ridge='long', stories=1,
        part_styles=[dict(wall='boardbatten', wall_color='#e6dfcf', trim='#ffffff', roof='boards', front='S', ridge='long', stories=1, bays=2, gable_bays=1,
                          front_openings=[['win', 0.2], ['door', 0.5], ['win', 0.8]], chimney_at=dict(**{'from': 'W'}, at=[1.0]), chimney_h=0.6),
                     dict(wall='drop', wall_color='#e9e4d8', trim='#ffffff', roof='shingle', front='S', ridge='long', stories=1, bays=0, gable_bays=0,
                          front_openings=[['door', 0.45]], chimney_at=dict(**{'from': 'W'}, at=[4.0]), chimney_h=0.6)],
        basis='Haynes 1881 (SHSND 00119-00017 = MHS 108837): two attached one-storey gabled blocks along the track, ridges parallel to it. West block: very light board-and-batten, a roof of boards laid eave to ridge, window-door-window on the track side, a stovepipe; east block: deeper and higher, smooth light walls, shingle roof, a single door with a small plaque. A plank platform along the track. Colours from the light tones of the print'),
 'pyramid-park-hotel': dict(wall='drop', front='S', ridge='long', stories=1.5,
        part_styles=[dict(wall='drop', wall_color='#7d6f60', trim='#d8d0c0', roof='shingle', front='S', ridge='long', stories=1.5, bays=4, gable_bays=1,
                          front_openings=[['door', 0.07], ['win', 0.22], ['win', 0.36], ['win', 0.5], ['win', 0.64]], chimneys=3, chimney_h=0.7),
                     dict(wall='drop', wall_color='#7d6f60', trim='#d8d0c0', roof='shingle', front='S', ridge='front', stories=1.5, bays=1, gable_bays=2,
                          front_openings=[['door', 0.5]], chimneys=0),
                     dict(wall='clapboard', wall_color='#ece6d6', trim='#ffffff', roof='shingle', front='S', ridge='front', stories=1.5, bays=1, gable_bays=1,
                          front_openings=[['win', 0.5]], chimneys=0),
                     dict(wall='drop', wall_color='#8a7c6c', trim='#d8d0c0', roof='shingle', front='S', ridge='long', stories=1, bays=1, gable_bays=1, chimneys=1)],
        basis='Haynes 1881 (SHSND 00119-00017): a main block with its ridge along the track and its front to the south, one tall storey with a loft under a steep roof (Hagedorn\'s "loft with 14 beds"), a front-facing cross gable with two upper windows at the east end, a separate light front-gabled block at the west end and a low block behind it. Dark weathered horizontal siding on the main block, new light boards on the west block, three or four stovepipes; no porch roof, only a plank walk. No sign is visible'),
 'cantonment': dict(wall='vlog', wall_color='#8d877c', trim='#5b4a3a', roof='shingle', roof_color='#8f877a', front='S', ridge='long', stories=1, bays=6, gable_bays=0, chimneys=0, eave=2.7,
        basis='Haynes 1880 (MHS 91738): long one-storey barracks of vertical cedar logs, stockade style, weathered grey, with a shingle or board gable roof (not sod), evenly spaced doors and windows along the long side, eave about 2.7 m. The barracks were 200 x 22 ft (HM52); the buildings here are the plat\'s schematic symbols, so their sizes are placeholders'),
 # ---- packing plant
 'pp-foundation': dict(wall='drop', front='S', ridge='flat', stories=3,
        part_styles=[dict(wall='drop', wall_color='#9e9586', trim='#8a8173', timber='#6e6558', roof='tin', roof_color='#77736c', front='S', ridge='flat', parapet=0.4, stories=3,
                          bays=0, gable_bays=0, blank=True, no_front_door=True, plinth=dict(h=0.9, color='#a39882'), monitor=dict(len_frac=0.2, at=-0.1, w=3.0),
                          gallery=dict(side='S', levels=3, frac=0.38, end='E', depth=2.4), runway=dict(end='W', len=24, h=11.5), chimneys=0,
                          signs=[dict(id='pp-rentfree', side='S', w=22, aspect=0.057, at=2.2, along=0.45, **{'from': 1887.0}, photo='SHSND 00042-00180')]),
                     dict(wall='drop', wall_color='#a39a8c', trim='#8a8173', roof='tin', roof_color='#77736c', front='S', ridge='flat', parapet=0.3, stories=3,
                          bays=6, gable_bays=2, no_front_door=True, monitor=dict(len_frac=0.5, w=2.0), chimneys=0)],
        basis='SHSND 00042-00074 (= 00042-00153 and 0039_00001, the same 1885 exposure; the "1883" on the card is wrong), 00042-00075 (from the north), Huffman 1886 (MHS 72460) and 00042-00180: two parts, a tall nearly windowless block (eave about 10.5 m) of horizontal siding on a stone foundation course, with a short box ventilator on its low roof and three levels of galleries at the east end of its south face (a roofed porch below, open framing above); and a lower annex at the west end with three rows of small windows and a louvred monitor. An enclosed horizontal runway runs from the tall block over the annex to a tapered timber pier about 6 m beyond it; a raised loading platform runs along the north side. Lengths from the 1957 foundation line (46 m), split by the photos\' proportions. Sign: the undated "rent free" banner (00042-00180) is on the south wall; shown only in the spring 1887 view'),
 'pp-ice-house': dict(wall='boardbatten', wall_color='#5e564c', trim='#4a443c', roof='shingle', roof_color='#4f4a44', front='S', ridge='long', stories=2, bays=0, gable_bays=0,
        vents=2, chimneys=0, eave=5.8, rise=3.2, barn=True,
        basis='MHS 72460 (left) and SHSND 00042-00075 (right): a long dark gabled shed of vertical boards, ridge east-west, two square ridge ventilators, eave about 5.8 m; 00042-00188 shows it being built in 1883. The tower and cupola once modelled here belong to the cooling house'),
 'pp-cooling-house': dict(wall='clapboard', wall_color='#d9d3c4', trim='#bdb5a5', roof='shingle', roof_color='#5f5a54', front='N', ridge='hip', stories=3, bays=2, gable_bays=2,
        cupola=dict(w=2.0, h=1.6, cap=1.2), chimneys=0, rise=3.0,
        basis='SHSND 00042-00150 and -00188 (1883), seen behind the plant in 00042-00074/-00075 and MHS 72460: a near-cubic block of painted clapboard, eave about 9 m (scaled from the refrigerator car beside it), a hipped roof with a square louvred cupola, a loading platform on trestle legs at car-floor height'),
 'pp-east-building': dict(wall='boardbatten', wall_color='#5e564c', trim='#4a443c', roof='shingle', roof_color='#4f4a44', front='S', ridge='long', stories=1, bays=0, gable_bays=0,
        vents=2, barn=True, chimneys=0, eave=6.0, rise=3.0,
        basis='SHSND 00042-00074 (= 0039_00001), MHS 72460, 00042-00071: a dark gabled building of vertical boards with its ridge east-west and its gable end to the east, two ridge ventilators, eave about 6 m; identity unknown'),
 'pp-east-tower': dict(wall='boardbatten', wall_color='#4f483f', trim='#4a443c', roof='shingle', roof_color='#4a453f', front='S', ridge='hip', stories=3, bays=0, gable_bays=0,
        blank=True, no_front_door=True, chimneys=0, rise=1.8, basis='SHSND 00042-00074, MHS 72460: a tall narrow dark tower with a pyramid cap and an open-framed lower part. Position along the east building is a guess'),
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
 'photo85-f': dict(wall='clapboard', wall_color='#b9ad98', trim='#e8e2d4', roof='shingle', roof_color='#9a917f', front='E', ridge='front', stories=1, bays=1, gable_bays=1, chimneys=1,
        basis='SHSND 00042-00071/-00195: small one-storey gabled frame building, gable and door facing east, light new-shingle roof'),
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
 'photo85-u04': dict(wall='clapboard', wall_color='#e9e4d8', trim='#ffffff', roof='shingle', roof_color='#a8a090', front='', ridge='long', stories=1, bays=3, gable_bays=1, chimneys=1, eave=3.0,
        basis='SHSND 00042-00193/-00071: long low light-roofed gabled building (low confidence)'),
 'photo85-u05': dict(wall='clapboard', wall_color='#ece8de', trim='#ffffff', roof='shingle', front='', ridge='shed', stories=1, bays=1, gable_bays=1, chimneys=0, eave=2.5, rise=0.6,
        basis='SHSND 00042-00071: low white shed-roofed building (low confidence)'),
 'photo85-u07': dict(wall='boardbatten', wall_color='#d9d2c2', trim='#ffffff', roof='shingle', roof_color='#a8a090', front='', ridge='long', stories=1, bays=2, gable_bays=1, chimneys=1, eave=2.8, rise=1.5,
        basis='SHSND 00042-00193: long low light-roofed gabled building, long axis about NNE-SSW'),
 'photo85-u08': dict(wall='clapboard', wall_color='#ece8de', trim='#ffffff', roof='shingle', front='S', ridge='front', stories=1, bays=1, gable_bays=1, chimneys=1, eave=3.0,
        front_openings=[['door', 0.5], ['win', 0.8]], basis='SHSND 00042-00195: white one-storey front-gabled building, central door and small window, gable to the south'),
 'photo85-u09': dict(wall='clapboard', wall_color='#f0ece2', trim='#ffffff', roof='shingle', front='E', ridge='front', stories=1.5, bays=2, gable_bays=1, chimneys=1,
        bay_window=dict(side='E', w=2.4, d=0.7, eave=2.6, offset=1.0, offset_dir='S'), porch=[dict(side='S', depth=1.8)],
        basis='SHSND 00042-00071/-00193: white one-and-a-half-storey house, front gable to the east with a bay window, porch in the angle on the south'),
 'photo85-u11': dict(wall='boardbatten', wall_color='#6e6458', trim='#5b5248', roof='shingle', front='', ridge='long', stories=1, bays=1, gable_bays=0, chimneys=0, eave=2.5,
        basis='SHSND 00042-00195/-00193: small dark low shed'),
 'photo85-u12': dict(wall='clapboard', wall_color='#ece8de', trim='#ffffff', roof='shingle', roof_color='#a8a090', front='E', ridge='front', stories=1.5, bays=2, gable_bays=1, chimneys=0,
        split=dict(n=2, gap=0.0), barn=True, eave=4.0, rise=3.0,
        basis='SHSND 00042-00071/-00193 (still there in 00259-00003): twin front-gabled building, two equal parallel gables facing east, white walls, light roofs, a large wagon or store door'),
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
        # one-storey rear wing with its ridge running north-south (MHS 72389, SHSND 00042-00197/-00157)
        st['parts'] = [dict(rect=[q(0.08, 9), q(0.92, 9), q(0.92, 15.5), q(0.08, 15.5)], eave=3.0, ridge=5.0,
                            style=dict(front='N', ridge='front', stories=1, bays=2, gable_bays=3, porch=[], chimneys=1, shutters='#8b2e24'))]
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
    if rng.random() > 0.55 * math.exp(-(off - 17) / 35): continue   # sparser than a modern grove (photo audit: the 1885 river grove is thin)
    trees.append([round(e, 1), round(n, 1), round(g - ORIGIN[2], 2), round(float(rng.uniform(9, 19)), 1), int(rng.integers(0, 1000))])
# a few trees in and around town (two large ones stand in the middle of town in SHSND 00042-00071 and -00195)
for lo, la in [(-103.52520, 46.91420), (-103.52450, 46.91432), (-103.52395, 46.91370), (-103.52300, 46.91470), (-103.52205, 46.91445)]:
    x, y = T.transform(lo, la)
    if min(math.dist((x - ORIGIN[0], y - ORIGIN[1]), c) for c in ((190.5, 30.0), (261.8, -32.2))) < 45: continue   # none beside St. Mary's or the Von Hoffman House in 1885
    trees.append([round(x - ORIGIN[0], 1), round(y - ORIGIN[1], 1), round(zat(x, y) - ORIGIN[2], 2), 13.0, int(rng.integers(0, 1000))])
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
