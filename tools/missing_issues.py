#!/usr/bin/env python3
"""Open an issue for every project the firmware's installer bundles that has
no entry in catalog.json, and close it once the entry exists.

Runs in .github/workflows/versions.yml right after update_versions.py, which
leaves the installer's list in versions.json under "_installer". Each issue is
titled "Falta en el catálogo: owner/repo" and labelled "falta-en-catalogo";
an open one with that title is never opened twice. Its body carries what is
needed to write the entry: the repo, its latest release and, for a core, the
tabs read from its header. It is closed once the entry exists (or the
project leaves the installer).

Needs GH_TOKEN with issues:write and GITHUB_REPOSITORY (both set by Actions).
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import update_versions as uv  # noqa: E402

ROOT = uv.ROOT
LABEL = "falta-en-catalogo"
PREFIX = "Falta en el catálogo: "


def gh(method, path, body=None):
    req = urllib.request.Request(f"https://api.github.com/{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Accept": "application/vnd.github+json",
                                          "User-Agent": "gnw-catalog",
                                          "Authorization": f"Bearer {os.environ['GH_TOKEN']}"})
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        return json.loads(data) if data else None


def describe(repo):
    """Markdown for the issue body: the release and, for a core, its header."""
    lines = [f"https://github.com/{repo}", ""]
    try:
        entry = uv.releases(repo, None)
        uv.add_core_info(entry, None)
    except (urllib.error.URLError, OSError) as e:
        return "\n".join(lines + [f"(No se pudieron leer sus releases: {e})"])
    for key, label in (("release", "Release"), ("pre", "Pre-release")):
        r = entry.get(key)
        if not r:
            continue
        lines.append(f"- **{label}:** [{r['version']}]({r['url']}) · {r['date']} · `{r['file']}`")
        info = r.get("info")
        if info:
            fw = "v2.0.0-rc1 o posterior" if info.get("header", 0) >= 3 else "1.x"
            lines.append(f"  - Core `{info.get('core', '')}` · firmware {fw}")
            for s in info.get("systems", []):
                ext = " ".join("." + e for e in s["ext"])
                lines.append(f"  - {s['name']} · `/roms/{s['dir']}/` · {ext}")
    if not entry.get("release") and not entry.get("pre"):
        lines.append("- Sin releases publicadas todavía.")
    lines += ["", "Está en el `packages.list` del instalador del firmware "
              "(sylverb/installer-retro-go-sd) y no tiene ficha en `catalog.json`. "
              "Este issue se cierra solo cuando se añade."]
    return "\n".join(lines)


def main():
    me = os.environ["GITHUB_REPOSITORY"]
    with open(os.path.join(ROOT, "catalog.json"), encoding="utf-8") as fh:
        cat = json.load(fh)
    with open(os.path.join(ROOT, "versions.json"), encoding="utf-8") as fh:
        installer = json.load(fh).get("_installer", [])
    known = {it["repo"].lower() for it in cat["items"]}
    missing = [r for r in installer if r.lower() not in known]

    try:
        gh("POST", f"repos/{me}/labels", {"name": LABEL, "color": "d12f2c",
                                           "description": "Un proyecto del instalador sin ficha"})
    except urllib.error.HTTPError as e:
        if e.code != 422:                   # 422 = it already exists
            raise

    q = urllib.parse.urlencode({"labels": LABEL, "state": "open", "per_page": 100})
    open_issues = {i["title"][len(PREFIX):].strip().lower(): i
                   for i in gh("GET", f"repos/{me}/issues?{q}") or []
                   if i["title"].startswith(PREFIX)}

    for repo in missing:
        if repo.lower() in open_issues:
            continue
        issue = gh("POST", f"repos/{me}/issues",
                   {"title": PREFIX + repo, "body": describe(repo), "labels": [LABEL]})
        print(f"opened #{issue['number']}: {repo}", file=sys.stderr)

    still = {r.lower() for r in missing}
    for repo, issue in open_issues.items():
        if repo in still:
            continue
        added = repo in known                       # else: dropped from the installer
        gh("POST", f"repos/{me}/issues/{issue['number']}/comments",
           {"body": "Añadido al catálogo." if added else "Ya no está en el instalador."})
        gh("PATCH", f"repos/{me}/issues/{issue['number']}",
           {"state": "closed", "state_reason": "completed" if added else "not_planned"})
        print(f"closed #{issue['number']}: {repo}", file=sys.stderr)

    print(f"installer: {len(installer)}, missing: {len(missing)}", file=sys.stderr)


if __name__ == "__main__":
    main()
