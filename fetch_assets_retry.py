#!/usr/bin/env python3
"""
fetch_assets_retry.py -- companion to fetch_assets.py.

Fills in whatever fetch_assets.py left MISSING, using only thumbnail
sizes Wikimedia permits (640px portraits, 1280/1024/800px maps) with
polite pacing and 429 back-off. Same output paths (img/portraits/<id>.jpg,
img/maps/<id>.jpg); skips anything already present. Does not touch the
HTML files or fetch_assets.py.

    python3 fetch_assets_retry.py
"""
import json, os, re, sys, time, urllib.request
from urllib.parse import quote

HEADERS = {"User-Agent": "RisingSunReadingCompanion/1.0 (personal history project; gconz19@gmail.com)"}
CHART, ATLAS = "rising-sun-org-chart.html", "rising-sun-atlas.html"
PACE = 1.0

def get(url, timeout=60, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            time.sleep(PACE)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(5 * (i + 1)); continue
            time.sleep(PACE)
            return None
        except Exception:
            time.sleep(PACE)
            return None

def is_img(d):
    return d and (d[:3] == b"\xff\xd8\xff" or d[:4] in (b"\x89PNG", b"GIF8", b"RIFF"))

def commons(name, w):
    return "https://commons.wikimedia.org/wiki/Special:FilePath/%s?width=%d" % (quote(name), w)

def portraits(html):
    os.makedirs("img/portraits", exist_ok=True)
    people = re.findall(r'\{id:"([^"]+)".*?wiki:"([^"]+)"', html)
    m = re.search(r"const CANDS = (\{.*?\});", html, re.S)
    cands = json.loads(m.group(1)) if m else {}
    ok, miss = [], []
    for pid, wiki in people:
        wiki = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), wiki)
        dest = "img/portraits/%s.jpg" % pid
        if os.path.exists(dest):
            ok.append(pid); continue
        data = None
        j = get("https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(wiki.replace(" ", "_")))
        if j:
            try:
                j = json.loads(j)
                thumb = (j.get("thumbnail") or {}).get("source")
                if thumb:
                    thumb = thumb.split("?")[0]
                    for cand in (re.sub(r"/\d+px-", "/640px-", thumb), thumb, re.sub(r"/\d+px-", "/320px-", thumb)):
                        d = get(cand)
                        if is_img(d): data = d; break
            except Exception:
                pass
        if data is None:
            for name in cands.get(pid, []):
                d = get(commons(name, 640))
                if is_img(d): data = d; break
        if data:
            open(dest, "wb").write(data); ok.append(pid); print("  portrait %-12s ok" % pid)
        else:
            miss.append(pid); print("  portrait %-12s MISSING" % pid)
    return ok, miss

def maps(html):
    os.makedirs("img/maps", exist_ok=True)
    entries = json.loads(re.search(r"const MAPS = (\[.*?\]);", html, re.S).group(1))
    ok, miss = [], []
    for e in entries:
        mid = e["id"]; dest = "img/maps/%s.jpg" % mid
        if os.path.exists(dest):
            ok.append(mid); continue
        data = None
        for f in e["files"]:
            if f.startswith("http"):
                d = get(f, timeout=90)
                if is_img(d): data = d; break
            else:
                for w in (1280, 1024, 800):
                    d = get(commons(f, w), timeout=90)
                    if is_img(d): data = d; break
            if data: break
        if data:
            open(dest, "wb").write(data); ok.append(mid); print("  map %-16s ok (%d KB)" % (mid, len(data)//1024))
        else:
            miss.append(mid); print("  map %-16s MISSING" % mid)
    return ok, miss

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    for f in (CHART, ATLAS):
        if not os.path.exists(f): sys.exit("Cannot find %s" % f)
    print("Portraits..."); p_ok, p_miss = portraits(open(CHART, encoding="utf-8").read())
    print("Maps...");      m_ok, m_miss = maps(open(ATLAS, encoding="utf-8").read())
    print("\nDone. Portraits: %d present, %d missing. Maps: %d present, %d missing." % (len(p_ok), len(p_miss), len(m_ok), len(m_miss)))
    if p_miss or m_miss: print("Missing:", ", ".join(p_miss + m_miss))

if __name__ == "__main__":
    main()
