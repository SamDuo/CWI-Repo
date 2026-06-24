# CWI — questions to confirm + things to do

Status: a **tract-level** CWI (`data/tracts.geojson`, 30 Portsmouth tracts, CWI 0–100) is
built and validated at a glance. Before we trust the numbers and go parcel-level, here are the
things to confirm with the researcher and the next actions.

## A. Parcel data — the big unblock
The map is **tract-level only** right now because the **parcel geometry is missing** from
`CWI.zip`: the `SHAPE` column in both CSVs is empty (43 of 36,662 rows), and only the QGIS
*project file* (`Reprojected_MasterPortsmouth.qgz`) is included — that file *points at* an
external parcel layer that wasn't shared.

**To do / to ask the researcher:**
1. Share the **parcel geometry layer** the QGIS project references — a GeoPackage (`.gpkg`),
   shapefile (`.shp`), or parcel GeoJSON — keyed by `PARCELID` (or `OBJECTID`/`fid`).
2. Or point me at **Portsmouth's open parcel GIS** (the data lists `AGENCYURL =
   portsmouthva.gov` IT dept) so I can pull boundaries directly.
3. Confirm the **join key** (`PARCELID`) between the geometry and the CSV.
> Once we have geometry, a parcel-level `parcels.geojson` builds the same way (the script is
> already structured for it). PII note: the raw CSV has owner names + addresses — it stays out
> of the repo; only aggregated/geometry outputs get committed.

## B. Index methodology — confirm these assumptions
The CWI was computed as `Σ(domain weight × domain score)`, domain score = mean of its
(oriented) indicators. Please confirm:

1. **Polarity (most important).** I treated the `*_pct` values as **raw percentiles** and
   **inverted the "bad" ones** so higher = better wellbeing: crime, flood risk, unemployment,
   distance-to-bus, distance-to-hospital, % no-HS-diploma. Kept as-is: % in college,
   walkability, % owner-occupied. **If your standardization already oriented everything (higher
   = better), tell me — I'd remove all inversions** (one-line flip per indicator in
   `build_cwi.py`).
2. **Domain → variable mapping.** Current grouping (see `build_cwi.py DOMAINS`): Economic =
   unemployment; Education = no-HS + in-college; Environment = flood + walkability;
   Infrastructure = bus distance; Health = hospital distance; Housing = owner-occupied; Safety =
   crime. Confirm — e.g. should **walkability** sit under Environment or Infrastructure?
3. **Opportunity-zone flag** (`if_op_zone`) — I **excluded** it from the score (being in an
   opportunity zone isn't itself "wellbeing"; it's context). Keep excluded, or include?
4. **Social & Community (weight 0.099)** has **no indicator** in the data. I **excluded it and
   renormalized** the other 7 weights to sum to 1. Do you have a Social variable (voting %,
   community orgs, survey) to add, or is excluding it fine?
5. **Single-indicator domains.** Economic, Infrastructure, Health, Housing, Safety each rest on
   **one** indicator right now. Acceptable for v1, or add the "No Data" variables from
   `Variables.docx` (housing cost burden, vacancy, median income, green space, etc.)?
6. **Tract vintage.** The data had ~53 distinct GEOIDs but Portsmouth has **30** current (2020)
   tracts — extras are likely an older vintage or boundary spillover. Confirm we use 2020 tracts.
7. **Validation.** Is there a **precomputed CWI** (parcel or tract) to check my numbers against?
   And do the **top/bottom tracts match known neighborhoods** (low: 2105/2120/2118; high:
   2130.02/2127.02/2125)?

## C. Product decisions (for Sam)
1. **Audience** — public-facing city dashboard, or internal staff tool? (drives polish + a11y)
2. **Default level** — tract (clean, available now) vs parcel (needs geometry).
3. **Visual direction** — confirm the civic palette (warm base, teal "wellbeing", colorblind-safe
   diverging, Public Sans) vs an alternative.
4. **Path** — GeoLibre-first preview (load `tracts.geojson` now) → then the custom build.

## D. What you can do right now
- **Preview in GeoLibre:** open geolibre.app → load `data/tracts.geojson` → graduated symbology
  on `cwi` (and per-domain `econ/edu/env/...`) + a legend → optionally a story map. Zero code.
- **Chase the parcel layer** (A.1/A.2) — the single biggest unlock.
- **Send the researcher §B** to lock the methodology.
