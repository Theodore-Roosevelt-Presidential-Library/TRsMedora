# Geography and overlay

## The basic layout

The Little Missouri River flows north. The Northern Pacific crossed it on a trestle of about 300 feet (HAG ch. I).

- **West bank:** Little Missouri, the Cantonment, and the Chateau de Mores on the bench above.
- **East bank:** Medora, built on "the flat under the bluff" (HAG ch. I), with the packing plant at its west edge near the river (NRHP 75001300).

There were no road bridges. People forded "a hundred yards north of the trestle," or walked the trestle at high water (HAG).

## Little Missouri in September 1883, per Hagedorn

Hagedorn's chapter I reads almost like a site plan. It was compiled from interviews with residents. Positions relative to the depot shack:

| Feature | Position given |
|---|---|
| Pyramid Park Hotel | "immediately north of the tracks"; T.R. walked "northeastward" to it from the depot |
| Bill Williams's saloon (one story) | "beside" the hotel |
| Johnny Nelson's store | "South of the track" |
| Mrs. McGeeney's boarding house | "next door" to Nelson's; within 50 feet of Mrs. Fitzgerald |
| Fitzgerald's shack | "Directly to the east, on the brink of the river" |
| Jake Maunders's shack | "At a corresponding place on the other side of the track" |
| The Cantonment | "A quarter of a mile west of" Maunders, "in a grove of cottonwood trees" |
| Miners' shacks | "under the butte to the south" |

This is enough for a **grade C (inferred)** schematic of Little Missouri once the 1883 track alignment and the riverbank are fixed.

## Medora: the original plat appears to still be in use

Two National Register nominations locate surviving 1884 buildings by today's street addresses and by the **Original Plat of Medora**:

- Von Hoffman House: Lots 7–10, Block 15, Original Plat, at Broadway and Fifth Street (NRHP 77001018).
- St. Mary's Church: Fourth Street and Third Avenue (NRHP, 1977).

If de Mores's 1883–84 plat is the same grid as today's, the Medora overlay becomes a matter of matching lots, not warping a map. That is **inferred; it needs confirming** against the recorded plat at the Billings County Register of Deeds.

## Fixed points for georeferencing

| Point | Why it is reliable | Coordinates |
|---|---|---|
| Packing plant chimney and foundations | Survive; WPA corner markers; NRHP boundary | NRHP boundary approx. 46°54'56"–46°55'06" N, 103°31'29"–103°31'52" W (Sec. 27, T140N R102W) |
| Chateau de Mores | Standing | TBD (survey from imagery) |
| St. Mary's Church | Standing, original site | TBD |
| Von Hoffman House | Standing, original lots | TBD |
| Joe Ferris store (Ferris Inn) | Standing | TBD |
| Metropolitan / Rough Riders Hotel | Standing but expanded; original footprint TBD | TBD |
| Railroad crossing | Alignment probably unchanged since the 1880s (verify) | TBD |

## Overlay plan

1. **Base:** current Medora parcel and street data (Billings County GIS or OpenStreetMap), plus USGS 3DEP lidar terrain and NAIP imagery.
2. **Survey layer:** the General Land Office township plat for T140N R102W and the surveyor's field notes. These come from the BLM GLO Records site and are already within scope of the Library's **Homestead** repo. They show the 1880s river channel, the railroad and sometimes buildings.
3. **Town plat:** the recorded Original Plat of Medora, georeferenced to the surviving buildings above.
4. **Photo positions:** for each town-view photo, estimate where the camera stood and its direction, using butte skylines matched against the lidar terrain. Hagedorn's 1919 panorama, with its labeled buildings, is the anchor image.
5. **Buildings:** place each `buildings.csv` row as a footprint polygon with its grade.

## Watch for

- **The river has moved.** The Little Missouri migrates. The 1880s bank lines, fords and the ice dam need the GLO plat or old photos, not today's channel.
- **"Southwest" and "west bank" for the Chateau.** Sources agree. Keep the camera notes ("from the eastern bank") as a check.
- **Little Missouri's exact site.** The town's location on the west bank is clear, but no plat or footprint has been found yet. It is the biggest gap.
