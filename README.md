# TRsMedora

Visualizing what Medora looked like during Theodore Roosevelt's time.

This is an internal experiment by the Theodore Roosevelt Presidential Library. It rebuilds the two towns of Roosevelt's ranching years as a map, with a simple 3D model to follow. Those towns are Little Missouri on the west bank of the Little Missouri River and Medora on the east bank, plus the Chateau de Mores. The map shows how they changed from his arrival in September 1883 to the hard winter of 1886–87.

**Map:** https://trsmedora.labs.trlibrary.com/map/ (source in `map/`).
**3D:** https://trsmedora.labs.trlibrary.com/map3d/ (source in `map3d/`; data from `tools/build_3d.py`).

## What is here

| Path | What it is |
|---|---|
| `map3d/` | The 3D massing model: lidar terrain, buildings with measured or estimated heights, the four dates, and views from the solved photo cameras with the photo overlaid |
| `map/` | The 2D map: four dates, the 1883 plat fitted to today's map, the 1883 river channel, today's lots, and building details with sources |
| `data/buildings.csv` | Gazetteer: every known structure with dates, form, placement method, confidence grades, evidence, sources and photos. **Generated, so edit `tools/build_features.py` instead.** |
| `data/sources/cowboy_building_mentions_1884-1886.csv` | Every building mention in the *Bad Lands Cow Boy*, 1884–86 (446 rows, OCR-checked) |
| `data/site_photos_2026/` | Matt Briney's 2026 photos of the Historic Medora panels and of buildings today (reference only) |
| `data/photo_catalog_1880s.csv` | Every 1880s Medora image checked online (SHSND, MHS, Harvard), with what each one was used for |
| `data/photos_trc_ranching_in_dakota.csv` | The 209 Harvard "Ranching in Dakota" photos, tagged and linked to buildings |
| `data/reference/` | Today's lots (ND GIS Hub), survey sections, OpenStreetMap extract, and the plat fit (control points) |
| `tools/photomatch/`, `data/photomatch/` | Camera solving and back-projection for period photos, and the solved cameras |
| `tools/build_features.py` | The single spec for all historic features; writes the gazetteer and the map data |
| `docs/research-log.md` | What has been done and found, and next steps |
| `docs/timeline.md` | How the towns changed, 1879–1888 |
| `docs/geography-and-overlay.md` | How the plat was fitted and how each building is placed |
| `docs/sources.md` | Source keys, archives, photos, maps and what is still to read |
| `docs/photo-matching.md` | How buildings are placed from period photos, with results |
| `docs/archive-requests.md` | Exact citations to request from SHSND, MHS, MNHS and others |
| `docs/arrival-train.md` | The train T.R. arrived on, and images of it |
| `docs/modeling-approach.md` | Plan for the map and the 3D model |

## Confidence grades

Each building has a separate grade for **location** and for **form**:

- **A, documented.** It survives, or there are measurements plus photos.
- **B, supported.** A period photo or a specific written description.
- **C, inferred.** Reasoned from written sources.
- **D, conjectural.** Known to exist; the placement or shape is a placeholder.

## Updating the data

```
pip install shapely numpy
python3 tools/build_features.py
python3 tools/build_3d.py
```

Then open the map from a web server, for example `python3 -m http.server` in the `map/` folder.

## Image rights

The map links out to photographs rather than copying them. The 1883 plat is shown from the State Historical Society of North Dakota's public web image. Order a high-resolution copy and check terms before any public use. Montana Historical Society images are for educational use only without permission.
