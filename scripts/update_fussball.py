#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import json, re, html as htmlmod, urllib.request
from pathlib import Path
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
CLUBS_FILE = BASE / "vereine.json"
OUT = ROOT / "fussball" / "spiele.json"
PAST_DAYS = 21
FUTURE_DAYS = 35
MAX_MATCHES_PER_CLUB_PAGE = 40
WORKERS = 6
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151 Safari/537.36"

class TextExtractor(HTMLParser):
    BLOCK={"p","div","li","section","article","header","footer","main","h1","h2","h3","h4","h5","h6","tr","td","th","br"}
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in self.BLOCK:self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in self.BLOCK:self.parts.append("\n")
    def handle_data(self,data): self.parts.append(data)
    def text(self):
        s="".join(self.parts).replace("\xa0"," ")
        s=re.sub(r"[ \t]+"," ",s); s=re.sub(r"\n[ \t]+","\n",s); s=re.sub(r"\n{3,}","\n\n",s)
        return htmlmod.unescape(s).strip()

def html_to_text(raw):
    p=TextExtractor()
    try:
        p.feed(raw); return p.text()
    except Exception:
        raw=re.sub(r"(?is)<script\b.*?</script>"," ",raw)
        raw=re.sub(r"(?is)<style\b.*?</style>"," ",raw)
        raw=re.sub(r"(?s)<[^>]+>","\n",raw)
        return htmlmod.unescape(raw)

def fetch(url,timeout=20):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept-Language":"de-DE,de;q=0.9","Cache-Control":"no-cache"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read(); charset=r.headers.get_content_charset() or "utf-8"
        return raw.decode(charset,errors="replace")

def load_json(path,fallback):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return fallback

def extract_match_urls(raw):
    pattern = r"href=[\"']((?:https://www\.fupa\.net)?/match/[^\"'?#]+(?:\?[^\"']*)?)[\"']"
    found=re.findall(pattern,raw,flags=re.I)
    out=[]; seen=set()
    for u in found:
        if u.startswith("/"):u="https://www.fupa.net"+u
        u=u.split("#",1)[0]
        if u not in seen:seen.add(u);out.append(u)
    return out

def date_from_match_url(url):
    m=re.search(r"-(\d{6})(?:\?|$)",url)
    if not m:return None
    y,mn,d=int(m.group(1)[:2]),int(m.group(1)[2:4]),int(m.group(1)[4:6])
    try:return date(2000+y,mn,d)
    except ValueError:return None

def clean_name(s):
    return re.sub(r"\s+"," ",htmlmod.unescape(s)).strip(" -–|")

def parse_title(raw):
    m=re.search(r"(?is)<title[^>]*>(.*?)</title>",raw)
    if not m:return None
    title=clean_name(re.sub(r"<[^>]+>"," ",m.group(1)))
    m=re.match(r"Spielbericht\s+(.+?)\s+vs\.\s+(.+?)\s+-\s+(.+?)\s+-\s+FuPa",title,re.I)
    if not m:return None
    return clean_name(m.group(1)),clean_name(m.group(2)),clean_name(m.group(3))

def parse_match(url):
    raw=fetch(url); txt=html_to_text(raw); title=parse_title(raw)
    d=date_from_match_url(url)
    if not d:
        dm=re.search(r"(\d{1,2})\.(\d{1,2})\.(20\d{2})",txt)
        if dm:d=date(int(dm.group(3)),int(dm.group(2)),int(dm.group(1)))
    if not d:raise ValueError("Datum nicht ermittelbar")
    if title:home,away,competition=title
    else:
        hm=re.search(r"(?m)^\s*([^\n]{2,80}?)\s+-\s+([^\n]{2,80}?)\s*$",txt)
        home,away=(clean_name(hm.group(1)),clean_name(hm.group(2))) if hm else ("Heim","Gast")
        competition="Fußball"

    score=None
    for sm in re.finditer(r"(?<!\d)(\d{1,2})\s+:\s+(\d{1,2})(?!\d)",txt):
        a,b=int(sm.group(1)),int(sm.group(2))
        if a<=30 and b<=30:score=(a,b);break

    low=txt.lower()
    if "absetzung" in low or "spielabsetzung" in low:status="cancelled"
    elif "abbruch" in low and score is None:status="cancelled"
    elif score is not None:status="finished"
    else:status="scheduled"

    tm=re.search(r"(?<!\d)([0-2]?\d:[0-5]\d)(?!\d)",txt)
    kick=tm.group(1) if tm else ""
    return {"date":d.isoformat(),"time":kick,"competition":competition,"home":home,"away":away,
            "home_score":score[0] if score else None,"away_score":score[1] if score else None,
            "status":status,"tracked_clubs":[],"scope":"umfeld","source":"FuPa","source_url":url}

def key_game(g):
    return (g.get("date",""),re.sub(r"\W+","",g.get("home","").lower()),re.sub(r"\W+","",g.get("away","").lower()))

def within_window(url):
    d=date_from_match_url(url)
    if not d:return True
    t=date.today()
    return t-timedelta(days=PAST_DAYS)<=d<=t+timedelta(days=FUTURE_DAYS)

def update(verbose=True):
    cfg=load_json(CLUBS_FILE,{"clubs":[]}); old=load_json(OUT,{"games":[]})
    clubs=[c for c in cfg.get("clubs",[]) if c.get("enabled",True)]
    url_meta={}; errors=[]

    for club in clubs:
        base=club["source_url"]
        for page_url in (base,base+"?pointer=prev"):
            try:
                if verbose:print(f"[Verein] {club['name']}: {page_url}")
                raw=fetch(page_url); urls=extract_match_urls(raw)[:MAX_MATCHES_PER_CLUB_PAGE]
                if verbose:print(f"         -> {len(urls)} Match-Links")
                for u in urls:
                    if not within_window(u):continue
                    meta=url_meta.setdefault(u,{"clubs":[],"scopes":[],"places":[]})
                    if club["name"] not in meta["clubs"]:meta["clubs"].append(club["name"])
                    meta["scopes"].append(club.get("scope","umfeld"))
                    place=club.get("place","Umgebung")
                    if place not in meta["places"]:meta["places"].append(place)
            except Exception as e:
                errors.append(f"{club['name']}: {type(e).__name__}: {e}")
                if verbose:print(f"         -> FEHLER: {e}")

    fresh=[]; urls=list(url_meta)
    if verbose:print(f"\n[Matches] {len(urls)} eindeutige Spiele im Zeitfenster")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs={pool.submit(parse_match,u):u for u in urls}
        for i,f in enumerate(as_completed(futs),1):
            u=futs[f]
            try:
                g=f.result(); meta=url_meta[u]
                g["tracked_clubs"]=meta["clubs"]
                g["tracked_places"]=meta["places"]
                g["scope"]="kern" if "kern" in meta["scopes"] else "umfeld"
                fresh.append(g)
                if verbose and (i%10==0 or i==len(futs)):print(f"          {i}/{len(futs)} gelesen")
            except Exception as e:
                errors.append(f"Match {u}: {type(e).__name__}: {e}")

    cutoff=date.today()-timedelta(days=PAST_DAYS); upper=date.today()+timedelta(days=FUTURE_DAYS)
    old_valid=[]
    for g in old.get("games",[]):
        try:
            gd=date.fromisoformat(g["date"])
            if cutoff<=gd<=upper:old_valid.append(g)
        except Exception:pass

    merged={}
    for g in old_valid:merged[key_game(g)]=g
    for g in fresh:merged[key_game(g)]=g
    games=sorted(merged.values(),key=lambda g:(g.get("date",""),g.get("time","99:99"),g.get("home","")))

    payload={"updated":datetime.now().astimezone().isoformat(timespec="seconds"),
             "status":f"Live-Abgleich erfolgreich: {len(fresh)} Spiele neu gelesen" if fresh else "Keine neuen Live-Daten – letzte gespeicherte Ergebnisse bleiben sichtbar",
             "region":cfg.get("region","Pritzwalk"),"season":cfg.get("season",""),"errors":errors,"games":games}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    if verbose:
        print(f"\n[OK] {OUT}\n     {len(games)} Spiele gespeichert.")
        if errors:print(f"     {len(errors)} Hinweise/Fehler (Details in spiele.json).")
    return payload

if __name__=="__main__":
    update(True)
