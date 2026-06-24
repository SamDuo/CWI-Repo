# CWI — Community Wellness Index Dashboard (Portsmouth, VA)

A dashboard for the **Community Wellness Index (CWI)** for the City of Portsmouth — a composite
of 8 weighted domains (Economic, Housing/Neighborhood, Safety/Crime, Education, Health/
Healthcare, Environment, Social/Community, Infrastructure) over census tracts and parcels.

North star: **GeoLibre** patterns (open browser GIS) on an open stack (MapLibre + shadcn) —
deliberately distinct from any other in-house product. See `docs/CWI_DASHBOARD_PLAN.md`.

## Status
- ✅ **Tract-level CWI** built: `data/tracts.geojson` (30 tracts, CWI 0–100 + 7 domain scores).
- ⏳ **Parcel-level** pending the parcel geometry layer (not in the source zip). See
  `docs/cwi_methodology_notes.md` §A.
- ⏳ Dashboard UI — next, after methodology is confirmed.

## Data pipeline
```bash
# point at your local extraction of CWI.zip (the raw CSV is gitignored — it has PII)
export CWI_RAW_CSV="/path/to/standardized_csv_combined_data_pct.csv"
python3 data/build_cwi.py        # -> data/tracts.geojson
```
The script aggregates the standardized parcel indicators to tract, orients them (polarity),
computes `Σ(weight × domain score)`, and joins to public Census TIGER tract geometry (FIPS 51740).

## Important
- **Never commit the raw CSV** — it contains owner names + mailing addresses (PII). `.gitignore`
  blocks `*.csv`/`*.zip`. Only aggregated, no-PII outputs (`tracts.geojson`) are committed.
- The index **methodology has open assumptions to confirm** (polarity, domain mapping, the
  no-data Social domain). See `docs/cwi_methodology_notes.md` §B before trusting the numbers.

## Docs
- `docs/CWI_DASHBOARD_PLAN.md` — full build plan (GeoLibre-borrowed patterns, stack, phases).
- `docs/cwi_methodology_notes.md` — questions to confirm + next actions.
