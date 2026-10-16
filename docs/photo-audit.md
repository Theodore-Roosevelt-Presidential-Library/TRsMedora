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
- **Little Missouri tracks:** Haynes shows **three tracks** there in 1881; the model has one.
- **Cooling-house spur:** the plant's spur track and the cooling house's siding (00042-00150) aren't modelled yet. They need the 1956–57 NPS plans.
- **Streets:** the 1885 overviews show worn tracks and paths, not a fully formed street grid. The streets probably need thinning.
- **Von Hoffman House colour** and its north roof end: check against the standing house.
- **Photo 193's date:** it shows the Von Hoffman House and St. Mary's but no cottages, so it may be autumn 1884 rather than 1886.
- **SHSND 00098-00019 ("Foley's house"):** not in the local photo set; worth downloading.
