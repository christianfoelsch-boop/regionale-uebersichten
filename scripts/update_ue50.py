#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import html as htmlmod
import json
import re
import urllib.request
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
OUT = ROOT / "ue50" / "ue50-spiele.json"
HTML_FILES = (ROOT / "ue50" / "index.html", ROOT / "ue50" / "druck.html")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36"


def fetch(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept-Language": "de-DE,de;q=0.9",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_text(value: str) -> str:
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    value = htmlmod.unescape(value).replace("\u200b", "")
    return re.sub(r"\s+", " ", value).strip()


def normalize(value: str) -> str:
    value = clean_text(value).lower()
    value = value.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    value = value.replace("spg veritas/esv", "spg veritas esv")
    return re.sub(r"[^a-z0-9]+", "", value)


def team_lookup(data: dict) -> dict[str, str]:
    lookup = {}
    aliases = {
        "wittenberge": ["SpG Veritas/ESV Wittenberge", "SpG Veritas ESV Wittenberge"],
        "blumenthal": ["SV Blumenthal-Grabow", "SV Blumenthal-Grabow (Ü50)"],
        "karstaedt": ["SC Hertha Karstädt", "SC Hertha Karstaedt"],
    }
    for team in data.get("teams", []):
        names = [team.get("name", ""), team.get("short", ""), team.get("id", "")]
        names.extend(aliases.get(team.get("id", ""), []))
        for name in names:
            if name:
                lookup[normalize(name)] = team["id"]
    return lookup


def extract_rows(raw: str, data: dict) -> tuple[list[dict], list[str]]:
    lookup = team_lookup(data)
    rows = re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", raw)
    games = []
    errors = []
    for row in rows:
        if "column-score" not in row or "club-name" not in row or "spielfrei" in row.lower():
            continue
        names = [clean_text(name) for name in re.findall(r'(?is)<div class="club-name">\s*(.*?)\s*</div>', row)]
        if len(names) != 2:
            continue
        home = lookup.get(normalize(names[0]))
        away = lookup.get(normalize(names[1]))
        links = re.findall(r'href="(https://www\.fussball\.de/spiel/[^"]+)"', row)
        if not home or not away:
            errors.append(f"Team nicht zugeordnet: {names[0]} - {names[1]}")
            continue
        if not links:
            errors.append(f"Kein Spiel-Link gefunden: {names[0]} - {names[1]}")
            continue
        games.append(
            {
                "home": home,
                "away": away,
                "home_name": names[0],
                "away_name": names[1],
                "source_url": links[0],
                "external_id": links[0].rsplit("/", 1)[-1],
                "verified_result": "icon-verified" in row,
            }
        )
    return games, errors


def merge_source_links(data: dict, source_games: list[dict]) -> tuple[dict, list[str]]:
    errors = []
    remaining = source_games[:]
    changed = False
    for game in data.get("games", []):
        match_index = next(
            (
                index
                for index, source_game in enumerate(remaining)
                if source_game["home"] == game.get("home") and source_game["away"] == game.get("away")
            ),
            None,
        )
        if match_index is None:
            errors.append(f"Keine passende FUSSBALL.DE-Zeile gefunden: {game.get('home')} - {game.get('away')}")
            continue
        source_game = remaining.pop(match_index)
        for key in ("source_url", "external_id"):
            if game.get(key) != source_game[key]:
                game[key] = source_game[key]
                changed = True
        if source_game["verified_result"] and game.get("result") and game.get("status") != "finished":
            game["status"] = "finished"
            changed = True
    for source_game in remaining:
        errors.append(f"Nicht im lokalen Datensatz: {source_game['home_name']} - {source_game['away_name']}")
    if changed:
        data["updated"] = date.today().isoformat()
    data["lastSourceCheck"] = date.today().isoformat()
    return data, errors


def sync_fallback(data: dict) -> None:
    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    for path in HTML_FILES:
        text = path.read_text(encoding="utf-8")
        new_text, count = re.subn(
            r"const fallbackData=.*?;\nlet data=fallbackData;",
            f"const fallbackData={compact};\nlet data=fallbackData;",
            text,
            count=1,
            flags=re.S,
        )
        if count != 1:
            raise RuntimeError(f"fallbackData nicht gefunden: {path}")
        path.write_text(new_text, encoding="utf-8")


def update(verbose: bool = True) -> dict:
    data = load_json(OUT)
    source = data.get("source", {}).get("leagueUrl")
    if not source:
        raise RuntimeError("Keine source.leagueUrl in ue50-spiele.json gefunden.")
    raw = fetch(source)
    source_games, parse_errors = extract_rows(raw, data)
    if not source_games:
        raise RuntimeError("Keine Ü50-Spiele aus FUSSBALL.DE gelesen.")
    data, merge_errors = merge_source_links(data, source_games)
    data["sourceCheckStatus"] = f"{len(source_games)} FUSSBALL.DE-Spielzeilen gelesen"
    errors = parse_errors + merge_errors
    if errors:
        data["sourceCheckErrors"] = errors
    else:
        data.pop("sourceCheckErrors", None)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_fallback(data)
    if verbose:
        print(f"[OK] {len(source_games)} Ü50-Spielzeilen gelesen.")
        print(f"[OK] {OUT} gespeichert.")
        if errors:
            print(f"[Hinweis] {len(errors)} Prüfhinweise in sourceCheckErrors.")
    return data


if __name__ == "__main__":
    update(True)
