#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import html as htmlmod
import json
import re
import urllib.request
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
SCHEDULE_FILE = ROOT / "ue50" / "ue50-spiele.json"
OUT = ROOT / "ue50" / "statistik.json"
FOCUS_NAME = "SpG Veritas/ESV Wittenberge"
CANONICAL_NAMES = {
    "svblumenthalgrabow": "SV Blumenthal-Grabow",
    "svblumenthalgrabowue50": "SV Blumenthal-Grabow",
    "scherthakarstaedt": "SC Hertha Karstädt",
    "scherthakarstadt": "SC Hertha Karstädt",
}
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


def clean_text(value: str) -> str:
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    value = htmlmod.unescape(value).replace("\u200b", "")
    return re.sub(r"\s+", " ", value).strip()


def normalize(value: str) -> str:
    value = clean_text(value).lower()
    value = value.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    value = value.replace("spg veritas/esv", "spg veritas esv")
    return re.sub(r"[^a-z0-9]+", "", value)


def unique_match_links(raw: str) -> list[str]:
    links = re.findall(r'https://www\.fussball\.de/spiel/[^"<> ]+', raw)
    seen = set()
    out = []
    for link in links:
        clean = link.split("#", 1)[0]
        match_id = urlsplit(clean).path.rsplit("/", 1)[-1]
        if match_id in seen:
            continue
        seen.add(match_id)
        out.append(clean)
    return out


def parse_title(raw: str) -> tuple[str, str, str, str] | None:
    match = re.search(r"(?is)<title>(.*?)</title>", raw)
    if not match:
        return None
    title = clean_text(match.group(1))
    parsed = re.match(r"(.+?) - (.+?) Ergebnis: (.+?) - Herren Ü50 - (\d{2}\.\d{2}\.\d{4})", title)
    if not parsed:
        return None
    home, away, competition, date_text = parsed.groups()
    return clean_text(home), clean_text(away), clean_text(competition), date_text


def iso_date(date_text: str) -> str:
    return datetime.strptime(date_text, "%d.%m.%Y").date().isoformat()


def season_from_date(value: str) -> str:
    d = date.fromisoformat(value)
    start = d.year if d.month >= 7 else d.year - 1
    return f"{start}/{start + 1}"


def parse_result(raw: str) -> str | None:
    if "icon-verified" not in raw:
        return None
    events_match = re.search(r'data-match-events="(.*?)"', raw, flags=re.S)
    if not events_match:
        return None
    events_text = htmlmod.unescape(events_match.group(1))
    try:
        events_data = ast.literal_eval(events_text)
    except (ValueError, SyntaxError):
        return None
    score = {"home": 0, "away": 0}
    for section in ("first-half", "second-half", "extra-time"):
        for event in events_data.get(section, {}).get("events", []):
            if event.get("type") == "goal" and event.get("team") in score:
                score[event["team"]] += 1
    return f"{score['home']}:{score['away']}"


def parse_match(url: str) -> dict | None:
    raw = fetch(url)
    title = parse_title(raw)
    if not title:
        return None
    home, away, competition, date_text = title
    if normalize(FOCUS_NAME) not in {normalize(home), normalize(away)}:
        return None
    result = parse_result(raw)
    game = {
        "date": iso_date(date_text),
        "season": season_from_date(iso_date(date_text)),
        "competition": competition,
        "home": home,
        "away": away,
        "source_url": url,
    }
    if result:
        game["result"] = result
    return game


def empty_totals() -> dict:
    return {"played": 0, "wins": 0, "draws": 0, "losses": 0, "goalsFor": 0, "goalsAgainst": 0, "goalDiff": 0, "points": 0}


def add_game(totals: dict, game: dict) -> None:
    if not game.get("result"):
        return
    home_goals, away_goals = [int(part) for part in game["result"].split(":", 1)]
    focus_home = normalize(game["home"]) == normalize(FOCUS_NAME)
    goals_for = home_goals if focus_home else away_goals
    goals_against = away_goals if focus_home else home_goals
    totals["played"] += 1
    totals["goalsFor"] += goals_for
    totals["goalsAgainst"] += goals_against
    if goals_for > goals_against:
        totals["wins"] += 1
        totals["points"] += 3
    elif goals_for == goals_against:
        totals["draws"] += 1
        totals["points"] += 1
    else:
        totals["losses"] += 1
    totals["goalDiff"] = totals["goalsFor"] - totals["goalsAgainst"]


def canonical_name(value: str) -> str:
    return CANONICAL_NAMES.get(normalize(value), value)


def opponent_of(game: dict) -> str:
    opponent = game["away"] if normalize(game["home"]) == normalize(FOCUS_NAME) else game["home"]
    return canonical_name(opponent)


def build_stats(games: list[dict], source_url: str) -> dict:
    finished = sorted([g for g in games if g.get("result")], key=lambda g: g["date"])
    scheduled = sorted([g for g in games if not g.get("result")], key=lambda g: g["date"])
    totals = empty_totals()
    home = empty_totals()
    away = empty_totals()
    by_season: dict[str, dict] = {}
    opponents: dict[str, dict] = {}
    for game in finished:
        add_game(totals, game)
        add_game(home if normalize(game["home"]) == normalize(FOCUS_NAME) else away, game)
        season = by_season.setdefault(game["season"], {"season": game["season"], **empty_totals()})
        add_game(season, game)
        opponent = opponent_of(game)
        opponent_stats = opponents.setdefault(opponent, {"opponent": opponent, **empty_totals()})
        add_game(opponent_stats, game)
    return {
        "team": FOCUS_NAME,
        "updated": date.today().isoformat(),
        "source": {"label": "FUSSBALL.DE", "teamUrl": source_url},
        "status": f"{len(finished)} verifizierte Spiele aus {len(games)} offiziellen Spielseiten ausgewertet",
        "totals": totals,
        "home": home,
        "away": away,
        "seasons": sorted(by_season.values(), key=lambda item: item["season"], reverse=True),
        "opponents": sorted(opponents.values(), key=lambda item: (-item["played"], item["opponent"])),
        "recent": list(reversed(finished[-8:])),
        "scheduled": scheduled[:8],
    }


def update(verbose: bool = True) -> dict:
    schedule = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
    source_url = schedule.get("source", {}).get("teamUrl")
    if not source_url:
        raise RuntimeError("Keine source.teamUrl in ue50-spiele.json gefunden.")
    raw = fetch(source_url)
    links = unique_match_links(raw)
    games = []
    errors = []
    for link in links:
        try:
            game = parse_match(link)
        except Exception as exc:
            errors.append(f"{link}: {type(exc).__name__}: {exc}")
            continue
        if game:
            games.append(game)
    if not games:
        raise RuntimeError("Keine offiziellen Ü50-Spiele für Wittenberge gefunden.")
    payload = build_stats(games, source_url)
    if errors:
        payload["errors"] = errors
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if verbose:
        print(f"[OK] {len(games)} offizielle Wittenberge-Spiele gelesen.")
        print(f"[OK] {payload['totals']['played']} verifizierte Spiele ausgewertet.")
        print(f"[OK] {OUT} gespeichert.")
    return payload


if __name__ == "__main__":
    update(True)
