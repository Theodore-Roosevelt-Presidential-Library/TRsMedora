# Research log

## 2026-10-15 (late): Cow Boy pass, 1957 NPS maps, archive search, drone models

**Done**
- Went through all 131 issues of the *Bad Lands Cow Boy* for building mentions: 446 records, in `data/sources/cowboy_building_mentions_1884-1886.csv`. Coordinate this with the BadlandsCowboy repo.
- Read Brooks 1957 and Hagen & Mattison 1952 in full. Found the NPS "Tour of Medora" map (Aug 1957, scaled), used to place the packing-plant foundation, ice house, east building and holding pens.
- Searched what the Montana and Minnesota historical societies have online. Every Little Missouri Haynes image and six Huffman 1886 Medora prints are on mtmemory. No Northern Pacific maps of Medora are digitized. Request lists are in [archive-requests.md](archive-requests.md).
- Added the Chateau and Chimney Park drone models to the map (cleared for Library use).
- Map now has 42 placed features and 22 known but unplaced. Live at trsmedora.labs.trlibrary.com.

**Findings**
- **The train.** The westbound "Pacific Express No. 1" stopped at Medora at 4:01 a.m. in Feb 1884 (*Cow Boy* time table). That fits T.R.'s "about three in the morning" and makes "Pacific Express" the likely name. See [arrival-train.md](arrival-train.md).
- **The chimney dates from June 1885** (Peter Book), so it does not belong in the 1883–84 views.
- **Main Street was Medora's business street.** It held the Hotel de Mores (Northern Pacific Hotel), the Ferris store, the rink (Roberts's saloon from Aug 1885) and Mrs. Malloy's hotel. The *Cow Boy*'s March 1886 fire warning runs along it.
- **The 1883 Little Missouri billiard hall of Pennell & Roberts moved to Roberts Hall in Medora on July 3, 1884.** This supports reading Hagedorn's "Bill Williams" as Robert Roberts.
- **Hotel de Mores rebuild, 1885:** brick veneer, porches west and south, kitchen and laundry on the north. Its orientation conflicts with HMdb's "faced north."
- **The Chateau's 1885 colors** were "green sides and red roof" (*Cow Boy*), not the restored French grey.
- **Little Missouri's site** is at the west end of the old US 10 bridge near the Chateau road (1957 Tour map). The Tiser House there, 0.1 mi west of the bridge, was called the last original building in 1957.
- **The Cantonment site** was destroyed by highway gravel mining before 1952 (Hagen & Mattison), although SHSND's 2025 survey suggests some remains.
- **1947 Medora "line change"** (NP records). This may explain why today's track east of the river differs from the 1883 plat.

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
