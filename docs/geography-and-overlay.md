# Geography and overlay

## The layout

The Little Missouri River flows north. The Northern Pacific crossed it on a timber trestle: Hagedorn gives "three hundred feet of trestle" over the river, and the 1880 and 1886 photographs show a longer pile trestle running on over the flood plain (the 3D view reconstructs about 210 m in all).

- **West bank:** Little Missouri grew up around the depot, about half a mile southeast of the 1879 Cantonment. The Chateau sits on a terrace to the south.
- **East bank:** Medora was platted on the flat under the bluff, with the packing plant at its west edge by the track.

There was no road bridge. People forded "a hundred yards north of the trestle," or walked the trestle at high water (HAG).

## Fitting the 1883 plat to today's map

The plat (SHSND 00042-00183) is drawn north-up at 1 inch to 400 feet. It shows:
- section and quarter-section lines;
- circled crosses at the section corners.

Two of those corners are one mile apart on the line between Sections 26 and 27, T140N R102W. That gives the scale (about 16 ft per pixel on the 469×525 web image) and confirms north.

**Control points**, with today's positions from the ND GIS Hub PLSS layer:

| Plat pixel | Survey point | Lon, lat |
|---|---|---|
| 301.7, 179.3 | Corner of Secs. 22/23/26/27 | −103.525078, 46.918352 |
| 302.0, 504.7 | Corner of Secs. 26/27/34/35 | −103.525178, 46.903822 |
| 136.7, 179.0 | North quarter corner, Sec. 27 | −103.535529, 46.918370 |

A three-point affine fit is stored in `data/reference/plat_1883_georef.json`. Two independent checks:

- **Today's lots match the plat's north grid.** Today's parcels north of the track fall on the plat's blocks. Block 15 is where the 1977 National Register nomination puts the Von Hoffman House (lots 7–10). So the 1883 north grid is today's town, and the block numbers appear to carry over.
- **The track matches west of the river.** Today's BNSF (former NP) track lies on the plat's track there.

## What the overlay shows

- **The river has moved.** In 1883 the channel ran east of today's. The plat trace (the solid line on the 2D map) bends close under the north end of Medora and crosses the track a little east of where the river is today; it is approximate. At the crossing itself the 1880–86 photographs (MHS 72459, Haynes 1881, the town views) put the channel in a loop south of the grade, turning north under the west end of the trestle, with a narrow slough north of the track. That reconstruction (the dashed line on the 2D map, and the water in the 3D view) is low confidence and is one of the questions for Rolf Sletten.
- **The southern grid is gone.** The plat's rotated grid of about 40 blocks south of the track does not survive in today's lots. Was it vacated, replatted or never built on? Ask the Billings County Recorder.
- **East of the river the plat draws the track up to about 100 m south of today's line.** It is either schematic there or the line was later moved. NP valuation and right-of-way maps at the Minnesota Historical Society would settle it.
- **The Cantonment is drawn on the plat** as eight building symbols about half a mile northwest of the crossing. They are schematic. The 1879 reserve map (SHSND MAP.032-00111) and SHSND's 2025 remote-sensing survey can pin down the real buildings.

## How each building is placed

Every feature in `data/buildings.csv` records its method:

| Method | Meaning | Typical grade |
|---|---|---|
| osm | Footprint of a surviving building on its original site | A |
| plat | Read off the fitted 1883 plat | B |
| address | Street corner or lot and block from a period source, matched to today's streets and lots | B–C |
| relative | Worked out from a written description relative to another feature (for example "north of the depot") | C |
| schematic | Near where sources put it; the spot itself is a guess | D |

**Little Missouri.** The depot and the Pyramid Park Hotel are fixed by the Haynes 1881 photograph (SHSND 00119-00017), whose camera is solved against the depot and the rails to about 1%. The store, boarding house and shacks are placed from Hagedorn's description of September 1883 (hotel north of the track, store and boarding house south, shacks on the riverbank) relative to those two, and Huffman's spring 1886 view shows the ground there empty, so they end at 1886.0. The Cantonment reserve map would still improve the rest.

**Medora.** Uses the period street names that survive today: Third Avenue, Third Street, Main Street and Broadway (*Cow Boy*, 1884–85).

## Fixed points

| Point | Basis | Position |
|---|---|---|
| Packing plant chimney | Survives; WPA corner markers; NRHP boundary | −103.52779, 46.91608 (OSM ruins node) |
| Chateau de Mores | Standing | OSM footprint |
| St. Mary's, Von Hoffman House, Joe Ferris store | Standing on original sites | OSM footprints |
| Medora depot site | "near today's Medora Convenience Store" (HMdb 87986) | −103.52629, 46.91351 |
| Section corners | ND GIS Hub PLSS | table above |

## Next improvements

1. Re-fit with a high-resolution scan of the plat and many more control points (block corners).
2. Compare the TRMF-01 1883 "Map of Medora with Lot Prices."
3. Fit the 1884 GLO township plat: river, railroad and perhaps buildings.
4. Place unlocated buildings from the 1883–86 overview photos by matching butte skylines against lidar terrain.
