# TRsMedora

Visualizing what Medora looked like during Theodore Roosevelt's time.

An internal Theodore Roosevelt Presidential Library experiment. The goal is to rebuild the two Little Missouri River towns of Roosevelt's ranching years, and the Chateau de Mores above them, as a map and a simple 3D model. The model should show how they changed from his arrival in September 1883 to his retreat from ranching after the winter of 1886–87.

## The two towns

- **Little Missouri** was the older settlement on the **west bank**. It grew up around an abandoned army post (the Cantonment) and a railroad "depot" shack. It had the Pyramid Park Hotel, where Roosevelt slept his first night (September 7–8, 1883).
- **Medora** was founded on the **east bank** in April 1883 by the Marquis de Mores and named for his wife. By the end of 1884 it had 251 permanent residents and had largely absorbed Little Missouri.
- **The Chateau de Mores** sits on the bench above the west bank, about half a mile southwest of Medora. It still stands.

## Scope (phase 1)

| | |
|---|---|
| Period | September 1883 to 1887, shown as time slices (see [docs/timeline.md](docs/timeline.md)) |
| Area | Little Missouri, Medora, the de Mores packing plant, the Chateau |
| Model | Simple massing (boxes and gable roofs) with basic materials, on real terrain |
| Standard | Educated guesses are fine when they rest on evidence. Every building carries a confidence grade. |
| Audience | Internal staff, to see what is possible |

## What is here

| Path | What it is |
|---|---|
| [docs/research-log.md](docs/research-log.md) | Dated log of what has been looked at and found |
| [docs/timeline.md](docs/timeline.md) | How the towns changed, 1879–1888, with sources. This drives the time slices. |
| [docs/geography-and-overlay.md](docs/geography-and-overlay.md) | Where things were, and how to line the old towns up with today's Medora |
| [docs/sources.md](docs/sources.md) | Survey of archives, photos, maps and texts, with access notes |
| [docs/modeling-approach.md](docs/modeling-approach.md) | Plan for the map overlay and the 3D model |
| [data/buildings.csv](data/buildings.csv) | Gazetteer: one row per known structure, with dates, form, location evidence, confidence and sources |
| [data/photos_trc_ranching_in_dakota.csv](data/photos_trc_ranching_in_dakota.csv) | All 209 photos in the Harvard "Ranching in Dakota" collection (via trphotos.labs.trlibrary.com), tagged by relevance and linked to buildings |

## Confidence grades

Used in `buildings.csv` separately for **location** and **form**:

- **A, documented.** The building survives, or measured drawings or written dimensions plus photos exist.
- **B, supported.** Period photo or specific written description, but no measurements.
- **C, inferred.** Located or shaped by reasoning from written sources (for example, "south of the track, next door to Nelson's store").
- **D, conjectural.** The building is known to exist, but its placement or form is a placeholder.

The model should show the grade visually so no one mistakes a guess for a fact.

## Status

October 2026: research seeded; nothing modeled yet. See the research log for next steps.
