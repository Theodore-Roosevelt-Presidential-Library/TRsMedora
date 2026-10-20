# Research log

## 2026-10-20: Accuracy audit, Oct 20, 2026

Two read-only audits of Oct 19 (quotations; factual claims) were applied to the source files. Nothing was committed.

**Sources reached for the check**
- *Bad Lands Cow Boy*: the repo's own `cowboy_building_mentions` CSV (34 rows re-checked against the paper: all faithful), plus the NDNP ALTO OCR of 25 issues from `tile.loc.gov`; *Dickinson Press* (1883-08-18, 09-22, 1887-06-04, 06-18), *Bismarck Tribune* 1882-10-06, *Bismarck Weekly Tribune* 1885-11-20 and 1887-03-18, *St. Paul Daily Globe* 1884-02-13 and 1885-06-05, same way.
- Hagedorn 1921 and Lang 1926 (archive.org full text); BROOKS57 and HM52 (TRC page images, OCR'd; BROOKS57 p. 33 "Section 34" read on the page image); NPSHB 1962; TR *Autobiography* ch. IV; NRHP 75001299, 75001300, 77001016/17/18 text PDFs; HMdb 87804, 87982, 87986, 88016, 88037, 88045, 88062, 87499, 87796, 87799, 88033; TRC "Cantonment"; trlibrary.com/tr/timeline and /tr/badlands/timeline; the Historic Medora panels in `data/site_photos_2026/`.
- Not reachable: Harvard Houghton captions, MHS mtmemory titles, SHSND Photobook card backs, DMC Omeka, the Eaton letter (TRC o292533), Digital Horizons TRMF-01. The TR Center's 1883–84 diary (o288501) was reached but holds no September 1883 entries, so the arrival date still rests on secondary accounts.

**Counts.** Quotations examined: 124 in `buildings.csv`, 11 in `timeline.md` (about 95 real quotations): 68 verbatim, 9 close, 6 paraphrase-as-quote, 3 not found, 1 wrong attribution, 8 unchecked. Factual claims checked externally: 41 (31 confirmed, 8 differ, 2 uncheckable). Internal discrepancies: 16. Overclaims: 10. The one Roosevelt quotation ("about three in the morning") is verbatim.

**Changes made (all in `tools/build_features.py` unless noted; the CSV and geojson were rebuilt)**
- Quotations: "destroyed the site" re-attributed from BROOKS57 to HM52 p. 9 and given in full; "lot 7, block 17 ... in full view from the railroad" replaced by the paper's sentence; Hagedorn's inverted "opposite Fisher's rink and Joe Ferris's store" unquoted; "the former John Nelson building", "across Quick creek", "the brick-kiln butte" (two rows), "Main street opposite the Northern Pacific hotel" (two places), "Third Ave near Main St", "Third St between Third Ave and Broadway", "near today's Medora Convenience Store" (two places), "Best store building", "between ... Bob Roberts' saloon" (two rows) replaced with the source wording; the freight-house composite split into three dated quotations; "well-built, substantial" credited to the Mandan Pioneer via HAG; "stockade style" and "three buildings" unquoted (HM52 "the stockade"; NPSHB "served as the office, warehouse, and baggage room"); "Published in Medora" stated as the LOC catalogue note (CSV and timeline); "next to the company's store" now marks the unreadable last word; the 1886 fire warning no longer asserts "Main Street" (rink and Malloy rows); the Globe quotation bracketed "[the]" and labelled a correspondent's estimate; the Huidekoper "long and low" quotation given in full; the St. Mary's/courthouse-panel caption no longer carries "(1886)" inside the quotation.
- Dates: Ferris store opened Aug 13, 1885 (timeline row changed from Aug 4; medora.com's date kept only as a note); first slaughter at the new plant June 2, 1885 with cattle received June 1 (timeline said June 1 "per HAG", which HAG does not say); smokestack completed June 17, 1885; Hotel de Mores reopened as the Northern Pacific (June 1 per HMdb; renaming announced June 4) in the CSV and timeline; Jorgens corner store first reported Oct 16, 1884; Paddock's livery built_year 1885.1 to 1885.29 (finished April 16); holding pens removed_year 1887.0 to 1886.9; rink "about March 11"; April 1, 1883 softened to April 1883 with Hagedorn's day in parentheses; "Dec 1886" to "late 1886"; "early 1887" given as the TR Center's phrase.
- Roosevelt's arrival: stated one way everywhere — about three in the morning on September 8, 1883 — in `timeline.md` (with a footnote giving Hagedorn's Sept 7, the TRC's Sept 7–8 and the Library's Sept 8 / "Sept 7–9"), `arrival-train.md` and the Pyramid Park Hotel row; the dignitaries' bonfire row moved to the night of Sept 6–7 (Hagedorn's "twenty-four hours previous"); the OTD post's "shortly after two" flagged for correction.
- Overclaims softened: Roberts Hall "probable identification", removed_text now records HMdb's 1923 dismantling and the NRHP's "destroyed by fire at an undetermined date", and HAG's "built by the Marquis" vs HMdb's McClung; Cow Boy office built_year 1884.1 to 1885.2 (Medora site first evidenced 1885; 1884 office at Little Missouri; fire location undocumented); Little Missouri saloon renamed "Saloon and billiard hall beside the Pyramid Park Hotel (Hagedorn's 'Bill Williams's'; possibly Pennell & Roberts's)"; Hotel de Mores popup opens "Site inferred from the 1885–86 photographs; orientation and the 1885 brick veneer are not yet reconciled"; Ferris store "reported both ways" (HMdb/panel "current structure" vs KFYR rebuild); group E renamed as three joined buildings with the identification stated as inferred, notes reconciled with its B location grade; the four Little Missouri buildings now "not visible in Huffman's spring 1886 view; removal date unknown"; school row renamed "Site of the Congregational church, said in 1951 to have been an early schoolhouse"; **Medora depot form grade A to B** (Oct 2026 audit: one oblique photo scaled from an assumed door); Metropolitan renaming "soon after" 1901 (HMdb) vs 1903 (SAH), name no longer says "1901-03".
- Cantonment: conflicts recorded in built_text/notes — 50 (TRC) vs "up to 60" (HMdb) vs "40 to 60" (HM52) men; 8 (plat, HMdb) vs 11 (TRC, HM52) buildings; HAG quarter-mile vs HM52 "3/4 of a mile northwest" vs plat ~0.5 mi; HM52's note that Hagedorn's "Maunders" is Paddock (so `maunders-shack` may equal `lm-paddock-cabin`); HMdb's later uses (first school, Cow Boy office); Little Missouri depot "by 1880" with the unmodelled 1883 "new depot" noted.
- Packing-plant capacity rewritten as design vs throughput (1883: 15–25/day, Press claim 200; 1885: rated 150, run at 100–125; Globe's 500 caveated). The SHSND 00042-00153 caption is now given as the photo catalogue has it ("Medora (D.T.)"), with the earlier "N.D." reading flagged.
- `data/photo_views.json`: three Huffman prints re-credited to the Montana (not Minnesota) Historical Society with mtmemory links; 00042-00149 date marked as the SHSND catalogue date; Houghton 3013539 retitled as Hagedorn's "Bill Williams' saloon" (probably Roberts Hall). `data/photo_catalog_1880s.csv` row 3013539 softened likewise.
- `docs/sources.md`: HM52 dating (TRC: 1949), the LOC "Published in Medora" note, and a quoting rule for Cow Boy material.

**Not applied, and why**
- The packing-plant row's built_year stays 1885.46: the 3D viewer draws the chimney from that row (point geometry, `roof: chimney`), so an 1883.75 date would put the chimney in the 1883–84 views. The 1883 plant is carried by the holding pens, the ice house and (3D only) the 1883 cooling house; a separate 1883-abattoir row was not added because its footprint is undocumented.
- `company-store-offices` location grade kept at B (the position is triangulated); the notes now say the identification, not the position, is the inference.
- The four Little Missouri removal dates (1886.0) are kept for the views, with the wording softened.
- The unchecked Harvard, MHS, SHSND card-back, DMC and Eaton-letter quotations were left as they are, marked unchecked in the audit.

## 2026-10-16 (morning): Lot numbers, more buildings, site photos

**Done**
- Found the online scan of the 1883 "Map of Medora with Lot Prices" and its price list (TRMF-01, Digital Horizons ndshs-dm 4188–4194). It is only about 600 px, which is too coarse to read block numbers on the map.
- Triangulated five more unidentified 1885 buildings (C, F, G, M, O) and added them to the map. The map now has 48 placed buildings.
- Located Sylvane Ferris's house photo (SHSND 00129-10002). It was not placed: the camera fit was not credible.
- Ran a lidar relief check of the town and the Cantonment flats. Modern grading has erased small features in town. On the Cantonment flats the gravel pits dominate, and no building platforms are clearly visible.
- Matt sent site photos of the Historic Medora panels and the Street View locations of the Ferris store, St. Mary's, the Cow Boy office, the Von Hoffman House, and the bank and post office.

**Findings**
- **Roberts Hall:** its triangulated position is on today's lot 7 of Block 13, the same lot number the *Cow Boy* gives. Today's Block 17 was empty sagebrush in 1885. So "block 17" is either the 1883 plat's number for this block or a misprint for 13.
- **The Cow Boy office** is placed at the building Matt identified at 398 Main St, beside the marker. The office burned in January 1887, so today's building is not the original. Its shed roof also differs from the original's front gable in Houghton 3013536.
- **Hotel de Mores:** the on-site panel says the hotel "faced west", but the HMdb transcription of the same marker says "faced north". "West" fits a front on Main Street.
- **Coal mining panel:** the first NP mine, west of town, closed in 1884, and a new mine opened at the foot of the east butte. That second mine is not yet located.
- **Not from TR's time:** the Stockmens State Bank dates from 1909 and the livery stable from the early 1900s. The Ferris store (1963) and the Rough Riders (1963) are reconstructions on their original sites.

## 2026-10-16: Harvard photos checked through the browser

**Done**
- Viewed the Houghton (Harvard) Medora photos in Chrome through Harvard's image server. That server supports zoomed crops of the full-resolution images, up to 5000 px.
- Re-solved SHSND 00042-00193: the camera stood on the butte top southeast of town, and the scan is **not** mirrored (Harvard's copy 3013473 matches it). The first attempt had mistaken St. Mary's side wall for a fence.
- Tried to solve Hagedorn's 1919 overview (3013472). It didn't fit well, so it is used for relative positions only.

**Findings**
- **Roberts Hall:** Hagedorn's "Bill Williams' saloon" (1919) is a two-story frame hall. In his 1919 overview a building of that form stands where D2 is, and the Roberts Hall marker is about 10 m from D2. Location raised to B.
- **Hotel de Mores:** Harvard's photos (3013534, 1895 3013559) confirm the long brick building with a tall gabled end block is the hotel. That matches D's tall east gable in the 1885 view. Location raised to B.
- **Group E** matches Harvard 3013533, "the office and company store of the Marquis" (1883): three joined front-gabled buildings. It is now placed as the company office and store, which the stage company probably used later.

## 2026-10-15 (late night): Every reachable photo checked

**Done**
- Downloaded and reviewed 52 SHSND Photobook images and 9 Montana Historical Society images from TR's years. Each is listed with its outcome in `data/photo_catalog_1880s.csv`.
- Solved three more cameras: SHSND 00042-00195 and -00194 (one camera spot on the hillside southeast of town, within 4 m) and the c.1905 postcard SHSND 00259-00003. Partly solved Huffman's 1886 "Medora from railway bridge."
- Added triangulation (crossing sight lines from two or three photos) to `tools/photomatch/`. Four buildings are now placed this way.
- Could not solve: 00042-00193 (it fits only mirrored, and the dates don't add up), 00042-00151 (ground level, 1883), Haynes's 1881 Little Missouri stereo, and 00042-00176.

**Findings**
- **Hotel de Mores** is probably building "D": a long two-story building about 60 m north-east of the depot, with its long side facing north and its west end on Main Street. It is gone in the c.1905 postcard; the hotel burned in 1897. It looks white in the 1885–86 views despite the 1885 brick veneer, which is unresolved.
- **Roberts Hall** is possibly building "D2": two stories, about 80 ft, with few upper windows, beside today's Old Town Hall Theater. It still stands in the c.1905 postcard. This conflicts with the *Cow Boy*'s "lot 7, block 17".
- **Medora Stage & Forwarding Co.** is probably the row of three matching gabled buildings ("E") on the west side of Main Street, where the 1957 NPS Tour map puts it.
- **Metropolitan Hotel** is pinned by three photos to the south end of today's Rough Riders complex.
- **Depot**: Huffman's 1886 photo shows its long side along the track, not perpendicular to it as HMdb says. *(Corrected Oct 16, 2026: the photo audit shows the gable end on the track, so HMdb was right; see docs/photo-audit.md.)*
- **Caption conflicts**: SHSND 00042-00184 and 00097-00045 are the same stage-coach photo, catalogued as Medora 1883 and Dickinson 1885. SHSND 00042-00194 and -00195 were taken from the same spot, despite their 1886 and 1885 dates.

## 2026-10-15 (night): Photo matching begins

**Done**
- Solved the camera for the 1885 bird's-eye view (SHSND 00042-00071) against the 2021 lidar terrain: skyline fit 5.3 px, four control points. Method and results in [photo-matching.md](photo-matching.md); scripts in `tools/photomatch/`.
- Back-projected 20 buildings from the photo onto today's map.
- Added three photo-located buildings to the map (D, D2, and a row of three gabled buildings, E). The map now has 45 placed features.

**Findings**
- The Ferris store, the Metropolitan (Rough Riders) site, the depot and the packing-plant ice house all check out in the photo, to within about 25 m.
- A long two-story building about 80 ft long stood next to today's Old Town Hall Theater in 1885. It may be Roberts Hall, which would contradict the *Cow Boy*'s "lot 7, block 17," or the Hotel de Mores.
- A row of three matching white gabled buildings stood on today's Block 12.

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
2. Photo matching: all online SHSND/MHS images done (see `data/photo_catalog_1880s.csv`). Next: view the Harvard 1885 and 1919 town photos in a browser to confirm Roberts Hall; ask SHSND about the 00042-00193 scan orientation.
3. Read BROOKS57 in full and place the stage company buildings and the brickyard.
4. Request:
   - from SHSND: the 2025 Cantonment survey and the Goplen papers;
   - from the Billings County Recorder: the plat filing;
   - from MNHS: NP station and right-of-way maps.
5. Do a full pass through the *Cow Boy* with the BadlandsCowboy repo, adding every building mention.
6. Confirm T.R.'s train (see [arrival-train.md](arrival-train.md)).
7. Then: terrain from lidar and simple 3D massing.
