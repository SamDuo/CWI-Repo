/* Portsmouth Community Wellness Index — MapLibre dashboard (tract level).
   No API key (CARTO basemap). Loads data/tracts.geojson.
   3 design directions via ?theme=warm|gov|dark (for stakeholder review). */

const THEMES = {
  // A — Civic Warm: community-first, approachable
  warm: { basemap: "light_all", sel: "#1b2733",
    ramp: ["#b4574e", "#e0a96d", "#efe6d2", "#7bb5a9", "#2f8f83"] },
  // B — Government Clean: official, trustworthy (USWDS-aligned blues)
  gov: { basemap: "light_all", sel: "#1b1b1b",
    ramp: ["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"] },
  // C — Editorial Dark: striking, presentation-forward
  dark: { basemap: "dark_all", sel: "#eef2f4",
    ramp: ["#c1666b", "#d9a05b", "#5d6b74", "#4b9e8e", "#5fd0bf"] },
};
const THEME = new URLSearchParams(location.search).get("theme") || "warm";
const T = THEMES[THEME] || THEMES.warm;
document.body.className = "theme-" + THEME;
const RAMP = T.ramp;

const METRICS = [
  { key: "cwi", label: "Overall CWI" },
  { key: "econ", label: "Economic" },
  { key: "edu", label: "Education" },
  { key: "env", label: "Environment" },
  { key: "infra", label: "Infrastructure" },
  { key: "health", label: "Health & Healthcare" },
  { key: "housing", label: "Housing & Neighborhood" },
  { key: "safety", label: "Safety & Crime" },
];
const DOMAINS = METRICS.slice(1); // for the report card

const $ = (id) => document.getElementById(id);

function quantileBreaks(values, k = 5) {
  const v = values.filter((x) => typeof x === "number").sort((a, b) => a - b);
  if (!v.length) return [0, 0, 0, 0];
  const at = (q) => v[Math.min(v.length - 1, Math.floor(q * v.length))];
  return [at(0.2), at(0.4), at(0.6), at(0.8)];
}

function colorExpr(metric, b) {
  return [
    "step", ["get", metric],
    RAMP[0], b[0], RAMP[1], b[1], RAMP[2], b[2], RAMP[3], b[3], RAMP[4],
  ];
}

function bounds(fc) {
  let mnx = 180, mny = 90, mxx = -180, mxy = -90;
  const walk = (c) => {
    if (typeof c[0] === "number") {
      mnx = Math.min(mnx, c[0]); mxx = Math.max(mxx, c[0]);
      mny = Math.min(mny, c[1]); mxy = Math.max(mxy, c[1]);
    } else c.forEach(walk);
  };
  fc.features.forEach((f) => walk(f.geometry.coordinates));
  return [[mnx, mny], [mxx, mxy]];
}

const map = new maplibregl.Map({
  container: "map",
  style: {
    version: 8,
    sources: {
      carto: {
        type: "raster",
        tiles: ["a", "b", "c", "d"].map(
          (s) => `https://${s}.basemaps.cartocdn.com/${T.basemap}/{z}/{x}/{y}@2x.png`,
        ),
        tileSize: 256,
        attribution: "© OpenStreetMap contributors © CARTO",
      },
    },
    layers: [
      // warm fallback canvas so the map reads cleanly even before/without tiles
      { id: "bg", type: "background", paint: { "background-color": THEME === "dark" ? "#10141a" : "#ece7df" } },
      { id: "carto", type: "raster", source: "carto", paint: { "raster-opacity": 0.9 } },
    ],
  },
  center: [-76.33, 36.83],
  zoom: 11,
  attributionControl: { compact: true },
});
map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

let DATA = null;
let metric = "cwi";

map.on("load", async () => {
  DATA = await fetch("./data/tracts.geojson").then((r) => r.json());
  map.addSource("tracts", { type: "geojson", data: DATA });

  map.addLayer({
    id: "fill",
    type: "fill",
    source: "tracts",
    paint: {
      "fill-color": colorExpr("cwi", quantileBreaks(DATA.features.map((f) => f.properties.cwi))),
      "fill-opacity": 0.82,
    },
  });
  map.addLayer({
    id: "line",
    type: "line",
    source: "tracts",
    paint: { "line-color": "#ffffff", "line-width": 1 },
  });
  map.addLayer({
    id: "sel",
    type: "line",
    source: "tracts",
    paint: { "line-color": T.sel, "line-width": 2.5 },
    filter: ["==", "GEOID", "__none__"],
  });

  map.fitBounds(bounds(DATA), { padding: 40, duration: 0 });

  // metric selector
  const sel = $("metric");
  METRICS.forEach((m) => {
    const o = document.createElement("option");
    o.value = m.key; o.textContent = m.label; sel.appendChild(o);
  });
  sel.addEventListener("change", (e) => setMetric(e.target.value));

  setMetric("cwi");
  cityStat();

  // interactions
  map.on("mousemove", "fill", (e) => {
    map.getCanvas().style.cursor = "pointer";
    const p = e.features[0].properties;
    const tt = $("tooltip");
    tt.innerHTML = `<b>Tract ${p.NAME}</b> · <span class="tt-cwi">${p[metric]}</span> ${labelFor(metric)}`;
    tt.style.left = e.originalEvent.clientX + "px";
    tt.style.top = e.originalEvent.clientY + "px";
    tt.classList.remove("hidden");
  });
  map.on("mouseleave", "fill", () => {
    map.getCanvas().style.cursor = "";
    $("tooltip").classList.add("hidden");
  });
  map.on("click", "fill", (e) => showDetail(e.features[0].properties));
});

function labelFor(k) {
  return (METRICS.find((m) => m.key === k) || {}).label || k;
}

function setMetric(key) {
  metric = key;
  const vals = DATA.features.map((f) => f.properties[key]);
  const b = quantileBreaks(vals);
  map.setPaintProperty("fill", "fill-color", colorExpr(key, b));

  $("legend-name").textContent = labelFor(key);
  $("legend-scale").innerHTML = RAMP.map((c) => `<div style="background:${c}"></div>`).join("");
}

function showDetail(p) {
  $("detail").classList.remove("hidden");
  $("d-name").textContent = "Tract " + p.NAME;
  $("d-cwi").textContent = p.cwi;
  map.setFilter("sel", ["==", "GEOID", p.GEOID]);

  $("d-domains").innerHTML = DOMAINS.map((d) => {
    const v = p[d.key];
    const w = typeof v === "number" ? v : 0;
    return `<div class="drow"><span class="dl">${d.label}</span>
      <span class="dbar"><i style="width:${w}%"></i></span>
      <span class="dv">${typeof v === "number" ? v : "—"}</span></div>`;
  }).join("");

  $("d-foot").textContent = `${p.n_parcels.toLocaleString()} parcels · GEOID ${p.GEOID} · scores 0–100, higher = better.`;
}

function cityStat() {
  const cwis = DATA.features.map((f) => f.properties.cwi).sort((a, b) => a - b);
  const med = cwis[Math.floor(cwis.length / 2)];
  $("stat").innerHTML = `<b>${DATA.features.length}</b> tracts · city median CWI <b>${med}</b>`;
}
