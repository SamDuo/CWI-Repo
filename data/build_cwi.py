#!/usr/bin/env python3
"""
Build the tract-level Community Wellness Index (CWI) GeoJSON for Portsmouth, VA
(FIPS 51740) from the researcher's standardized parcel CSV.

WHY TRACT LEVEL: the parcel geometry is NOT in CWI.zip (the SHAPE column is empty;
only the QGIS *project* file is included, which points at an external parcel layer).
So we aggregate the parcel rows to their census tract (Cen_GEOID), compute the CWI
per tract, and join to the PUBLIC Census TIGER tract geometry. When the researcher
shares the parcel layer, a parcel-level build can be added the same way.

PII: the raw CSV contains OWNERNME1 + mailing addresses. It must NEVER be committed.
Only the aggregated `tracts.geojson` (no PII) is an output. See .gitignore.

ASSUMPTIONS TO CONFIRM WITH THE RESEARCHER (see cwi_methodology_notes.md):
  1. The *_pct values are raw percentiles (0..1) with NO polarity applied yet, so we
     invert "bad" indicators here (POLARITY below). If the researcher already oriented
     them so higher = better, set every POLARITY entry to False.
  2. Variable -> domain mapping (DOMAINS below). Some domains rest on one indicator.
  3. Social_Community has NO indicator in this file -> it is EXCLUDED and the remaining
     7 domain weights are renormalized to sum to 1. Confirm or supply a Social variable.
"""

import csv
import json
import urllib.request
import os

# --- paths -------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
# The raw standardized CSV (kept OUT of the repo — PII + 18 MB). Point this at your
# local extraction of CWI.zip.
RAW_CSV = os.environ.get(
    "CWI_RAW_CSV",
    "/tmp/claude-1000/-workspaces-polymetron/bbb44459-7126-4ea8-bde8-b512e972d316/"
    "scratchpad/cwi/CWI/Processed Data/standardized_csv_combined_data_pct.csv",
)
OUT_GEOJSON = os.path.join(HERE, "tracts.geojson")

# --- domain weights (from "Normalized Index Weight.png") ---------------------
WEIGHTS = {
    "Economic": 0.145859,
    "Education": 0.137637,
    "Environment": 0.114495,
    "Infrastructure": 0.088916,
    "Health_Healthcare": 0.133983,
    "Housing_Neighborhood": 0.140378,
    "Safety_Crime": 0.140073,
    "Social_Community": 0.098660,  # no indicator in data -> excluded below
}

# --- indicator columns (header name -> True if "higher value is BAD" -> invert) --
# POLARITY[col] = True  means we transform v -> (1 - v) so the indicator becomes
# "higher = better wellbeing" before averaging into its domain.
POLARITY = {
    "NUMPOINTS_cime_data": True,       # more crime = worse
    "RISK_SCORE_flood": True,          # more flood risk = worse
    "HubDist_bus_stop": True,          # farther from transit = worse
    "HubDist_hospital": True,          # farther from a hospital = worse
    "NatWalkInd_walking_index": False, # more walkable = better
    "pct_own_occ_hous_unit": False,    # more owner-occupied = better
    "pct_unemp_rate_16yover": True,    # more unemployment = worse
    "pct_no_high_schl_dip": True,      # more without diploma = worse
    "pct_in_college": False,           # more in college = better
}

# --- which indicators make up each domain ------------------------------------
DOMAINS = {
    "Economic": ["pct_unemp_rate_16yover"],
    "Education": ["pct_no_high_schl_dip", "pct_in_college"],
    "Environment": ["RISK_SCORE_flood", "NatWalkInd_walking_index"],
    "Infrastructure": ["HubDist_bus_stop"],
    "Health_Healthcare": ["HubDist_hospital"],
    "Housing_Neighborhood": ["pct_own_occ_hous_unit"],
    "Safety_Crime": ["NUMPOINTS_cime_data"],
    "Social_Community": [],  # no data
}
# Short keys for the GeoJSON properties.
DOMAIN_KEY = {
    "Economic": "econ", "Education": "edu", "Environment": "env",
    "Infrastructure": "infra", "Health_Healthcare": "health",
    "Housing_Neighborhood": "housing", "Safety_Crime": "safety",
    "Social_Community": "social",
}

GEOID_COL = "Cen_GEOID"
NAME_COL = "Cen_NAME"

TIGER = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
    "Tracts_Blocks/MapServer/0/query?where=STATE%3D%2751%27+AND+COUNTY%3D%27740%27"
    "&outFields=GEOID,NAME&returnGeometry=true&outSR=4326&f=geojson"
)


def norm_geoid(raw: str) -> str:
    """'51740211900.0' -> '51740211900'."""
    raw = (raw or "").strip()
    if raw.endswith(".0"):
        raw = raw[:-2]
    return raw


def fnum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def main():
    # 1) aggregate indicators to tract (mean over parcels) -------------------
    indicators = list(POLARITY.keys())
    sums = {}   # geoid -> {indicator: [sum, count]}
    names = {}
    counts = {}
    with open(RAW_CSV, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g = norm_geoid(row.get(GEOID_COL, ""))
            if not g or len(g) < 11:
                continue
            names.setdefault(g, (row.get(NAME_COL) or "").strip())
            counts[g] = counts.get(g, 0) + 1
            d = sums.setdefault(g, {k: [0.0, 0] for k in indicators})
            for k in indicators:
                v = fnum(row.get(k))
                if v is not None:
                    d[k][0] += v
                    d[k][1] += 1

    # 2) per-tract indicator means, polarity, domain scores, CWI ------------
    active_weight = sum(w for dom, w in WEIGHTS.items() if DOMAINS[dom])
    tract_props = {}
    for g, agg in sums.items():
        means = {}
        for k in indicators:
            tot, n = agg[k]
            if n == 0:
                continue
            m = tot / n
            means[k] = (1.0 - m) if POLARITY[k] else m  # orient higher = better

        domain_scores = {}
        for dom, cols in DOMAINS.items():
            vals = [means[c] for c in cols if c in means]
            if vals:
                domain_scores[dom] = sum(vals) / len(vals)

        # CWI = weighted mean over domains-with-data, weights renormalized to 1.
        cwi = sum(WEIGHTS[dom] * s for dom, s in domain_scores.items()) / active_weight

        props = {
            "GEOID": g,
            "NAME": names.get(g, ""),
            "n_parcels": counts.get(g, 0),
            "cwi": round(cwi * 100, 1),
        }
        for dom, s in domain_scores.items():
            props[DOMAIN_KEY[dom]] = round(s * 100, 1)
        # raw (oriented) indicator means too, for the report card
        for k, m in means.items():
            props[f"ind_{k}"] = round(m * 100, 1)
        tract_props[g] = props

    # 3) fetch TIGER tract geometry + join ----------------------------------
    print(f"Fetching tract geometry for {len(tract_props)} Portsmouth tracts…")
    with urllib.request.urlopen(TIGER, timeout=60) as resp:
        geo = json.load(resp)

    out_features = []
    matched = 0
    for feat in geo.get("features", []):
        g = norm_geoid(str(feat["properties"].get("GEOID", "")))
        props = tract_props.get(g)
        if not props:
            continue
        matched += 1
        out_features.append(
            {"type": "Feature", "geometry": feat["geometry"], "properties": props}
        )

    fc = {
        "type": "FeatureCollection",
        "metadata": {
            "title": "Portsmouth Community Wellness Index (tract level)",
            "fips": "51740",
            "domains_used": [d for d in DOMAINS if DOMAINS[d]],
            "domains_excluded_no_data": [d for d in DOMAINS if not DOMAINS[d]],
            "weights": WEIGHTS,
            "note": "CWI 0-100, higher = better. Social_Community excluded (no data); "
            "remaining weights renormalized. Polarity per POLARITY in build_cwi.py "
            "(CONFIRM with researcher).",
        },
        "features": out_features,
    }
    with open(OUT_GEOJSON, "w") as f:
        json.dump(fc, f)

    # 4) validation summary --------------------------------------------------
    cwis = sorted(((p["cwi"], p["GEOID"], p["NAME"]) for p in tract_props.values()))
    print(f"Joined geometry for {matched}/{len(tract_props)} tracts -> {OUT_GEOJSON}")
    if cwis:
        lo = cwis[0]
        hi = cwis[-1]
        mid = cwis[len(cwis) // 2]
        print(f"CWI range: {lo[0]} ({lo[2]}) … median {mid[0]} … {hi[0]} ({hi[2]})")
        print("Lowest 3:", [(c[0], c[2]) for c in cwis[:3]])
        print("Highest 3:", [(c[0], c[2]) for c in cwis[-3:]])


if __name__ == "__main__":
    main()
