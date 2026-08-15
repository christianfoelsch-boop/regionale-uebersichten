#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Krombacher-Angebote für Wittenberge aktualisieren.
Nur Python-Standardbibliothek erforderlich.

Die Quellen können ihr HTML ändern. Deshalb:
- lokale Hauptquelle: kaufDA Wittenberge / Bier
- offizielle Filialquelle: Netto Wittenberge
- Kontrollquelle: Marktguru Krombacher
- bei Fehlschlag bleiben die letzten funktionierenden Daten erhalten
"""
from __future__ import annotations
import json, re, sys, html, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, date, timedelta

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
OUT = ROOT / "angebote" / "angebote.json"

SOURCES = {
    "kaufda": "https://www.kaufda.de/Wittenberge/Angebote/Bier",
    "netto": "https://www.netto-online.de/filialen/wittenberge/perleberger-str-117/5192",
    "marktguru": "https://www.marktguru.de/b/krombacher",
}

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36"

def load_old():
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:
        return {"offers": []}

def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.5",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
        charset = r.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")

def to_text(s: str) -> str:
    # Script/Style entfernen, HTML in gut parsebaren Klartext verwandeln
    s = re.sub(r"(?is)<script\b.*?</script>", " ", s)
    s = re.sub(r"(?is)<style\b.*?</style>", " ", s)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(?:p|div|li|tr|h1|h2|h3|h4|section|article)>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s).replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()

def iso_from_dm(d, m, year=None):
    y = year or date.today().year
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

def parse_date_range(text: str):
    # 09.08. - 15.08. oder 09.08.2026 - 15.08.2026
    m = re.search(
        r"(\d{1,2})\.(\d{1,2})\.(?:\d{2,4})?\s*[-–]\s*"
        r"(\d{1,2})\.(\d{1,2})\.(?:(\d{2,4}))?",
        text
    )
    if not m:
        return None
    year = int(m.group(5)) if m.group(5) else date.today().year
    if year < 100:
        year += 2000
    return iso_from_dm(m.group(1), m.group(2), year), iso_from_dm(m.group(3), m.group(4), year)

def euro_number(s):
    return float(s.replace(".", "").replace(",", "."))

def parse_marktguru(raw: str):
    txt = to_text(raw)
    offers = []
    # In überschaubare Blöcke um jedes "Pils" zerlegen
    positions = [m.start() for m in re.finditer(r"\bPils\b", txt, re.I)]
    for pos in positions:
        block = txt[max(0,pos-80):pos+650]
        if "Krombacher" not in block:
            continue
        pm = re.search(r"Preis:\s*€?\s*(\d{1,2}[,.]\d{2})", block, re.I)
        dm = re.search(r"Gültig:\s*(\d{1,2})\.(\d{1,2})\.\s*[-–]\s*(\d{1,2})\.(\d{1,2})\.", block, re.I)
        hm = re.search(r"Händler:\s*([A-Za-zÄÖÜäöüß \-]+)", block, re.I)
        if not (pm and dm and hm):
            continue
        retailer = hm.group(1).strip().split("\n")[0].strip()
        if "Netto Marken-Discount" not in retailer:
            continue
        lp = re.search(r"€\s*(\d[,.]\d{2})\s*/\s*l", block, re.I)
        pack = re.search(r"(20\s*x\s*0[,.]5\s*(?:Liter|l))", block, re.I)
        offers.append({
            "retailer": "Netto Marken-Discount",
            "product": "Krombacher Pils / alkoholfrei",
            "pack": (pack.group(1).replace("x","×").replace(",",".") if pack else "20 × 0,5 l"),
            "price": euro_number(pm.group(1)),
            "liter_price": euro_number(lp.group(1)) if lp else None,
            "start": iso_from_dm(dm.group(1), dm.group(2)),
            "end": iso_from_dm(dm.group(3), dm.group(4)),
            "scope": "Kontrollquelle; Filialgültigkeit für Wittenberge prüfen",
            "source": "Marktguru",
            "source_url": SOURCES["marktguru"],
            "note": "Automatisch aus der Angebotsseite gelesen."
        })
    return offers

def parse_netto(raw: str):
    txt = to_text(raw)
    offers = []
    for m in re.finditer(r"Krombacher\s+Biere", txt, re.I):
        block = txt[max(0,m.start()-250):m.start()+700]
        packm = re.search(r"20\s*x\s*0[,.]5\s*l", block, re.I)
        # bevorzugt Preis nach UVP/statt, sonst plausible 2-stellige Preise
        vals = [euro_number(x) for x in re.findall(r"\b(\d{1,2}[,.]\d{2})\b", block)]
        plausible = [x for x in vals if 5 <= x <= 25]
        if not plausible:
            continue
        # typischerweise steht der Aktionspreis nach UVP
        price = plausible[-1]
        lpm = re.search(r"(\d[,.]\d{2})\s*/\s*l", block, re.I)

        # Auf der Filialseite stehen Prospektstarts. Den naheliegenden Montag ermitteln.
        starts = []
        for dm in re.finditer(r"ab Montag,\s*(\d{1,2})\.(\d{1,2})\.(\d{2,4})", txt, re.I):
            y=int(dm.group(3)); y = y+2000 if y<100 else y
            dt=date(y,int(dm.group(2)),int(dm.group(1)))
            starts.append(dt)
        if starts:
            # Angebot der aktuellen/nächsten Prospektwoche wählen.
            today=date.today()
            candidates=[d for d in starts if d >= today-timedelta(days=6)]
            start=min(candidates) if candidates else max(starts)
        else:
            start=date.today()-timedelta(days=date.today().weekday())
        end=start+timedelta(days=5)

        offers.append({
            "retailer": "Netto Marken-Discount",
            "product": "Krombacher Biere, verschiedene Sorten",
            "pack": "20 × 0,5 l" if packm else "Gebinde siehe Quelle",
            "price": price,
            "liter_price": euro_number(lpm.group(1)) if lpm else None,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "scope": "Offizielle Netto-Filialseite Wittenberge",
            "source": "Netto Marken-Discount",
            "source_url": SOURCES["netto"],
            "note": "Automatisch aus der offiziellen Wittenberger Filialseite gelesen."
        })
    return offers

def parse_kaufda(raw: str):
    # Lokale Quelle. Der Parser ist absichtlich konservativ:
    # Nur Blöcke mit Krombacher + Preis + Händler werden übernommen.
    txt = to_text(raw)
    offers = []
    for m in re.finditer(r"Krombacher", txt, re.I):
        block = txt[max(0,m.start()-180):m.start()+850]
        if not re.search(r"\b(Pils|Bier)\b", block, re.I):
            continue
        pm = re.search(r"(\d{1,2}[,.]\d{2})\s*€", block)
        if not pm:
            continue
        retailer = None
        for name in [
            "Netto Marken-Discount","Kaufland","REWE","Penny",
            "E center","ALDI Nord","Lidl","Netto mit dem Scottie"
        ]:
            if name.lower() in block.lower():
                retailer=name
                break
        if not retailer:
            continue

        dr=parse_date_range(block)
        if not dr:
            # Laufzeit aus dem Wochenprospekt nicht eindeutig -> nicht raten
            continue
        product = "Krombacher Pils" if re.search(r"\bPils\b", block, re.I) else "Krombacher Bier"
        lp = re.search(r"(?:1\s*l\s*=\s*|)(\d[,.]\d{2})\s*/?\s*l", block, re.I)
        offers.append({
            "retailer": retailer,
            "product": product,
            "pack": "Gebinde siehe Quelle",
            "price": euro_number(pm.group(1)),
            "liter_price": euro_number(lp.group(1)) if lp else None,
            "start": dr[0],
            "end": dr[1],
            "scope": "Lokale Quelle: Wittenberge",
            "source": "kaufDA Wittenberge",
            "source_url": SOURCES["kaufda"],
            "note": "Automatisch aus der lokalen Wittenberger Angebotsseite gelesen."
        })
    return offers

def key(o):
    return (
        str(o.get("retailer","")).lower(),
        str(o.get("product","")).lower(),
        str(o.get("start","")),
        str(o.get("end","")),
        round(float(o.get("price",0)),2),
    )

def unique(items):
    out=[]; seen=set()
    # lokale/offizielle Treffer zuerst behalten
    items=sorted(items, key=lambda o: (
        0 if "Wittenberge" in o.get("scope","") else 1,
        o.get("start","9999")
    ))
    for o in items:
        k=key(o)
        if k not in seen:
            seen.add(k); out.append(o)
    return out

def update(verbose=True):
    old=load_old()
    fresh=[]
    errors=[]
    parsers={"kaufda":parse_kaufda, "netto":parse_netto, "marktguru":parse_marktguru}

    for name,url in SOURCES.items():
        try:
            if verbose: print(f"[Abruf] {name}: {url}")
            raw=fetch(url)
            found=parsers[name](raw)
            fresh.extend(found)
            if verbose: print(f"        -> {len(found)} Krombacher-Treffer")
        except Exception as e:
            errors.append(f"{name}: {type(e).__name__}: {e}")
            if verbose: print(f"        -> FEHLER: {e}")

    # Alte Angebote als Fallback behalten, aber sehr alte Einträge entfernen.
    cutoff=date.today()-timedelta(days=7)
    old_valid=[]
    for o in old.get("offers",[]):
        try:
            if date.fromisoformat(o["end"]) >= cutoff:
                old_valid.append(o)
        except Exception:
            pass

    merged=unique(fresh + old_valid)
    payload={
        "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
        "region": "19322 Wittenberge",
        "status": (
            f"Live-Abgleich: {len(fresh)} Treffer"
            if fresh else
            "Keine neuen Live-Treffer – letzte gespeicherte Daten bleiben sichtbar"
        ),
        "errors": errors,
        "offers": merged
    }
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    if verbose:
        print(f"\n[OK] {OUT}")
        print(f"     {len(merged)} Angebote gespeichert.")
        if errors:
            print("[Hinweise]")
            for e in errors: print(" -",e)
    return payload

if __name__=="__main__":
    update(True)
