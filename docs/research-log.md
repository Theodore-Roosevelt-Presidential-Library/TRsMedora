# Research log

## 2026-10-15: Project scoping and first sweep

**Decisions (Matt Briney)**
- Model the towns from T.R.'s arrival (September 1883) to when he left ranching, and show change over time if possible.
- Phase 1 area: the two towns and the Chateau.
- Educated guesses are acceptable when they rest on evidence.
- Simple shapes and basic materials to start.
- Internal staff curiosity for now. TRPL has archive access and people to call on when stuck.
- Confirmed: T.R.'s first night was at the **Pyramid Park Hotel** in Little Missouri.

**Done**
- Extracted the full T.R. Photograph Collection catalog (8,487 records) from trphotos.labs.trlibrary.com. Saved the 209 "Ranching in Dakota" records to `data/photos_trc_ranching_in_dakota.csv`, tagged `town` (25), `context` (136) or `other` (48), and linked to building IDs.
- Read the key passages of Hagedorn (1921): Little Missouri in Sept. 1883 (ch. I), the Cantonment purchase (ch. II), Medora in 1885, the abattoirs, and the trestle and ford.
- Read the NRHP nominations for the Von Hoffman House, St. Mary's Church and the de Mores packing plant; the TRC Cantonment entry; and SHSND's Chateau materials.
- Built `data/buildings.csv`: 30 structures or groups, graded for location and form.
- Wrote the timeline, geography and overlay plan, sources survey and modeling approach.

**Findings worth noting**
- Hagedorn ch. I gives relative positions for almost every Little Missouri building in September 1883. That is enough for a schematic plan.
- The 1884 Von Hoffman House is recorded by lot and block of the **Original Plat of Medora** and by today's street corner (Broadway and Fifth); St. Mary's (1884) is recorded by today's streets. The modern grid is probably de Mores's plat, which would make the overlay straightforward. (Inferred; needs the recorded plat.)
- **No Sanborn maps** exist for 1880s Medora.
- No photograph of Little Missouri, the Pyramid Park Hotel or the Cantonment has turned up yet.
- The packing plant's dates and capacity differ by source: HAG has a small 1883 plant and a larger one opened June 1, 1885 (100 head a day); NRHP says it was completed in 1883 at 150 a day; the NPS Historical Handbook says 200 a day.

## Open questions

1. Where exactly was Little Missouri? Is there a plat, a railroad station plan or a photo? (Ask SHSND and check Northern Pacific records at the Minnesota Historical Society.)
2. The recorded **Original Plat of Medora**: date, and does it match today's grid? (Billings County Register of Deeds.)
3. The Hotel de Mores: where was it, and what happened to it? Distinct from the Metropolitan?
4. When did the depot move from Little Missouri to Medora?
5. Chateau de Mores: is there a Historic Structure Report or measured drawings, and what outbuildings existed in 1883–86?
6. Was the "town hall" T.R. visited in 1903 the hall over Bill Williams's saloon?
7. Was the Metropolitan's builder, George Fitzgerald, the same man as Little Missouri's section foreman Fitzgerald?

## Next steps

1. Read the Brooks 1957 NPS report (TRC o275515).
2. Request from SHSND: pre-1890 Medora and Little Missouri photos; any Chateau structure report; Goplen 1939.
3. Request the Original Plat of Medora from Billings County.
4. Pull the GLO plat and field notes for T140N R102W (with the Homestead repo).
5. Pull the BadlandsCowboy repo's ads and notices into the gazetteer (names, dates, fires, construction).
6. Do a full building-mention pass through Hagedorn.
7. Start the 2D overlay map (modeling step 2).
