# Catálogo G&W

*[Read in English](README.md)*

Catálogo de cores y homebrews para la Game & Watch con
[Retro-Go SD](https://github.com/sylverb/game-and-watch-retro-go-sd), con un
enlace de descarga a la última versión de cada proyecto.

**Ábrelo: <https://julenvitoria.github.io/gnw-catalog/>**

## Cómo funciona

- `catalog.json` es la lista de proyectos, que se edita a mano: repo, nombre,
  tipo (`core`, `homebrew` o `tool`), sistema, descripción (en inglés y en
  español; los demás idiomas muestran la inglesa) y, si hace falta, `asset`
  (el patrón del archivo de la release que se ofrece) o `web` (una página que
  se abre en lugar de una descarga), `upstream` (en un fork: el repo original,
  cuya versión se muestra al lado) y `data` (`own` = necesita los archivos del
  juego original, `free` = necesita archivos gratuitos) y `bios`
  (`{dir, files, optional, included, when}`) y `official` (los que sylverb
  cita en el README del firmware; «en el instalador» se lee del
  `packages.list` de installer-retro-go-sd). La ficha `firmware`
  de arriba se muestra como un panel aparte.
- `.github/workflows/versions.yml` se ejecuta cada 8 horas (y cada vez que
  cambia `catalog.json`): `tools/update_versions.py` consulta la última release
  de cada proyecto, y también la pre-release más reciente si es más nueva (la RC del
  firmware, o un core que la necesita), y escribe `versions.json` (versión, fecha y enlace de
  descarga). En los cores lee además la cabecera del `.bin` (una vez por
  versión): las pestañas que añade, su carpeta en `/roms/`, las extensiones y
  para qué firmware es. La página lee ese archivo, así que no consulta a GitHub en cada
  visita.
- Si el instalador del firmware incluye un proyecto que no tiene ficha aquí,
  se abre un issue («Falta en el catálogo: owner/repo», etiqueta
  `falta-en-catalogo`) con su release y su cabecera; se cierra solo cuando se
  añade la ficha.
- Para actualizarlo al momento: Actions → Versions → Run workflow.

## Añadir un proyecto

Añade una ficha a `catalog.json`, o [abre un issue](https://github.com/julenvitoria/gnw-catalog/issues/new)
con el enlace al repo.

## Desarrollo

HTML, CSS y módulos de JavaScript tal cual, sin compilación. Para probarlo en
local: `python3 -m http.server 8000`. El icono se genera con
`python3 tools/make_logo.py`. Los idiomas están en `js/lang/` (uno por archivo;
lo que falte sale en inglés).
