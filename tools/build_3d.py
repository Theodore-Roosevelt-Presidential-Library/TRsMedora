"""Build the data for the 3D view (map3d/) from the gazetteer and the lidar terrain.

Run after tools/build_features.py:
    python3 tools/build_3d.py

Reads  map/data/historic_features.geojson, map/data/river_1883.geojson, map3d/data/terrain.{bin,json}
Writes map3d/data/scene.json  (local metres: x = east, y = north, z = up; origin ORIGIN below)
"""
import json, math, os
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, Polygon, LineString

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
out['river_1883'] = [loc(q.x, q.y) + [round(zat(q.x, q.y) - ORIGIN[2] + 0.3, 2)] for q in dense]
out['terrain'] = {'x0': meta['x0'] - ORIGIN[0], 'y1': meta['y1'] - ORIGIN[1], 'res': meta['res'], 'cols': meta['cols'], 'rows': meta['rows'],
                  'z0': meta['z0'] - ORIGIN[2], 'scale': meta['scale'], 'file': 'terrain.bin'}

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
