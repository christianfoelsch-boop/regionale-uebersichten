# Projekt: Ü50-Spielplan SpG Veritas/ESV Wittenberge

Dieser Bereich enthält eine statische GitHub-Pages-Seite für die
**SpG Veritas/ESV Wittenberge**, **Altsenioren Ü50 Staffel A**, Saison
**2026/2027**.

## Dateien

- `index.html`: Darstellung, Kreuztabelle, Spielpläne, Druckansichten, Quellenlink und Fallback-Daten
- `druck.html`: A4-optimierte Druckansicht für Wittenberge oder die gesamte Staffel
- `ue50-spiele.json`: getrennte Spielplandaten

## Datenformat

Die Daten enthalten `teams` und `games`. Spielreferenzen verwenden stabile Team-IDs.

Ein Spiel:

```json
{
  "nr": "610639002",
  "date": "2026-09-02",
  "time": "18:30",
  "home": "wittenberge",
  "away": "perleberg",
  "status": "scheduled"
}
```

Optional:

- `result`: Ergebnis als Text, z. B. `"2:1"`
- `venue`: Spielort
- `status`: `scheduled`, `postponed`, `cancelled`, `finished`

## Grundregeln

- rein statisch, ohne Serverlogik
- keine Frameworks, keine Build-Tools, keine externen Fonts
- JSON bleibt von Darstellung getrennt
- Wittenberge bleibt Fokusmannschaft
- Kreuztabelle: Zeile = Heimteam, Spalte = Gastteam
- eingebettete Fallback-Daten in `index.html` erhalten
- bei Schemaänderungen diese Datei aktualisieren

## Aktueller Stand

- 5 Mannschaften
- 20 Staffelspiele
- 8 Wittenberge-Spiele
- konkrete FUSSBALL.DE-Links in `source.leagueUrl` und `source.teamUrl`
- eigene A4-Druckansicht über `druck.html?typ=wittenberge` und `druck.html?typ=staffel`
