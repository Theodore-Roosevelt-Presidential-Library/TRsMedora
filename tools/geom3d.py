"""Footprint changes and extra buildings for the 3D view, from the photo audit of Oct 16, 2026
(docs/photo-audit.md). The 2D gazetteer (build_features.py) is left as it is except where noted there.

build_3d.py calls overrides(...) before it levels the building pads, so pads follow these footprints.
All coordinates are local metres (e = east, n = north) from build_3d.ORIGIN.
"""
import math
import numpy as np
from shapely.geometry import shape, LineString, Polygon, Point
from shapely.ops import linemerge, unary_union


def _rect_frame(rect):
    """centre, unit long axis u, unit short axis v, length, width of a 4-corner rect"""
    R = np.array(rect, float); c = R.mean(0)
    e0, e1 = R[1] - R[0], R[2] - R[1]
    if np.hypot(*e0) >= np.hypot(*e1): u, L, W = e0 / np.hypot(*e0), np.hypot(*e0), np.hypot(*e1)
    else: u, L, W = e1 / np.hypot(*e1), np.hypot(*e1), np.hypot(*e0)
    return c, u, np.array([-u[1], u[0]]), L, W


def rect_c(c, L, W, u):
    """rect of length L along unit vector u and width W, centred on c"""
    u = np.asarray(u, float) / np.hypot(*u); v = np.array([-u[1], u[0]]); c = np.asarray(c, float)
    return [[round(float(x), 2), round(float(y), 2)] for x, y in (c - u * L / 2 - v * W / 2, c + u * L / 2 - v * W / 2, c + u * L / 2 + v * W / 2, c - u * L / 2 + v * W / 2)]


def bearing_u(deg):
    """unit vector for a compass bearing (0 = north, 90 = east)"""
    r = math.radians(deg); return np.array([math.sin(r), math.cos(r)])


def overrides(osm, T, ORIGIN, orig_rect):
    """orig_rect(id) -> the feature's footprint rect (local) as the gazetteer has it.
    Returns (geom, extra, style_add, props):
      geom      {id: rect}            new footprints
      extra     [item dicts]          buildings the gazetteer lacks (each has 'rect')
      style_add {id: dict}            style keys that depend on geometry (parts, decks, fences)
      props     {id: dict}            property changes (grades, dates, notes)"""
    rails = [shape(f['geometry']) for f in osm['features'] if f['properties'].get('kind') == 'rail']
    rl = linemerge(unary_union(rails)); rl = max(rl.geoms, key=lambda g: g.length) if hasattr(rl, 'geoms') else rl
    track = LineString([(x - ORIGIN[0], y - ORIGIN[1]) for x, y in (T.transform(*c) for c in rl.coords)])

    def foot(p):
        d = track.project(Point(p)); q = track.interpolate(d)
        a, b = track.interpolate(max(0, d - 3)), track.interpolate(min(track.length, d + 3))
        u = np.array([b.x - a.x, b.y - a.y]); u /= np.hypot(*u)
        if u[0] < 0: u = -u                                   # point east along the line
        return np.array([q.x, q.y]), u, np.array([-u[1], u[0]])   # normal points to the north side

    def tn(q, u, nrm, t0, t1, n0, n1):
        return [[round(float(x), 2), round(float(y), 2)] for x, y in (q + u * t0 + nrm * n0, q + u * t1 + nrm * n0, q + u * t1 + nrm * n1, q + u * t0 + nrm * n1)]

    geom, extra, style_add, props = {}, [], {}, {}

    # ------------------------------------------------ Medora depot (MHS 72461, Huffman 1886)
    # Gable end on the track, long axis perpendicular to it, about 4.5 m from the track centreline; the roof runs on
    # about 8 m past the north end wall over open posts. 5.6 m wide, about 13.5 m of enclosed walls.
    c0 = np.array(orig_rect('medora-depot'), float).mean(0); q, u, nrm = foot(c0)
    geom['medora-depot'] = tn(q, u, nrm, -2.8, 2.8, 4.5, 18.0 + 8.0)       # pad and footprint include the open end
    style_add['medora-depot'] = dict(
        skip_main=True,
        parts=[dict(rect=tn(q, u, nrm, -2.8, 2.8, 4.5, 18.0), eave=3.3, ridge=5.2, style=dict(_main=True))],
        decks=[dict(rect=tn(q, u, nrm, -16, 16, 1.9, 4.5), h=0.45,
                    rails=[[list(q + u * -16 + nrm * 4.4), list(q + u * -3.4 + nrm * 4.4)], [list(q + u * 3.4 + nrm * 4.4), list(q + u * 16 + nrm * 4.4)]])])

    # ------------------------------------------------ Little Missouri group, re-placed against the 3D track
    # The gazetteer places these against the 1883 plat's railroad line; the 3D track follows today's line, which put
    # the group on the wrong sides. Hagedorn: hotel "immediately north of the tracks", Nelson's store "south of the
    # track"; Haynes 1881: depot about 6-8 m north of the nearest track, hotel 20-25 m north of the depot.
    c0 = np.array(orig_rect('lm-depot'), float).mean(0); q, u, nrm = foot(c0)
    geom['lm-depot'] = tn(q, u, nrm, -7, 7, 7, 13.5)
    style_add['lm-depot'] = dict(skip_main=True, parts=[
        dict(rect=tn(q, u, nrm, -7, -1, 7, 11.5), eave=2.4, ridge=4.0, style=dict(_west=True)),
        dict(rect=tn(q, u, nrm, -1, 7, 7, 13.5), eave=2.6, ridge=4.8, style=dict(_east=True))],
        decks=[dict(rect=tn(q, u, nrm, -12, 12, 2.2, 5.0), h=0.3)])
    c0 = np.array(orig_rect('pyramid-park-hotel'), float).mean(0); q, u, nrm = foot(c0)
    geom['pyramid-park-hotel'] = tn(q, u, nrm, -12, 7, 28.5, 43)
    style_add['pyramid-park-hotel'] = dict(skip_main=True, parts=[
        dict(rect=tn(q, u, nrm, -7, 7, 29, 37), eave=4.1, ridge=7.4, style=dict(_main=True)),
        dict(rect=tn(q, u, nrm, 3, 7, 28.6, 37), eave=4.1, ridge=7.5, style=dict(_cross=True)),
        dict(rect=tn(q, u, nrm, -12, -7, 29, 37), eave=3.6, ridge=6.4, style=dict(_west=True)),
        dict(rect=tn(q, u, nrm, -11, -6.5, 37, 43), eave=2.6, ridge=4.2, style=dict(_rear=True))],
        decks=[dict(rect=tn(q, u, nrm, -12, 7, 27.2, 28.9), h=0.2)])
    for fid, off in (('lm-roberts-saloon', 38), ('nelson-store', -30), ('mcgeeney-boarding-house', -30), ('fitzgerald-shack', -28), ('maunders-shack', 28)):
        try: R0 = orig_rect(fid)
        except KeyError: continue
        c0 = np.array(R0, float).mean(0); q, u, nrm = foot(c0)
        _, _, _, L, W = _rect_frame(R0)
        geom[fid] = rect_c(q + nrm * off, L, W, u)
        props[fid] = dict(notes_add='In the 3D view this building is placed against the 3D track (today\'s line) on the side Hagedorn gives.')
    for fid in ('lm-depot', 'pyramid-park-hotel'):
        props[fid] = dict(notes_add='In the 3D view placed against the 3D track (today\'s line): Hagedorn and the Haynes 1881 photo put the depot about 6-8 m north of the tracks and the hotel 20-25 m north of the depot.')

    # ------------------------------------------------ courthouse cottages: two separate small hipped cottages (SHSND 00042-00194/-00195)
    c, uu, vv, L, W = _rect_frame(orig_rect('courthouse-cottages'))
    ns = uu if abs(uu[1]) > abs(uu[0]) else vv
    ns = ns if ns[1] > 0 else -ns
    south_end = c - ns * (L if abs(uu[1]) > abs(uu[0]) else W) / 2
    geom['courthouse-cottages'] = rect_c(south_end + ns * 21.5 / 2, 21.5, 8.0, ns)

    # ------------------------------------------------ packing plant
    # main house: a tall block (east, about 30 m) and a lower windowed annex (west, about 16 m) - SHSND 00042-00074/-75, MHS 72460
    c, uu, vv, L, W = _rect_frame(orig_rect('pp-foundation'))
    ew = uu if abs(uu[0]) >= abs(uu[1]) else vv; ew = ew if ew[0] > 0 else -ew; ns_ = np.array([-ew[1], ew[0]])
    L46, W18 = 46.0, 18.0
    west = c - ew * L46 / 2
    geom['pp-foundation'] = rect_c(c, L46, W18, ew)
    tall = rect_c(west + ew * (16 + 15), 30, W18, ew)
    annex = rect_c(west + ew * 8, 16, 14, ew)
    style_add['pp-foundation'] = dict(skip_main=True, parts=[
        dict(rect=tall, eave=10.5, style=dict(_tall=True)),
        dict(rect=annex, eave=8.5, style=dict(_annex=True))],
        decks=[dict(rect=rect_c(west + ew * 12.5 + ns_ * (W18 / 2 + 1.5), 25, 3, ew), h=1.2,
                    rails=[[list(west + ns_ * (W18 / 2 + 2.9)), list(west + ew * 25 + ns_ * (W18 / 2 + 2.9))]])])
    # cooling house of 1883 (SHSND 00042-00150, -00188; seen behind the plant in 00042-00074/-75, MHS 72460): not in the gazetteer
    extra.append(dict(id='pp-cooling-house', name='Cooling house (1883)', town='Medora', kind='building', built=1883.8, built_text='summer-fall 1883 (SHSND 00042-00188)',
                      removed=None, removed_text='', use='refrigerated cooling house for dressed beef, with a car-loading platform', material='frame, painted clapboard',
                      stories='3', loc='C', form='B', rect=rect_c((-172.0, 183.0), 11, 11, ew), eave=9.0, ridge=12.0,
                      evidence='Located by crossing the sight lines to its cupola in the solved photos SHSND 00042-00071 and 00042-00193, and its place behind the east end of the main house in Huffman 1886 (MHS 72460); good to about +/-10 m.',
                      sources='SHSND 00042-00150, 00042-00188, 00042-00074, 00042-00075; MHS 72460',
                      photos='shsnd:00042-00150; shsnd:00042-00188; shsnd:00042-00074; mhs:72460',
                      notes='Added from the 2026 photo audit. A refrigerator car (NP 4800) stands at its loading platform in 00042-00150.'))
    # east building: ridge east-west (its gable end faces east in 0039_00001 and 00042-00071)
    c, uu, vv, L, W = _rect_frame(orig_rect('pp-east-building'))
    geom['pp-east-building'] = rect_c(c, 30, 13, ew)
    extra.append(dict(id='pp-east-tower', name='Plant tower (east)', town='Medora', kind='building', built=1885.3, built_text='by 1885', removed=None, removed_text='',
                      use='unknown (a walkway from the main house reached it)', material='frame, dark boards', stories='', loc='D', form='C',
                      rect=rect_c(c - ew * (15 + 2.5), 3.2, 3.2, ew), eave=11.0, ridge=12.8,
                      evidence='A tall narrow dark tower with a pyramid cap stands at the west end of the east building, reached by an open walkway about 7 m up (SHSND 00042-00074, MHS 72460, 00042-00180). Position along the building is a guess.',
                      sources='SHSND 00042-00074; MHS 72460; SHSND 00042-00180', photos='shsnd:00042-00074; mhs:72460', notes='Added from the 2026 photo audit.'))

    # ------------------------------------------------ Chateau outbuildings (SHSND 00042-00152, 1883; 00042-00157, 1884)
    extra.append(dict(id='chateau-outbuilding-east', name='Chateau outbuilding (east of the house)', town='Chateau', kind='building', built=1883.6, built_text='by 1883',
                      removed=None, removed_text='', use='outbuilding (kitchen or wash house?)', material='frame, light painted', stories='1', loc='C', form='C',
                      rect=rect_c((-700.0, -241.0), 6, 5, bearing_u(110)), eave=2.6, ridge=4.3,
                      evidence='A small light gabled one-storey building close east of the house, with smoke or steam beside it (SHSND 00042-00152, 1883). Distance from the house estimated (10-20 m).',
                      sources='SHSND 00042-00152', photos='shsnd:00042-00152', notes='Added from the 2026 photo audit.'))
    p = orig_rect('chateau-outbuildings', point=True)
    extra.append(dict(id='chateau-stable', name='Chateau carriage shed and stable (provisional place)', town='Chateau', kind='building', built=1883.6, built_text='by 1884',
                      removed=None, removed_text='', use='carriage shed / stable', material='frame, dark', stories='1', loc='D', form='C',
                      rect=rect_c(p, 20, 7, bearing_u(90)), eave=3.0, ridge=5.0,
                      evidence='A long, low gabled building with wagons in front (SHSND 00042-00157, 1884). The NRHP nomination puts the coachman\'s house, carriage shed and stable to the south and further east; placed at the gazetteer\'s outbuildings point. Its direction from the house in the photo is uncertain.',
                      sources='SHSND 00042-00157; NRHP 1974', photos='shsnd:00042-00157', notes='Added from the 2026 photo audit; place provisional.'))

    # ------------------------------------------------ buildings in the 1885-86 overviews that the gazetteer lacks
    extra.append(dict(id='photo85-x1', name='Unidentified cottage (south-east of St. Mary\'s)', town='Medora', kind='building', built=1885.0, built_text='by 1885',
                      removed=None, removed_text='', use='dwelling?', material='frame, white', stories='1', loc='B', form='C',
                      rect=rect_c((215.0, -85.0), 8, 5, bearing_u(90)), eave=2.7, ridge=4.2,
                      evidence='Located in three solved photos (SHSND 00042-00195, -00194, -00193): a white one-storey side-gabled cottage, ridge about east-west, chimney at the west gable, lower lean-to with a door at the west end. Good to about +/-10 m.',
                      sources='SHSND 00042-00193/-00194/-00195', photos='shsnd:00042-00195; shsnd:00042-00194; shsnd:00042-00193', notes='Added from the 2026 photo audit.'))
    extra.append(dict(id='photo85-x2', name='Unidentified house east of the Von Hoffman House', town='Medora', kind='building', built=1885.0, built_text='by 1885-86',
                      removed=None, removed_text='', use='dwelling?', material='frame, white', stories='1', loc='C', form='C',
                      rect=rect_c((295.0, -20.0), 8, 6, bearing_u(90)), eave=2.8, ridge=4.4,
                      evidence='A white side-gabled house with a chimney, a door and two windows facing south, with a darker building against it and a small white shed (SHSND 00042-00194, -00193; still there in 00259-00003). Position good to about +/-15 m.',
                      sources='SHSND 00042-00193/-00194', photos='shsnd:00042-00194; shsnd:00042-00193', notes='Added from the 2026 photo audit.'))
    extra.append(dict(id='photo85-x2b', name='Unidentified dark building east of the Von Hoffman House', town='Medora', kind='building', built=1885.0, built_text='by 1885-86',
                      removed=None, removed_text='', use='unknown', material='log or unpainted boards', stories='1', loc='C', form='D',
                      rect=rect_c((295.0, -30.0), 7, 5, bearing_u(90)), eave=2.5, ridge=3.8,
                      evidence='Adjoining the white house to its south in SHSND 00042-00194 (M).', sources='SHSND 00042-00194', photos='shsnd:00042-00194', notes='Added from the 2026 photo audit.'))
    extra.append(dict(id='von-hoffman-outbuilding', name='Von Hoffman House yard outbuilding', town='Medora', kind='building', built=1885.0, built_text='by 1885',
                      removed=None, removed_text='', use='outbuilding (stable or carriage house?)', material='frame', stories='1', loc='B', form='C',
                      rect=rect_c((257.0, -7.0), 13, 6, bearing_u(90)), eave=2.5, ridge=4.2,
                      evidence='Low gabled building inside the fenced yard north of the house, with a light roof and a small cross gable (SHSND 00042-00071, -00193; 00259-00003; background of 00042-00182).',
                      sources='SHSND 00042-00071/-00193/-00182', photos='shsnd:00042-00071; shsnd:00042-00193', notes='Added from the 2026 photo audit.'))
    style_add['von-hoffman-house'] = dict(fences=[dict(kind='rail', h=1.2, pts=[[255.8, -40.5], [240.0, -40.5], [240.0, 3.0], [273.0, 3.0], [273.0, -23.0]])])

    # ------------------------------------------------ unidentified buildings: footprints the photos size differently
    for fid, L, W, brg in (('photo85-u04', 12, 6, None), ('photo85-u07', 11, 5, 20), ('photo85-u11', 5, 4, None), ('photo85-u12', 16, 10, 0), ('photo85-f', 7.3, 4.9, 90)):
        try: c, uu, vv, L0, W0 = _rect_frame(orig_rect(fid))
        except KeyError: continue
        geom[fid] = rect_c(c, L, W, bearing_u(brg) if brg is not None else uu)
    # u03: an ell at the south end projecting east
    try:
        c, uu, vv, L0, W0 = _rect_frame(orig_rect('photo85-u03'))
        ns = uu if abs(uu[1]) > abs(uu[0]) else vv; ns = ns if ns[1] > 0 else -ns; eo = np.array([ns[1], -ns[0]])
        Lns = L0 if abs(uu[1]) > abs(uu[0]) else W0; Wew = W0 if abs(uu[1]) > abs(uu[0]) else L0
        style_add['photo85-u03'] = dict(parts=[dict(rect=rect_c(c - ns * (Lns / 2 - 2) + eo * (Wew / 2 + 1), 4, 4.0 + Wew / 2, ns), eave=2.9, ridge=4.8, style=dict(front='E', ridge='front', bays=1, gable_bays=1))])
    except KeyError: pass

    # ------------------------------------------------ Hotel de Mores: kitchen and laundry wing on the north side near the east end (Cow Boy 1885; seen in 00042-00071/-00195)
    c, uu, vv, L, W = _rect_frame(orig_rect('hotel-de-mores'))
    ew = uu if uu[0] > 0 else -uu; nn = np.array([-ew[1], ew[0]])
    style_add['hotel-de-mores'] = dict(parts=[dict(rect=rect_c(c + ew * (L / 2 - 6) + nn * (W / 2 + 2.0), 8, 4, ew), eave=3.2, ridge=4.6)])
    # cooling house loading platform (SHSND 00042-00150), north side
    ch = [x for x in extra if x['id'] == 'pp-cooling-house'][0]
    style_add['pp-cooling-house'] = dict(decks=[dict(rect=rect_c(np.array((-172.0, 183.0)) + np.array([-ew[1], ew[0]]) * 7.0, 11, 3, ew), h=1.2)])
    # company store: three joined front-gabled buildings of unequal width (Houghton 3013533), south to north 7.3 : 6.0 : 4.3
    c, uu, vv, L, W = _rect_frame(orig_rect('company-store-offices'))
    ns = uu if uu[1] > 0 else -uu; eo = np.array([ns[1], -ns[0]])
    fr = [7.3, 6.0, 4.3]; tot = sum(fr); pos = -L / 2; parts = []
    for w in fr:
        seg = L * w / tot; parts.append(dict(rect=rect_c(c + ns * (pos + seg / 2), seg, W, ns), eave=3.2, ridge=5.4)); pos += seg
    style_add['company-store-offices'] = dict(skip_main=True, parts=parts, decks=[dict(rect=rect_c(c + eo * (W / 2 + 0.6), L, 1.2, ns), h=0.45)])
    # Cow Boy office: board entry vestibule on the west gable, right of centre as seen from the street (Houghton 3013536)
    c, uu, vv, L, W = _rect_frame(orig_rect('cowboy-office'))
    ew = uu if uu[0] > 0 else -uu; nn = np.array([-ew[1], ew[0]])
    style_add['cowboy-office'] = dict(parts=[dict(rect=rect_c(c - ew * (L / 2 + 0.5) - nn * 0.8, 1.0, 1.5, ew), eave=2.2, ridge=2.6)])

    # ------------------------------------------------ dates and grades the photos change
    props['photo85-u10'] = dict(built=1886.0, built_text='after 1885 (open ground in SHSND 00042-00071)', notes_add='Photo audit: SHSND 00042-00071 (1885) shows open ground and a cottonwood here, so the building is shown from 1886.')
    props['photo85-u06'] = dict(removed=1885.3, removed_text='gone by summer 1885?', notes_add='Photo audit: seen in SHSND 00042-00193 (probably autumn 1884) but not in 00042-00194/-00195 (1885-86), where it should show; shown only before summer 1885.')
    props['freight-house'] = dict(loc='D', notes_add='Photo audit: the 1885-86 overviews (SHSND 00042-00194/-00195) show open ground at this spot; a long gabled building with boxcars stands further south-west. Position unconfirmed.')
    props['cowboy-office'] = dict(notes_add='Photo audit: in SHSND 00042-00071 (1885) the modelled spot reads as open ground and a small flat-roofed building stands about 20 m south. The site follows Matt Briney\'s identification of the surviving building; check against the photo.')
    props['medora-depot'] = dict(notes_add='Photo audit: MHS 72461 shows the long axis perpendicular to the track with the gable end, bay window and sign facing the track, which agrees with HMdb; the depot stood about 4-5 m from the track. The 3D model follows the photo.')
    return geom, extra, style_add, props
