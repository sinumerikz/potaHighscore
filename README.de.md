# 🌲 POTA Highscore

*[🇬🇧 English version](README.md)*

Ein inoffizielles Auswertungs-Tool für [Parks on the Air (POTA)](https://parksontheair.com/) –
zeigt Ranglisten nach Aktivierungen, QSOs und Betriebsarten, wahlweise für ein einzelnes Land
oder weltweit über mehrere Länder kombiniert. Optional lässt sich die Auswertung auf eine eigene
Rufzeichen-Liste filtern (z. B. die Mitglieder eines Discord-Servers oder Clubs).

Läuft komplett als statische Webseite (`index.html`, reines HTML/JS, kein Build-Prozess).

> ⚠️ Nicht offiziell mit Parks on the Air verbunden. Nutzt die inoffizielle, undokumentierte
> POTA-API (`api.pota.app`).

---

## Features

### Daten & Filter
- **Länderauswahl**: einzelnes Land, mehrere Länder per Komma (`DE,AT,CH`), oder
  „🌍 Weltweit" (feste Liste aus 19 Ländern)
- **Zeitraum**: letzte 30 Tage, aktuelles Jahr, gesamter Verlauf, oder ein bestimmtes Jahr
  (2018 bis heute)
- **Zwei Datenquellen**:
  - 🚀 **Statischer Tages-Snapshot** (Standard) – lädt eine vorberechnete JSON-Datei aus dem
    Repo, sehr schnell, bis zu 24 Std. alt
  - 🔴 **Live von der POTA-API** – fragt aktuelle Daten in Echtzeit ab, bei großen Auswahlen
    langsamer
- **Rufzeichen-Filter** (einklappbar unter „Erweitert"): nur Rufzeichen aus einer eigenen Liste
  berücksichtigen (URL, Live-Reload mit CORS-Proxy-Fallback, oder manuelles Einfügen)
- **Betriebsart-Filter**: Alle Modes / Nur CW / Nur SSB/Phone / Nur Digital – filtert sowohl die
  Aktivierungen- als auch die QSO-Rangliste

### Tab „Highscore"
- Ranglisten nach meisten Aktivierungen und meisten QSOs, mit CW/SSB/Digital-Aufschlüsselung
  direkt am Rufzeichen
- Übersichtskacheln (Gesamt-Rufzeichen, Aktivierungen, QSOs, Mode-Summen)
- Zeigt zu jedem Rufzeichen den meist aktivierten Park, verlinkt zur POTA-Seite
- Rufzeichen-Suche mit automatischem Sprung zur richtigen Tabellenseite
- Pagination über alle gefundenen Rufzeichen (nicht nur Top 25)
- Jedes Rufzeichen verlinkt direkt zum POTA-Profil

### Tab „Statistiken"
- Interaktives Liniendiagramm (Chart.js): QSOs pro Jahr von 2018 bis heute, mit getrennten Linien
  für Gesamt / CW / SSB / Digital
- Berücksichtigt alle aktuell gewählten Filter (Land, Rufzeichen-Liste, Datenquelle) – nur der
  Zeitraum-Filter wird hier bewusst ignoriert, da es ja gerade um den Verlauf über mehrere Jahre
  geht
- Optionale Einzel-Rufzeichen-Ansicht, um den persönlichen Jahresverlauf einer Person statt der
  gefilterten Gesamtsumme zu sehen

### Sprache
- DE/EN-Umschalter oben rechts im Header – übersetzt die komplette Oberfläche, inklusive
  dynamischer Statusmeldungen, Tabellenüberschriften und Diagramm-Beschriftungen
- Die Auswahl wird lokal gemerkt (kein sichtbarer Hinweis nötig)

### Performance
- Live-Modus-Abfragen laufen über einen kleinen Concurrency-Pool (mehrere Requests parallel statt
  nacheinander)
- API-Antworten werden 12 Stunden lang lokal im Browser zwischengespeichert, still im Hintergrund
- Beim Laden der Aktivierungen wird eine geschätzte Restzeit angezeigt

## Funktionsweise

```
scripts/update_snapshot.py   ──▶  data/pota-snapshot.json  ──▶  index.html
   (läuft täglich per                (statischer Snapshot,       (lädt die Datei
    GitHub Actions)                   im Repo committet)           und wertet sie aus)
```

Ein zeitgesteuerter GitHub-Actions-Workflow lädt Parks und Aktivierungen für die konfigurierten
Länder (Top 150 aktivste Parks pro Land, für Deutschland alle Parks), fragt sie parallel ab und
committet das Ergebnis als `data/pota-snapshot.json`. Die Seite lädt diese Datei im
Snapshot-Modus direkt; der Live-Modus fragt stattdessen direkt `api.pota.app` ab.

## Konfiguration

**`scripts/update_snapshot.py`**
| Variable | Standard | Bedeutung |
|---|---|---|
| `COUNTRIES` | 19 Länder | welche Länder-Programme im Snapshot enthalten sind |
| `PARKS_PER_COUNTRY` | `150` | wie viele der aktivsten Parks pro Land (Standard) |
| `COUNTRY_PARK_LIMITS` | `{"DE": alle}` | Pro-Land-Ausnahmen vom Standard-Limit |
| `MAX_WORKERS` | `12` | Anzahl paralleler Requests |

**`index.html`**
- `WORLD_COUNTRIES` – muss mit `COUNTRIES` im Python-Skript synchron gehalten werden, sonst
  passen „Weltweit"-Auswahl und Snapshot-Inhalt nicht zusammen
- `EMBEDDED_CALL_LIST` – eingebetteter Fallback-Snapshot der Rufzeichen-Filterliste
- `LIVE_CONCURRENCY` – Anzahl paralleler Requests im Live-Modus

## Bekannte Einschränkungen

- **Inoffizielle API**: `api.pota.app` ist nicht dokumentiert, Endpunkte und Feldnamen können
  sich jederzeit ändern. Bei Auffälligkeiten hilft der Bereich „Debug / Rohdaten" mit der
  rohen API-Antwort.
- **Kein P2P (Park-to-Park)**: Der genutzte Endpunkt liefert diese Info nicht, daher zeigt das
  Tool stattdessen eine CW/SSB/Digital-Aufschlüsselung.
- **Mindest-QSO-Regel angewendet**: Aktivierungen mit weniger als 10 QSOs zählen laut POTA-Regeln
  offiziell nicht und werden überall konsequent ausgeschlossen, damit unsere Zahlen mit dem
  offiziellen Leaderboard übereinstimmen.
- **Snapshot ist eine Stichprobe, keine Vollerhebung**: bis auf Deutschland werden nur die
  Top-150-Parks pro Land berücksichtigt, nicht wirklich jeder jemals aktivierte Park.
- **CORS**: Live-Nachladen der externen Rufzeichen-Liste kann an fehlenden CORS-Headern
  scheitern – das Tool versucht dann automatisch einen öffentlichen Proxy und fällt sonst auf
  die eingebettete Liste zurück.

## Lizenz / Haftungsausschluss

Privates Hobby-Projekt, keine Gewähr auf Richtigkeit der Daten. Keine offizielle Verbindung zu
Parks on the Air oder Anthropic/Claude.
