# 🌲 POTA Highscore

Inoffizielles Auswertungs-Tool für [Parks on the Air (POTA)](https://parksontheair.com/) –
zeigt Ranglisten nach Aktivierungen, QSOs und Mode-Verteilung (CW/SSB/Digital),
wahlweise für ein einzelnes Land oder weltweit über mehrere Länder kombiniert.
Optional lässt sich die Auswertung auf eine eigene Rufzeichen-Liste filtern
(z.B. die Mitglieder eines Discord-Servers oder Clubs).

Läuft komplett als statische Webseite (`index.html`, reines HTML/JS, kein
Build-Prozess) und ist für **GitHub Pages** gedacht.

> ⚠️ Nicht offiziell mit Parks on the Air verbunden. Nutzt die inoffizielle,
> undokumentierte POTA-API (`api.pota.app`).

---

## Features

- **Länderauswahl**: einzelnes Land, mehrere Länder per Komma (`DE,AT,CH`),
  oder „🌍 Weltweit" (feste Liste aus 19 Ländern, siehe unten)
- **Zeitraum-Filter**: letzte 30 Tage, aktuelles Jahr, gesamter Verlauf, oder
  ein bestimmtes Jahr (2018 bis heute)
- **Zwei Datenquellen**:
  - 🚀 **Statischer Tages-Snapshot** (Standard) – lädt eine vorberechnete
    JSON-Datei aus dem Repo, extrem schnell, bis zu 24 Std. alt
  - 🔴 **Live von der POTA-API** – fragt aktuelle Daten in Echtzeit ab,
    dauert je nach Land-Auswahl deutlich länger
- **Rufzeichen-Filter** (einklappbar unter „Erweitert"): nur Rufzeichen aus
  einer eigenen Liste berücksichtigen (URL, Live-Reload mit CORS-Proxy-
  Fallback, oder manuelles Einfügen)
- **Ranglisten** nach meisten Aktivierungen und meisten QSOs, mit
  Mode-Aufschlüsselung (CW / SSB / Digital) direkt am Rufzeichen
- **Übersichtskacheln** (Gesamt-Rufzeichen, Aktivierungen, QSOs, CW/SSB/Digital)
- **Rufzeichen-Suche** mit automatischem Sprung zur richtigen Tabellenseite
- **Pagination** für alle gefundenen Rufzeichen (nicht nur Top 25)
- Jedes Rufzeichen verlinkt direkt zum POTA-Profil (`pota.app/#/profile/...`)

## Wie es funktioniert

```
scripts/update_snapshot.py   ──▶  data/pota-snapshot.json  ──▶  index.html
   (läuft täglich per                (statischer Snapshot,       (lädt die Datei
    GitHub Actions)                   im Repo committet)           und wertet sie aus)
```

### Täglicher Snapshot (Standard-Modus)

`.github/workflows/update-snapshot.yml` läuft automatisch **täglich um
04:15 UTC** (per `cron`) und zusätzlich manuell auslösbar über
**Actions → POTA Snapshot aktualisieren → Run workflow**.

Das Skript `scripts/update_snapshot.py`:
1. Lädt die Parkliste für 19 Länder (`COUNTRIES` im Skript).
2. Ermittelt pro Land die aktivsten Parks bis zu einem Limit
   (`PARKS_PER_COUNTRY`, Standard **150** – für Deutschland gilt eine
   Ausnahme in `COUNTRY_PARK_LIMITS`: **alle** jemals aktivierten Parks).
3. Fragt für alle diese Parks die komplette Aktivierungshistorie ab –
   **parallel** (`MAX_WORKERS = 12` gleichzeitige Requests), damit der Lauf
   innerhalb des 6-Stunden-Limits von GitHub Actions bleibt.
4. Schreibt alles gesammelt als eine JSON-Datei nach `data/pota-snapshot.json`
   und committet sie automatisch (nur bei tatsächlichen Änderungen).

Die Webseite lädt im Snapshot-Modus einfach `./data/pota-snapshot.json` und
wertet sie clientseitig aus (Zeitraum- und Rufzeichen-Filter passieren im
Browser, nicht neu von der API).

### Live-Modus

Fragt bei jedem Laden direkt `api.pota.app` ab (Parkliste pro Land, dann pro
Park die Aktivierungen). Bietet aktuellere Daten, ist aber bei „Weltweit"
oder großen Parks-Limits spürbar langsamer (viele einzelne Requests).

## Konfiguration

Alles Wichtige liegt oben in den jeweiligen Dateien als Konstanten:

**`scripts/update_snapshot.py`**
| Variable | Standard | Bedeutung |
|---|---|---|
| `COUNTRIES` | 19 Länder | Welche Länder-Programme im Snapshot enthalten sind |
| `PARKS_PER_COUNTRY` | `150` | Wie viele aktivste Parks pro Land (Standard) |
| `COUNTRY_PARK_LIMITS` | `{"DE": alle}` | Pro-Land-Ausnahmen vom Standard-Limit |
| `MAX_WORKERS` | `12` | Anzahl paralleler Requests |

**`index.html`**
- `WORLD_COUNTRIES` – muss mit `COUNTRIES` im Python-Skript synchron gehalten
  werden, sonst passen „Weltweit"-Auswahl und Snapshot-Inhalt nicht zusammen.
- `EMBEDDED_CALL_LIST` – eingebetteter Snapshot der Rufzeichen-Filterliste
  (Fallback, falls Live-Laden der URL fehlschlägt).

## Hosting (GitHub Pages)

1. Repo-Settings → **Pages** → Source: „Deploy from a branch", Branch `main`,
   Ordner `/ (root)`.
2. Seite ist danach erreichbar unter
   `https://<username>.github.io/<repo-name>/`.
3. Erster Snapshot: einmal manuell **Run workflow** unter dem Actions-Tab
   auslösen, sonst ist `data/pota-snapshot.json` bis zum ersten geplanten
   Lauf noch der leere Platzhalter.

## Bekannte Einschränkungen

- **Inoffizielle API**: `api.pota.app` ist nicht dokumentiert, Feldnamen und
  Endpunkte können sich jederzeit ändern. Bei Problemen hilft der
  „Debug / Rohdaten"-Bereich unten auf der Seite (zeigt das erste rohe
  API-Antwortobjekt).
- **Kein P2P (Park-to-Park)**: Der genutzte Endpunkt
  (`park/activations/{ref}`) liefert diese Zahl nicht mit, daher zeigt das
  Tool stattdessen die Mode-Aufschlüsselung (CW/SSB/Digital).
- **Snapshot ist eine Stichprobe, keine Vollerhebung**: bis auf Deutschland
  werden nur die Top-150-Parks pro Land berücksichtigt, nicht wirklich alle
  jemals aktivierten Parks.
- **CORS**: Live-Nachladen der externen Rufzeichen-Liste kann an fehlenden
  CORS-Headern scheitern – das Tool versucht dann automatisch einen
  öffentlichen Proxy (`allorigins.win`), fällt sonst auf die eingebettete
  Liste zurück.

## Lizenz / Haftungsausschluss

Privates Hobby-Projekt, keine Gewähr auf Richtigkeit der Daten. Keine
offizielle Verbindung zu Parks on the Air oder Anthropic/Claude.
