# 🌲 POTA Highscore

*[🇩🇪 Deutsche Version](README.de.md)*

An unofficial evaluation tool for [Parks on the Air (POTA)](https://parksontheair.com/) — shows
leaderboards for activations, QSOs and operating modes, either for a single country or worldwide
across multiple countries combined. Optionally filters the results down to a custom list of
callsigns (e.g. the members of a Discord server or club).

Runs entirely as a static webpage (`index.html`, plain HTML/JS, no build step).

> ⚠️ Not officially affiliated with Parks on the Air. Uses the unofficial, undocumented POTA API
> (`api.pota.app`).

---

## Features

### Data & filtering
- **Country selection**: a single country, several countries comma-separated (`DE,AT,CH`), or
  "🌍 Worldwide" (a fixed list of 19 countries)
- **Time range**: last 30 days, current year, all time, or a specific year (2018 to today)
- **Two data sources**:
  - 🚀 **Static daily snapshot** (default) — loads a pre-computed JSON file from the repo, very
    fast, up to 24h old
  - 🔴 **Live from the POTA API** — queries current data in real time; slower for large selections
- **Callsign filter** (collapsible under "Advanced"): only include callsigns from a custom list
  (URL, live-reload with a CORS-proxy fallback, or paste manually)
- **Mode filter**: All modes / CW only / SSB/Phone only / Digital only — filters both the
  activations and QSO rankings

### Highscore tab
- Rankings by most activations and most QSOs, with a CW/SSB/Digital breakdown right on each
  callsign
- Summary tiles (total callsigns, activations, QSOs, per-mode totals)
- Shows each callsign's most-activated park, linked to its POTA page
- Callsign search that jumps straight to the right page in the ranking
- Pagination across all found callsigns (not just the top 25)
- Every callsign links directly to its POTA profile

### Statistics tab
- Interactive line chart (Chart.js): QSOs per year from 2018 to today, with separate lines for
  Total / CW / SSB / Digital
- Respects all currently selected filters (country, callsign list, data source) — only the time
  range filter is ignored here, since the whole point is the multi-year trend
- Optional single-callsign view to see one person's personal year-by-year trend instead of the
  filtered total

### Language
- DE/EN switch top-right in the header — translates the entire UI, including dynamic status
  messages, table headers, and chart labels
- Choice is remembered locally (no visible toggle needed)

### Performance
- Live-mode requests run through a small concurrency pool (several requests in parallel instead
  of one after another)
- API responses are cached locally in the browser for 12 hours, silently in the background
- An estimated time remaining is shown while activations are loading

## How it works

```
scripts/update_snapshot.py   ──▶  data/pota-snapshot.json  ──▶  index.html
   (runs daily via                  (static snapshot,             (loads the file
    GitHub Actions)                  committed to the repo)         and evaluates it)
```

A scheduled GitHub Actions workflow fetches parks and activations for the configured countries
(top 150 most active parks per country, all parks for Germany), queries them in parallel, and
commits the result as `data/pota-snapshot.json`. The page loads that file directly in snapshot
mode; live mode queries `api.pota.app` directly instead.

## Configuration

**`scripts/update_snapshot.py`**
| Variable | Default | Meaning |
|---|---|---|
| `COUNTRIES` | 19 countries | which country programs are included in the snapshot |
| `PARKS_PER_COUNTRY` | `150` | how many of the most active parks per country (default) |
| `COUNTRY_PARK_LIMITS` | `{"DE": all}` | per-country overrides of the default limit |
| `MAX_WORKERS` | `12` | number of parallel requests |

**`index.html`**
- `WORLD_COUNTRIES` — must be kept in sync with `COUNTRIES` in the Python script, otherwise
  "Worldwide" selection and snapshot content won't match
- `EMBEDDED_CALL_LIST` — embedded fallback snapshot of the callsign filter list
- `LIVE_CONCURRENCY` — number of parallel requests in live mode

## Known limitations

- **Unofficial API**: `api.pota.app` is undocumented; endpoints and field names may change at any
  time. If something looks off, check the "Debug / raw data" section for the raw API response.
- **No P2P (park-to-park) numbers**: the endpoint used doesn't provide this, so the tool shows a
  CW/SSB/Digital breakdown instead.
- **Minimum QSO rule applied**: activations with fewer than 10 QSOs don't officially count per
  POTA rules and are excluded everywhere, to match the official leaderboard.
- **Snapshot is a sample, not a full census**: except for Germany, only the top 150 parks per
  country are included, not literally every park ever activated.
- **CORS**: live-reloading the external callsign list can fail due to missing CORS headers; the
  tool then automatically tries a public proxy, and falls back to the embedded list if that fails
  too.

## License / disclaimer

Personal hobby project, no guarantee of data accuracy. No official affiliation with Parks on the
Air or Anthropic/Claude.
