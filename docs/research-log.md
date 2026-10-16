# Research log

## 2026-10-15 (evening): Online sweep, fitted plat, first 2D map

**Done**
- Ran four parallel online sweeps: photos, maps and plats, written and newspaper sources, and building documentation. A fifth sweep covered the train T.R. arrived on. Findings are in [sources.md](sources.md) and [arrival-train.md](arrival-train.md).
- Fitted the 1883 plat of Medora (SHSND 00042-00183) to today's survey corners. Today's north-side lots and the railroad west of the river line up with it. See [geography-and-overlay.md](geography-and-overlay.md).
- Rebuilt the gazetteer from one spec (`tools/build_features.py`): 33 placed features plus 14 known-but-unplaced, each with dates, evidence, sources, photos and grades.
- Built the first 2D map (`map/index.html`): four dates, the plat overlay, the 1883 river channel, today's lots and streets, and building details with sources.

**Findings**
- The 1883 plat exists and fits today's grid; Block 15 (Von Hoffman House) checks out. The plat's southern grid did not survive.
- The river ran east of today's channel in 1883.
- There are photos of Little Missouri itself: Haynes, 1880–81, including the Pyramid Park Hotel and depot.
- Huffman photographed Medora in 1886, and the de Mores albums at SHSND include 1883–86 overviews.
- Army building plans and sizes for the Cantonment exist. SHSND surveyed the site in 2025.
- The *Cow Boy* prints building sizes, lots and streets: Roberts Hall 24×75 on lot 7, block 17; Paddock's livery 88×50 on Third St; the freight house 240×42.
- Hagedorn appears to have used pseudonyms ("Frank Vine" for Frank Moore, "P. McGeeney" for Peter Malloy, "Bill Williams" by his own admission). Checked against the *Dickinson Press* of Sept 22, 1883.
- In 1887 many Medora buildings were taken apart and shipped by rail to Dickinson. Some may survive there.

**Open questions (new)**
1. Do the plat's block numbers match today's everywhere? Roberts Hall on block 17 conflicts with HMdb's "near the Hotel de Mores."
2. Was the track east of the river moved after 1883?
3. Which corner of Third Ave and Third St, and which side of the Ferris store (the rink), are right?
4. Do any of the buildings shipped to Dickinson in 1887 survive?

## 2026-10-15: Project scoping and first sweep

**Decisions (Matt Briney)**
- Model from T.R.'s arrival (September 1883) to when he left ranching, and show change over time.
- Phase 1 area: the two towns and the Chateau.
- Educated guesses are acceptable when they rest on evidence.
- Simple shapes and basic materials to start.
- Internal staff curiosity for now. TRPL has archive access and people to call on.
- Confirmed: T.R.'s first night was at the **Pyramid Park Hotel** in Little Missouri.
- A 2D map comes first. GitHub Pages may be used for HTML.

**Done**
- Extracted the 209 "Ranching in Dakota" photo records from trphotos.labs.trlibrary.com (`data/photos_trc_ranching_in_dakota.csv`).
- Read the key passages of Hagedorn, the NRHP nominations, and the TRC and SHSND materials.

## Next steps
1. Order the high-resolution plat scan (SHSND 00042-00183) and re-fit it.
2. Study the 1883–86 overview photos (SHSND 00042-00151, -00071, -00193/4/5; Huffman 72459) to place the unlocated buildings.
3. Read BROOKS57 in full and place the stage company buildings and the brickyard.
4. Request:
   - from SHSND: the 2025 Cantonment survey and the Goplen papers;
   - from the Billings County Recorder: the plat filing;
   - from MNHS: NP station and right-of-way maps.
5. Do a full pass through the *Cow Boy* with the BadlandsCowboy repo, adding every building mention.
6. Confirm T.R.'s train (see [arrival-train.md](arrival-train.md)).
7. Then: terrain from lidar and simple 3D massing.
