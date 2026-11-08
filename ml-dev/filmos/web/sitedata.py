#!/usr/bin/env python3
"""The website's data, from the files the README is made from, so the two never disagree:

  cameras.json   ml-dev/cameras.txt: every camera, its firmware, status and notes (English, Thai)
  films.json     FILMS.md: the 72 films on their four shelves, with each one's photo
  films/*.jpg    docs/films: the same RAW developed with each film
  app/*.jpg      docs/images/app-*.jpg: Darkrooms

  sitedata.py <out dir>
"""

import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def firmware(platform):
    v = platform.split(".")[1]
    return ".".join(v)                      # "202" -> "2.0.2"


def cameras():
    out, later = [], []
    for line in (ROOT / "ml-dev/cameras.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        m = re.match(r"(\S+)\s+(\S+)\s+(\S+)\s+(.*)$", line)
        if not m:
            continue
        platform, status, _limit, rest = m.groups()
        status = status.split(":")[0]
        name, note, note_th = (part.strip() for part in (rest.split("|") + ["", ""])[:3])
        if status in ("working", "issues", "testing", "nodark"):
            out.append({"platform": platform, "name": name, "firmware": firmware(platform),
                        "status": status, "note": note, "note_th": note_th,
                        "zip": f"M-Film-camera-{platform}.zip"})
        else:
            later.append({"name": re.sub(r"\s*\(.*\)$", "", name), "why": status})
    return {"cameras": out, "later": later}


def films():
    text = (ROOT / "FILMS.md").read_text(encoding="utf-8")
    shelves = []
    for head, body in re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", text, re.S | re.M):
        title = re.sub(r"\s*·\s*\d+$", "", head).strip()
        items = []
        for key, name, sub in re.findall(
                r'<a href="docs/films/([\w-]+)\.jpg">.*?<b>(.*?)</b><br><sub>(.*?)</sub>', body):
            parts = [html.unescape(p.strip()) for p in sub.split("·")]
            iso = parts[0].replace("ISO", "").strip() if parts else ""
            items.append({"key": key, "name": html.unescape(name), "iso": iso,
                          "process": parts[1] if len(parts) > 1 else "",
                          "desc": " · ".join(parts[2:]) if len(parts) > 2 else ""})
        if items:
            shelves.append({"shelf": title, "films": items})
    return shelves


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "site/fos")
    out.mkdir(parents=True, exist_ok=True)
    cams = cameras()
    (out / "cameras.json").write_text(json.dumps(cams, ensure_ascii=False, indent=1), encoding="utf-8")
    shelves = films()
    (out / "films.json").write_text(json.dumps(shelves, ensure_ascii=False, indent=1), encoding="utf-8")
    photos = out / "films"
    photos.mkdir(exist_ok=True)
    n = 0
    for shelf in shelves:
        for f in shelf["films"]:
            src = ROOT / "docs/films" / (f["key"] + ".jpg")
            if src.exists():
                shutil.copyfile(src, photos / src.name)
                n += 1
    app = out / "app"
    app.mkdir(exist_ok=True)
    for src in sorted((ROOT / "docs/images").glob("app-*.jpg")):
        shutil.copyfile(src, app / src.name)
    total = sum(len(s["films"]) for s in shelves)
    print(f"{len(cams['cameras'])} cameras ({len(cams['later'])} not yet), {total} films on "
          f"{len(shelves)} shelves, {n} photos")
    if total < 60 or n < total:
        sys.exit("FILMS.md or docs/films don't look right: the site would miss films")


if __name__ == "__main__":
    main()
