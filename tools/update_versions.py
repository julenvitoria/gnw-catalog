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

For a core it also downloads that file once per version and reads the header
the firmware itself reads (gnw_core_meta_t, see read_core()): the launcher tabs
the core adds, their /roms/ folder and extensions, and the header version,
which says which firmware it is for (3 = v2.0.0-rc1 and later, older = 1.x).

Runs in .github/workflows/versions.yml with GITHUB_TOKEN; locally it works
too (set GH_TOKEN for more than 60 requests an hour). A repo that cannot be
read keeps its previous entry, so one failure never blanks the rest.
"""
import fnmatch
import io
import json
import os
import struct
import sys
import zipfile
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


# ------------------------------------------------------------ core header
# "CORE", u16 header_version, u16 header_length, then gnw_core_meta_t
# (Core/Inc/retro-go/gnw_core_meta.h in the firmware):
#   u32 abi_version, abi_min_size, flags, segments_count; 4 x 12-byte segments;
#   u32 systems_count at 72; 4 x 116-byte gnw_core_system_t at 76;
#   u8 version[3] + char core_name[24] at 540.
SYSTEM = struct.Struct("<32s16s32sIIIII8s8s")


def cstr(b):
    return b.split(b"\0", 1)[0].decode("utf-8", "replace").strip()


def parse_core(b):
    if len(b) < 8 or b[:4] != b"CORE":
        return None
    header = struct.unpack_from("<H", b, 4)[0]
    info = {"header": header}
    if header >= 3 and len(b) >= 567:
        info["abi"] = struct.unpack_from("<I", b, 8)[0]
        n = min(struct.unpack_from("<I", b, 72)[0], 4)
        info["systems"] = []
        for i in range(n):
            name, dirname, exts, parse, *_rest, cheat, _ = SYSTEM.unpack_from(b, 76 + SYSTEM.size * i)
            sysinfo = {"name": cstr(name), "dir": cstr(dirname), "ext": cstr(exts).split()}
            if cstr(cheat):
                sysinfo["cheat"] = cstr(cheat)
            if parse == 1:
                sysinfo["cdrom"] = True
            info["systems"].append(sysinfo)
        info["core"] = cstr(b[543:567])
    return info


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "gnw-catalog"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def read_core(rel):
    """The header of the core in this release's file (a .bin, or a zip holding cores/*.bin)."""
    if not rel or not rel.get("download"):
        return None
    data = download(rel["download"])
    if data[:4] == b"CORE":
        return parse_core(data[:2048])
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return None
    for name in sorted(z.namelist(), key=lambda n: (not n.startswith("cores/"), n)):
        if name.lower().endswith(".bin"):
            info = parse_core(z.read(name)[:2048])
            if info:
                return info
    return None


def add_core_info(entry, previous):
    """Fill entry[...]["info"]; reuse the previous run's when the file is the same."""
    for key in ("release", "pre"):
        rel = entry.get(key)
        if not rel:
            continue
        old = (previous or {}).get(key) or {}
        if old.get("download") == rel["download"] and "info" in old:
            rel["info"] = old["info"]
            continue
        try:
            rel["info"] = read_core(rel)
        except (urllib.error.URLError, OSError) as e:
            print(f"  {rel['download']}: {e}", file=sys.stderr)


INSTALLER_LIST = "https://raw.githubusercontent.com/sylverb/installer-retro-go-sd/main/packages.list"


def installer_repos():
    """The repos the firmware's core installer bundles (lines 'github:owner/repo[:glob]')."""
    text = download(INSTALLER_LIST).decode("utf-8", "replace")
    repos = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("github:"):
            repos.append(line[len("github:"):].split(":", 1)[0])
        elif "|" in line:                                   # old 'kind | id | name | source' form
            src = line.split("|")[-1].strip()
            if src.startswith("github:"):
                repos.append(src[len("github:"):].split(":", 1)[0])
    return sorted(set(repos))


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
    cores = set()                                    # repos whose header is read
    fw = cat.get("firmware")
    if fw:
        wanted[fw["repo"]] = fw.get("asset")
    for it in cat["items"]:
        if not it.get("web"):
            wanted[it["repo"]] = it.get("asset")
            if it["kind"] == "core":
                cores.add(it["repo"])
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
        if repo in cores:
            add_core_info(out[repo], previous.get(repo))
        r, p = out[repo]["release"], out[repo]["pre"]
        print(f"{repo}: {r['version'] if r else '-'}{' + pre ' + p['version'] if p else ''}", file=sys.stderr)

    try:
        out["_installer"] = installer_repos()
        print(f"installer: {len(out['_installer'])} projects", file=sys.stderr)
    except (urllib.error.URLError, OSError) as e:
        out["_installer"] = previous.get("_installer", [])
        print(f"installer list: {e} (kept the previous one)", file=sys.stderr)

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


if __name__ == "__main__":
    main()
