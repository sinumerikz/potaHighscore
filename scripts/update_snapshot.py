#!/usr/bin/env python3
"""
Erzeugt einen statischen JSON-Snapshot der POTA-Aktivierungsdaten
für die konfigurierten Länder und speichert ihn unter data/pota-snapshot.json.

Fragt die Park-Aktivierungen PARALLEL ab (statt nacheinander), damit auch
mehrere hundert Parks pro Land in vertretbarer Zeit (innerhalb des
6-Stunden-Limits von GitHub Actions) durchlaufen werden können.

Wird von .github/workflows/update-snapshot.yml täglich automatisch ausgeführt
(läuft auf den GitHub-Actions-Runnern, die eigenen Internetzugang haben).

Lokal manuell ausführen:
    pip install requests
    python3 scripts/update_snapshot.py
"""

import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests

API = "https://api.pota.app"

# Gleiche Länderliste wie im Frontend (WORLD_COUNTRIES in index.html).
# Bei Bedarf hier UND im Frontend synchron halten.
COUNTRIES = ["DE", "AT", "CH", "HR", "GB", "FR", "ES", "IT", "NL", "BE",
             "PL", "DK", "SE", "NO", "FI", "US", "CA", "AU", "JP"]

# Wie viele der aktivsten Parks pro Land berücksichtigt werden (Standard für
# alle Länder ohne eigene Ausnahme in COUNTRY_PARK_LIMITS unten).
PARKS_PER_COUNTRY = int(os.environ.get("PARKS_PER_COUNTRY", "150"))

# Pro-Land-Ausnahmen: überschreiben PARKS_PER_COUNTRY für einzelne Länder.
# Deutschland: alle jemals aktivierten Parks laden (kein Limit).
# Weitere Ausnahmen einfach als zusätzliche Zeile ergänzen, z.B. "AT": 500.
COUNTRY_PARK_LIMITS = {
    "DE": int(os.environ.get("PARKS_PER_COUNTRY_DE", "999999")),
}


def limit_for_country(cc):
    return COUNTRY_PARK_LIMITS.get(cc, PARKS_PER_COUNTRY)


# Wie viele Park-Aktivierungs-Abfragen gleichzeitig laufen.
# Höher = schneller, aber mehr Last auf den (inoffiziellen!) POTA-Servern
# und höheres Risiko von Rate-Limiting/Fehlern. 10-15 ist ein vernünftiger
# Mittelweg.
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "12"))

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pota-snapshot.json")

# Eine gemeinsame Session pro Thread (Connection-Pooling), statt für jeden
# Request eine neue Verbindung aufzubauen.
_thread_local = threading.local()


def get_session():
    if not hasattr(_thread_local, "session"):
        _thread_local.session = requests.Session()
    return _thread_local.session


def fetch_json(url, retries=3):
    last_err = None
    session = get_session()
    for attempt in range(retries):
        try:
            resp = session.get(url, headers={"Accept": "application/json"}, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.0 * (attempt + 1))
    print(f"  WARNUNG: {url} fehlgeschlagen nach {retries} Versuchen: {last_err}", file=sys.stderr)
    return None


def top_activated_parks(parks, n):
    activated = [p for p in parks if (p.get("activations") or 0) > 0]
    activated.sort(key=lambda p: p.get("activations") or 0, reverse=True)
    return activated[:n]


def fetch_park_activations(cc, ref):
    """Wird parallel für jeden Park aufgerufen. Gibt (cc, ref, activations|None) zurück."""
    acts = fetch_json(f"{API}/park/activations/{ref}?count=all")
    if not isinstance(acts, list):
        return cc, ref, None
    for act in acts:
        act["_country"] = cc
        act["_parkRef"] = ref
    return cc, ref, acts


def main():
    start_time = time.time()

    # 1) Parklisten pro Land laden (sequenziell, nur 19 schnelle Requests)
    countries_ok = []
    countries_failed = []
    park_jobs = []  # Liste von (country, ref)

    for i, cc in enumerate(COUNTRIES, start=1):
        print(f"[{i}/{len(COUNTRIES)}] Lade Parkliste für {cc} ...")
        parks = fetch_json(f"{API}/program/parks/{cc}")
        if not parks:
            countries_failed.append(cc)
            continue
        countries_ok.append(cc)

        cc_limit = limit_for_country(cc)
        top_parks = top_activated_parks(parks, cc_limit)
        limit_label = "alle" if cc_limit >= 99999 else str(cc_limit)
        print(f"    {len(top_parks)} Parks werden zur Abfrage vorgemerkt (Limit: {limit_label}) ...")

        for park in top_parks:
            ref = park.get("reference") or park.get("ref")
            if ref:
                park_jobs.append((cc, ref))

    # 2) Alle Park-Aktivierungen PARALLEL abfragen
    total = len(park_jobs)
    print(f"\nStarte parallele Abfrage von {total} Parks mit {MAX_WORKERS} gleichzeitigen Requests ...")

    all_activations = []
    done = 0
    failed_parks = 0
    progress_lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_park_activations, cc, ref) for cc, ref in park_jobs]

        for future in as_completed(futures):
            cc, ref, acts = future.result()
            with progress_lock:
                done += 1
                if acts is None:
                    failed_parks += 1
                else:
                    all_activations.extend(acts)
                if done % 50 == 0 or done == total:
                    elapsed = time.time() - start_time
                    print(f"  {done}/{total} Parks abgefragt "
                          f"({len(all_activations)} Aktivierungen bisher, "
                          f"{elapsed:.0f}s vergangen) ...")

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "parks_per_country": PARKS_PER_COUNTRY,
        "parks_per_country_by_country": {cc: limit_for_country(cc) for cc in COUNTRIES},
        "countries_requested": COUNTRIES,
        "countries_ok": countries_ok,
        "countries_failed": countries_failed,
        "activation_count": len(all_activations),
        "activations": all_activations,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, separators=(",", ":"))

    elapsed_total = time.time() - start_time
    print(f"\nFertig in {elapsed_total/60:.1f} Min.: {len(all_activations)} Aktivierungen aus "
          f"{len(countries_ok)} Ländern gespeichert in {OUTPUT_PATH}")
    if failed_parks:
        print(f"Übersprungen (Park-Abfrage fehlgeschlagen): {failed_parks} von {total} Parks")
    if countries_failed:
        print(f"Übersprungen (Land komplett fehlgeschlagen): {', '.join(countries_failed)}")


if __name__ == "__main__":
    main()
