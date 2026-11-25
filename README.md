# G&W Catalog

*[Leer en español](README.es.md)*

Catalog of cores and homebrews for the Game & Watch running
[Retro-Go SD](https://github.com/sylverb/game-and-watch-retro-go-sd), with a
download link to each project's latest release.

**Open it: <https://julenvitoria.github.io/gnw-catalog/>**

## How it works

- `catalog.json` lists the projects, edited by hand: repo, name, kind (`core`,
  `homebrew` or `tool`), system, description (English and Spanish; other
  languages show the English one), and optionally `asset` (a glob of the
  release file to offer) or `web` (a page to open instead of a download),
  `upstream` (for a fork: the original repo, whose version is shown beside it)
  and `data` (`own` = needs the original game's files, `free` = needs free
  game files), `bios` (`{dir, files, optional, included, when}`) and `official` (listed
  by sylverb in the firmware's README; "in the installer" is read from
  installer-retro-go-sd's `packages.list`). The `firmware` entry at the top is shown as its own panel.
- `.github/workflows/versions.yml` runs every 8 hours (and whenever
  `catalog.json` changes): `tools/update_versions.py` reads each project's
  latest full release, plus its newest pre-release when that one is newer (the
  firmware's RC, or a core that needs it), and writes `versions.json`
  (version, date, download link). For a core it also reads the header inside
  the `.bin` (once per version): the tabs it adds, their `/roms/` folder and
  extensions, and which firmware it is for. The
  page reads that file, so it never has to ask GitHub on every visit.
- A project the firmware's installer bundles that has no entry here gets an
  issue ("Falta en el catálogo: owner/repo", label `falta-en-catalogo`) with
  its release and header; it closes itself once the entry is added.
- To refresh at once: Actions → Versions → Run workflow.

## Adding a project

Add an entry to `catalog.json`, or [open an issue](https://github.com/julenvitoria/gnw-catalog/issues/new?template=new-project.yml)
with the repo's link.

## Development

Plain HTML, CSS and JavaScript modules, no build step. To try it locally:
`python3 -m http.server 8000`. The logo is made by `python3 tools/make_logo.py`.
Languages live in `js/lang/` (one file each; missing texts fall back to English).
