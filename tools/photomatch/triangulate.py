import os
import sys, json, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from camlib import *
from scipy.optimize import least_squares
"""Triangulate features seen in two or more solved photos.

Input JSON: {"feature_id": {"cam_file.json": [u, v] or [u, null], ...}, ...}
For each camera the pixel column u gives a bearing (azimuth) line on the ground. Lines from two or
more cameras are intersected by least squares (angles weighted equally). If v is given, the ground
back-projection from that camera is reported as a check, and the triangulated point is projected
back into every photo so the pixel residuals can be read.
"""
obs = json.load(open(sys.argv[1]))
cams = {}
def cam(f):
    if f not in cams:
        K = json.load(open(f)); K['C'] = np.array(K['C']); cams[f] = K
    return cams[f]

def az_of(K, u, v):
    vv = K['cy'] if v is None else v
    d = ray_dir(u, vv, K['yaw'], K['pitch'], K['f'], K['cx'], K['cy'], K.get('roll', 0.0))
    return math.atan2(d[0], d[1])

out = {}
for fid, views in obs.items():
    rays = []
    for cf, (u, v) in views.items():
        K = cam(cf); rays.append((cf, K, u, v, az_of(K, u, v)))
    res = {'id': fid, 'n': len(rays)}
    # ground back-projections (single-photo estimates)
    gp = {}
    for cf, K, u, v, a in rays:
        if v is not None:
            p, d = ray_ground(u, v, K['C'], K['yaw'], K['pitch'], K['f'], K['cx'], K['cy'], K.get('roll', 0.0), step=1.0)
            if p is not None: gp[os.path.basename(cf)] = [round(c, 6) for c in ll(p[0], p[1])] + [round(d)]
    res['ground'] = gp
    if len(rays) >= 2:
        def r(x):
            return [math.remainder(math.atan2(x[0] - K['C'][0], x[1] - K['C'][1]) - a, 2 * math.pi) for _, K, _, _, a in rays]
        # start from the intersection of the first two lines
        (_, K1, _, _, a1), (_, K2, _, _, a2) = rays[0], rays[1]
        A = np.array([[math.sin(a1), -math.sin(a2)], [math.cos(a1), -math.cos(a2)]])
        try:
            t = np.linalg.solve(A, K2['C'][:2] - K1['C'][:2]); x0 = K1['C'][:2] + t[0] * np.array([math.sin(a1), math.cos(a1)])
        except np.linalg.LinAlgError:
            x0 = (K1['C'][:2] + K2['C'][:2]) / 2
        s = least_squares(r, x0)
        X = s.x; lon, lat = ll(*X)
        res['lonlat'] = [round(lon, 6), round(lat, 6)]
        res['resid_deg'] = [round(math.degrees(e), 3) for e in s.fun]
        # intersection angle (geometry strength) and 1-sigma error for 2 px bearing noise
        angs = [math.degrees(a) for *_, a in rays]
        dists = [float(np.hypot(*(X - K['C'][:2]))) for _, K, *_ in rays]
        res['dist_m'] = [round(d) for d in dists]
        cut = abs(math.remainder(math.radians(angs[0] - angs[1]), math.pi))
        res['cut_deg'] = round(math.degrees(cut), 1)
        sig = [2.0 / K['f'] * d for (_, K, *_), d in zip(rays, dists)]
        res['err_m'] = round(float(math.hypot(*sig[:2]) / max(math.sin(cut), 0.05)), 1)
        zz = z(*X)
        res['reproj'] = {}
        for cf, K, u, v, a in rays:
            q, _ = project([X[0], X[1], zz], K['C'], K['yaw'], K['pitch'], K['f'], K['cx'], K['cy'], K.get('roll', 0.0))
            res['reproj'][os.path.basename(cf)] = {'obs': [u, v], 'base_px': [round(q[0], 1), round(q[1], 1)]}
    out[fid] = res
    print(json.dumps(res))
if len(sys.argv) > 2:
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
