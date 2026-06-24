# CWI Dashboard — design directions (for team review)

Same data, same layout, three visual identities. Pick one (or mix) before we invest in polish.
View any of them **live** by adding `?theme=…` to the dashboard URL:

| Option | Theme param | Feel | Best when the audience is… |
|---|---|---|---|
| **A · Civic Warm** | `?theme=warm` | Warm off-white, teal "wellbeing", Public Sans. Approachable, community-first. | residents / community meetings |
| **B · Government Clean** | `?theme=gov` | White, USWDS navy-blue, accessible. Official and trustworthy. | city council / official site |
| **C · Editorial Dark** | `?theme=dark` | Dark canvas, bright teal, glowing. Striking, presentation-forward. | slides / press / a "wow" demo |

Screenshots: `docs/design-options/A-civic-warm.png`, `B-government-clean.png`, `C-editorial-dark.png`.

## How to run
```bash
cd CWI-Repo && python3 -m http.server
# open  http://localhost:8000/?theme=warm   (or gov, or dark)
```

## Questions to ask the team
1. **Which direction** (A / B / C) fits the audience and the city's brand?
2. **Color of the index ramp** — diverging (low ↔ high, A/C) or sequential (B)? Any city brand colors to honor? Must it be **colorblind-safe / Section 508**?
3. **Default geography** — tract (now) or parcel (once we get the geometry)?
4. **Layout** — keep sidebar + map, or do you want a **dashboard grid** (map + charts) or a **scrollytelling story** for the public page?
5. **Scope of views** — just the map + tract card, or also **compare two tracts**, a **rank table**, and a **methodology page**?

Once a direction is chosen, the rest (legend per domain, compare view, story, polish) builds on it.
