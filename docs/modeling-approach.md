# Modeling approach

## Principles

1. **Data first, model second.** The model is generated from `data/buildings.csv` (later GeoJSON), so new evidence changes the data, not hand-edited geometry.
2. **Show the confidence.** Each building is drawn according to its grade: solid for A, lighter for B, outline or translucent for C and D. A click shows the evidence and sources.
3. **Time is a property.** Every building has a built date and a removed date. A slider over September 1883 to 1887 filters what is visible, with four presets that match the timeline slices:
   - A: September 1883 (Roosevelt arrives)
   - B: summer 1884 (boom)
   - C: summer 1885 (height)
   - D: early 1887 (decline)
4. **Simple first.** Boxes, gable or hip roofs and flat colors by material (log, frame, brick). Add detail only where a photo supports it.

## Pieces

| Piece | Approach |
|---|---|
| Terrain | USGS 3DEP lidar DEM clipped to roughly 3 × 3 km around the crossing, turned into a mesh. Today's terrain is close enough except along the river. |
| River | Draw the 1880s channel from the GLO plat and photos; it may differ from today's. |
| Railroad | Track and trestle alignment from the GLO plat and NP records. |
| Buildings | Footprint polygon + stories + roof type + material, generated as glTF. |
| Modern overlay | Toggle today's streets, parcels and surviving buildings, so staff can see "this was here." |
| Photo viewpoints | Markers where historic photos were taken. Clicking one moves the camera to that view and shows the photo semi-transparent over the model. This is also how the model gets checked. |

## Suggested stack

Match the Library's other 3D work (CampusMap, LBCSystems) so it can share hosting and code: a static web page using three.js or MapLibre with a terrain layer, data in GeoJSON, hosted at a labs subdomain. Confirm what CampusMap uses before starting.

## Build order

1. Georeference: fix the control points in [geography-and-overlay.md](geography-and-overlay.md) and bring in the GLO plat and the Medora plat.
2. 2D map first: footprints by time slice, colored by grade, over today's Medora. This is the cheapest useful result.
3. Terrain and simple extruded buildings.
4. Photo viewpoints to check positions against Hagedorn's 1919 panorama and the 1880s views.
5. Refine the grade A and B buildings from photos (rooflines, porches, signs).

## Out of scope for now

Interiors, people and animals, the ranches (Maltese Cross and Elkhorn), and photorealistic texturing.

## Lidar point cloud (added Oct 16, 2026)

- **Source.** USGS 3DEP point cloud ND_SouthWest_1_D21 (2021), public on AWS: `s3://usgs-lidar-public/ND_SouthWest_1_D21/` (Entwine format). It has about 3.7 points per square metre over town. `tools/photomatch/ept_fetch.py` downloads any lon/lat box. The town box (-103.5365 to -103.5185, 46.9080 to 46.9185) is 195 tiles, about 41 MB, and 5.9 million points.
- **Classes present.** Ground (2), building (6), unclassified (1), low noise (7), water (9), bridge (17), high noise (18) and 20.
- **Elevations match the bare-earth terrain** used for photo matching. Ground at the Von Hoffman House is 691.6 m in both.
- **Saved in the repo.**
  - `data/reference/lidar2021_buildings_class6_utm13.npz`: all building-class points (UTM 13N, metres).
  - `data/reference/lidar_building_heights.json`: per-building heights above surrounding ground. Eave is the 10th percentile of roof points, ridge the 98th.

| Building | Status | Footprint (m) | Eave (m) | Ridge (m) |
|---|---|---|---|---|
| Von Hoffman House | original 1884 | 16.5 × 11.8 (with porch) | 3.6 | 7.2 |
| St. Mary's Church | original 1884 | 16.8 × 7.8 | 4.2 | 7.7 (belfry too thin to register) |
| Chateau de Mores | original 1883 | 26.1 × 24.6 | 3.8 | 9.4 |
| Courthouse Museum | 1884 cottages, 1913 floor, later additions | 30.5 × 18.4 | 3.2 (cottage wings) | 9.2 |
| Rough Riders | 1963 replica, 2008 wing | 58.9 × 56.7 | 4.7 | 11.4 |
| Ferris store | 1963 reconstruction | 17.6 × 7.6 | 6.5 | 8.9 |

Only the original buildings are used as references for measuring vanished buildings in the 1880s photos. The thin packing-plant chimney is mostly missed by the lidar.
