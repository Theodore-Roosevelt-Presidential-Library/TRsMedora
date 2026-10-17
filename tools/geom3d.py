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


def overrides(osm, T, ORIGIN, orig_rect, feats=()):
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
    # one X-braced bay (about 2.3 m) past the north end wall over open posts (fitted camera, Oct 16 evening). 5.6 m wide.
    c0 = np.array(orig_rect('medora-depot'), float).mean(0); q, u, nrm = foot(c0)
    geom['medora-depot'] = tn(q, u, nrm, -2.8, 2.8, 4.5, 18.0 + 2.3)       # pad and footprint include the open end
    style_add['medora-depot'] = dict(
        skip_main=True,
        parts=[dict(rect=tn(q, u, nrm, -2.8, 2.8, 4.5, 18.0), eave=3.5, ridge=5.6, style=dict(_main=True))],
        decks=[dict(rect=tn(q, u, nrm, -16, 16, 1.9, 4.5), h=0.45,
                    rails=[[list(q + u * -16 + nrm * 4.4), list(q + u * -3.4 + nrm * 4.4)], [list(q + u * 3.4 + nrm * 4.4), list(q + u * 16 + nrm * 4.4)]])])

    # ------------------------------------------------ Little Missouri group, re-placed against the 3D track
    # The gazetteer places these against the 1883 plat's railroad line; the 3D track follows today's line, which put
    # the group on the wrong sides. Hagedorn: hotel "immediately north of the tracks", Nelson's store "south of the
    # track"; Haynes 1881: depot about 6-8 m north of the nearest track, hotel 20-25 m north of the depot.
    # Depot and hotel solved from the Haynes 1881 photo (SHSND 00119-00017) with its camera fitted to the depot and
    # the track (Oct 16 evening): depot front 9.5 m from the main-track centreline; the hotel 38 m north of the track
    # and about 50 m east of the depot's west end, front parallel to the track, 14 m frontage (scale from the door).
    dW = [[-586.41, 219.76], [-581.45, 216.47], [-579.44, 219.51], [-584.40, 222.79]]
    dE = [[-581.45, 216.47], [-575.34, 212.42], [-571.91, 217.60], [-578.02, 221.65]]
    q = np.array(dW[0]); u = np.array(dE[1]) - q; u /= np.hypot(*u); nrm = np.array([-u[1], u[0]])
    geom['lm-depot'] = tn(q, u, nrm, 0, 13.28, 0, 6.21)
    style_add['lm-depot'] = dict(skip_main=True, parts=[
        dict(rect=dW, eave=2.4, ridge=3.7, style=dict(_west=True)),
        dict(rect=dE, eave=2.6, ridge=3.9, style=dict(_east=True))],
        decks=[dict(rect=tn(q, u, nrm, -5, 18, -3.0, -0.05), h=0.3)])
    q = np.array([-532.80, 219.57]); u = np.array([-521.81, 210.90]) - q; u /= np.hypot(*u); nrm = np.array([-u[1], u[0]])
    geom['pyramid-park-hotel'] = tn(q, u, nrm, -6.2, 14, -0.4, 14)
    style_add['pyramid-park-hotel'] = dict(skip_main=True, parts=[
        dict(rect=tn(q, u, nrm, 0, 14, 0, 8), eave=5.15, ridge=8.4, style=dict(_main=True)),
        dict(rect=tn(q, u, nrm, 6.8, 14, -0.4, 8), eave=5.15, ridge=8.9, style=dict(_cross=True)),
        dict(rect=tn(q, u, nrm, -6.2, 0, 0, 4.5), eave=5.6, ridge=8.5, style=dict(_west=True)),
        dict(rect=tn(q, u, nrm, -4, 0.5, 8, 14), eave=2.6, ridge=4.2, style=dict(_rear=True))],
        decks=[dict(rect=tn(q, u, nrm, -6.2, 14, -2.1, -0.4), h=0.2)])
    for fid, off in (('lm-roberts-saloon', 38), ('nelson-store', -30), ('mcgeeney-boarding-house', -30), ('fitzgerald-shack', -28), ('maunders-shack', 28)):
        try: R0 = orig_rect(fid)
        except KeyError: continue
        c0 = np.array(R0, float).mean(0); q, u, nrm = foot(c0)
        _, _, _, L, W = _rect_frame(R0)
        geom[fid] = rect_c(q + nrm * off, L, W, u)
        props[fid] = dict(notes_add='In the 3D view this building is placed against the 3D track (today\'s line) on the side Hagedorn gives.')
    for fid in ('lm-depot', 'pyramid-park-hotel'):
        props[fid] = dict(notes_add='In the 3D view placed from the Haynes 1881 photo (SHSND 00119-00017) with its camera fitted to the depot and the track: depot front about 9.5 m north of the main track; hotel front about 38 m north of the track and about 50 m east of the depot\'s west end, 14 m frontage. The hotel\'s distance trades off against its size (an 11.4 m frontage would put it about 6 m nearer).')

    # ------------------------------------------------ courthouse cottages: two separate small hipped cottages (SHSND 00042-00194/-00195)
    c, uu, vv, L, W = _rect_frame(orig_rect('courthouse-cottages'))
    ns = uu if abs(uu[1]) > abs(uu[0]) else vv
    ns = ns if ns[1] > 0 else -ns
    south_end = c - ns * (L if abs(uu[1]) > abs(uu[0]) else W) / 2
    geom['courthouse-cottages'] = rect_c(south_end + ns * 21.5 / 2, 21.5, 8.0, ns)

    # ------------------------------------------------ packing plant
    # Solved jointly from SHSND 00042-00074 (1885) and MHS 72460 (1886) with both cameras fitted to the surviving
    # chimney (Oct 16 evening): the chimney stands about 26 m north of the tall block's south face and about 5 m east of
    # its south-west corner. Tall block 30.9 m long, eave 9.6 m; the photos cannot measure its depth, and 7 m keeps it
    # clear of the cooling house behind its east end (the 1957 foundation note gives 14-24 ft). Annex 15.6 m, its south
    # face 1.7 m back; the runway's timber pier about 25 m west of the tall block.
    c, uu, vv, L, W = _rect_frame(orig_rect('pp-foundation'))
    ew = uu if abs(uu[0]) >= abs(uu[1]) else vv; ew = ew if ew[0] > 0 else -ew; ns_ = np.array([-ew[1], ew[0]])
    sw = np.array((-205.7, 164.9)); LT, WT, LA, WA, SA = 30.9, 7.0, 15.6, 10.0, 1.7
    tall = rect_c(sw + ew * LT / 2 + ns_ * WT / 2, LT, WT, ew)
    annex = rect_c(sw - ew * LA / 2 + ns_ * (SA + WA / 2), LA, WA, ew)
    geom['pp-foundation'] = rect_c(sw + ew * (LT - LA) / 2 + ns_ * (SA + WA) / 2, LT + LA, SA + WA, ew)
    style_add['pp-foundation'] = dict(skip_main=True, parts=[
        dict(rect=tall, eave=9.6, style=dict(_tall=True)),
        dict(rect=annex, eave=8.5, style=dict(_annex=True))],
        decks=[dict(rect=rect_c(sw + ew * LT / 2 + ns_ * (WT + 1.5), LT, 3, ew), h=1.2,
                    rails=[[list(sw + ns_ * (WT + 2.9)), list(sw + ew * LT + ns_ * (WT + 2.9))]])])
    # cooling house of 1883 (SHSND 00042-00150, -00188; seen behind the plant in 00042-00074/-75, MHS 72460): not in the gazetteer
    CH = np.array((-175.4, 178.1))
    extra.append(dict(id='pp-cooling-house', name='Cooling house (1883)', town='Medora', kind='building', built=1883.8, built_text='summer-fall 1883 (SHSND 00042-00188)',
                      removed=None, removed_text='', use='refrigerated cooling house for dressed beef, with a car-loading platform', material='frame, painted clapboard',
                      stories='3', loc='B', form='B', rect=rect_c(CH, 11, 11, ew), eave=9.0, ridge=12.0,
                      evidence='Located by triangulating its cupola in the two fitted plant photos (SHSND 00042-00074 and MHS 72460), which agree with the sight lines in the solved overviews 00042-00071 and -00193; good to about +/-2 m. The cupola top solves at 14.8 m, as modelled.',
                      sources='SHSND 00042-00150, 00042-00188, 00042-00074, 00042-00075; MHS 72460',
                      photos='shsnd:00042-00150; shsnd:00042-00188; shsnd:00042-00074; mhs:72460',
                      notes='Added from the 2026 photo audit. A refrigerator car (NP 4800) stands at its loading platform in 00042-00150.'))
    # east building: ridge east-west (its gable end faces east in 0039_00001 and 00042-00071); south face and west end from the fitted plant photos
    geom['pp-east-building'] = rect_c(np.array((-160.0 + 15, 164.0 + 6.5)), 30, 13, ew)
    extra.append(dict(id='pp-east-tower', name='Plant tower (east)', town='Medora', kind='building', built=1885.3, built_text='by 1885', removed=None, removed_text='',
                      use='unknown (a walkway from the main house reached it)', material='frame, dark boards', stories='', loc='C', form='C',
                      rect=rect_c((-163.7, 168.8), 3.2, 3.2, ew), eave=9.2, ridge=10.7,
                      evidence='A tall narrow dark tower with a pyramid cap stands at the west end of the east building, reached by an open walkway about 7 m up (SHSND 00042-00074, MHS 72460, 00042-00180). Its peak is triangulated in the two fitted plant photos (+/-3 m), top about 10.7 m.',
                      sources='SHSND 00042-00074; MHS 72460; SHSND 00042-00180', photos='shsnd:00042-00074; mhs:72460', notes='Added from the 2026 photo audit.'))
    # ice house: only Huffman shows it; its east end is hidden behind the runway pier, so it stands just north of the pier line
    c, uu, vv, L, W = _rect_frame(orig_rect('pp-ice-house'))
    geom['pp-ice-house'] = rect_c(np.array(((-260.1 - 231.9) / 2, 174.0 + W / 2)), 28.2, W, ew)
    # ------------------------------------------------ Chateau outbuildings (SHSND 00042-00152, 1883; 00042-00157, 1884)
    extra.append(dict(id='chateau-outbuilding-east', name='Chateau outbuilding (east of the house)', town='Chateau', kind='building', built=1883.6, built_text='by 1883',
                      removed=None, removed_text='', use='outbuilding (kitchen or wash house?)', material='frame, light painted', stories='1', loc='C', form='C',
                      rect=rect_c((-705.0, -237.0), 6, 5, bearing_u(110)), eave=2.6, ridge=4.3,
                      evidence='A small light gabled one-storey building close east of the house, with smoke or steam beside it (SHSND 00042-00152, 1883), placed from that photo\'s fitted camera; a chimney seen past the east gable in 00042-00196 (1886) fits it.',
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
                      rect=rect_c((307.0, -20.0), 8, 6, bearing_u(90)), eave=2.8, ridge=4.4,
                      evidence='A white side-gabled house with a chimney, a door and two windows facing south, with a darker building against it and a small white shed (SHSND 00042-00194, -00193; still there in 00259-00003); moved 12 m east to fit the fitted camera of 00042-00176. Position good to about +/-15 m.',
                      sources='SHSND 00042-00193/-00194', photos='shsnd:00042-00194; shsnd:00042-00193', notes='Added from the 2026 photo audit.'))
    extra.append(dict(id='photo85-x2b', name='Unidentified dark building east of the Von Hoffman House', town='Medora', kind='building', built=1885.0, built_text='by 1885-86',
                      removed=None, removed_text='', use='unknown', material='log or unpainted boards', stories='1', loc='C', form='D',
                      rect=rect_c((312.0, -30.0), 7, 5, bearing_u(90)), eave=2.5, ridge=3.8,
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
    style_add['pp-cooling-house'] = dict(decks=[dict(rect=rect_c(CH + np.array([-ew[1], ew[0]]) * 7.0, 11, 3, ew), h=1.2)])
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
    # ------------------------------------------------ keep buildings off the platted streets
    # The streets follow the 1883 plat (today's lot lines match it), and no 1885-86 photo shows a building standing in a
    # street. Where a photo-placed footprint overlaps a street, it is slid off the street the way its evidence allows:
    #  - placed by back-projection from ONE photo: along that photo's line of sight (the bearing is well fixed, the
    #    distance is the uncertain part, +/-25 m);
    #  - triangulated or from a written source: by the smallest move that clears the street.
    CAMS = {'00042-00193': (610.3, -159.1), '00042-00071': (518.5, -7.1), '00042-00195': (494.7, -267.0)}
    TOWN = Polygon([T.transform(lo, la) for lo, la in [(-103.5272, 46.9128), (-103.5200, 46.9128), (-103.5200, 46.9168), (-103.5272, 46.9168)]])
    TOWN = Polygon([(x - ORIGIN[0], y - ORIGIN[1]) for x, y in TOWN.exterior.coords])
    GRID = {'Main Street': 10 + 2 * 2.4, '3rd Avenue': 10, '2nd Avenue': 6, '3rd Street': 6, '4th Street': 6, '5th Street': 6, 'Broadway': 6}
    sp = []
    for f in osm['features']:
        pr = f['properties']
        if pr.get('kind') != 'road' or pr.get('name') not in GRID: continue
        g = shape(f['geometry']); lines = [g] if g.geom_type == 'LineString' else list(g.geoms)
        for l in lines:
            L = LineString([(x - ORIGIN[0], y - ORIGIN[1]) for x, y in (T.transform(*c) for c in l.coords)]).intersection(TOWN)
            if not L.is_empty: sp.append(L.buffer(GRID[pr['name']] / 2 + 0.5))
    streets = unary_union(sp)
    moved = {}
    for pr in feats:
        fid = pr['id']
        if fid in style_add or pr.get('kind') in ('landmark', 'railroad', 'bridge'): continue
        try: R0 = geom.get(fid) or orig_rect(fid)
        except Exception: continue
        P = Polygon(R0)
        if P.area > 4000 or P.intersection(streets).area < 1.0: continue
        ev = pr.get('evidence') or ''
        cam = next((CAMS[k] for k in CAMS if ('solved camera of ' + k) in ev), None) if 'Back-projected' in ev else None
        c = np.array(P.centroid.coords[0])
        if cam is not None:
            d = c - np.array(cam); d /= np.hypot(*d); cands = [d * t for t in sorted(np.arange(-35, 35.1, 0.5), key=abs)]
            how = 'slid %.1f m along its line of sight from the camera of SHSND %s' % (0, next(k for k in CAMS if CAMS[k] == cam))
        else:
            cands = sorted([np.array([math.cos(a) * r, math.sin(a) * r]) for r in np.arange(0.5, 20.1, 0.5) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)], key=lambda v: np.hypot(*v))
            how = 'moved by the smallest shift that clears the street'
        for v in cands:
            Q = Polygon([(x + v[0], y + v[1]) for x, y in R0])
            if Q.intersection(streets).area < 0.5:
                geom[fid] = [[round(x, 2), round(y, 2)] for x, y in Q.exterior.coords[:4]]
                dist = float(np.hypot(*v)); moved[fid] = dist
                note = ('Placement check (Oct 16, 2026): the footprint overlapped a platted street, so it was ' + (how.replace('0.0', '%.1f' % dist) if cam is not None else how) + ' (%.1f m) in the 3D view.' % dist)
                props.setdefault(fid, {}); props[fid]['notes_add'] = ((props[fid].get('notes_add') or '') + ' ' + note).strip()
                break
    print('declash:', {k: round(v, 1) for k, v in moved.items()})
    return geom, extra, style_add, props
