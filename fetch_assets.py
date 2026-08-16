#!/usr/bin/env python3
"""
fetch_assets.py -- makes the Rising Sun chart and atlas fully self-contained.

Put this script in the same folder as rising-sun-org-chart.html and
rising-sun-atlas.html, then run:

    python3 fetch_assets.py

It reads both HTML files, downloads every portrait and map into
img/portraits/ and img/maps/, and prints a report. The HTML already
prefers those local copies, so nothing else needs to change. Re-run it
any time the chart or atlas gets a new version; it skips files it
already has.

Uses only the Python standard library. Needs an internet connection
for the one run.
"""
import json
import os
import re
import sys
import urllib.request

HEADERS = {"User-Agent": "RisingSunReadingCompanion/1.0 (personal history project)"}
CHART = "rising-sun-org-chart.html"
ATLAS = "rising-sun-atlas.html"


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_json(url):
    return json.loads(get(url).decode("utf-8"))


def commons_url(filename, width):
    from urllib.parse import quote
    return ("https://commons.wikimedia.org/wiki/Special:FilePath/"
            + quote(filename) + "?width=%d" % width)


def save(path, data):
    with open(path, "wb") as f:
        f.write(data)


def looks_like_image(data):
    return data[:4] in (b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1", b"\x89PNG",
                        b"GIF8", b"RIFF") or data[:3] == b"\xff\xd8\xff"


def fetch_portraits(html):
    os.makedirs("img/portraits", exist_ok=True)
    people = re.findall(r'\{id:"([^"]+)".*?wiki:"([^"]+)"', html)
    cands = {}
    m = re.search(r"const CANDS = (\{.*?\});", html, re.S)
    if m:
        cands = json.loads(m.group(1))
    ok, miss = [], []
    for pid, wiki in people:
        dest = "img/portraits/%s.jpg" % pid
        if os.path.exists(dest):
            ok.append(pid)
            continue
        data = None
        # 1. authoritative: Wikipedia article lead image
        try:
            j = get_json("https://en.wikipedia.org/api/rest_v1/page/summary/"
                         + urllib.request.quote(wiki.replace(" ", "_")))
            src = (j.get("originalimage") or {}).get("source") or \
                  (j.get("thumbnail") or {}).get("source")
            if src:
                # ask for a mid-size thumbnail instead of the full original
                src2 = re.sub(r"/(\d+)px-", "/640px-", src)
                for candidate in (src2, src):
                    try:
                        d = get(candidate)
                        if looks_like_image(d):
                            data = d
                            break
                    except Exception:
                        pass
        except Exception:
            pass
        # 2. fallback: the candidate filenames baked into the chart
        if data is None:
            for name in cands.get(pid, []):
                try:
                    d = get(commons_url(name, 640))
                    if looks_like_image(d):
                        data = d
                        break
                except Exception:
                    pass
        if data is not None:
            save(dest, data)
            ok.append(pid)
            print("  portrait %-12s ok" % pid)
        else:
            miss.append(pid)
            print("  portrait %-12s MISSING" % pid)
    return ok, miss


def fetch_maps(html):
    os.makedirs("img/maps", exist_ok=True)
    m = re.search(r"const MAPS = (\[.*?\]);", html, re.S)
    maps = json.loads(m.group(1))
    ok, miss = [], []
    for entry in maps:
        mid = entry["id"]
        dest = "img/maps/%s.jpg" % mid
        if os.path.exists(dest):
            ok.append(mid)
            continue
        data = None
        for f in entry["files"]:
            url = f if f.startswith("http") else commons_url(f, 1600)
            try:
                d = get(url, timeout=90)
                if looks_like_image(d):
                    data = d
                    break
            except Exception:
                pass
        if data is not None:
            save(dest, data)
            print("  map %-16s ok (%d KB)" % (mid, len(data) // 1024))
            ok.append(mid)
        else:
            print("  map %-16s MISSING" % mid)
            miss.append(mid)
    return ok, miss


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    for f in (CHART, ATLAS):
        if not os.path.exists(f):
            sys.exit("Cannot find %s in this folder. Put fetch_assets.py "
                     "next to both HTML files and run it again." % f)
    print("Downloading portraits...")
    p_ok, p_miss = fetch_portraits(open(CHART, encoding="utf-8").read())
    print("Downloading maps...")
    m_ok, m_miss = fetch_maps(open(ATLAS, encoding="utf-8").read())
    print()
    print("Done. Portraits: %d saved, %d missing. Maps: %d saved, %d missing."
          % (len(p_ok), len(p_miss), len(m_ok), len(m_miss)))
    if p_miss or m_miss:
        print("Missing:", ", ".join(p_miss + m_miss))
        print("(Missing items keep their online fallback and kanji seal.)")
    print()
    print("The folder is now self-contained. Copy the whole folder")
    print("(both HTML files plus img/) to your web server or into the")
    print("Documents app. Images load from img/ first, with the old")
    print("online sources kept only as a fallback.")


if __name__ == "__main__":
    main()
