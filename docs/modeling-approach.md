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
