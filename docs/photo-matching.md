# Photo matching

This doc covers placing buildings from period photographs by working out where each camera stood. It started on October 15, 2026, and the October 15 (night) pass went through every 1880s Medora image that could be reached online. Each image and its outcome is listed in `data/photo_catalog_1880s.csv`.

## Method

1. **Terrain.** USGS 3DEP 1 m lidar (project ND_SouthWest_2021_D21, tiles x60–61 / y520–521), merged and resampled to 5 m. It is too large for the repo. Rebuild it from the USGS National Map as `work/dem/dem5.npy`, with `work/dem/dem5.json` holding `x0`, `y1`, `res` and `shape`, in UTM 13N.
2. **Camera.** The camera model is a simple pinhole: position, height above ground, heading, tilt, roll and focal length. It is solved by least squares against three things:
   - **Control points.** These are buildings that still stand (Von Hoffman House, St. Mary's, the packing-plant chimney) and other fixed points.
   - **The skyline.** The ridge line traced in the photo must match the skyline computed from the lidar.
   - **Lines** (optional). Points on a straight feature in the photo, such as a railroad track, must fall on that line on the map.
   
   When the camera position is unknown, the solver starts from a grid of positions and headings and keeps the best fit.
3. **Placing buildings.**
   - *From one photo:* the base of a wall is followed down to the lidar ground ("back-projection"). This works from high viewpoints. From a low viewpoint the ground is seen at a grazing angle and the depth becomes unreliable.
   - *From two or more photos:* the sight lines to the same building are crossed ("triangulation"). This uses only directions, which are much more accurate than depth. As a check, the crossing point is projected back into each photo. It must land at the building's base in every photo, which catches pairs that are really two different buildings.
4. **Check.** Today's streets, buildings and the computed skyline are drawn back onto each photo with `overlay.py`.

Scripts are in `tools/photomatch/`. Run them from the repo root, with `PHOTOMATCH_WORK` pointing at a folder that holds `dem/` and the photos:

```
python3 tools/photomatch/horizon.py  <photo> x0 x1 y0 y1 data/photomatch/hzNN.json   # trace the skyline in a band
python3 tools/photomatch/solve_joint.py data/photomatch/cfgNN.json                    # solve the camera
python3 tools/photomatch/overlay.py  <photo> data/photomatch/camNN.json out.jpg       # visual check
python3 tools/photomatch/backproj.py data/photomatch/cam71.json data/photomatch/pts71.json out.json
python3 tools/photomatch/triangulate.py data/photomatch/triangulate_in.json data/photomatch/triangulate_out.json
```

The photos are not in the repo, for rights reasons. Download them from the SHSND Photobook and the Montana Memory Project.

## Cameras solved

| Photo | Catalogue date | Camera | Fit | Notes |
|---|---|---|---|---|
| SHSND 00042-00071 | 1885 | Bluff east of town, about 2 m up, looking west | skyline 5.3 px; 4 control points | High view. Back-projection works, but depth runs about 40 m off toward the north end of town (see the Metropolitan below). |
| SHSND 00042-00195 | 1885 | Hillside southeast of town (-103.51878, 46.91185), looking northwest | skyline 1.2 px; 3 control points within 1 px | Low view. Bearings are excellent; depth is poor. |
| SHSND 00042-00194 | 1886 | **Same spot as 00042-00195** (within 4 m), wider lens | skyline 2.1 px | One session, so the two catalogue dates can't both be right. |
| SHSND 00259-00003 (postcard) | c.1901–09 | About 90 m north-east of the 00042-00195 spot, about 35 m higher | skyline 4.9 px; control points 2–7 px | After TR's period. Used to see which buildings survived. |
| Huffman, MHS 72459 | 1886 | Near the railway bridge, looking along the track toward town | skyline 6.2 px | Camera height and the track don't fit together. Used only as a rough check; the online copy is 999 px. |

## Not solved

| Photo | What happened |
|---|---|
| SHSND 00042-00193, "View from top of butte", 1886 | It fits only **when flipped left to right**, from the same hill as the postcard, so the online scan may be mirrored. Even then, buildings standing by 1884–85 (hotel, depot, St. Mary's) don't appear where they should, and the town looks thinly built. Either the date is earlier than 1886 or a building was misidentified. Ask SHSND to check the original's orientation. |
| SHSND 00042-00151, "View of Medora", 1883 | Ground-level view with no surviving building to anchor it. The best skyline fit (on the west bluffs) isn't credible. |
| Haynes, "Bad Land City, Little Missouri", 1881 (SHSND 00119-00017; MHS 108837) | No position near the Little Missouri station fits the skyline and track together. The Pyramid Park Hotel and depot stay where they are; the photo is used for their form only. |
| SHSND 00042-00176, horse near the Von Hoffman House | The control points don't fit (34 px). The photo is used for identification only. |
| Haynes 1880 views (MHS 91737, 91738) | Online copies are too small, about 480 px per stereo half. |

## Results

Two sight lines always cross, so for two-photo features the real test is whether the crossing point projects back onto the building's base in both photos. Three-photo features also test whether three lines meet. Allowing for picking error, treat the positions as about ±10 m.

| Feature | Position | Photos | Check |
|---|---|---|---|
| Metropolitan Hotel (Rough Riders) | -103.524125, 46.914850 | 71, 195, postcard | Three sight lines agree within 0.06°. In 00042-00071 the reprojected base is about 40 px below the picked base, the depth bias of that camera noted above. It sits about 30 m south of the centre of today's Rough Riders complex. |
| Building "D" → **Hotel de Mores (probable)** | -103.525635, 46.913867 | 71, 195 | The base height agrees in both photos (5 px and 2 px). Swapping D and D2 fails this test by 60 px. |
| Building "D2" → **Roberts Hall (possible)** | -103.524683, 46.913916 | 71, 195, postcard | Three sight lines agree within 0.5°. |
| Group "E" → **Medora Stage & Forwarding Co. (probable)** | -103.526333, 46.914082 | 71, 195 | The base height agrees in both photos (1 px and 8 px). |
| Consistency check: packing-plant chimney | 3 m from its true position | 71, 195 | Not independent: the chimney is a control point in both cameras. |

### How the identities were reached

**D, the Hotel de Mores.** D is a long two-story building with evenly spaced windows on both floors, a gable end facing east, and an outside stair at that end. It stands about 60 m north-east of the depot site, with its west end on Main Street. The evidence for the hotel:
- it matches the 1883 frame hotel (SHSND 00042-00149) in shape;
- it is "a few steps from the depot" (*Cow Boy*);
- it "faced north" (HMdb), and its west end on Main Street fits the race track that ran to "Main street opposite the Northern Pacific hotel" (*Cow Boy*) and the porch added on the west side in 1885;
- it is **gone in the c.1905 postcard**, and the hotel burned in 1897.

The block it stands on is De Mores Memorial Park on the 1957 NPS Tour map.

The open conflict is colour. D looks white or light-painted in the 1885–86 overviews, yet the *Cow Boy* says the hotel was brick-veneered in spring 1885, and SHSND 00042-00076 shows a long brick building. Either the overviews predate the veneer, or the brick read light, or the brick building is a different structure.

**D2, Roberts Hall.** D2 is two full stories, about 80 ft long, with few upper windows: a hall rather than hotel rooms. It has a raised front on its south end and runs north–south. It is **still standing in the c.1905 postcard**, and Roberts Hall stood until 1923. It also sits next to today's Old Town Hall Theater. Against this, the *Cow Boy* puts Roberts Hall on "lot 7, block 17", and today's Block 17 is about 300 m southeast. So the location is graded C until the plat numbering is checked. The hotel and the stage company are graded C as well, because their locations rest on inferred identities. The 1919 Hagedorn photos at Harvard (3013539 "Bill Williams' saloon", 3013472–75) should settle it.

**E, the stage company.** E is three matching front-gabled buildings facing east on the west side of Main Street. The 1957 Tour map places the Medora Stage & Forwarding Co. (office, warehouse and baggage room, per the 1958/1962 NPS handbook) on the small triangular block there. The stage line ran from October 1884 to May 1885 (HMdb).

### Single-building photos used for form
- **Depot** (Huffman 1886, MHS 72461): 1½ stories, board-and-batten, long side **along** the track, bay window for the agent facing the track. HMdb's "perpendicular to the tracks" doesn't fit this photo. MHS dates the print to 1886, but its caption says "North Dakota" (statehood 1889), so confirm the date of the negative.
- **Hotel**: the 1883 frame building (00042-00149) and the 1885 brick building (00042-00076/-00086).
- **St. Mary's** (00042-00077): front gable with belfry.
- **Packing plant**: 00042-00150, -00153, -00188 (1883 cards), -00074/-00075 (1885), Huffman 72460 (1886). The "1883" card 00042-00153 shows a tall stack, although the brick chimney dates from June 1885.
- **Brick cottages** (later the court house): 00042-00176 and BROOKS57 Fig. 13.

### Caption conflicts found
- SHSND **00042-00184** ("Medora-Deadwood Stage in front of the brick Hotel de Mores", 1883) and **00097-00045** ("Medora-Deadwood Stagecoach, Dickinson (D.T.)", 1885) are the same Ingersoll image with different places and dates.
- **00042-00194 (1886) and 00042-00195 (1885)** were taken from the same camera position, apparently in the same session.

## Next steps
1. View the Harvard 1880s and 1919 town photos in a browser; they can't be fetched from the workspace. The 1885 views (3013473, 3013560) can be triangulated, and the 1919 ones can confirm Roberts Hall.
2. Ask SHSND whether the 00042-00193 scan is reversed, and for a high-resolution scan.
3. Request higher-resolution copies of Haynes 91737/91738 and Huffman 72459 from MHS.
4. Check whether De Mores Memorial Park was laid out on the hotel site.
