# PROJECT_CONTEXT.md

## Projektziel

Dieses Repository stellt zwei kleine regionale Informationsseiten bereit:

1. **Krombacher-Angebote für Wittenberge, Perleberg und Pritzwalk**
   - Händler
   - Produkt/Gebinde
   - Preis und ggf. Literpreis
   - Ort
   - Angebotslaufzeit
   - Quelle

2. **Fußball für Pritzwalk, Wittenberge, Perleberg und Umgebung**
   - vergangene Ergebnisse
   - heutige Spiele
   - kommende Spiele
   - Filter nach Ort
   - Filter nach Verein
   - Quelle

3. **Ü50-Spielserie SpG Veritas/ESV Wittenberge**
   - Kreuztabelle
   - gesamter Spielplan
   - Wittenberger Spielplan
   - Drucklisten
   - eingebetteter Fallback-Datensatz

Die Seiten sollen übersichtlich, wartungsarm und auch auf kleineren Displays bzw.
einem TV-Browser gut lesbar sein.

---

## Hosting

Die Website wird als **statische GitHub-Pages-Site** veröffentlicht.

Es wird kein eigener Webserver benötigt.

Die Daten liegen als JSON direkt im Repository:

- `angebote/angebote.json`
- `fussball/spiele.json`

GitHub Actions aktualisiert diese Dateien automatisch und veröffentlicht danach
GitHub Pages neu.

Eine eigene Domain kann später per DNS mit GitHub Pages verbunden werden.
Aktuell soll zuerst die normale `github.io`-Adresse getestet werden.

---

## Verzeichnisstruktur

```text
/
├── .github/
│   └── workflows/
│       └── pages-und-daten.yml
├── .vscode/
│   ├── extensions.json
│   └── settings.json
├── angebote/
│   ├── index.html
│   └── angebote.json
├── assets/
│   └── style.css
├── fussball/
│   ├── index.html
│   └── spiele.json
├── ue50/
│   ├── druck.html
│   ├── index.html
│   ├── ue50-spiele.json
│   └── CODEX_PROJECT.md
├── scripts/
│   ├── update_angebote.py
│   ├── update_fussball.py
│   └── vereine.json
├── AGENTS.md
├── PROJECT_CONTEXT.md
├── TODO.md
├── README.md
├── index.html
├── impressum.html
├── datenschutz.html
├── quellen.html
├── robots.txt
├── .nojekyll
└── .gitignore
```

---

## Aktualisierung

Workflow:

`.github/workflows/pages-und-daten.yml`

Der Workflow:

1. lädt das Repository,
2. richtet Python ein,
3. startet `scripts/update_angebote.py`,
4. startet `scripts/update_fussball.py`,
5. committed geänderte JSON-Dateien,
6. baut den statischen Veröffentlichungsordner,
7. veröffentlicht ihn über GitHub Pages.

Geplante Aktualisierungen:

- 06:15
- 11:15
- 16:15
- 20:15
- 23:15

Zeitzone:

`Europe/Berlin`

Manueller Start ist über **Actions → Run workflow** möglich.

---

## Angebotsseite

Datei:

`angebote/index.html`

Daten:

`angebote/angebote.json`

Updater:

`scripts/update_angebote.py`

### Ziel

Nur sachliche Angebotsinformationen darstellen.

### Nicht übernehmen

- Prospektbilder
- Händlerlogos
- Krombacher-Logo
- längere Werbetexte
- fremde Gestaltungselemente

### Robustheit

Wenn eine Datenquelle nicht erreichbar ist, sollen bereits gespeicherte,
noch relevante Daten nach Möglichkeit erhalten bleiben.

Web-Scraping ist grundsätzlich fehleranfällig. Änderungen an Quellen müssen
deshalb vorsichtig umgesetzt und getestet werden.

---

## Fußballseite

Datei:

`fussball/index.html`

Daten:

`fussball/spiele.json`

Updater:

`scripts/update_fussball.py`

Vereinsauswahl:

`scripts/vereine.json`

Die Vereinskonfiguration enthält zusätzlich einen `place`-Wert für den Ortsfilter
der Fußballseite.

### Aktueller regionaler Schwerpunkt

- Pritzwalker FHV 03
- SG Einheit Pritzwalk 1952
- FSV Veritas Wittenberge/Breese
- ESV Wittenberge
- SSV Einheit Perleberg
- SC Hertha Karstädt 1923
- SV Rot-Weiß Gerdshagen
- Meyenburger SV Wacker 1922
- Putlitzer SV 1921
- SG Aufbau Stepenitz
- SV Blumenthal-Grabow
- FK Hansa Wittstock 1919

Die Liste darf später angepasst werden.

---

## Ü50-Seite

Datei:

`ue50/index.html`

Daten:

`ue50/ue50-spiele.json`

Projektbeschreibung:

`ue50/CODEX_PROJECT.md`

Die Seite zeigt die Altsenioren Ü50 Staffel A für die SpG Veritas/ESV
Wittenberge mit Kreuztabelle, Wittenberger Spielplan, Gesamtspielplan und
Drucklisten. Die Daten bleiben statisch und getrennt von der Darstellung.
Die Drucklisten nutzen eine eigene A4-optimierte Ansicht unter `ue50/druck.html`.

---

## Rechtliche und Datenschutz-Vorgaben

Die Site ist öffentlich erreichbar, soll aber bewusst sehr datensparsam bleiben.

### Unbedingt beibehalten

- `impressum.html`
- `datenschutz.html`
- `quellen.html`
- Links zu diesen Seiten im Footer
- `noindex,nofollow,noarchive`
- `robots.txt`

### Nicht ohne ausdrücklichen Auftrag hinzufügen

- Google Analytics
- Matomo
- Werbenetzwerke
- Tracking-Pixel
- Cookies
- `localStorage` für Nutzertracking
- externe Webfonts
- eingebettete YouTube-Videos
- eingebettete Karten
- Social-Media-Widgets
- fremde Logos oder Prospektbilder

Externe Quellen sollen möglichst nur als normale Links geöffnet werden.

### Persönliche Pflichtangaben

Impressum und Datenschutzerklärung enthalten bereits die vorgesehenen
persönlichen Pflichtangaben. Diese nicht automatisch ersetzen, anonymisieren
oder entfernen.

---

## Gestaltung

Gewünscht ist:

- übersichtlich
- große, gut erkennbare Bedienelemente
- responsive
- mobil nutzbar
- möglichst TV-tauglich
- ruhige Gestaltung
- wenig visuelle Ablenkung

Die aktuelle grün/weiße Gestaltung darf beibehalten und schrittweise verbessert werden.

---

## Raspberry / Enigma2

Ein Raspberry mit Enigma2 ist **nicht mehr für das Hosting erforderlich**.

Später kann die Website jedoch auf einem Enigma2-Gerät im Browser angezeigt werden.
Dafür sollte die Bedienung möglichst auch mit Pfeiltasten/OK-Taste funktionieren.

Das ist eine spätere Erweiterung und derzeit kein Deployment-Ziel.

---

## Sicherheit

Keine Zugangsdaten in das öffentliche Repository schreiben.

Insbesondere niemals speichern:

- GitHub Personal Access Tokens
- FTP-/SFTP-Passwörter
- IONOS-Zugangsdaten
- E-Mail-Passwörter
- private SSH-Schlüssel
- API-Schlüssel

Falls später Secrets nötig werden, ausschließlich **GitHub Actions Secrets**
verwenden.

---

## Validierung nach Änderungen

Mindestens prüfen:

```bash
python3 -m py_compile scripts/update_angebote.py
python3 -m py_compile scripts/update_fussball.py
python3 -m json.tool angebote/angebote.json >/dev/null
python3 -m json.tool fussball/spiele.json >/dev/null
python3 -m json.tool scripts/vereine.json >/dev/null
```

Zusätzlich prüfen:

- interne Links funktionieren,
- Impressum/Datenschutz/Quellen sind erreichbar,
- keine persönlichen Pflichtangaben versehentlich entfernt,
- keine Secrets hinzugefügt,
- GitHub-Workflow bleibt gültiges YAML,
- mobile Darstellung ist brauchbar.

---

## Aktueller Projektstand

Die Grundstruktur steht.

Nächster praktischer Schritt:

1. Repository auf GitHub anlegen,
2. diesen kompletten Ordner hochladen,
3. GitHub Pages auf **GitHub Actions** stellen,
4. Workflow einmal manuell starten,
5. `github.io`-Seite testen,
6. erst danach optional eigene Domain anbinden.

Siehe auch `TODO.md`.
