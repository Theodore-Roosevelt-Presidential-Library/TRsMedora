# Photo matching

Placing buildings from period photographs by solving where the camera stood. Started October 15, 2026.

## Method

1. **Terrain.** USGS 3DEP 1 m lidar (project ND_SouthWest_2021_D21, tiles x60–61 / y520–521), merged and resampled to 5 m. It covers 600000–620000 E, 5190000–5210000 N (UTM 13N, EPSG:26913). The file is too large for the repo; rebuild it from the USGS National Map and save it as `work/dem/dem5.npy` with `work/dem/dem5.json` (`x0`, `y1`, `res`, `shape`).
2. **Camera.** A simple pinhole camera: position, height above ground, heading, tilt, roll and focal length. The image centre is held fixed. It is solved by least squares against two kinds of evidence:
   - **Control points:** buildings that still stand, or fixed points, picked in the photo and known on today's map.
   - **The skyline:** the ridge line traced in the photo is matched to the skyline computed from the lidar for each heading (with earth curvature and refraction).
3. **Back-projection.** For each building, the pixel at the base of a wall is turned into a ray from the camera and run out until it meets the lidar ground. That gives its position on today's map.
4. **Check.** Today's streets, buildings and the computed skyline are drawn back onto the photo (`tools/photomatch/overlay.py`). If they line up with the 1885 streets and hills, the camera is right.

Scripts are in `tools/photomatch/`. Run them from the repo root with `PHOTOMATCH_WORK` pointing at a folder that holds `dem/` and the photos:

```
python3 tools/photomatch/horizon.py  <photo> data/photomatch/hz71.json          # trace the skyline
python3 tools/photomatch/solve_joint.py data/photomatch/cfg71.json               # solve the camera
python3 tools/photomatch/overlay.py  <photo> data/photomatch/cam71.json out.jpg  # visual check
python3 tools/photomatch/backproj.py data/photomatch/cam71.json data/photomatch/pts71.json data/photomatch/bp71.json
```

The photos themselves are not in the repo (rights). Download them from the SHSND Photobook.

## Photo 1: SHSND 00042-00071, bird's-eye view of Medora, 1885

Taken from the bluff east of town, looking west across Medora to the packing plant, the river and the railroad bridge.

**Camera solution** (`data/photomatch/cam71.json`)
- Position about -103.51840, 46.91418, on the bluff east of town, about 2.4 m above the ground (the photographer on a rise or a stand).
- Heading 273° (just north of due west), tilted 6.5° down, focal length about 2,960 px.
- Skyline fit: 5.3 px RMS over 97 points.
- Control points: Von Hoffman House, St. Mary's Church, the packing-plant chimney, and the railroad crossing of the 1883 channel (half weight). Residuals 4–18 px.

**Accuracy.** At 450–600 m from the camera, one pixel up or down in the photo moves a point 1–2 m along the line of sight. Allowing for picking error and the camera fit, treat back-projected positions as **±25 m, mostly east–west**. That is good enough to place a building on a block, not on a lot.

**Checks against known buildings**

| Building in the photo | Back-projected to | Known site | Offset |
|---|---|---|---|
| Two-story gabled building ("H") | -103.52608, 46.91506 | Ferris store | about 25 m |
| Flat-roofed two-story building ("J") | -103.52454, 46.91490 | Rough Riders Hotel site | on the site |
| Depot-sized building and sheds ("A", "A2") | -103.52598, 46.91324 / -103.52616, 46.91350 | Depot (near today's convenience store) | 13–45 m |
| Large plant building | -103.52844, 46.91594 | Packing-plant ice house (1957 Tour map) | about 13 m |

**New placements**

| Feature | Position | Grade (location / form) | Identity |
|---|---|---|---|
| `photo85-d2`: long two-story building, about 25 × 80 ft | -103.52478, 46.91392 | B / B | Unknown. Size fits Roberts Hall (24 × 75), and it stands beside today's Old Town Hall Theater, but the *Cow Boy* puts Roberts Hall on block 17, about 300 m southeast. Could also be the Hotel de Mores. |
| `photo85-d`: taller gabled block directly behind D2 | between D2 and -103.52572, 46.91386 | C / C | Its base is hidden, so its spot is a range. About 70 m north of the depot: a good candidate for the Hotel de Mores, or part of it. |
| `photo85-e`: row of three matching white gabled buildings | -103.52636, 46.91408 | B / C | Unknown. Matching buildings suggest one builder, perhaps de Mores company houses. |

The Hotel de Mores and Roberts Hall placements were **not moved**. Each now carries a note pointing at D and D2. Settle the identities by comparing D and D2 with SHSND 00042-00076 (Hotel de Mores, 1885) and Houghton 3013539 (Hagedorn's "Bill Williams' saloon," 1919).

Other buildings picked in this photo (B, C, F, G, I, K–R) are in `data/photomatch/bp71.json`, with the nearest block and nearest known feature. They are not yet on the map.

## Next photos to solve

1. **SHSND 00042-00151** (Ingersoll, 1883). The only overview from T.R.'s arrival year.
2. **Huffman 1886, "Medora from the railway bridge"** (MHS 72459). A view from the opposite direction; with photo 1 it allows triangulation, which pins D and D2 much more tightly.
3. **SHSND 00042-00195** (1885) and **00042-00193 / -00194** (1886). The 00193 web copy is too small; order the scans with the plat request.
