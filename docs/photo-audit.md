# Photo audit of the 3D buildings (Oct 16, 2026)

Every modelled building was checked against every period photograph the project holds (SHSND, MHS/Huffman and Haynes, Harvard Houghton). Each finding is marked:
- **seen**: visible in a photo;
- **measured**: scaled with a door (2.1 m), window or person as reference;
- **inferred**: reasoned.

Where a photo postdates 1887 it was used as context only.

How to reproduce the comparisons:
- `map3d/index.html#look=e,n,h,te,tn,th` puts the camera anywhere.
- `#date=0..3` picks the date slice.
- The photo buttons overlay the solved overview photos.

Footprint changes and added buildings are in `tools/geom3d.py`. Looks are in `STYLE` (`tools/build_3d.py`), and each building's "Appearance in the model" text cites its photos.

## The big corrections

| Building | Before | Photo evidence | Now |
|---|---|---|---|
| **Medora depot** | 1½ storeys, long side on the track, about 25 m from it, flat bay box | MHS 72461 (Huffman 1886): **one storey, gable end on the track** (as HMdb said), about 4–5 m from the rails, at the back of a plank platform at rail height. The roof is about 30° with very deep eaves on knee braces and **continues about 8 m past the north wall over open X-braced posts**. A **canted bay window with its own hip roof** sits just east of centre; there is a door with a transom to its west, two corbelled chimneys, and railings. It measures 5.6 m across and about 13.5 m enclosed. | Rebuilt and moved to the track. The generator gained deep overhangs, knee braces, roof extensions, canted bays and placed chimneys. |
| **Little Missouri group** | Placed against the 1883 plat's railroad line, which put it on the wrong sides of the 3D track (hotel south, depot on the rails) | Hagedorn: hotel "immediately north of the tracks", Nelson's store "south of the track". Haynes 1881: depot 6–8 m north of the tracks, hotel 20–25 m north of the depot. | Re-placed against the 3D track; the 2D map is unchanged. |
| **LM depot** | One block | Haynes 1881: **two joined blocks**. The west one has a light board-and-batten finish and a roof of boards laid eave to ridge. The east one is deeper and higher, with a shingle roof and a single door. | Two blocks, plus a platform. |
| **Pyramid Park Hotel** | Two-storey front-gabled box with a porch facing north | Haynes 1881: **one tall storey with a loft** under a steep roof (Hagedorn's "loft with 14 beds"). The front faces south to the track, there is a cross gable at the east end, a light front-gabled block at the west end, a low block behind it, and **no porch roof**. | Rebuilt from four blocks. |
| **Hotel de Mores, 1885–87** | Red brick, arched windows, a taller cross-gabled east block, 8.5 m eave | **The brick-hotel photos (SHSND 00042-00076/-00086, Houghton 3013534) date from the 1890s** (dress, wires). The 1885–86 overviews show a **light** building of one eave height with a plain east gable, an **outside stair up the east gable**, and a **north wing**. | Pale (cream) brick: this fits both the Cow Boy's 1885 brick veneer and the light tone of the prints, and matches St. Mary's of the same year. The end block is removed. The stair, the north wing and unroofed plank platforms are added. Eave is 6.8 m. |
| **Hotel, 1883** | 9 bays, 3 chimneys | SHSND 00042-00149: 10 openings below and 8 above, 6/6 flat-head sash, **2 chimneys**, window–double door–window on the gable end | Matched. |
| **Company store** | Three equal 1½-storey storefronts | Houghton 3013533 (1883): three **one-storey** front gables of **unequal width** (7.3 : 6.0 : 4.3 m), with door and window positions as photographed, 2 chimneys and a raised floor | Matched. The footprint is kept because it fits the 1885 overview, although the photo suggests 18–19 m of frontage. |
| ***Cow Boy* office** | Plain box | Houghton 3013536: eave about 2.7 m, an off-centre board **entry vestibule** with a shed roof, a chimney at the rear | Matched. In SHSND 00042-00071 the site reads as open ground. The site follows Matt's identification of the surviving building, so it is flagged, not moved. |
| **Packing plant** | One 46 × 18 m board-and-batten block with a long monitor and a 34 m sloping runway | One 1885 exposure in three copies (00042-00074 = -00153 = 0039_00001; **the "1883" card is wrong**), plus 00042-00075 and MHS 72460. Together they show a **tall nearly windowless block** about 30 m long with a 10.5 m eave, horizontal siding on a **stone foundation course**, a short roof ventilator, and galleries at the east end of the south face. Beside it is a **lower west annex** with three rows of windows and a monitor. An **enclosed horizontal runway** runs to a tapered timber **pier**, and there is a loading platform on the north. | Rebuilt as two blocks with the pier, platform and plinth. |
| **Ice house** | Tower and cupola | Dark gabled shed with **two ridge ventilators**; the tower and cupola belong to the **cooling house** | Fixed. |
| **Cooling house** | Not modelled | 00042-00150/-00188 (1883) and later views: an 11 m cubic clapboard block with a **hip roof and cupola** and a car-loading platform. Located by crossing sight lines in the solved photos 71 and 193 (±10 m). | **Added.** |
| **East building** | Ridge north–south | Ridge east–west, gable end facing east, two ventilators, a tall dark tower at its west end | Rotated. The tower is added at a guessed position. |
| **Von Hoffman House** | Full hip roof | 00042-00176/-00182/-00071/-00195, and the NRHP's "hip-gabled" roof: **long north–south ridge with a clipped (jerkinhead) south gable** over a full-width porch, segmental-arch 2/2 windows, two chimneys, a fenced yard with an outbuilding | Matched. The fence and yard outbuilding are added. The wall colour is not recorded; check it against the house. |
| **St. Mary's** | Tan walls, evenly spaced round-headed windows, large belfry | 00042-00077: near-white brick, **four lancet windows on the rear three-quarters** of the side, a blank east gable, the west door under a pointed hood, a small open belfry | Matched. The tree beside the church is removed (none appears in 1885). |
| **Brick cottages** | One 30 × 18 m red block | 00042-00195/-00194: **two separate white hipped cottages**, each about 8 m square, about 5.5 m apart | Matched. |
| **Chateau** | Two-storey rear block, full-length south veranda | Main block has no dormers and **board shutters**. The **rear wing is one storey with a north–south ridge**. The veranda covers the whole east end and only the **eastern half of the south front**. | Matched. The SHSND colours are kept. The eave is set at 6.3 m: the lidar's 3.8 m was the veranda roof. |
| **Cantonment** | Horizontal logs, sod roof | MHS 91738 (1880): **vertical logs stockade style**, a shingle or board roof (not sod), eave about 2.7 m | Matched. The building sizes are still the plat's schematic symbols. |
| **Roberts Hall, Metropolitan** | Even windows; unconfirmed east stair | Windows in **pairs**; Roberts Hall has an upper front door with a hood; no stair is seen | Matched. The stair is removed. |
| **Ferris store** | Front-gabled | Houghton 3013537/3013655 (later): **square false front**, porch on a raised platform | Matched. |
| **Livery** | Side-gabled | 00042-00071: **gable-fronted barn facing east** with a wagon door | Matched. |

## Buildings added from the overviews
- **photo85-x1:** a white cottage south-east of St. Mary's, located in three photos.
- **photo85-x2 and x2b:** a white house and a dark building east of the Von Hoffman House.
- **The Von Hoffman yard outbuilding.**
- **Two Chateau outbuildings:** a small light building east of the house (00042-00152), and a long dark carriage shed or stable (00042-00157) at a provisional place.

## Dates and grades changed
- **photo85-u10:** shown from 1886. SHSND 00042-00071 shows open ground there in 1885.
- **photo85-u06:** shown only before summer 1885. It appears in 00042-00193 (probably autumn 1884) but not in 00042-00194/-00195.
- **freight-house:** location grade lowered to D. The 1885–86 overviews show open ground at its spot.
- **The unidentified photo85 buildings:** each now has a style from what the photos show (roof form, gable direction, tone, size). Before, they used a generic default.

## Open questions
- **Depot mileboards:** the figures are partly legible (about "595.3 M" to St. Paul, "1465.? M" to Portland). A better scan of MHS 72461 would settle them.
- **Cooling-house spur:** the plant's spur track and the cooling house's siding (00042-00150) aren't modelled yet. They need the 1956–57 NPS plans.
- **Von Hoffman House colour** and its north roof end: check against the standing house.
- **Photo 193's date:** it shows the Von Hoffman House and St. Mary's but no cottages, so it may be autumn 1884 rather than 1886.
- **SHSND 00098-00019 ("Foley's house"):** not in the local photo set; worth downloading.

## Second pass (Oct 16, afternoon)
- **Little Missouri sidings:** two sidings now run south of the main line at Little Missouri, so three tracks show as in Haynes 1881. Each is about 340 m long with tapered ends. Which of the three was the main line isn't known.
- **Streets:** side streets are drawn as narrow, faint wagon tracks; only Main Street and Third Avenue are full-width roads. This matches the worn paths in the 1885 overviews.
- **Ground:** the valley floor is a greyer sage, which reads closer to the overviews.
- **1883 river course:** the trace is smoothed so the channel bends instead of zig-zagging. This affects both the ground cut and the water.
- **People, horses and wagons:** representative figures, each tied to the building it stands at so it appears only while that building stands. They show:
  - a team at each wagon;
  - a few people at the depot platform, the hotel and the stores.

  A checkbox hides them. They are not documented individuals.
- **Still open:**
  - The plant's spur track needs the 1956–57 NPS plans; no source in hand locates it.
  - Von Hoffman House wall colour: the 1885 prints read light. Check the standing house, and its north roof end.

## Placement check against the streets (Oct 16, evening)
The streets follow the 1883 plat. Today's lot lines match it: no street centreline falls inside a modern parcel.

Nine buildings overlapped a street, so the build now slides any such footprint off the street (`tools/geom3d.py`, "keep buildings off the platted streets"). How far a building may move depends on what placed it:
- **Placed from one photo:** the bearing from the camera is well fixed, but the distance is only good to ±25 m. These buildings slide along the camera's line of sight. That covers photo85-u02, -u04, -u05, -u06, -u08, -u09 and -u12, which moved 1–9 m.
- **Triangulated or placed from a written source:** these take the smallest move that clears the street.
  - **Metropolitan Hotel:** moved 6.5 m north at first; superseded on Oct 17 (see below).
  - **Roller rink:** moved 3 m.

Every move is within the stated uncertainty of the original placement and is recorded in the building's notes. No building now overlaps a street or another building in any date view.

## Chateau and St. Mary's from today's buildings (Oct 16, evening)
- **Chateau:** doors, windows, chimneys and the north ell now follow the 2023 drone photogrammetry model (Sketchfab, ajkclark) and the 1975 National Register nomination.
  - **South front:** two windows and a door with a small gabled hood at the west end. Under the veranda, windows either side of a door. Upstairs, two windows at the west end and three windows with their shutters closed.
  - **East end:** a door between two windows, three windows above.
  - **West gable:** two windows below, one above.
  - **North side:** six upper windows.
  - **North ell:** a long one-storey hipped wing along the whole north wall, with a front-gabled wing projecting north at its east end. That wing has a hooded entry.
  - **Chimneys:** three on the main ridge.
  - **Veranda:** starts about 40% along the south front.
- **St. Mary's:** the 1886 photo governs. It shows a single door under a pointed blind arch and pointed side windows. Today the door and arch are the same but the side windows are round-headed, a later change. The door is now drawn that way.

## Photo gallery
"Compare with the period photographs" opens a gallery of the photos with a camera. Choosing one draws the model from the photographer's position, at the date slice the photo shows, with an opacity slider and Model only / Photo only buttons.

Every view's camera is solved by least squares on control points: the corners, eaves and gable peaks of surviving buildings (Von Hoffman House, St. Mary's, the Chateau, the plant chimney) and of buildings placed from other evidence. The target is a worst-point error under 5% of the building's width in the photo; every view now meets it.

| View | Camera fitted to | RMS (px, original scan) | Worst point, % of building width |
|---|---|---|---|
| Town overviews 00042-00071, -00195, -00194, -00193, 00259-00003 | survivors across the town | 5.8, 6.6, 4.3, 6.3, 4.6 | – |
| MHS 72461, Medora depot | depot roof, eaves, wall base, chimneys | 4.4 | 1.2 |
| 00042-00077, St. Mary's | church (lidar geometry) | 8.9 | 1.8 |
| 00042-00149, 1883 hotel | hotel corners, gable | 15.2 | 2.3 |
| 00042-00176, horse and Von Hoffman House | house ridge and eaves, St. Mary's | 4.7 | 2.5 |
| 00119-00017, Haynes 1881 | LM depot, main-line rails | 3.9 | 1.3 |
| 00042-00074, plant 1885 | chimney top, plant blocks (joint solve) | 2.1 | 1.3 |
| MHS 72460, plant 1886 | chimney top, plant blocks (joint solve) | 0.7 | 0.5 |
| 00042-00152, Chateau 1883 | Chateau corners and ridge; hotel and company store in the distance | 5.8 | 2.7 |
| 00042-00196, Chateau 1886 | Chateau east gable, eave and ridge lines; far waterline sets the distance | 2.1 | 2.3 |

The view definitions are in `data/photo_views.json`. Copies of those photos, downsized to 1800 px, with thumbnails, are in `map3d/photos/`. Each record links back to the holding archive. The town overviews still load from the State Historical Society's servers.

## Camera re-solve and what it moved (Oct 16, late)
The five overview cameras had been solved from three or four points each. Re-solved from surviving-building control points, they now fit at 4-7 px. With the better cameras, and with a camera fitted to every single-building photo, the buildings were checked again. Model changes that followed (each is within the earlier placement's stated uncertainty and is noted on the building):
- **Packing plant** (both plant photos solved together, chimney fixed): the tall block moved about 13 m west and 13 m north, so the chimney stands about 26 m behind its south face; 30.9 m long, eave 9.6 m (was 10.5), 7 m deep. The runway pier is 25 m west of it. The cooling house, east tower and east building moved 2-22 m; the east building's eave is 5.2 m. The galleries move to the east face: Huffman's 1886 view shows the south face plain.
- **Ice house**: only Huffman shows it, and its height and distance trade off. It now stands just behind the runway pier (which hides its east end), eave 5.2 m. Low confidence.
- **Little Missouri depot** (Haynes 1881 camera fitted to the depot and rails): 2.5 m further north; the two blocks re-sized (west 6.0 x 3.6 m, east 7.3 x 6.2 m).
- **Pyramid Park Hotel**: about 30 m further east than before: its front is about 38 m north of the main track and about 50 m east of the depot's west end, parallel to the track, 14 m frontage with a 7.2 m cross gable. Its floor sits about 1.1 m above the depot's, so its pad is raised. Distance and size trade off (an 11.4 m frontage would put it 6 m nearer).
- **Medora depot**: the roof runs on one X-braced bay (about 2.3 m) past the north wall, not 8 m; ridge 5.6 m.
- **Chateau outbuilding (east)**: about 6 m west-north-west, on the terrace.
- **photo85-x2 and x2b**: 12-17 m east, from the horse photo (00042-00176).
- **Overview buildings**: photo85-u01 (27.5 m west), -u09 (10.9 m east), -o, -g, -f, -m, -c (3-7 m).
- Trees are kept out of the near foreground of each photo view; none shows in those photographs.

Still open:
- **Chateau stable**: neither Chateau photo shows a long building at its provisional place. The 1883 photo shows two gabled sheds in the bottom land south of the house instead, around 100-120 m south.
- **Paddock's livery**: the re-solved cameras suggest the east side of Third Street, but the barn's gable faces east, which fits the west side. Left in place.
- **1883 Hotel de Mores**: the photo suggests a narrower, taller block with a steeper roof than the recorded 100 x 25 ft. Not changed; seven points on one building cannot settle it.
- **St. Mary's**: the 1886 roof reads slightly steeper than today's (eave about 4.1, ridge about 8.1), and the belfry about 0.5 m higher.

## Second round with the overviews (Oct 17)
Open questions are collected for the historian Rolf Sletten in `docs/questions-for-rolf-sletten.md`.

Prompted by Matt's comparison of the gallery views, every building in the town core and the packing plant was checked against all five overview cameras at once.

- **Packing plant rotated about 14 degrees.** The two ground photos could not fix the plant's rotation about the chimney: with the chimney as the only known point, any rotation fitted them about equally. The overviews 00042-00071 and -00195 do fix it. The runway pier and the cooling-house cupola, at opposite ends, give 15 and 12 degrees independently. The long axis now runs at a bearing of about 76 degrees (ENE-WSW); the tall block is 33 m long, eave about 10 m; the chimney 22.7 m. The two ground-photo cameras were refitted (2.5 and 0.7 px RMS). The road to the ford was rerouted around the plant. The DMC river panorama independently needed the plant's west end about 4 m further east, which the rotation supplies. That panorama also suggests the east tower and east building sit about 5 m further west; not applied (one 600 px view).
- **Metropolitan Hotel (Rough Riders site): long axis east-west, not north-south.** A rectangle fitted to 13 corners in four overviews (2.4 px RMS) gives 22.4 x 10.1 m (about 74 x 33 ft, the Cow Boy's 35 x 80), eave 7.1 m, a low hipped roof, dark walls in 1885-86 and white by c.1905. The TRC view from the south-east hills agrees independently. The white, shorter building in front of it in 00042-00194 is the cottage photo85-m.
- **Roberts Hall** about 8 m west. **Paddock's livery** moved to the east side of Third Street, where 00042-00071 shows a large barn with its gable and wagon door facing east (identity inferred; length a placeholder). **photo85-u07** and **-u11** moved to the buildings the photos show (40 m and 30 m). **photo85-u12** removed: it was the company store's left gables seen twice.
- **Camera 193 (from the butte)** re-solved with terrain constraints as well as building picks: bluff skyline, the spur edge, the valley floor in front of town, and rays along the bottom of the frame. The photographer stood at the south-west tip of the butte plateau, 1.5 m above the ground; yesterday's ground-pinned camera stood 8 m too far back, where the plateau lip hid the lower town. Building RMS 4.5 px, skyline 4.5 px. Cameras 194 and 195 have no terrain problem and are unchanged.
- **New views:** the TRC view from the south-east hills (SHSND 10797-00036, c.1890s-1906; 5.4 px RMS, worst 6.9% on St. Mary's) and the Dickinson Museum Center river panorama (DMC 25741, 1887-1907; a swing-lens panorama re-projected to a flat view; 2.2 px RMS, worst 5.6%). Both open at the spring 1887 slice, the latest the model has. A third, the TRC winter view from the west bluff (SHSND_0103, 1890s; long lens from the bluff beside the NP cut; 6.6 px RMS, worst 5.3% on Roberts Hall), was added the same way. It suggests the ice house was taller by the 1890s (eave about 6.6 m) and that the Pyramid Park Hotel was gone by then; the depot reads taller, perhaps rebuilt or a car in front. None of these later states is modelled.

Still open:
- **Roller rink and Malloy's hotel:** 00042-00071 shows open ground at their mapped spots; no photo yet gives their true positions.
- **Freight house:** two photos show open ground at its spot (grade D already).
- **Stockyards:** the TRC south-east view shows a two-pen stockyard with two loading chutes about 115 m south of the main line (around local 277-345 E, -515 to -468 N). That photo is c.1890s, so the yard is not yet modelled for 1883-87.
- **St. Mary's** reads about 8% shorter in the TRC south-east view than the lidar footprint; the church is trusted, so it is not changed. Worth checking whether the lidar includes a later addition.
- **Chimney height:** the solves give 22.7 +/- 2 m from the plant photos, up to about 27 m from the far butte view. 22.7 m is used.

## Grades revised (Oct 17)
After the overview re-solve and the photo fits, location (first letter) and form (second) grades changed:

| Building | Was | Now | Why |
|---|---|---|---|
| Packing house | C/C | B/B | Position and angle fixed by six photos and the chimney |
| Ice house | C/C | B/C | Located consistently in four photos |
| Company store and offices | C/C | B/B | Triangulated; gables match; storefronts measured from Houghton 3013533 |
| Little Missouri depot | C/B | B/B | Fitted Haynes 1881 camera, about 1% |
| Pyramid Park Hotel | C/B | B/B | Fitted Haynes 1881 camera (distance/size trade-off about 6 m) |
| Chateau outbuilding (east) | C/C | B/C | Fitted 1883 Chateau photo; chimney in the 1886 one |
| Medora depot | B/B | B/A | Huffman 1886 matched to about 1% |
| Brick cottages | B/C | B/B | Two hipped cottages in three photos |
| Plant east building | C/D | C/C | Form seen in several photos |
| Roller rink | C/C | D/C | Open ground at its spot in 00042-00071 |
| Mrs. Malloy's hotel | C/D | D/D | Open ground at its spot in 00042-00071 |
| Metropolitan Hotel | B/A | B/B | Orientation and roof just corrected; front and porch inferred |

## Close-up views (Oct 17, afternoon)
- **Added to the gallery:** the cooling house with a frame going up beside it (SHSND 00042-00188, 1883; worst 1.7%), the "Rent Free" sign on the closed plant (00042-00180, 1887+; 2.2%), the Bad Lands Cow Boy office (Houghton 3013536 via Hagedorn 1921; 0.9%), and Huffman's view from the west bluff (MHS 72459, spring 1886; a 999 px scan of a distant town, worst about 10% on Roberts Hall, otherwise 3.2 px RMS).
- **Cow Boy office reshaped:** the photo only fits a long building, about 12 x 5 m (2.5 times as long as wide; scale from the man at the door, so possibly 20% larger), eave about 2.1 m, floor about 0.5 m up, with the board vestibule on the **east (Main Street) gable** and the chimney at the west end. With the vestibule on the west gable the camera falls in the back lot, where the terrain would put a bluff in what is clear sky. The photo fits the 398 Main St site but cannot prove it.
- **Little Missouri:** Huffman's spring 1886 view shows open ground where the Pyramid Park Hotel and the McGeeney, Fitzgerald and Maunders shacks stand in the model, so they now end at 1886.0 (exact dates unknown).
- **Cross-checks from MHS 72459:** the rotated packing plant and Roberts Hall's westward move both agree; the Metropolitan and livery can't be told apart at that distance.
- **Not fitted:** 00042-00075 (plant from the north; the ice house and runway/pier heights don't agree with it, so the ice house may sit further north), 00042-00150 (one wall only), 00042-00182 (Von Hoffman porch close-up), 00098-00025 (depot, 1913: by then its long side ran along the track, so it was turned or rebuilt after 1886), the two cattle-shipping photos (no locatable background; 00098-00017's stock cars look 1900-20, not c.1880), and Houghton 3013533 (company store: one flat facade, so the camera distance can't be fixed). The company store photo suggests a frontage of about 20 m (model 27.4) with blocks about 8.3, 7.2 and 4.5 m wide and eaves of 3.4-3.9 m; not applied until a second view confirms it.
- **New lead:** 00042-00188 shows a large timber frame going up north of the cooling house in 1883 (around local -158 to -184 E, 203-222 N), not at the modelled ice house.
- **Chateau views added:** 00042-00157 (1884, from across the river; 3.0%), 00042-00158 (1883, Ingersoll; 3.3%), 00042-00197 (1886, riverbank; 1.7%) and MHS 72389 (Huffman 1886; 3.9%). MHS 72403 (view from the veranda) could not be fitted: it does not look toward town and its hills don't match the terrain.
- **Chateau stable moved:** the long low building with wagons in 00042-00157 stands on the upper terrace about 45 m west-north-west of the house (range +/-15-25 m), not in the bottom land; it is absent in the 1883 photo, so it dates from 1883-84. Two small sheds in the bottom land about 110-120 m south of the house (00042-00152, 1883) are added as candidates for the NRHP coachman's house / carriage shed group. The photos suggest a Chateau eave nearer 6.7 m than 6.3 m (not changed).
- **Cantonment:** Haynes's 1880 photo (MHS 91738), with its camera fixed by the butte skyline (1 px), shows one log building about 29.5 x 6.8 m (97 x 22 ft: the storehouse or a 100-ft barracks block), eave about 1.9 m, long axis WNW-ESE, about 87 m west of the plat-based symbol. The 3D view now shows that building; the plat's eight schematic symbols stay on the 2D map. Added to the gallery (0.75%).
- **Not added:** MHS 108837 is the same exposure as SHSND 00119-00017; MHS 91737 (the 1880 crossing) has no modelled buildings and its camera can only be placed somewhere on the east bluffs. It shows the near channel running straight to the crossing and a trestle about twice the modelled bridge's length.
- **Trees:** the model's trees are hidden while comparing with a photo; several ground-level views looked straight into them.

## Late Oct 17: partial fits, railroad, plant, church, Little Missouri
- **Partial fits added (gallery "best-effort"):** 00042-00075 (plant from the north), 00042-00150 (cooling-house platform), 00042-00182 (Von Hoffman porch; porch posts re-spaced from it), 00098-00025 (depot 1913, shown on the 1887 model so the turn is visible), Houghton 3013533 (company store), MHS 72403 (from the Chateau veranda), the two cattle photos (00042-00021 placed at the stockyard chutes by inference only; 00098-00017, c.1900-20) and MHS 91737 (Haynes 1880 crossing, left half of the stereo). These cameras are approximate and say so in their titles.
- **1883 frame:** 00042-00188 now shows an open timber frame north of the cooling house (1883.5-1883.95), followed by a low barn on the same footprint.
- **Railroad 1880-86, from MHS 72459 (re-fitted camera):** the main line runs on a raised grade (about +4.5) west of Medora and crosses the river on a 210 m pile trestle (47 bents); the sidings at Little Missouri end short of the bridge (outer siding gone by mid-1884); telegraph poles on the south side; the river loops south of the track and a north slough is shown (low confidence). The 2D map's 1883 river trace is unchanged. The Little Missouri depot was raised to sit level with the new grade.
- **Packing plant refit to 00042-00074 (1885) and MHS 72460 (1886):** sloped, enclosed runway (top 10.9 m at the block to 12.3 m at the pier, pier about 25.5 m west) with a knee brace and one strut; block 32.6 m long (8.2 m depth assumed); low east wing; galleries moved to the wing front (they stand in the 1885 photo and appear gone in 1886, but the model cannot remove them yet); log hut 6 x 3.6 m; east building 17.5 x 11 m; tower 2.7 m square on a gabled board base; walkway rising to the tower; annex eave 8.4-9.4 m. The two ridge ventilators in 00074 may belong to the barn behind the east building (not moved). The photo's cooling-house cupola reads taller than the model's.
- **St. Mary's:** lancet side windows with sills, smaller arched door, dark belfry with no lattice, tan walls, and the zigzag rail fences seen in the c.1886 photo.
- **Little Missouri:** Pyramid Park Hotel reshaped from the Haynes photo (cross-gabled main block, west block, rear wing), no road or raised ground in front, plank walk running to the track, Maunders shack reduced to a small hut north-west of the hotel.
