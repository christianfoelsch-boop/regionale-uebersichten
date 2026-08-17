# Regionale Übersichten – Wittenberge, Perleberg & Pritzwalk

Dieses Repository enthält zwei statische Webseiten:

- 🍺 **Krombacher-Angebote für Wittenberge, Perleberg und Pritzwalk**
- ⚽ **Regionalfußball für Pritzwalk, Wittenberge, Perleberg und Umgebung**
- 📋 **Ü50-Spielserie SpG Veritas/ESV Wittenberge** als eigener Bereich

Die Daten werden automatisch mit GitHub Actions aktualisiert und anschließend
über GitHub Pages veröffentlicht.

## Für VS Code

Am besten den **gesamten Repository-Ordner** in VS Code öffnen.

Wichtige Kontextdateien:

- `AGENTS.md` – kurze Arbeitsregeln für Codex
- `PROJECT_CONTEXT.md` – vollständiger Projektkontext
- `TODO.md` – nächste Schritte

Wenn Codex im VS-Code-Projekt arbeitet, sollte `PROJECT_CONTEXT.md` die
wesentlichen Entscheidungen aus der bisherigen Planung verfügbar halten.

## Erster Upload zu GitHub

1. Neues **öffentliches** Repository anlegen, z. B. `regionale-uebersichten`.
2. In VS Code diesen Ordner öffnen.
3. Über **Source Control** ein Git-Repository initialisieren, falls noch nicht geschehen.
4. Alle Dateien committen.
5. Repository mit GitHub verbinden und `main` pushen.

Alternativ kann der komplette Inhalt auch zunächst über die GitHub-Weboberfläche
hochgeladen werden.

## GitHub Pages aktivieren

Im Repository:

`Settings` → `Pages`

Unter **Build and deployment**:

`Source` → **GitHub Actions**

Danach:

`Actions` → **Daten aktualisieren und GitHub Pages veröffentlichen** → **Run workflow**

Nach erfolgreichem Deployment liegt eine Projektseite typischerweise unter:

```text
https://DEIN-GITHUB-NAME.github.io/REPOSITORY-NAME/
```

## Automatische Aktualisierung

Workflow:

`.github/workflows/pages-und-daten.yml`

Geplante Läufe in `Europe/Berlin`:

- 06:15
- 11:15
- 16:15
- 20:15
- 23:15

Dabei werden:

1. Angebotsdaten aktualisiert,
2. Fußballdaten aktualisiert,
3. geänderte JSON-Dateien committed,
4. GitHub Pages veröffentlicht.

Die Datei `fussball/spiele.json` bleibt der stabile Datensatz für die
Regionalfußballseite und externe Verbraucher wie TV-/Enigma2-Addons. Die
Ü50-Spielserie nutzt getrennt davon `ue50/ue50-spiele.json`.

## Lokale Prüfung

Für die Python-Dateien:

```bash
python3 -m py_compile scripts/update_angebote.py
python3 -m py_compile scripts/update_fussball.py
```

JSON prüfen:

```bash
python3 -m json.tool angebote/angebote.json >/dev/null
python3 -m json.tool fussball/spiele.json >/dev/null
python3 -m json.tool scripts/vereine.json >/dev/null
```

Die HTML-Seiten können für reine Layout-Tests lokal geöffnet werden.
Für Fetch-Aufrufe der JSON-Dateien ist ein kleiner lokaler HTTP-Server praktischer:

```bash
python3 -m http.server 8000
```

Dann:

```text
http://127.0.0.1:8000/
```

## Datenschutz und öffentliche Veröffentlichung

Die Website selbst verwendet bewusst:

- kein Analytics,
- kein Werbetracking,
- keine externen Webfonts,
- keine eingebetteten Drittanbieterbilder,
- keine Social-Media-Widgets,
- keine eigenen Tracking-Cookies.

Die rechtlichen Seiten liegen im Repository:

- `impressum.html`
- `datenschutz.html`
- `quellen.html`

Diese Dateien nicht versehentlich entfernen.

## Eigene Domain

Die eigene Domain wird erst eingerichtet, wenn die `github.io`-Version zuverlässig läuft.

Danach können DNS-Einträge bei IONOS auf GitHub Pages zeigen.

## Weitere Informationen

Siehe:

- `PROJECT_CONTEXT.md`
- `TODO.md`
- `AGENTS.md`
