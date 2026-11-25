#!/usr/bin/env python3
"""Write versions.json: the latest release of every project in catalog.json.

For each repo: its latest release (or, if it only has pre-releases, the
newest one), and the file the page should offer for download -- the entry's
"asset" glob if it has one, else the first .zip, else the first .bin, never a
file with "debug" in its name. Entries with "web" (a page, not a download)
are skipped.

Runs in .github/workflows/versions.yml with GITHUB_TOKEN; locally it works
too (set GH_TOKEN for more than 60 requests an hour).
"""
import fnmatch
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def api(path):
    req = urllib.request.Request(f"https://api.github.com/{path}",
                                 headers={"Accept": "application/vnd.github+json",
                                          "User-Agent": "gnw-catalog"})
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def pick_asset(assets, pattern):
    assets = [a for a in assets if "debug" not in a["name"].lower()]
    if pattern:
        hits = [a for a in assets if fnmatch.fnmatch(a["name"], pattern)]
        if hits:
            return hits[0]
    for ext in (".zip", ".bin"):
        hits = [a for a in assets if a["name"].lower().endswith(ext)]
        if hits:
            return hits[0]
    return assets[0] if assets else None


def main():
    with open(os.path.join(ROOT, "catalog.json"), encoding="utf-8") as fh:
        items = json.load(fh)["items"]
    path = os.path.join(ROOT, "versions.json")
    try:
        with open(path, encoding="utf-8") as fh:
            previous = json.load(fh)
    except (OSError, ValueError):
        previous = {}
    out = {}
    for it in items:
        if it.get("web"):
            continue
        repo = it["repo"]
        try:
            rel = api(f"repos/{repo}/releases/latest")
            if rel is None:                  # no full release: the newest pre-release, if any
                rels = api(f"repos/{repo}/releases?per_page=5") or []
                rel = next((r for r in rels if not r.get("draft")), None)
        except (urllib.error.URLError, OSError) as e:
            # keep what we had for it: one unreachable repo must not blank the rest
            out[repo] = previous.get(repo)
            print(f"{repo}: {e} (kept the previous entry)", file=sys.stderr)
            continue
        if rel is None:
            out[repo] = None
            print(f"{repo}: no release", file=sys.stderr)
            continue
        a = pick_asset(rel.get("assets", []), it.get("asset"))
        out[repo] = {
            "version": rel["tag_name"],
            "date": (rel.get("published_at") or "")[:10],
            "prerelease": bool(rel.get("prerelease")),
            "url": rel["html_url"],
            "file": a["name"] if a else None,
            "download": a["browser_download_url"] if a else None,
            "size": a["size"] if a else None,
        }
        print(f"{repo}: {rel['tag_name']} {a['name'] if a else '(no file)'}", file=sys.stderr)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


if __name__ == "__main__":
    main()
