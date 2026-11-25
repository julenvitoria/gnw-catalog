#!/usr/bin/env python3
"""Write versions.json: the latest releases of every repo in catalog.json.

For each repo -- every item, the firmware, and the "upstream" of every fork --
it records two things:

  release  the newest full release
  pre      the newest pre-release, only when it is newer than that release
           (a core whose next version needs the firmware's RC, the RC itself)

each with its version, date, page and the file to offer for download: the
item's "asset" glob if it has one, else the first .zip, else the first .bin,
never a file with "debug" in its name. Items with "web" (a page, not a
download) are skipped.

Runs in .github/workflows/versions.yml with GITHUB_TOKEN; locally it works
too (set GH_TOKEN for more than 60 requests an hour). A repo that cannot be
read keeps its previous entry, so one failure never blanks the rest.
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


def describe(rel, pattern):
    a = pick_asset(rel.get("assets", []), pattern)
    return {
        "version": rel["tag_name"],
        "date": (rel.get("published_at") or "")[:10],
        "url": rel["html_url"],
        "file": a["name"] if a else None,
        "download": a["browser_download_url"] if a else None,
        "size": a["size"] if a else None,
    }


def releases(repo, pattern):
    rels = [r for r in (api(f"repos/{repo}/releases?per_page=30") or []) if not r.get("draft")]
    rels.sort(key=lambda r: r.get("published_at") or "", reverse=True)
    full = next((r for r in rels if not r.get("prerelease")), None)
    pre = next((r for r in rels if r.get("prerelease")), None)
    if pre and full and (pre.get("published_at") or "") <= (full.get("published_at") or ""):
        pre = None                       # an older pre-release is history, not an option
    return {"release": describe(full, pattern) if full else None,
            "pre": describe(pre, pattern) if pre else None}


def main():
    with open(os.path.join(ROOT, "catalog.json"), encoding="utf-8") as fh:
        cat = json.load(fh)
    wanted = {}                                      # repo -> asset glob
    fw = cat.get("firmware")
    if fw:
        wanted[fw["repo"]] = fw.get("asset")
    for it in cat["items"]:
        if not it.get("web"):
            wanted[it["repo"]] = it.get("asset")
        if it.get("upstream"):
            wanted.setdefault(it["upstream"], it.get("asset"))

    path = os.path.join(ROOT, "versions.json")
    try:
        with open(path, encoding="utf-8") as fh:
            previous = json.load(fh)
    except (OSError, ValueError):
        previous = {}

    out = {}
    for repo, pattern in wanted.items():
        try:
            out[repo] = releases(repo, pattern)
        except (urllib.error.URLError, OSError) as e:
            out[repo] = previous.get(repo)
            print(f"{repo}: {e} (kept the previous entry)", file=sys.stderr)
            continue
        r, p = out[repo]["release"], out[repo]["pre"]
        print(f"{repo}: {r['version'] if r else '-'}{' + pre ' + p['version'] if p else ''}", file=sys.stderr)

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


if __name__ == "__main__":
    main()
