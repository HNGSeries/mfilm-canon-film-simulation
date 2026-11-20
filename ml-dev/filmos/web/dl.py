#!/usr/bin/env python3
"""The cameras' zips on mfilm.app, for the install page's "Install onto the card" (docs/easy-install.md).

GitHub's release downloads can't be fetched by a web page (no CORS), so the pages workflow copies the
newest release's zips into site/dl/ and this writes their list next to them:

  dl/index.json   {"tag": "v0.2.3", "zips": {"650D.104": {"name": ..., "size": ..., "sha256": ...}, ...}}

The page fetches the zip from dl/, checks its SHA-256 against this list, and writes it onto the card.

  python3 ml-dev/filmos/web/dl.py <dir with the zips> <tag>
"""

import hashlib
import json
import re
import sys
from pathlib import Path

# M-Film-<version>-camera-<platform>.zip since 0.2.4, M-Film-camera-<platform>.zip before (js/releases.js)
NAME = re.compile(r"^M-Film-(?:\d[\w.]*-)?camera-(?P<platform>[^/]+)\.zip$")


def main():
    d, tag = Path(sys.argv[1]), sys.argv[2]
    zips = {}
    for f in sorted(d.glob("*.zip")):
        m = NAME.match(f.name)
        if not m:
            continue
        zips[m["platform"]] = {"name": f.name, "size": f.stat().st_size,
                               "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
    if not zips:
        sys.exit(f"no camera zips in {d}")
    (d / "index.json").write_text(json.dumps({"tag": tag, "zips": zips}, indent=1) + "\n", encoding="utf-8")
    print(f"{len(zips)} camera zips of {tag} in {d}")


if __name__ == "__main__":
    main()
