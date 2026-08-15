# AGENTS.md

## Vor jeder Änderung

1. Lies zuerst `PROJECT_CONTEXT.md`.
2. Lies bei Deployment-/Einrichtungsfragen zusätzlich `README.md`.
3. Prüfe `TODO.md`, wenn es um den nächsten Projektschritt geht.

## Projektregeln

- Halte die Website statisch und GitHub-Pages-kompatibel.
- Verwende für die Daten weiterhin JSON-Dateien im Repository.
- Keine Zugangsdaten, Tokens, Passwörter oder privaten Schlüssel committen.
- Keine Analytics-, Tracking-, Werbe- oder Social-Media-Skripte hinzufügen.
- Keine Cookies oder Nutzerprofile hinzufügen.
- Keine externen Fonts oder automatisch eingebetteten Drittanbieterinhalte hinzufügen.
- Keine fremden Händler-, Marken- oder Vereinslogos/Prospektbilder hinzufügen.
- Impressum, Datenschutz und Quellenhinweise nicht entfernen.
- Bereits eingetragene persönliche Pflichtangaben nicht ohne ausdrücklichen Auftrag ändern.
- Externe Datenquellen möglichst als normale Links kennzeichnen.
- Bei Scraper-Änderungen bestehende Fallback-Daten nicht unnötig löschen.
- UI-Änderungen responsive, mobilfreundlich und möglichst TV-tauglich halten.

## Dateien

- `angebote/index.html`: Angebotsansicht
- `angebote/angebote.json`: Angebotsdaten
- `fussball/index.html`: Fußballansicht
- `fussball/spiele.json`: Fußballdaten
- `scripts/update_angebote.py`: Angebots-Updater
- `scripts/update_fussball.py`: Fußball-Updater
- `scripts/vereine.json`: überwachte Fußballvereine
- `.github/workflows/pages-und-daten.yml`: Aktualisierung + Deployment

## Tests vor Abschluss

Führe nach relevanten Änderungen möglichst aus:

```bash
python3 -m py_compile scripts/update_angebote.py
python3 -m py_compile scripts/update_fussball.py
python3 -m json.tool angebote/angebote.json >/dev/null
python3 -m json.tool fussball/spiele.json >/dev/null
python3 -m json.tool scripts/vereine.json >/dev/null
```

Prüfe außerdem die YAML-Datei des GitHub-Workflows und die relativen Pfade der Website.

## Änderungen klein halten

- Keine unnötigen Frameworks einführen.
- Kein npm-/Node-Projekt daraus machen, solange es nicht wirklich nötig ist.
- Standardbibliothek Python bevorzugen.
- Bestehende einfache HTML/CSS/JS-Struktur bevorzugen.
- Größere Architekturänderungen zuerst in `PROJECT_CONTEXT.md` dokumentieren.
