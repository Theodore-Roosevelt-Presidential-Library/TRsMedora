# Evaluation of the model and the gallery, Oct 19, 2026

*A fresh review of the repo at commit 9ce0d12, done cold: every gallery overlay was re-rendered at 50% and looked at, along with the five solved overviews, the four date slices and the six "start from" spots, and the data and docs were read against each other. Nothing was changed; this is the list of what holds up and what should be fixed, in order.*

## Short verdict

The method is sound and most of the model is now well evidenced. Twenty-one of the thirty-two gallery views are real solved cameras, and all but three of those sit within 3% of the photo across the building (the three wide views from the hills are at 5–7%, which is as good as a 1890s print of a distant town allows). The packing plant, both depots, St. Mary's, the Chateau group, the Cantonment and Roberts Hall each line up with two or more independent photographs. The gazetteer carries a stated basis and a two-part grade for every feature, and the open questions are written down in one place for Rolf Sletten.

What needs attention is mostly consistency between parts of the project that were built at different times: the trestle, the river, the 2D map, the start spots and some of the captions now disagree with each other or with the sources quoted in the data. None of it is hard to fix, but several items would be caught by the first careful outside reader.

## What holds up

- **The camera solving.** Positions triangulated from the two solved 1885–86 overviews (00042-00071 and -00195) have been confirmed by later, independent fits: Roberts Hall by the 1919 Hagedorn plate (1.4%), the packing plant by six photos from four directions, the Medora depot by Huffman (1.2%), the Metropolitan's east-west axis by the TRC winter view.
- **The close-up fits.** Depot, church, Cantonment, cooling house (with the 1883 frame), Hotel de Mores 1883, the Chateau from four sides and the packing plant from south and north all overlay within a few pixels. These are the views that will sell the model.
- **The paper trail.** `buildings.csv` gives evidence, sources, photos and a grade per feature; `photo-audit.md` records every fit, what it changed and why; `questions-for-rolf-sletten.md` collects the unknowns. This is the right shape for a presidential library's internal experiment.
- **Honesty about the weak parts.** Eleven views are labelled partial, the unplaced buildings are listed as such, and 24 features are graded D/D rather than quietly drawn.

## What to fix, in order

### 1. The trestle contradicts its own source
The 3D model now carries a 212 m pile trestle (47 bents), built from the Haynes 1880 and Huffman 1886 photos. The gazetteer entry for the same feature still says `~300 ft long (HAG)` and quotes Hagedorn: "rumbled across three hundred feet of trestle." `geography-and-overlay.md` says the same. 300 ft is 91 m, less than half of what is modelled. Either the long approach trestle over the flood plain and the river span proper are different things (likely, and worth saying), or one of the two is wrong. The Rolf question (4.7) should quote Hagedorn's figure so he can reconcile them.

### 2. The 2D map and the 3D model disagree about the river
The 3D terrain, water and trees now follow a proposed 1880–86 channel that loops south of the track, with a slough to the north. The 2D map still draws `river_1883.geojson` traced from the plat, and `geography-and-overlay.md` still describes the channel bending "close under the north end of Medora." The ford marker, placed "100 yards north of the trestle" against the old channel, now sits 54 m from the 3D river centreline. The two views of the project should tell one story: either carry the new channel into the 2D map (with its low confidence stated) or mark the 3D channel as the hypothesis it is.

### 3. The Roosevelt start spot shows nothing
"Little Missouri depot, where Roosevelt stepped off the train (Sept. 1883)" opens at the default date (summer 1885), when the depot (removed 1884.5), the Pyramid Park Hotel and the shacks are all gone. The visitor sees an empty bank, a wagon and a telegraph line. Clicking a start spot should set the date it names; this one should open on Sept. 1883. The same applies to the `date=` hash when combined with `walk=`, which the render ignored.

### 4. A telegraph pole stands 4 m in front of Huffman's depot camera
The south-side poles are spaced 50 m with an arbitrary phase, and one lands at (−94.7, −119.6), straight in front of the MHS 72461 camera at (−94.1, −123.7). It blots out the left third of the best close-up in the gallery. Shift the phase, or better, fix two or three pole positions from the photos that show them (72461 and 72459 both do).

### 5. Captions and credits
- Every view, including the eleven partial ones, says "The camera is solved from the buildings in the photo." For the cattle photo "placed by inference" and the veranda view that is not true. Partial views need their own line ("Camera approximate; placed from the skyline / by inference").
- Each view stores a `credit` (SHSND, MHS, Houghton, DMC) but the viewer never displays it. The archive-record link is good; the credit line should be there too.
- `README.md` still says "The map links out to photographs rather than copying them" and "Montana Historical Society images are for educational use only without permission." `map3d/photos/` now holds 8.5 MB of SHSND, MHS, Houghton and DMC copies, served from the site. That is fine for an internal experiment, but the README should say so, and permissions should be settled before anything public.

### 6. The company store overlay shows a mismatch
The model's three gables span about 27 m; the 1883 photo's span works out to 18–20 m, and at 50% the right-hand gables of the model sit visibly to the right of the photo's. The footprint was kept because it fits the 1885 overview. Either narrow it to what both views allow, or say in the caption that the width is unresolved; as it stands the gallery shows the disagreement without explaining it.

### 7. Two start spots no longer frame their subject
- "Below the packing-plant chimney" now stands under the gallery posts of the refitted plant, looking at a blank wall: no chimney in view.
- "St. Mary's Church and the Von Hoffman House" faces ESE and shows the Von Hoffman House and its fence; the church is out of frame to the north.
Re-aim both (heading, and move the plant spot back 20–30 m).

### 8. The opening view cuts off the town
The default overview is centred on the river crossing; Medora itself is at the bottom-right edge of the frame and mostly outside it. The first thing a visitor should see is the two towns and the Chateau in one frame, then be invited to walk.

### 9. September 1883 is too empty on the Medora bank
Slice 0 has 19 features in all, and on the east bank only the cooling house and the plant frame. The timeline says the slaughter house with its tracks, the Chateau and the company office and store were going up in summer 1883 and that by Sept. 22 "new buildings of every description are going up." The company store is dated 1883.9 in the data and "summer 1883" in the timeline; the Hotel de Mores 1883.8. A few of these could reasonably be shown as frames in Sept. 1883, as the plant's 1883 frame already is.

### 10. Docs that have drifted behind the model
- `modeling-approach.md`: says confidence is shown by transparency (it is shown by markers, which is better) and that people and animals are out of scope (there are figures, horses and wagons).
- `geography-and-overlay.md`: Little Missouri is "a reasoned guess" anchored 110 m from the crossing (it is now fitted to the Haynes 1881 camera); the river and bridge statements above.
- `photo-matching.md` "Not solved" table still lists the Haynes 1881 view, 00042-00176 and the two Haynes 1880 views, all of which are now fitted.
- Two slice choices look odd: the 1883 Chateau photo (00042-00152) opens on summer 1884, and the 1883 hotel photo (-00149) likewise. Both are explainable (the hotel is dated 1883.8) but a reader will wonder.

### 11. Smaller things seen in the renders
- The Haynes 1880 crossing view: the photo's pale channel bed runs straight to the crossing; the model's water does not read there at all. Expected for a best-effort view, but it is the one overlay where the river is the subject.
- The Rent Free view: the plant's open gallery framing shows at the right in the 1887 slice; the agent's report says the galleries seem gone by 1886. A removal date on that part would fix both this and the 72460 view.
- The Hotel de Mores 1883 overlay runs a little long at its west end (RMS 15 px, the weakest of the solved fits).

## Where the real uncertainty is

The fits are tight, but a tight fit proves position and shape, not identity. The grades that rest on an identification rather than a measurement are: the company store (the 1957 map's stage company buildings), the Hotel de Mores as building "D" (strong, from the 1890s photos and its absence in 1905), Roberts Hall ("lot 7, block 17" still unexplained), Paddock's livery as the barn on the east side of Third Street, and the Cantonment building as a barracks or storehouse. Those, the bridge, the river course, and what Little Missouri looked like in 1883 are the questions worth Rolf's time; the rest is detail.

## Suggested order of work

1. Fix items 3, 4, 7 and 8 (an hour: start spots set their date, pole phase, two headings, the opening camera).
2. Settle the trestle and river story (items 1 and 2) and put both in the 2D map and the Rolf questions.
3. Caption and credit fixes (item 5), and decide the image-rights position before any wider sharing.
4. Then the content items: the company store width, 1883 Medora, the gallery removal date, and the doc clean-up.
