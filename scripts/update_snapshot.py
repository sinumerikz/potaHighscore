#!/usr/bin/env python3
"""
Erzeugt einen statischen JSON-Snapshot der POTA-Aktivierungsdaten
für die konfigurierten Länder und speichert ihn unter data/pota-snapshot.json.

Wird von .github/workflows/update-snapshot.yml täglich automatisch ausgeführt
(läuft auf den GitHub-Actions-Runnern, die eigenen Internetzugang haben).

Lokal manuell ausführen:
    pip install requests
    python3 scripts/update_snapshot.py
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

API = "https://api.pota.app"

# Gleiche Länderliste wie im Frontend (WORLD_COUNTRIES in index.html).
# Bei Bedarf hier UND im Frontend synchron halten.
COUNTRIES = ["DE", "AT", "CH", "HR", "GB", "FR", "ES", "IT", "NL", "BE",
             "PL", "DK", "SE", "NO", "FI", "US", "CA", "AU", "JP"]

# Wie viele der aktivsten Parks pro Land berücksichtigt werden.
# Höher = vollständiger, aber deutlich mehr API-Calls und längere Laufzeit.
PARKS_PER_COUNTRY = int(os.environ.get("PARKS_PER_COUNTRY", "60"))

# Kleine Pause zwischen Requests, um die POTA-Server nicht zu stark zu belasten.
REQUEST_DELAY_SEC = float(os.environ.get("REQUEST_DELAY_SEC", "0.2"))

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pota-snapshot.json")


def fetch_json(url, retries=3):
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers={"Accept": "application/json"}, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    print(f"  WARNUNG: {url} fehlgeschlagen nach {retries} Versuchen: {last_err}", file=sys.stderr)
    return None


def top_activated_parks(parks, n):
    activated = [p for p in parks if (p.get("activations") or 0) > 0]
    activated.sort(key=lambda p: p.get("activations") or 0, reverse=True)
    return activated[:n]


def main():
    all_activations = []
    countries_ok = []
    countries_failed = []

    for i, cc in enumerate(COUNTRIES, start=1):
        print(f"[{i}/{len(COUNTRIES)}] Lade Parkliste für {cc} ...")
        parks = fetch_json(f"{API}/program/parks/{cc}")
        if not parks:
            countries_failed.append(cc)
            continue
        countries_ok.append(cc)

        top_parks = top_activated_parks(parks, PARKS_PER_COUNTRY)
        print(f"    {len(top_parks)} aktivste Parks werden abgefragt ...")

        for j, park in enumerate(top_parks, start=1):
            ref = park.get("reference") or park.get("ref")
            if not ref:
                continue
            acts = fetch_json(f"{API}/park/activations/{ref}?count=all")
            time.sleep(REQUEST_DELAY_SEC)
            if not isinstance(acts, list):
                continue
            for act in acts:
                act["_country"] = cc
                act["_parkRef"] = ref
                all_activations.append(act)

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "parks_per_country": PARKS_PER_COUNTRY,
        "countries_requested": COUNTRIES,
        "countries_ok": countries_ok,
        "countries_failed": countries_failed,
        "activation_count": len(all_activations),
        "activations": all_activations,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, separators=(",", ":"))

    print(f"\nFertig: {len(all_activations)} Aktivierungen aus {len(countries_ok)} Ländern "
          f"gespeichert in {OUTPUT_PATH}")
    if countries_failed:
        print(f"Übersprungen (Fehler): {', '.join(countries_failed)}")


if __name__ == "__main__":
    main()
