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
  se abre en lugar de una descarga).
- `.github/workflows/versions.yml` se ejecuta cada 8 horas (y cada vez que
  cambia `catalog.json`): `tools/update_versions.py` consulta la última release
  de cada proyecto y escribe `versions.json` (versión, fecha y enlace de
  descarga). La página lee ese archivo, así que no consulta a GitHub en cada
  visita.
- Para actualizarlo al momento: Actions → Versions → Run workflow.

## Añadir un proyecto

Añade una ficha a `catalog.json`, o [abre un issue](https://github.com/julenvitoria/gnw-catalog/issues/new)
con el enlace al repo.

## Desarrollo

HTML, CSS y módulos de JavaScript tal cual, sin compilación. Para probarlo en
local: `python3 -m http.server 8000`. El icono se genera con
`python3 tools/make_logo.py`. Los idiomas están en `js/lang/` (uno por archivo;
lo que falte sale en inglés).
