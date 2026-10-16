"""Build the TRsMedora historic-features data from one editable spec.

Run from the repo root:   python3 tools/build_features.py

Writes:
  data/buildings.csv                 gazetteer (one row per feature, placed or not)
  map/data/historic_features.geojson features with a location, for the map
  map/data/unplaced.json             features known from sources but not yet located
  map/data/river_1883.geojson        1883 river channel traced from the plat
  map/data/modern.geojson            modern parcels, streets, rail, river, buildings (context)

Placement methods (see docs/geography-and-overlay.md):
  osm      footprint of a surviving building from OpenStreetMap
  plat     position read off the georeferenced 1883 plat (SHSND 00042-00183)
  address  street corner or block/lot from a period source, matched to today's parcels
  relative position worked out from a written description relative to another feature
  schematic placeholder near where sources put it; position is a guess
Needs: pip install shapely numpy
"""
import csv, json, math, os
import numpy as np
from shapely.geometry import shape, Point, LineString, Polygon, mapping
from shapely.ops import unary_union, substring

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(ROOT, *p)

# ---------------------------------------------------------------- inputs
GEO = json.load(open(R('data', 'reference', 'plat_1883_georef.json')))
A = np.array(GEO['affine_px_to_lonlat'])
def plat(x, y):
    lon, lat = np.array([x, y, 1]) @ A
    return (round(float(lon), 7), round(float(lat), 7))

OSM = json.load(open(R('data', 'reference', 'osm_medora.geojson')))
PAR = json.load(open(R('data', 'reference', 'parcels_medora_ndgishub.geojson')))
def osm(name):
    for f in OSM['features']:
        if f['properties']['name'] == name and f['properties']['kind'] == 'building':
            return shape(f['geometry'])
    raise KeyError(name)
def road(name):
    return unary_union([shape(f['geometry']) for f in OSM['features']
                        if f['properties']['kind'] == 'road' and f['properties']['name'] == name])
def corner(a, b):
    p = road(a).intersection(road(b))
    return (p.x, p.y) if p.geom_type == 'Point' else (p.centroid.x, p.centroid.y)
def block(b):
    return unary_union([shape(f['geometry']) for f in PAR['features'] if f['properties']['Block'] == b])
from shapely.ops import linemerge
RAIL = linemerge(unary_union([shape(f['geometry']) for f in OSM['features'] if f['properties']['kind'] == 'rail']))

M_LAT = 111320.0
def off(pt, east=0.0, north=0.0):
    lon, lat = pt
    return (round(lon + east / (M_LAT * math.cos(math.radians(lat))), 7), round(lat + north / M_LAT, 7))
def rect(center, w_ft, l_ft, bearing_deg=0.0):
    """Rectangle footprint (feet) centred on a point; bearing = direction of the long side, degrees from north."""
    w, l = w_ft * 0.3048 / 2, l_ft * 0.3048 / 2
    b = math.radians(bearing_deg)
    ux, uy = math.sin(b), math.cos(b)          # long axis
    vx, vy = math.cos(b), -math.sin(b)         # short axis
    pts = []
    for sl, sw in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
        pts.append(off(center, east=sl * l * ux + sw * w * vx, north=sl * l * uy + sw * w * vy))
    pts.append(pts[0])
    return Polygon(pts)

# 1883 river channel, traced (centreline, approximate) from the 469x525 plat image
RIVER_PX = [(20,13),(83,20),(200,73),(260,110),(283,173),(273,190),(233,213),(207,233),(203,253),
            (205,283),(203,333),(200,383),(187,430),(157,470),(100,467),(33,440),(13,433)]
RIVER83 = LineString([plat(*p) for p in RIVER_PX])
CROSS = RAIL.intersection(RIVER83)
CROSS = (CROSS.x, CROSS.y)
if RAIL.geom_type != 'LineString':   # use the track piece that crosses the river
    RAIL = min(RAIL.geoms, key=lambda g: g.distance(Point(CROSS)))
# unit vector along the track toward the north-west (toward Little Missouri / the Cantonment)
d0 = RAIL.project(Point(CROSS))
_a = RAIL.interpolate(d0 - 0.0005); _b = RAIL.interpolate(d0 + 0.0005)
if _a.y < _b.y: _a, _b = _b, _a
_ve = (_a.x - _b.x) * M_LAT * math.cos(math.radians(CROSS[1])); _vn = (_a.y - _b.y) * M_LAT
_n = math.hypot(_ve, _vn); NW = (_ve / _n, _vn / _n)          # east, north components
PERP_N = (-NW[1], NW[0]) if NW[0] < 0 else (NW[1], -NW[0])     # perpendicular pointing north-east-ish
TRACK_BEARING = (math.degrees(math.atan2(NW[0], NW[1])) + 360) % 360
def along(m, side=0.0):
    """Point m metres north-west of the 1883 river crossing along the track, `side` metres to the north side."""
    return off(CROSS, east=m * NW[0] + side * PERP_N[0], north=m * NW[1] + side * PERP_N[1])
LM_DEPOT = along(150)   # 1957 NPS "Tour of Medora" map and BROOKS57 put Little Missouri at the west end of the old US 10 bridge, near today's Chateau Road

# ---------------------------------------------------------------- spec
# Dates: built/removed as decimal years (None = unknown / still standing). Grades A-D (see README).
F = []
def add(**k):
    k.setdefault('aka', ''); k.setdefault('photos', ''); k.setdefault('notes', '')
    k.setdefault('material', ''); k.setdefault('stories', ''); k.setdefault('footprint_ft', '')
    k.setdefault('removed', None); k.setdefault('removed_text', '')
    F.append(k)

# --- Railroad and river
_dc = RAIL.project(Point(CROSS))
_west = substring(RAIL, 0, _dc) if Point(RAIL.coords[0]).y > Point(RAIL.coords[-1]).y else substring(RAIL, _dc, RAIL.length)
_wc = list(_west.coords)
if _wc[0][1] < _wc[-1][1]: _wc = _wc[::-1]            # run north-west -> crossing
_east = [plat(204, 247), plat(330, 325), plat(469, 412)]   # track east of the river as drawn on the 1883 plat
add(id='np-railroad', name='Northern Pacific main line (as in 1883)', town='Between', bank='both', kind='railroad',
    built=1880.5, built_text='1880 (track reached the Little Missouri in 1880; bridge under construction in Haynes 1880 photo)',
    use='railroad', loc='B', form='B', method='plat',
    geom=LineString(_wc + [CROSS] + _east),
    evidence='West of the river, today\'s BNSF (former NP) track falls exactly on the track drawn on the 1883 plat. East of the river the plat draws the track up to ~100 m south of today\'s line, south of a row of blocks that today lies north of the track. Either the plat is schematic there or the line was later realigned - check NP valuation and right-of-way maps (MNHS).',
    sources='PLAT1883; OSM; HAG ch. I', photos='mhs:91737; mhs:95324 (bridge, 1880)')
add(id='np-bridge', name='Northern Pacific bridge (trestle) over the Little Missouri', town='Between', bank='both',
    kind='bridge', built=1880.5, built_text='1880', use='railroad bridge', material='timber', footprint_ft='~300 ft long (HAG)',
    loc='B', form='C', method='plat',
    geom=LineString([along(-45), along(45)]),
    evidence='Where the track crosses the 1883 channel traced from the plat. HAG: the train "rumbled across three hundred feet of trestle." People crossed on foot between the rails at high water (HAG).',
    sources='PLAT1883; HAG ch. I; Bismarck Weekly Tribune 1885-10-16 (an NP bridge west of Medora burned)',
    photos='mhs:91737 (under construction, 1880); mhs:95324; mhs:72459 (Huffman 1886, "Medora from railway bridge"); shsnd:00042-00151')
add(id='ford', name='Ford of the Little Missouri', town='Between', bank='river', kind='landmark', built=1879,
    built_text='in use 1883', use='river crossing', loc='C', form='D', method='relative',
    geom=Point(off(CROSS, north=91.4 * 0.9, east=91.4 * 0.3)),
    evidence='"the ford a hundred yards north of the trestle" (HAG ch. I). Placed 100 yd north of the 1883 crossing.',
    sources='HAG ch. I')

# --- Little Missouri (west bank)
add(id='cantonment', name='Bad Lands Cantonment (abandoned army post)', aka='"the Cantonment"; soldiers\' quarters',
    town='Little Missouri', bank='west', kind='building group', built=1879.86, built_text='Nov 10, 1879 (HM52; HMdb 87804)',
    removed=1887.15, removed_text='part burned early 1887; rest razed or hauled away; hospital moved to Dickinson fall 1888',
    use='army post 1879-83; ranch HQ, resort, homes and church services 1883-86', material='cedar log "stockade style"; hospital frame',
    stories='1', footprint_ft='barracks 200x22; officers\' quarters 124x30; hospital 52x25 + 23x14; storehouse 100x22; laundresses 41x28; guardhouse 25x30; bakery 30x20; blacksmith 18x18; stables 54x38; ice house 30x25; two cellars 18x16',
    loc='B', form='B', method='plat',
    geom=unary_union([rect(plat(x, y), 22, 60, 335) for x, y in [(104,74),(99,82),(113,87),(105,93),(123,92),(117,102),(127,104),(118,112)]]),
    evidence='Eight building symbols drawn on the 1883 plat, labelled "Cantonments," NW of the river crossing. HM52: about 3/4 mile NW of Medora under the bluffs; buildings ranged round a central parade ground (Lang). Symbols are schematic, so individual buildings are not identified.',
    sources='PLAT1883; HM52 pp. 10-11 (building sizes, from post Letters Sent, 1 Jan 1880); TRC-CANT; LANG; NARA RG77 file unit 4522386 (7 building plans); SHSND MAP.032-00111 (1879 reserve map); HAG ch. I-II',
    photos='mhs:91738 (Haynes 1880); shsnd:A2960-00001',
    notes='Dates conflict: established spring 1879 (TRC) vs Nov 10 1879 (HM52, HMdb); abandoned March 24 (TRC) vs March 4, 1883 (HMdb). SHSND surveyed the site with drone and magnetometry in June 2025 (PAC-MAC 2025 paper) - request the results. HAG puts it "a quarter of a mile west" of Maunders\'s shack; the plat puts it ~0.5 mi NW of the crossing.')
add(id='lm-depot', name='Little Missouri depot', aka='"depot" shack', town='Little Missouri', bank='west', kind='building',
    built=1880.5, built_text='1880 (HMdb 87982)', removed=1884.5, removed_text='replaced when NP trains began stopping at Medora (1884); later sold and moved to the HT Ranch',
    use='railroad station; NP Express and Western Union office', material='frame', stories='1',
    loc='C', form='B', method='relative', geom=rect(LM_DEPOT, 20, 40, TRACK_BEARING),
    evidence='Beside the track on the west bank. Fitzgerald\'s shack was "directly to the east, on the brink of the river" (HAG), so the depot was close to the river; placed 150 m NW of the 1883 crossing, near where the 1957 NPS Tour of Medora map marks the site of Little Missouri (west end of the old US 10 bridge). Long side parallel to the track, as in Haynes\'s 1881 photo. Size is a placeholder.',
    sources='HAG ch. I; LANG; HMdb 87982; Dickinson Press 1883-09-22 ("the new depot will soon be completed")',
    photos='mhs:108837 (Haynes "Bad Land City," fall 1881); shsnd:00119-00017; shsnd:2003-P-010-00092b (after its move to the HT Ranch)',
    notes='"Too wide to fit through the railroad bridges," so it was sold rather than moved (HMdb 87982). A "new depot" was being finished in Sept 1883, so there may have been two buildings.')
add(id='pyramid-park-hotel', name='Pyramid Park Hotel', aka='Moore\'s hotel; the loft was "the bull-pen"', town='Little Missouri', bank='west',
    kind='building', built=1880.85, built_text='completed Nov 1880 by Frank Moore & Co. (HM52); "will soon be enlarged" (Bismarck Tribune 1882-10-06)',
    use='hotel', material='frame', stories='2 (loft with 14 beds upstairs, HAG)',
    loc='C', form='B', method='relative', geom=rect(along(135, 38), 30, 50, TRACK_BEARING),
    evidence='"stood immediately north of the tracks" (HAG); T.R. walked "northeastward" to it from the depot (HAG). Haynes\'s 1881 photo shows it beside the depot.',
    sources='HAG ch. I; AUTO ch. IV [P]; LANG; HM52; Bismarck Tribune 1882-10-06, 1883-06-15 (holds 30-40); TRC-CANT; HMdb 154619',
    photos='mhs:108837 (Haynes, fall 1881: two-story frame building with porch); shsnd:00119-00017; npshb:thro10.jpg',
    notes='T.R.\'s first night in the Badlands, Sept 7-8, 1883. Fate unknown. Size is a placeholder until the Haynes photo is studied.')
add(id='lm-roberts-saloon', name='Saloon beside the hotel ("Bill Williams\'s" in Hagedorn)', aka='"Big-Mouthed Bob\'s Bug-Juice Dispensary" (Lang)',
    town='Little Missouri', bank='west', kind='building', built=1880.6, built_text='by 1881', removed=1885.0, removed_text='proprietor moved to Medora (date uncertain)',
    use='saloon', material='frame', stories='1 (HAG)', loc='C', form='D', method='relative', geom=rect(along(160, 38), 20, 40, TRACK_BEARING),
    evidence='"beside it [the hotel] stood the one-story palace of sin" (HAG); "near it stood Big-Mouthed Bob\'s" (LANG).',
    sources='HAG ch. I; LANG',
    notes='Hagedorn says "one, who shall, for the purposes of this story, be known as Bill Williams" - a pseudonym. Lang\'s "Big-Mouthed Bob" and the Roberts & Co. saloon at Medora (burned Jan 1885) suggest the real owner was Robert Roberts. Inference; verify.')
add(id='nelson-store', name="Johnny Nelson's store", town='Little Missouri', bank='west', kind='building', built=1883.0, built_text='by Sept 1883',
    use='store', loc='C', form='D', method='relative', geom=rect(along(150, -30), 20, 36, TRACK_BEARING),
    evidence='"South of the track" (HAG ch. I). Lang: "three or four rough shacks" across the track at the base of "Graveyard Butte."', sources='HAG ch. I; LANG')
add(id='mcgeeney-boarding-house', name="Mrs. McGeeney's boarding house", town='Little Missouri', bank='west', kind='building', built=1883.0, built_text='by Sept 1883',
    use='boarding house', loc='C', form='D', method='relative', geom=rect(along(128, -30), 20, 30, TRACK_BEARING),
    evidence='"next door" to Nelson\'s store; within fifty feet of Mrs. Fitzgerald (HAG ch. I, III).', sources='HAG ch. I and III')
add(id='fitzgerald-shack', name="Section foreman Fitzgerald's shack", town='Little Missouri', bank='west', kind='building', built=1881, built_text='by Sept 1883',
    use='dwelling', loc='C', form='D', method='relative', geom=rect(along(105, -28), 16, 20, TRACK_BEARING),
    evidence='"Directly to the east, on the brink of the river" (HAG). Within 50 ft of McGeeney\'s, so placed south of the track.', sources='HAG ch. I and III')
add(id='maunders-shack', name="Jake Maunders's shack", town='Little Missouri', bank='west', kind='building', built=1881, built_text='by Sept 1883',
    use='dwelling', loc='C', form='D', method='relative', geom=rect(along(105, 28), 16, 20, TRACK_BEARING),
    evidence='"At a corresponding place on the other side of the track" from Fitzgerald (HAG ch. I).', sources='HAG ch. I')
add(id='section-house', name='NP section house and water tank', town='Little Missouri', bank='west', kind='building group', built=1880.5, built_text='1880',
    use='railroad', loc='D', form='D', method='schematic', geom=Point(along(370, -20)),
    evidence='"A little further along the track to the westward, stood a section house and water tank" (LANG). The 1879 Cantonment reserve map ties its bounds to the NP water tank (SHSND MAP.032-00111) - that map can fix this point.',
    sources='LANG; HMdb 87982; SHSND MAP.032-00111')
add(id='malloy-hotel', name="Peter Malloy's hotel (the Western House?)", town='Little Missouri', bank='west', kind='building', built=1883.75,
    built_text='contract to James Collister Aug 1883; C. E. Cook carpenter (Dickinson Press)', use='hotel', loc='D', form='D', method='schematic',
    geom=Point(along(190, 60)),
    evidence='"James Collister has the contract for erecting a fine hotel for Peter Malloy at Little Missouri" (Dickinson Press 1883-08-18). Location not given.',
    sources='Dickinson Press 1883-08-18, 09-15, 09-22; Bad Lands Cow Boy 1885-07-16',
    notes='Possibly the "Western House" Mrs. Malloy left in July 1885 for a new building on Main Street, Medora. The "Malloy building at Medora" was torn down and moved to Dickinson in June 1887 (Dickinson Press 1887-06-18). HAG calls the owner "P. McGeeney" when quoting the same 1883 note - check.')

# --- Chateau and west-bank de Mores property
CH = osm('Chateau de Mores')
add(id='chateau-de-mores', name='Chateau de Mores', aka='the Marquis\'s house', town='Chateau', bank='west', kind='building',
    built=1883.6, built_text='1883 (ready "by August" per BROOKS57; SHSND says ready for Medora in spring 1884)',
    use='summer residence', material='frame; milled siding painted "French grey," red shingle roof, red shutters', stories='2, with one-story ell on north',
    footprint_ft='26 rooms; OSM outline ~5,550 sq ft incl. veranda', loc='A', form='A', method='osm', geom=CH,
    evidence='Standing on its original site on the second terrace above the river, about half a mile WSW of Medora (NRHP).',
    sources='NRHP 75001299; SHSND Chateau history; SAH ND-01-BI8; PLAT1883 ("Marquis de Mores")',
    photos='shsnd:00042-00152; shsnd:00042-00158 (Ingersoll 1883); shsnd:00042-00157 (1884); shsnd:00042-00196/-00197 (1886); mhs:72389; mhs:72403 (Huffman 1886); houghton:3013538; shsnd:1972.91 (Medora de Mores watercolor)',
    notes='Drone photogrammetry model of the Chateau today (Sketchfab, 2023) - cleared for Library use.')
add(id='chateau-outbuildings', name='Chateau outbuildings (coachman\'s house, carriage shed, stable, corral; woodshed)', town='Chateau', bank='west',
    kind='building group', built=1883.6, built_text='1883-84', use='service buildings', material='frame',
    loc='C', form='D', method='relative', geom=Point(off((CH.centroid.x, CH.centroid.y), east=70, north=-60)),
    evidence='Woodshed north of the house; "to the south and further east, on the next terrace towards the river," the coachman\'s house, carriage shed, stable and corral (NRHP). Ingersoll\'s 1883 photo shows the carriage house below the Chateau.',
    sources='NRHP 75001299; shsnd:00042-00152', photos='shsnd:00042-00152; shsnd:00042-00157; shsnd:1972.91')
add(id='vegetable-garden', name='Vegetable garden and irrigation ditch', town='Chateau', bank='west', kind='landmark', built=1883.4, built_text='1883',
    use='garden', loc='B', form='C', method='plat',
    geom=Polygon([plat(70, 420), plat(160, 418), plat(160, 456), plat(70, 458), plat(70, 420)]),
    evidence='Drawn and labelled "Vegetable Garden" with an irrigation ditch on the 1883 plat, south of the Chateau.', sources='PLAT1883')
add(id='coal-mine', name='Coal mine', town='Little Missouri', bank='west', kind='landmark', built=1883.0, built_text='by 1883', use='coal mine',
    loc='B', form='D', method='plat', geom=Point(plat(141, 247)), evidence='Labelled "Coal Mine" on the 1883 plat.', sources='PLAT1883')

# --- Medora (east bank)
SLAUGHTER = (-103.527793, 46.916084)   # OSM "Medora Slaughterhouse" ruins node (chimney)
add(id='demores-packing-plant', name='De Mores packing plant (abattoir)', aka='Northern Pacific Refrigerator Car Co. slaughter house',
    town='Medora', bank='east', kind='building group', built=1883.6, built_text='first plant being finished Sept 1883 and running by Oct 1883 (15-25 head/day; Dickinson Press 1883-09-22 already describes it); second, larger plant finished spring 1885 (opened June 1, 1885 per HAG)',
    removed=1907.21, removed_text='closed Nov 1886; used for storage; burned March 17, 1907; chimney stands',
    use='slaughterhouse, cold storage, ice houses, loading platform, holding pens', material='frame; brick chimney; sandstone and brick foundations',
    footprint_ft='abattoir 105x180; power house 30x40; cooper shop 25x30; fertilizer room 30x38; three ice houses 40x100 (NRHP). Dec 1884: main refrigerator building 40x130 (Cow Boy)',
    loc='A', form='B', method='osm', geom=Point(SLAUGHTER),
    evidence='Chimney and foundations survive in Chimney Park (SHSND), at the "Slaughter House" drawn on the 1883 plat beside the track. Building footprints not yet laid out; the 1956 De Haven site plan in BROOKS57 p. 25 shows the abattoir site, a separate packing-house foundation and the holding pens.',
    sources='NRHP 75001300; PLAT1883; HAG; BROOKS57; HMdb 87796, 87799; Bad Lands Cow Boy 1884-12-04, 1885-01-01, 1885-04-16; Dickinson Press 1883-09-22; St. Paul Daily Globe 1885-06-05',
    photos='shsnd:00042-00153; shsnd:00042-00150; shsnd:00042-00188 (Ingersoll 1883); shsnd:00042-00074/-00075 (1885); mhs:72460 (Huffman 1886); houghton:3013535; houghton:3013543 (ruins c.1919)',
    notes='Capacity varies by source: 100 head/day (HAG), 150 (NRHP), 200 (Dickinson Press 1883 claim). Spring 1887 flood surrounded the slaughter houses (Bismarck Weekly Tribune 1887-03-18). Drone photogrammetry model of Chimney Park today (Sketchfab, 2023) - cleared for Library use.')
DEPOT_M = (-103.5262926, 46.913509)    # Medora Convenience Store (OSM) - HMdb 87986 puts the depot near it
add(id='medora-depot', name='Northern Pacific depot, Medora', town='Medora', bank='east', kind='building', built=1884.3, built_text='1884 (NP trains began stopping at Medora)',
    removed=1925.5, removed_text='burned 1925', use='railroad station', material='frame', stories='1 (verify)', loc='B', form='C', method='address',
    geom=rect(off(DEPOT_M, north=8), 24, 60, (TRACK_BEARING + 90) % 180),
    evidence='"near today\'s Medora Convenience Store," set perpendicular to the tracks with the office and agent\'s window on the track side (HMdb 87986). Size is a placeholder.',
    sources='HMdb 87986; Prairie Public 2025-09-18', photos='mhs:72461 (Huffman 1886); shsnd:00042-00151; shsnd:00042-00194; shsnd:00042-00195; shsnd:00098-00025 (1913)')
add(id='hotel-de-mores', name='Hotel de Mores (Northern Pacific Hotel from 1885)', town='Medora', bank='east', kind='building', built=1883.8,
    built_text='1883, as a boarding house for up to 100 (HMdb); in use by Feb 1884 (Cow Boy); brick-veneered and reopened June 1, 1885',
    removed=1897.7, removed_text='burned Sept 13, 1897', use='hotel, with livery stable and bar', material='frame, brick veneer from 1885 (Medora brick)', stories='2',
    footprint_ft='100 x 25', loc='C', form='B', method='relative', geom=rect(off(DEPOT_M, north=55), 25, 100, 90),
    evidence='"located north of the railroad depot and faced north" (HMdb 88037). Placed north of the depot site, long side east-west.',
    sources='HMdb 88037; Bad Lands Cow Boy 1884-02-14, 1884-04-17; HAG (Mandan Pioneer: "a large hotel")',
    photos='shsnd:00042-00076; shsnd:00042-00086 (1885); houghton:3013534; houghton:3013529 (interior); houghton:3013559 (1895); shsnd:00042-00149 (1883?, wood-sided)',
    notes='SHSND 00042-00149 shows a wood-sided hotel in snow in 1883 - consistent with brick veneer added in 1885.')
add(id='roberts-hall', name='Roberts Hall (billiard hall and theatre)', aka='possibly Hagedorn\'s two-story "Bill Williams\'s" saloon and hall; possibly the 1903 "town hall"',
    town='Medora', bank='east', kind='building', built=1884.45, built_text='April-June 1884; builder Thomas McClung (HMdb)', removed=1923.5, removed_text='dismantled 1923',
    use='bar and club rooms below; hall with stage, two dressing rooms above; later county offices', material='frame; drop siding, board paper, plastered inside',
    stories='2 (each 12 ft clear; over 26 ft high)', footprint_ft='24 x 75', loc='C', form='A', method='address',
    geom=rect((block('17').centroid.x, block('17').centroid.y), 24, 75, 0),
    evidence='"located on lot 7, block 17" (Cow Boy 1884-06-26). Placed at today\'s Block 17, assuming the modern block numbers are the 1883 plat\'s (true for Block 15). HMdb puts it near the Hotel de Mores in full view of the railroad - conflicts with this placement; check the plat\'s block numbers on a high-resolution scan.',
    sources='Bad Lands Cow Boy 1884-05-01, 1884-06-26; HMdb 88016; HAG (Medora chapter); Dickinson Press 1885-01-17',
    photos='houghton:3013539 ("Bill Williams\' saloon," 1919)',
    notes='HAG\'s "Bill Williams" is a pseudonym. Roberts & Co.\'s saloon at Medora burned Jan 1885 (Dickinson Press) - HAG says the first saloon "near Joe\'s store" burned before the move into the two-story building. Treat the identification as a strong inference to verify.')
add(id='metropolitan-hotel', name='Metropolitan Hotel (Rough Riders Hotel from 1901-03)', town='Medora', bank='east', kind='building', built=1885.1,
    built_text='begun Nov 1884 by George Fitzgerald; "ready for occupancy" Feb 12, 1885 (Cow Boy)', removed=1963.5,
    removed_text='closed 1886, reopened 1901; disassembled and replaced by a replica in 1963 (HMdb 87499)',
    use='hotel: bar room, office, dining room, wash and baggage rooms below; 16 sleeping rooms and parlor above', material='frame, drop siding (brick veneer planned, never added)',
    stories='2', footprint_ft='35 x 80', loc='B', form='A', method='osm',
    geom=rect((osm('Rough Riders Hotel').centroid.x, osm('Rough Riders Hotel').centroid.y), 35, 80, 0),
    evidence='Same site as today\'s Rough Riders Hotel; the original 35x80 block is placed at the centre of the modern (much larger) complex until the 1963 photos fix its exact spot.',
    sources='HMdb 87499; Bad Lands Cow Boy 1885-02-12, 1885-07-02; SAH ND-01-BI1; HAG plate caption; BROOKS57',
    photos='houghton:3013530; houghton:3013598 (1919); trc:o277182; trc:o277198; trc:o277180 (1963 before/during demolition)',
    notes='Date conflict: 1884 (SAH) vs 1885 (NPS handbook); the Cow Boy shows it opened Feb 1885. Renaming: 1901 (HMdb) vs 1903 (SAH).')
add(id='ferris-store', name="Joe Ferris's store", aka='Ferris Inn / Joe Ferris General Store', town='Medora', bank='east', kind='building', built=1885.59,
    built_text='begun 1885; grand opening Aug 4, 1885 (medora.com)', use='general store; family quarters upstairs; T.R. kept a room (SE corner upstairs)',
    material='frame', stories='2', footprint_ft='25 x 75 (marker); OSM outline 25 x 58', loc='A', form='A', method='osm', geom=osm('Joe Ferris General Store'),
    evidence='Standing (rebuilt to the original plan in the 1960s per KFYR 2025). A feed stable stood behind it (HMdb 88062).',
    sources='HMdb 88062; HAG; NPSHB; medora.com; KFYR-TV 2025-06-19', photos='houghton:3013537; houghton:3013655 (c.1919-20); trc:o292512 (1890s, marked X); trc:o277205 (1964)',
    notes='Nearly burned in the fire of early 1887 (Eaton to Sewall, Feb 26, 1887).')
add(id='st-marys-church', name="St. Mary's Catholic Church", town='Medora', bank='east', kind='building', built=1884.84,
    built_text='contract July 1884 (Peter Book); cornerstone Sept 20, 1884 (stone dated Sept 15); blessed Nov 2, 1884',
    use='church', material='yellow brick, common bond; wood-shingled gable roof; open wooden belfry with pyramidal roof', stories='1', footprint_ft='24 x 50',
    loc='A', form='A', method='osm', geom=osm("St. Mary's Catholic Church"),
    evidence='Standing on its original site at Fourth Street and Third Avenue; facade faces west (NRHP photos).',
    sources='NRHP 77001017; Bad Lands Cow Boy 1884-09-25; HMdb 88001', photos='shsnd:00042-00077 (c.1886); shsnd:00042-00124 (1893)',
    notes='Rear chimney (1941), bell (1946) and interior changes are later.')
add(id='von-hoffman-house', name='Von Hoffman House', aka='Medora Doll House', town='Medora', bank='east', kind='building', built=1884.75,
    built_text='commissioned Aug 1884; Peter Book', use='residence of the Marquise\'s parents', material='common-bond brick; hip-gabled wood-shingle roof; front porch',
    stories='1.5', footprint_ft='~38 x 48', loc='A', form='A', method='osm', geom=osm('Von Hoffman House'),
    evidence='Lots 7-10, Block 15, Original Plat, at Broadway and Fifth Street (NRHP) - matches today\'s Block 15 parcels exactly. This is the link that ties the plat to today\'s grid.',
    sources='NRHP 77001018', photos='shsnd:00042-00071 (1885 bird\'s-eye, in front); shsnd:00042-00123 (1893); shsnd:00610-11')
add(id='courthouse-cottages', name='Brick cottages (core of the old Billings County courthouse)', town='Medora', bank='east', kind='building', built=1884.73,
    built_text='"rapidly nearing completion" Sept 25, 1884 (Cow Boy, per BROOKS57)', use='de Mores rental houses; later courthouse and jail',
    material='brick wings; clapboard core', stories='1', loc='B', form='C', method='osm', geom=osm('Billings County Courthouse Museum'),
    evidence='Lots 13-18, Block 18 (NRHP 77001016). BROOKS57 argues the brick wings are 1884 Medora-brick cottages; NRHP says the wings were added later. Conflict open.',
    sources='NRHP 77001016; BROOKS57; HMdb 88030; Bad Lands Cow Boy 1884-09-25', photos='dh:OFF-367A (1883-93?)')
J = corner('3rd Avenue', '3rd Street')
add(id='jorgens-drug-store', name="Dr. H. M. Jorgens's drug store", town='Medora', bank='east', kind='building', built=1884.8,
    built_text='store on the corner by Oct 1884; new 21x32 building with full glass front April 1885', use='drug store', material='frame', footprint_ft='21 x 32 (1885)',
    loc='B', form='C', method='address', geom=rect(off(J, east=-12, north=12), 21, 32, 0),
    evidence='"corner of Third Ave and Third St" (Cow Boy 1884); a drug store on the NW corner of 3rd Street (HMdb 88066). Placed on the NW corner of today\'s 3rd Ave and 3rd St.',
    sources='Bad Lands Cow Boy 1884-10-16, 1885-04-16; HMdb 88066')
add(id='fisher-stores', name="J. C. Fisher's two stores", town='Medora', bank='east', kind='building', built=1884.85, built_text='being built Nov 1884',
    use='stores', loc='C', form='D', method='address', geom=Point(off(corner('3rd Avenue', 'Main Street'), east=25, north=-14)),
    evidence='"two stores on Third Ave near Main St" (Cow Boy 1884-11-06).', sources='Bad Lands Cow Boy 1884-11-06')
FS = osm('Joe Ferris General Store')
add(id='roller-rink', name="Fisher's roller rink and shooting gallery", town='Medora', bank='east', kind='building', built=1885.2,
    built_text='planned Feb 1885; opened with a ball March 11, 1885', use='roller rink; church services held there 1885', footprint_ft='30 x 80 (planned)',
    loc='C', form='C', method='relative', geom=rect(off((FS.centroid.x, FS.centroid.y), east=-16), 30, 80, 0),
    evidence='"next to Joe\'s store, opposite the office of the Bad Lands Cowboy" (HAG). Side of the store not stated; placed west of it.',
    sources='HAG (Medora chapter); Bad Lands Cow Boy 1885-02-12, 1885-04-16; Dickinson Press 1885-03-14')
add(id='cowboy-office', name='Bad Lands Cow Boy office', town='Medora', bank='east', kind='building', built=1884.1,
    built_text='paper began Feb 1884 (masthead "Little Missouri, Medora P.O."); "Published in Medora" from Nov 1885', removed=1887.03, removed_text='destroyed by fire Jan 12, 1887 (HMdb 88045)',
    use='newspaper office', stories='1 (photo)', loc='C', form='B', method='relative', geom=rect(off((FS.centroid.x, FS.centroid.y), north=-30), 20, 30, 0),
    evidence='Opposite Fisher\'s rink and Joe Ferris\'s store (HAG). Placed across Third Avenue.',
    sources='HAG; LOC sn84024777; HMdb 88045; Eaton to Sewall 1887-02-26 (TRC o292533)', photos='houghton:3013536; npshb:thro15.jpg')
add(id='paddock-livery', name="Paddock's livery stable (Medora)", town='Medora', bank='east', kind='building', built=1885.1, built_text='described Feb 1885',
    removed=1887.45, removed_text='Paddock\'s buildings shipped to Dickinson by flat car, June 1887', use='livery stable', material='frame; drop siding; battlement front; 2-in floor',
    footprint_ft='88 x 50', loc='B', form='B', method='address',
    geom=rect(off(((J[0] + corner('3rd Street', 'Broadway')[0]) / 2, (J[1] + corner('3rd Street', 'Broadway')[1]) / 2), east=-22), 50, 88, 0),
    evidence='"on Third St between Third Ave and Broadway" (Cow Boy 1885-02-26). Side of the street not stated; placed west side.',
    sources='Bad Lands Cow Boy 1885-02-26; Dickinson Press 1887-06-04; HAG')
add(id='freight-house', name='Black Hills freight house (Medora & Black Hills Forwarding Co.)', town='Medora', bank='east', kind='building', built=1884.6,
    built_text='sills laid July 1884; nearly finished Aug 1884', use='freight warehouse for the Deadwood stage and freight line', footprint_ft='240 x 42',
    loc='D', form='B', method='schematic', geom=rect(off(DEPOT_M, east=170, north=-55), 42, 240, TRACK_BEARING),
    evidence='"on the south side of the track near the bluff" (Cow Boy 1884-05-01). Exact spot unknown; placed south of the track east of the depot.',
    sources='Bad Lands Cow Boy 1884-05-01, 1884-07-17; Dickinson Press 1884-07-12; Bismarck Weekly Tribune 1884-08-08; HAG ("well-built, substantial")',
    notes='BROOKS57: in 1957 one of the Medora Stage & Forwarding Co. buildings still stood on its original site - read BROOKS57 to place it.')
add(id='brickyard', name="Peter Book's brickyard", town='Medora', bank='east', kind='landmark', built=1884.4, built_text='opened spring 1884; first kiln fired May 21, 1884',
    use='brickworks (10,000+ bricks a day; dark red brick)', loc='C', form='D', method='relative',
    geom=Point(off(J, north=-1450, east=-150)),
    evidence='About 0.9 mile south of Medora by the river road, east bank; circular kiln base visible in 1957 at the town dump (BROOKS57). Placed 0.9 mi south of town centre.',
    sources='BROOKS57; Bad Lands Cow Boy 1884-04-03, 1884-05-08, 1884-05-22; NRHP 77001018')

# ================================================================ 2026-10-15 evening: Cow Boy full pass, BROOKS57, 1957 NPS maps
def upd(fid, **k):
    """Override or extend fields of an existing feature. Text values starting with '+' are appended."""
    for f in F:
        if f['id'] == fid:
            for key, val in k.items():
                if isinstance(val, str) and val.startswith('+'):
                    f[key] = (f.get(key) or '') + (' ' if f.get(key) else '') + val[1:]
                else:
                    f[key] = val
            return
    raise KeyError(fid)

upd('pyramid-park-hotel', footprint_ft='not recorded; Haynes 1881 photo shows a 2-story front-gabled main block with a 2-story gabled block attached behind (L or T plan)',
    notes='+Still operating 1884-85: second floor cut into rooms (Cow Boy 1884-02-28); reopened by Boyd & Alexander Oct 1884; Arch Boyd early 1885; J. B. Walker from March 1885 (Cow Boy). Lang calls it "recently erected" in April 1883 - perhaps the 1882-83 enlargement. In 1883 Moore also let rooms in the old Cantonment officers\' quarters (Mandan Daily Pioneer 1883-07-17, in HM52).',
    sources='+; Bad Lands Cow Boy 1884-02-28, 1884-10, 1885-03; HM52 pp. 20, 25-26; BROOKS57 Fig. 3')
upd('lm-roberts-saloon', name='Pennell & Roberts\'s saloon and billiard hall, Little Missouri ("Bill Williams\'s" in Hagedorn)', removed=1884.51,
    removed_text='Roberts & Co. moved the billiard hall to Roberts Hall in Medora, July 3, 1884 (Cow Boy)',
    notes='+Pennell & Roberts\'s hall at Little Missouri hosted the stockmen\'s meetings of Feb and Apr 1884 (Cow Boy).',
    sources='+; Bad Lands Cow Boy 1884-02, 1884-04, 1884-07-03')
upd('nelson-store', notes='Joe Ferris\'s dry-goods store opened in "the former John Nelson building" (Cow Boy 1884-03-27), apparently on the west side; Ferris added a large addition (June 1884) and a warehouse (Oct 1884), then moved to his new Medora store in Aug 1885.',
    removed=1885.6, removed_text='Ferris left for Medora, Aug 1885', sources='+; Bad Lands Cow Boy 1884-03-27, 1884-06-26, 1884-10-02')
upd('cantonment', notes='+Cow Boy 1884-85: the buildings housed the Hyde, Hannigan, Butler, McGregor and Barker families and contractor J. A. Freeze; attached and sold by the sheriff July-Oct 1885; sold at sheriff\'s sale to Beckett & Foote of Dickinson 1888-89 (Dickinson Press, in HM52). BROOKS57: state highway gravel operations "destroyed the site" before 1952. A sutler\'s store (Frank Moore) stood on the parade ground: "long and low," with an L used as a bar and sleeping quarters behind (Huidekoper, in HM52).')
upd('chateau-de-mores', notes='+Color conflict: Cow Boy 1885-11-26 describes "green sides and red roof"; the 1974 NRHP gives "French grey" siding with red roof and shutters (the 1930s restoration color). Windmill added 1884; Peter Book built a cellar for the heating plant in 1885 (Cow Boy).',
    sources='+; Bad Lands Cow Boy 1884-06, 1885-03, 1885-11-26', model='cd022732d9544bcca665760204975d53')
upd('demores-packing-plant', name='De Mores packing plant: chimney', built=1885.46,
    built_text='brick smokestack built by Peter Book, finished June 18, 1885 (Cow Boy); the plant itself: first abattoir Oct 1883, new plant opened June 2, 1885',
    footprint_ft='chimney only; see the other packing-plant features',
    notes='+BROOKS57: the new plant was finished about mid-April 1885 "except for the smoke stack," so an 1883-84 view should not show the chimney. Capacity 900 head a week (Cow Boy).',
    sources='+; Bad Lands Cow Boy 1885-03-26, 1885-06-18; BROOKS57 pp. 4, 17-19 and Fig. 6', model='889a6ec71b514d2cb59c1423647a6fd3')
upd('hotel-de-mores', geom=rect((-103.5262, 46.91395), 25, 100, 0),
    evidence='"a few steps from the depot" (Fitzgerald\'s ad, Cow Boy 1884); the race track ran to "Main street opposite the Northern Pacific hotel" (Cow Boy), so it fronted Main Street. HMdb 88037: north of the depot, faced north. Placed on Main Street just north of the depot site, long side along the street. Orientation conflicts with HMdb - check the 1885 overview photos.',
    notes='+1885 rebuild (Cow Boy, Feb-May 1885): new foundations, brick veneer by Peter Book, porches on the west and south sides, kitchen and laundry additions on the north side; lessee Arch Boyd; renamed the Northern Pacific Hotel June 4, 1885. Earlier managed by G. W. Fitzgerald. Arson attempt Oct 23, 1884.',
    sources='+; Bad Lands Cow Boy 1884-10-23, 1885-02 to 1885-06-04')
upd('medora-depot', notes='"A few steps" from the Hotel de Mores (Cow Boy). Used for church services and Sunday school. The perpendicular orientation (HMdb) is unusual - the Little Missouri depot ran parallel to the track - so check it against Huffman\'s 1886 photo (MHS 72461).',
    sources='+; Bad Lands Cow Boy 1884-08-28, 1885-01-08, 1885-07-23')
upd('metropolitan-hotel', built_text='lumber arrived Dec 11, 1884; "ready for occupancy" Feb 12, 1885 (Cow Boy)',
    notes='+Brick veneer and a long front porch were planned. Landlord J. B. Walker from Oct 15, 1885. The 1957 photo (BROOKS57) shows about 10 by 4 window bays, consistent with 35x80. Leave the later 1-story end wing and asphalt siding out of an 1885 model.')
upd('ferris-store', built=1885.62, built_text='cellar 25x60 and store 25x75 begun June 1885 on his Main Street lot; opened Aug 13, 1885 with the second story unfinished (Cow Boy); medora.com gives Aug 4',
    notes='+"Best store building in Medora" (Cow Boy). BROOKS57: exterior stair on the side wall to a second-floor door; T.R. stayed in the southeast corner room upstairs. Feed stable with Fisher behind the grocery (Nov 1885).',
    sources='+; Bad Lands Cow Boy 1885-06-18, 1885-07-02, 1885-08-13, 1885-11-19; BROOKS57 pp. 22-23')
upd('roller-rink', geom=rect(off((FS.centroid.x, FS.centroid.y), north=24), 30, 80, 90),
    evidence='"next to Joe\'s store, opposite the office of the Bad Lands Cowboy" (HAG). The Cow Boy\'s 1886 fire warning runs along Main Street from Mrs. Malloy\'s hotel to Bob Roberts\'s saloon (which moved into "the old skating rink" in Aug 1885), so both were on the Ferris block. Placed north of the store on Main Street.',
    notes='Built by Jim Butler; opened about March 11, 1885; post office briefly inside; church services held there. From Aug 1885 it was Bob Roberts\'s saloon - ceiled, papered, painted, glass front (Cow Boy).',
    sources='+; Bad Lands Cow Boy 1885-08, 1886-03-25')
upd('cowboy-office', geom=rect(off((FS.centroid.x, FS.centroid.y), east=-48, north=20), 20, 30, 0),
    evidence='Opposite Fisher\'s rink and Joe Ferris\'s store (HAG) - placed across Main Street. A saloon stood "next door to the Cow Boy office" and a frame building to rent south of it (Cow Boy 1884-04-24).',
    notes='+Painted April 1884 (Cow Boy).')
upd('jorgens-drug-store', evidence='Opened "on the corner of Third avenue and Third street" in Nov 1884 (Cow Boy); HMdb 88066 puts a drug store on the NW corner of 3rd Street. Placed on the NW corner of today\'s 3rd Ave and 3rd St. The new 21x32 building of April 1885 has no stated location.',
    notes='Earlier (Sept 1884) a temporary building moved "next to the company\'s store." The old "historical shack" was later rented to a clothing store (Cow Boy).')
upd('fisher-stores', notes='First planned May 1884 with Van Driesche as a three-store-room building. Tenants: Charles Cook, confectioner, and J. D. Garver, tinsmith (Nov 1884); later the Willard & Keeler meat market and Wells Fargo office (Dec 1885).',
    sources='+; Bad Lands Cow Boy 1884-05-15, 1884-11-13, 1884-11-20, 1885-12')
upd('paddock-livery', notes='Built by Jim Butler, finished April 16, 1885; size to be doubled (April 30). Livery office was the 1886 polling place. Paddock also moved Fitzgerald\'s old west-side dwelling next to his barn as Fred Banan\'s barber shop (May 1885).',
    sources='+; Bad Lands Cow Boy 1885-04-16, 1885-04-30, 1885-05-14')
upd('courthouse-cottages', built=1884.85, built_text='two brick cottages for the company, finished and accepted Nov 6, 1884 (Cow Boy)',
    notes='Lived in by the Hannigans and the Fortiers. Hipped roofs like the Von Hoffman House (BROOKS57). A central frame addition in the early 1900s made them the courthouse wings.',
    sources='+; Bad Lands Cow Boy 1884-11-06; BROOKS57 pp. 29-32')
upd('freight-house', footprint_ft='240 x 42 (planned 100 x 32 in March 1884)',
    evidence='"on the south side of the track near the bluff... as near as possible to the butte," built "across Quick creek" (Cow Boy 1884-05-01, 05-08, 1886-05-13). Quick creek not yet identified; placed south of the track east of the depot.',
    notes='Held 225 carloads; west end split into three rooms with a platform and derrick (Aug 1884); J. C. Fisher\'s office partitioned off inside (Sept 1884); underpinned May 1886.')
upd('brickyard', evidence='"south of town where the Deadwood trail separates from the river" (Cow Boy 1884-04-24); ".9 of a mile south by river road from U.S. Highway 10 at Medora on the east bank... Section 34" (BROOKS57 p. 33). Placed in Sec. 34 about 0.9 mi south.',
    notes='Book patented a "lignite kiln" (1885). Book\'s house near the kiln, to be brick-veneered (1885); lime burned just west of the kiln (1885); a side-track along the bluff to the yard was planned (1885). New stockyards were built at "the brick-kiln butte" in Oct 1885 (Cow Boy).')

CHIM = SLAUGHTER
FT = 0.3048
def at(bearing_deg, dist_ft):
    b = math.radians(bearing_deg)
    return off(CHIM, east=dist_ft * FT * math.sin(b), north=dist_ft * FT * math.cos(b))
PP_SRC = 'NPS "Tour of Medora" map, Aug 1957 (NMP-TR-7008, in NPSHB 1962 p. 54, 0-600 ft scale); 1956 site plan NMP-TR 3002-A (BROOKS57 Fig. 6); NRHP 75001300; Bad Lands Cow Boy 1884-12-04'
add(id='pp-foundation', name='Packing plant: main packing-house foundation', town='Medora', bank='east', kind='building', built=1885.3,
    built_text='new plant, spring 1885', removed=1907.21, removed_text='burned March 17, 1907; foundation remains',
    use='slaughter and packing house', material='heavy timber frame on sandstone and brick foundations', footprint_ft='~110-130 x 14-24 as drawn in 1956-57 (foundation remnant); NRHP gives the abattoir as 105 x 180',
    loc='C', form='C', method='plat', geom=rect(at(155, 110), 20, 120, 90),
    evidence='Long east-west foundation drawn about 100-125 ft south-southeast of the chimney on both 1950s NPS plans; scaled from the 1957 Tour map.',
    sources=PP_SRC, photos='mhs:72460 (Huffman 1886); shsnd:00042-00074', model='889a6ec71b514d2cb59c1423647a6fd3')
add(id='pp-ice-house', name='Packing plant: ice house', town='Medora', bank='east', kind='building', built=1884.9,
    built_text='company ice houses held 4,000 tons by Dec 1884, about 10,000 tons by Jan 1886 (Cow Boy)', removed=1907.21, removed_text='burned 1907 (inferred)',
    use='ice storage', material='frame; shingled roof (Cow Boy)', footprint_ft='~107 x 43 as drawn in 1957; NRHP: three ice houses 40 x 100',
    loc='C', form='C', method='plat', geom=rect(at(247, 210), 43, 107, 90),
    evidence='Dashed "ICE HOUSE" outline about 210 ft west-southwest of the chimney on the 1957 Tour map. NRHP says three ice houses adjoined the plant; only one is drawn.',
    sources=PP_SRC + '; Bad Lands Cow Boy 1884-12, 1886-01')
add(id='pp-east-building', name='Packing plant: building east of the chimney (unidentified)', town='Medora', bank='east', kind='building', built=1885.3,
    built_text='part of the 1885 plant (inferred)', removed=1907.21, removed_text='burned 1907 (inferred)', use='unknown - perhaps refrigerator or cooling building',
    footprint_ft='~100 x 95 as drawn in 1957', loc='C', form='D', method='plat', geom=rect(at(90, 195), 95, 100, 0),
    evidence='Unlabelled dashed rectangle about 195 ft east of the chimney on the 1957 Tour map. Cow Boy (Dec 1884): main refrigerator building 40x130, corridor about 36x180, passage 18x80.',
    sources=PP_SRC)
add(id='pp-holding-pens', name='Packing plant: holding pens', town='Medora', bank='east', kind='landmark', built=1883.8,
    built_text='1883-86', removed=1887.0, removed_text='plant closed Nov 1886', use='cattle pens', material='timber fences', footprint_ft='~220 ft wide, 4-5 pens',
    loc='C', form='C', method='plat', geom=rect(at(45, 840), 160, 220, 0),
    evidence='Dash-dot enclosure divided into 4-5 pens about 840 ft northeast of the chimney on the 1957 Tour map and 1956 site plan.',
    sources=PP_SRC)
add(id='river-dam', name="The Marquis's dam (ice pond)", town='Between', bank='river', kind='landmark', built=1884.35,
    built_text='built May 1884 just below the railroad bridge; rebuilt with flood-gates Oct 1885', use='ice harvesting; protected the slaughter house',
    loc='C', form='D', method='relative', geom=Point(off(CROSS, north=60, east=12)),
    evidence='"below the railroad bridge" (Cow Boy 1884-05-08); the river flows north, so below = just north of the bridge. Huffman\'s 1886 "Packing House" shows a pond in front of the plant.',
    sources='Bad Lands Cow Boy 1884-05-08, 1885-10-22; HAG', photos='mhs:72460')
MAIN_N = (FS.centroid.x, FS.centroid.y)
add(id='malloy-medora', name="Mrs. Malloy's hotel (Medora)", town='Medora', bank='east', kind='building', built=1885.54,
    built_text='built on one of Joe Ferris\'s lots on Main Street; Mrs. Malloy moved in July 15, 1885', removed=1887.46,
    removed_text='"the Malloy building at Medora" torn down and moved to Dickinson, June 1887', use='hotel',
    loc='C', form='D', method='relative', geom=rect(off(MAIN_N, north=62), 24, 50, 90),
    evidence='On Main Street on a Ferris lot (Cow Boy 1885-07-16). The 1886 fire warning ran "between Mrs. Malloy\'s hotel and Bob Roberts\' saloon," so it is placed at the other end of the Ferris block.',
    sources='Bad Lands Cow Boy 1885-07-16, 1886-03-25, 1886-10; Dickinson Press 1887-06-18', notes='Taken over by Arch Boyd Oct 1886.')
K9 = [f for f in PAR['features'] if f['properties']['Block'] == '9' and f['properties']['Lot'] == '13-18']
if K9:
    add(id='kiefer-house', name="John Kiefer's house", town='Medora', bank='east', kind='building', built=1885.45, built_text='built about June 1885 on Third Avenue',
        use='residence', loc='C', form='D', method='address', geom=shape(K9[0]['geometry']).centroid,
        evidence='Lots 13-14, Block 9, foreclosed 1886 (Cow Boy); house on Third Avenue (Cow Boy 1885-06). Placed on today\'s Block 9 lots 13-18 parcel.',
        sources='Bad Lands Cow Boy 1885-06, 1886')
add(id='pioneer-hotel', name='Pioneer Hotel, Little Missouri', town='Little Missouri', bank='west', kind='building', built=1884.0, built_text='advertised 1884',
    use='hotel', loc='D', form='D', method='schematic', geom=Point(along(175, -55)),
    evidence='"close to the depot" (Cow Boy ad, 1884). Placeholder near the depot.', sources='Bad Lands Cow Boy 1884')
add(id='tiser-house', name='Tiser House ("only original building of the town of Little Missouri")', town='Little Missouri', bank='west', kind='building',
    built=1882.0, built_text='dated by old-timers to 1881-86 (BROOKS57)', use='dwelling', material='frame', loc='D', form='D', method='schematic',
    geom=Point(along(250, 60)),
    evidence='"about .1 of a mile west of the Medora bridge" in 1957 (BROOKS57 p. 32). Placed roughly 0.1 mi west of the river on the north side; the 1957 bridge position needs fixing from the 1957-62 aerials.',
    sources='BROOKS57 p. 32', notes='Standing in 1957, occupied by the Ira Tiser family.')

# --- Photo matching (docs/photo-matching.md)
# Cameras solved against the 2021 lidar terrain for SHSND 00042-00071 (1885), 00042-00195 and -00194
# (1885-86, one camera station SE of town) and the c.1905 postcard SHSND 00259-00003. A building seen in two
# or three of these photos is placed where the sight lines cross ("triangulated"). Identities are inferences.
PH71 = "shsnd:00042-00071 (1885 bird's-eye, camera solved)"
PH195 = 'shsnd:00042-00195 (1885-86 overview, camera solved)'
PH194 = 'shsnd:00042-00194 (1885-86 overview, same camera station as -00195)'
PH259 = 'shsnd:00259-00003 (c.1905 postcard, camera solved)'
TRI = 'Triangulated from two or more solved photos; sight lines cross within about 1-3 m, so the position is good to roughly +/-10 m once picking error is allowed for.'

upd('hotel-de-mores', geom=rect((-103.525635, 46.913867), 25, 100, 90), loc='C', method='photo',
    evidence='Probably building "D" of the 1885 bird\'s-eye view, triangulated from SHSND 00042-00071 and 00042-00195; the reprojected base agrees with both photos (5 px and 2 px), and swapping D with D2 fails that test by about 60 px. ' + TRI +
             ' Why the hotel: (1) a long two-story building with evenly spaced windows on both floors, the shape of the 1883 frame hotel (SHSND 00042-00149); (2) about 60 m north-east of the depot site - "a few steps from the depot" (Fitzgerald\'s ad, Cow Boy 1884); (3) long side facing north (HMdb 88037: "faced north"), with its west end on Main Street, which fits the race track running to "Main street opposite the Northern Pacific hotel" (Cow Boy) and the 1885 porch on the west side; (4) gone in the c.1905 postcard - the hotel burned in 1897.',
    notes='+Open conflict: in the 1885-86 overviews this building reads as white or light-painted, with an outside stair at its east end, while the Cow Boy says the hotel was brick-veneered in spring 1885 and SHSND 00042-00076 shows a long brick building. Either the overviews predate the veneer, the brick read light, or the brick building is a different structure. The site falls on the block the 1957 NPS Tour map shows as De Mores Memorial Park; whether the memorial park was laid out on the old hotel site is worth checking.',
    sources='+; SHSND 00042-00149, 00042-00071, 00042-00195 (camera solutions, docs/photo-matching.md); Bad Lands Cow Boy 1884-02-07 (Fitzgerald ad)',
    photos='+; ' + PH71 + '; ' + PH195 + '; ' + PH194)
upd('roberts-hall', geom=rect((-103.524683, 46.913916), 24, 75, 0), loc='C', method='photo',
    evidence='Possibly building "D2" of the 1885 bird\'s-eye view, triangulated from three photos (SHSND 00042-00071, 00042-00195 and the c.1905 postcard 00259-00003; the three sight lines agree within 0.5 degrees). ' + TRI +
             ' Why Roberts Hall: two full stories about 80 ft long as scaled from the photo (the footprint uses the Cow Boy\'s 24 x 75) with few upper windows (a hall, not hotel rooms), a raised front on its south end, long axis north-south; still standing about 1905 (Roberts Hall stood until 1923, while the hotel burned in 1897); next to today\'s Old Town Hall Theater (Roberts Hall may be the "town hall" of a 1903 stereo, still to be checked); near the hotel and in view of the railroad (HMdb).',
    notes='+Conflict: the Cow Boy puts Roberts Hall on "lot 7, block 17", and today\'s Block 17 is about 300 m southeast. The earlier placement on Block 17 is replaced; check the plat\'s block numbering on the high-resolution scan.',
    photos='+; ' + PH71 + '; ' + PH195 + '; ' + PH259)
upd('metropolitan-hotel', geom=rect((-103.524125, 46.91485), 35, 80, 0), method='photo',
    sources='+; SHSND 00042-00071, 00042-00195, 00259-00003 (camera solutions, docs/photo-matching.md)',
    evidence='Same site as today\'s Rough Riders Hotel (HMdb 87499). Triangulated from three photos: the dark, flat-roofed two-story building with rows of windows in SHSND 00042-00071 ("J") and 00042-00195, and the same building, white-painted, in the c.1905 postcard (00259-00003), where it is the Rough Riders Hotel. The three sight lines agree within 0.06 degrees (in the 00042-00071 photo the reprojected base sits about 40 px below the picked base, a known depth bias of that camera at the north end of town). ' + TRI + ' It stands about 30 m south of the centre of today\'s (much larger) Rough Riders complex, i.e. at its south end.',
    photos='+; ' + PH71 + '; ' + PH195 + '; ' + PH259)
add(id='company-store-offices', name='De Mores company office and store (probable), three joined front-gabled buildings; on the site later given to the Medora Stage & Forwarding Co.', town='Medora', bank='east', kind='building group',
    built=1883.9, built_text='photographed winter 1883-84 (Houghton 3013533); standing in the 1885 photos', use='NPRC store, post office, meat market and company offices (Cow Boy); probably also the office, warehouse and baggage room of the Medora-Deadwood stage line (NPSHB), Oct 1884-May 1885', material='frame, white-painted', stories='1 1/2-2',
    footprint_ft='row about 90 ft long (placeholder)', loc='C', form='C', method='photo',
    geom=rect((-103.526333, 46.914082), 30, 90, 0),
    evidence='Building group "E" of the 1885 bird\'s-eye view, triangulated from SHSND 00042-00071 and 00042-00195. ' + TRI + ' Three matching front-gabled buildings facing east, on the west side of Main Street.',
    sources='SHSND 00042-00071, 00042-00195; HMdb 88033, 303699; NPSHB p. 58 and the 1957 NPS "Tour of Medora" map (site 3); BROOKS57 pp. 19, 22 and Fig. 8', photos=PH71 + '; ' + PH195,
    notes='Identification is inferred: the 1957 Tour map puts the Medora Stage & Forwarding Co. (described as three buildings - office, warehouse and baggage room) on the small triangular block west of De Mores Memorial Park, which is where this group stands. In 1957 one stood on its original site and two had been moved a few feet (BROOKS57 pp. 19, 22). Location graded C because it rests on this identification.')
upd('company-store-offices', notes='+Houghton 3013533 ("Medora in 1883. The office and company store of the Marquis") shows three joined front-gabled frame buildings, the form of group "E". The 1957 Tour map puts the stage company (also "three buildings") on this spot, so the stage line probably used the company buildings. Cow Boy: former carriage-house store room (1884-05-15); plank sidewalk in front of "the Co\'s stores" (1885-02-05); Howe scales in front of the offices (1885-06-25); NPRC general offices moved here from St. Paul, Oct 1885.',
    sources='+; Houghton 3013533; Bad Lands Cow Boy 1884-05-15, 1885-02-05, 1885-06-25', photos='+; houghton:3013533 (winter 1883-84)')
upd('hotel-de-mores', loc='B',
    evidence='+Further support (Oct 16): Houghton 3013534 and 3013559 (1895) label the long brick building with a taller gabled block at one end as the Hotel de Mores; building "D" seen from the east in 00042-00071 shows exactly such a tall gable at its east end. The Historic Medora marker for the hotel stands at Main Street and Pacific Avenue, about 20 m from this point (HMdb 88037; it shares a marker cluster, so this is weak support on its own). The high 1885 view Houghton 3013473 / SHSND 00042-00193 shows a large gabled building here too. Location raised to B.',
    sources='+; Houghton 3013534, 3013559; HMdb 88037 (marker location)', photos='+; houghton:3013534; houghton:3013559 (1895); houghton:3013473')
upd('roberts-hall', loc='B',
    evidence='+Further support (Oct 16): Hagedorn\'s 1919 photo of "Bill Williams\' saloon" (Houghton 3013539) shows a two-story frame hall with a fanlight in its front gable and a door to the upper floor; in his 1919 overview (Houghton 3013472) a dark two-story gabled building of that form, long axis north-south, stands south of the Rough Riders and north of the depot, which is where D2 is. The Roberts Hall marker (HMdb 88016) stands in a small park next to the Old Town Hall Theater, about 10 m from this point. Location raised to B; the Cow Boy\'s "lot 7, block 17" remains unexplained.',
    sources='+; Houghton 3013539, 3013472; HMdb 88016 (marker location)', photos='+; houghton:3013539 (1919); houghton:3013472 (1919)')
upd('ferris-store', notes='+1885 photo: a two-story gabled building ("H") back-projects within about 25 m of this placement; its match in the other photos is not certain, so it is not triangulated.', photos='+; ' + PH71)
upd('medora-depot', geom=rect(off(DEPOT_M, north=8), 24, 60, TRACK_BEARING % 180), form='B', stories='1 1/2',
    evidence='"near today\'s Medora Convenience Store" (HMdb 87986). Huffman\'s 1886 photo (MHS 72461) shows a one-and-a-half-story board-and-batten depot with its long side along the track, a bay window for the agent facing the track, a "MEDORA" sign with mileboards, and a covered freight end; HMdb\'s "perpendicular to the tracks" does not fit that photo. In the 1885-86 overviews a depot-sized building and loading sheds back-project within about 15-45 m of this spot.',
    notes='"A few steps" from the Hotel de Mores (Cow Boy). Used for church services and Sunday school. Size still a placeholder (about 24 x 60 ft from the photo\'s proportions). MHS dates its Huffman print to 1886 but the caption says "North Dakota" (statehood 1889), so the caption at least is later; confirm the date of the negative.', photos='+; ' + PH71)
upd('pp-ice-house', notes='+1885 photo: the plant\'s large building back-projects within about 15 m of this placement (docs/photo-matching.md).', photos='+; ' + PH71)
upd('courthouse-cottages', notes='+SHSND 00042-00176 (1883-86) shows the Von Hoffman House with a one-story, low-roofed house with a front porch to its right against the east bluff - probably one of the brick cottages. BROOKS57 Fig. 13 ("Medora 1886") shows the two cottages; Fig. 8 (about 1900) labels the court house.',
    photos='+; shsnd:00042-00176')
upd('demores-packing-plant', notes='+SHSND 00042-00153 is captioned "de Mores Packing Plant, Medora, N.D. 1883" on the card but shows a tall stack; either the caption date is later than the photo, or the 1883 plant had a stack of its own before Peter Book\'s 1885 chimney. Huffman 1886 (MHS 72460, 72459) and SHSND 00042-00074/-00075 (1885) show the finished plant.')

# --- known but not yet located
UNPLACED = [
    ('medora-hotel', 'Medora Hotel (Coleman & Brown boarding house and restaurant)', '1884', 'Lot bought June 19, 1884; nearly done July 3; ad Nov 20, 1884 (Cow Boy).'),
    ('company-barns', 'Company barn, stable and corral (Deffebach livery)', '1884-85', 'Rented to Bassie Deffebach as a livery (May 1884); additional barn south of the old one (March 1885) (Cow Boy).'),
    ('kennedy-restaurant', "Gill Kennedy's oyster restaurant", '1885', 'Building moved from the west side to John Warn\'s old lot, Sept 1885; ice-house south of it (Cow Boy).'),
    ('osullivan-barber', "John O'Sullivan's barber shop and house", '1884', 'Lot 11, Block 19 (Cow Boy 1885-09), "next to John Warn\'s" restaurant. Block 19 is not in today\'s parcel layer.'),
    ('mckenzie-blacksmith', "McKenzie & O'Brien blacksmith shop", '1885', 'Moved to the north side of the track, May 1885; sold to Alex Morton 1886 (Cow Boy).'),
    ('pryor-shoe-shop', "W. B. Pryor's shoe shop", '1885', 'On a lot "near the church," March-April 1885 (Cow Boy).'),
    ('grymes-house', "E. Grymes's brick dwelling", '1884', 'Cow Boy 1884-10-16.'),
    ('ellison-house', "C. F. Ellison's house by the Catholic church", '1885', 'Cow Boy, Nov-Dec 1885.'),
    ('np-coal-mine-powder-house', 'NP coal mine and powder house', '1884-85', 'Coal mine roof caving in (Cow Boy 1884-06-12); old powder-house north of the track.'),
    ('bank-lots', 'Merchants National Bank (planned)', '1884', 'Four lots at the corner of Third Street and Broadway bought April 1884; again planned "on the vacant hotel square" in 1885; never reported built (Cow Boy).'),
    ('medora-school', 'Medora school', '1885', '"A new school building has been erected" (Bismarck Weekly Tribune 1885-11-20); photo shsnd:00042-00037 "new schoolhouse".'),
    ('stockyards', 'Stockyards', '1885', 'Old NP yards "across the river" were too small; a small yard 50x50, then 100x100 (Cow Boy 1885-04-16); new yards at "the brick-kiln butte" with the river, butte and railroad as pen walls (Oct 1885).'),
    ('paddock-boston-house', "Paddock's building for the Boston clothing house", '1885', 'Nearly finished June 1885 (Cow Boy 1885-06-25); Paddock\'s residence moved to Dickinson in sections June 1887.'),
    ('sylvane-ferris-house', "Sylvane Ferris's house", '1885', 'Two-story section with bay window and porch wing (shsnd:00129-00012).'),
    ('demores-houses', 'De Mores rental houses ("Houses to be let")', '1884-85', 'shsnd:00042-00030 etc.; St. Paul Daily Globe 1884-02-13 mentions "numerous small residence houses."'),
    ('brick-block', 'De Mores brick business block (planned)', '1884', 'Two store rooms below, offices above (St. Paul Daily Globe 1884-02-13). Was it built?'),
    ('lm-shipping-corrals', 'Railroad shipping corrals', 'by 1884', '"the shipping corrals near the Cantonment" (HAG).'),
    ('lm-gifford-store', 'Gifford Bros. & Co. general store, Little Missouri', '1883', 'To open June 1883 (Dickinson Press 1883-06-16).'),
    ('lm-saloons-1883', 'Other 1883 Little Missouri saloons (Smith & Stevens; Edgar & Saebastian; J. J. Smith)', '1883', 'Dickinson Press ads, July 1883.'),
    ('lm-paddock-cabin', "Paddock's cabin and livery, Little Missouri", '1880', '"\'Little Misery.\' Paddock\'s cabin in foreground, 1880" (Haynes, in NPSHB).'),
]

# ---------------------------------------------------------------- write
def fmt_year(v):
    return '' if v is None else str(v)
COLS = ['id', 'name', 'aka', 'town', 'bank', 'kind', 'built_text', 'removed_text', 'built_year', 'removed_year', 'use', 'material', 'stories',
        'footprint_ft', 'placement_method', 'location_grade', 'form_grade', 'evidence', 'sources', 'photos', 'notes']
with open(R('data', 'buildings.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader()
    for k in F:
        w.writerow({'id': k['id'], 'name': k['name'], 'aka': k['aka'], 'town': k['town'], 'bank': k['bank'], 'kind': k['kind'],
                    'built_text': k['built_text'], 'removed_text': k['removed_text'], 'built_year': fmt_year(k['built']),
                    'removed_year': fmt_year(k['removed']), 'use': k['use'], 'material': k['material'], 'stories': k['stories'],
                    'footprint_ft': k['footprint_ft'], 'placement_method': k['method'], 'location_grade': k['loc'], 'form_grade': k['form'],
                    'evidence': k['evidence'], 'sources': k['sources'], 'photos': k['photos'], 'notes': k['notes']})
    for uid, name, when, ev in UNPLACED:
        w.writerow({'id': uid, 'name': name, 'built_text': when, 'placement_method': 'not yet placed', 'location_grade': 'D', 'form_grade': 'D', 'evidence': ev})

feats = []
for k in F:
    g = k['geom']
    props = {c: k.get(c) for c in ('id', 'name', 'aka', 'town', 'bank', 'kind', 'built_text', 'removed_text', 'use', 'material', 'stories',
                                   'footprint_ft', 'evidence', 'sources', 'photos', 'notes')}
    props.update(built=k['built'], removed=k['removed'], method=k['method'], loc=k['loc'], form=k['form'], model=k.get('model', ''))
    feats.append({'type': 'Feature', 'properties': props, 'geometry': mapping(g)})
os.makedirs(R('map', 'data'), exist_ok=True)
json.dump({'type': 'FeatureCollection', 'features': feats}, open(R('map', 'data', 'historic_features.geojson'), 'w'))
json.dump([{'id': a, 'name': b, 'when': c, 'evidence': d} for a, b, c, d in UNPLACED], open(R('map', 'data', 'unplaced.json'), 'w'), indent=1)
json.dump({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'name': 'Little Missouri River, 1883 channel (approximate centreline traced from the plat)'},
          'geometry': mapping(RIVER83)}]}, open(R('map', 'data', 'river_1883.geojson'), 'w'))
modern = [dict(f, properties=dict(f['properties'], layer='osm')) for f in OSM['features']]
modern += [{'type': 'Feature', 'properties': {'layer': 'parcel', 'block': f['properties']['Block'], 'lot': f['properties']['Lot']}, 'geometry': f['geometry']} for f in PAR['features']]
json.dump({'type': 'FeatureCollection', 'features': modern}, open(R('map', 'data', 'modern.geojson'), 'w'))
lon0, lat0 = GEO['affine_px_to_lonlat'][2]
W, H = GEO['image']['web_image_size_px']
nw, se = plat(0, 0), plat(W, H)
json.dump({'plat_bounds': [[se[1], nw[0]], [nw[1], se[0]]], 'plat_image': GEO['image']['web_image'], 'crossing_1883': CROSS},
          open(R('map', 'data', 'config.json'), 'w'), indent=1)
print(len(F), 'placed features;', len(UNPLACED), 'not yet placed; track bearing', round(TRACK_BEARING, 1))
