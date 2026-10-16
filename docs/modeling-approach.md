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

## 3D model, first version (Oct 16, 2026)

Live at `map3d/`, built by `tools/build_3d.py`.

- **Terrain.** The 2021 bare-earth lidar, resampled to 3 m and coloured by slope: river bottoms green, slopes tan, steep badlands banded, with a clinker tint high on the buttes. It still shows today's railroad embankment, highway and gravel pits. The 1883 river channel is drawn on top as a blue ribbon.
- **Buildings.** Walls are the footprint extruded to eave height. Roofs are gable or hip over the footprint's minimum rectangle, with the ridge on the long axis, or flat. Heights (`MASS` in `tools/build_features.py`) come from three sources:
  - **Lidar 2021, for surviving buildings:** Von Hoffman House, St. Mary's, the Chateau, and the courthouse cottage wings.
  - **Photo scale bars, for vanished buildings.** `tools/photomatch/scalebars.py` and `heights.py` read eave and ridge heights at a triangulated position on a solved camera. The method was checked against the lidar first: the Von Hoffman House eave reads 3.4 m in SHSND 00042-00071 against 3.6 m in the lidar, and St. Mary's about 3.2 m against 4.2 m in 00042-00195.
    - Roberts Hall: eave 7.0–7.9 m, ridge 9.7–10.5 m. The *Cow Boy*'s "two full stories each twelve feet clear … 26 feet high" is about 7.9 m, which supports the identification.
    - Hotel de Mores: eave 8.5–9.1 m, ridge 10.2–11.7 m.
    - Metropolitan: flat roof at about 7.6 m.
  - **Defaults by number of stories** for everything else: 1 story 3.2/5.2 m, 1½ stories 4.5/7.0 m, 2 stories 7.0/9.5 m.
- **Look by confidence.** The worse of the location and form grades sets the look: solid for A or B, see-through for C, near-invisible for D.
- **Photo views.** Each solved camera (`map3d/data/cameras.json`) sets the 3D camera's position, orientation and lens, including the off-centre principal point. The period photo, hotlinked from SHSND, sits over the canvas with adjustable opacity, so you can check the model against the photo directly.

**Next refinements:**
- Flatten the modern earthworks in town.
- Draw footprints from the photos for the larger unidentified buildings.
- Add porches and the hotel's tall east block.
- Get the drone models of the Chateau and chimney from their owner.

**Walk mode (added Oct 16).** You can drop a pin, or pick one of six preset spots in `tools/build_3d.py` (VIEWS), and stand there at eye height, 1.65 m above the lidar ground. Drag to look around, click the ground to walk to that spot, use the arrow keys or WASD to move, and scroll to zoom. The address bar keeps a shareable link to the current spot in the form `#walk=east,north,heading`, in local metres from the model origin. Walls don't stop you, so you can walk through buildings.

## Detailed models, streets and the train (added Oct 16)

**Buildings.** Each building is generated from a style entry (`STYLE` in `tools/build_3d.py`; renderer in `map3d/js/models.js`) that sets:
- siding: clapboard, drop siding, board-and-batten, brick or log;
- wall and trim colours;
- roof covering and form;
- the front side;
- window bays per floor;
- porches, outside stairs, chimneys, belfry, cupola, bay window and storefront.

Every entry's `basis` field says where the look comes from, and the building's info panel shows it.
- **From period photos:** the Hotel de Mores, Roberts Hall, the Metropolitan, the Ferris store, St. Mary's, the Von Hoffman House, the courthouse cottages, the company store, both depots, the Pyramid Park Hotel, the *Cow Boy* office and the packing-plant buildings.
- **Best guesses:** sides no photo shows, and all paint colours except the Chateau's "green sides and red roof" (*Cow Boy*, 1885).
- **Everything else:** a generic 1880s Dakota frame building, varied by id. Commercial buildings get a storefront and false front.

**Hotel de Mores changes over time.** Before spring 1885 it is the white frame hotel of the 1883 photo. After that it has the brick veneer, porches and taller east block.

**Streets.**
- **Town streets:** the 1883 plat's north grid, the part the 1885 photos show built up, drawn as rutted dirt.
- **Trails:** the road to the ford and Little Missouri, the road to the Chateau, and the Deadwood trail south.
- **Sidewalks:** plank sidewalks along the Main Street business block (*Cow Boy*, Feb 1885).
- The streets appear in the 1883 slice from late 1883 on.

**Railroad.** The 3D track follows today's alignment through town, with ballast, ties and rails. The 1885–86 photos put the depot and sheds beside this alignment, not beside the plat's line. The 2D map still shows the plat's line.

**The train.** It is a Northern Pacific 4-4-0 of the early 1880s with:
- a balloon stack, brass dome and red drivers;
- a tender, a baggage car, two coaches and a Pullman.

It stands at the Medora depot, pointed west like the westbound Pacific Express. In the September 1883 slice it stands at the Little Missouri depot instead. The engine is representative of NP power of the period, not a model of any particular locomotive.

**Chateau.** The Sketchfab drone models of the Chateau and the chimney show in the building panel. They can't be placed in the scene unless the owner provides the model files.

**Performance.** Shadows are on by default. Add `?lite` to the URL to turn them off on slow machines.
