# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PyVOA (Python Virus Open Analysis) is a Python library for accessing, standardizing, and visualizing COVID-19 and other viral epidemiological datasets from ~24 databases (JHU, OWID, PHE, RKI, DPC, etc.). It targets non-specialist audiences (students, journalists, researchers).

## Development Commands

```bash
# Install in editable mode, with the test dependencies
pip install -e ".[dev]"

# Run the test suite (offline tests only — network tests are deselected)
pytest

# Run the tests that genuinely hit upstream servers
pytest -m network

# Manual smoke test: exercises setwhom() for one or more databases
python test.py

# Install with full visualization support
pip install pyvoa-full
```

The `tests/` directory holds a pytest suite. Everything in the default selection runs offline: `tests/conftest.py` has an autouse fixture that makes any socket creation fail unless the test carries `@pytest.mark.network`, so a test can never quietly start depending on an upstream server. Tests that do need the network are marked and deselected by the `addopts` in `pyproject.toml`.

Two gotchas when adding tests:

- `geo.py` and `jsondb_parser.py` do `from pyvoa.tools import get_local_from_url`, so the name is bound in *their* module namespace. Monkeypatch `pyvoa.geo.get_local_from_url` / `pyvoa.jsondb_parser.get_local_from_url`, never `pyvoa.tools.get_local_from_url`.
- `GeoRegion.__init__` fetches about ten upstream pages, and `GeoManager()` builds one, so anything going through them belongs in `tests/test_network.py`. On a machine with a warm `~/.cache/pyvoa.data_<user>` they *look* offline; they are not on a fresh checkout.

`test.py` is an untracked local scratch script, not a committed part of the repo — treat it as a convenience harness, not a source of truth. It loops over `pf.listwhom()` and calls `pf.setwhom(w)` for each; check the `continue` filter at the top of the loop before relying on it, since it's routinely edited in place to target whichever database(s) are currently being debugged (a recurring set: covidtracking, escovid19data, jhu-usa, moh, rki, sciensano).

One test is a strict `xfail` recording a known bug rather than asserting it as correct: `return_nonan_dates_pandas` never drops leading all-NaN dates (sign error in the leading-edge loop — it computes `watchdate - timedelta(j-1)` where the trailing loop needs `+`). Fix the code and the xfail flips to a pass; do not delete the test.

`HANDOFF.md` at the repo root tracks the JOSS-readiness plan. Tasks 1–3 (the `shutil` import, PEP 621 packaging, the test suite) are done, as is the `__pycache__`/`.gitignore` bullet of task 4. The rest of task 4 (the CI workflow, ruff, README badges) and tasks 5–6 (community files, README) are not yet implemented.

## Architecture

### Data flow

```
front.setwhom(db_name)
    → GPDBuilder (geopd_builder.py)       # initializes database
        → MetaInfo + DataParser (jsondb_parser.py)  # reads pyvoa/data/<db>.json
        → downloads + caches data in ~/.cache/pyvoa.data_<username>/
        → GeoManager (geo.py)             # normalizes location names
front.get(...)                            # returns pandas/geopandas DataFrame
front.plot() / .map() / .histogram()
    → AllVisu (visualizer.py)             # dispatches to backend
        → visu_matplotlib / visu_bokeh / visu_seaborn / visu_folium
```

### Key modules

| Module | Role |
|--------|------|
| `front.py` | Main public API (`front` class) — entry point for all user operations |
| `geopd_builder.py` | `GPDBuilder`: database initialization, download, caching |
| `jsondb_parser.py` | `MetaInfo` + `DataParser`: reads the 23 JSON database configs in `pyvoa/data/` |
| `geo.py` | `GeoManager` (country-name normalization), `GeoInfo`, `GeoRegion`, `GeoCountry` |
| `visualizer.py` | `AllVisu`: visualization coordinator, dispatches to pluggable backends |
| `visu_*.py` | Visualization backends (matplotlib, bokeh, seaborn, folium) |
| `tools.py` | Shared utilities: caching (CRC32), kwargs validation, date parsing, and colored-terminal error/warning/info display (`PyvoaError`, `PyvoaWarning`, `PyvoaInfo`) |
| `kwarg_options.py` | `InputOption`: schema-based kwarg validation |

### Database configuration

Each supported database is described by a JSON file in `pyvoa/data/` (23 as of this writing). These files specify: data URLs, column definitions with aliases, granularity (country/region/subregion), and parsing rules. Adding a new database means adding a JSON file and no Python changes in most cases. `CONTRIBUTING.md` §6 has the checklist for new-database PRs (open licence, stable URL, ISO 3166-resolvable geography, documented caveats).

### Caching

Downloaded files are cached under `~/.cache/pyvoa.data_<username>/`. Files smaller than 1000 characters are considered corrupt/empty and re-downloaded. Cache invalidation is CRC32-based (in `tools.py`).

### Geographic normalization

All location names are normalized through `tostdstring()` (a module-level function in `tools.py`, not a `GeoManager` method), which strips accents via `unidecode`, collapses whitespace and hyphens, and upper-cases. Country names, ISO3 codes, regions, and subregions are all supported. Mappings use `pycountry` and `pycountry_convert`.

### Error handling

`PyvoaError` (in `tools.py`) is the single exception type of the library — there is no hierarchy, and the older `PyvoaTypeError` / `PyvoaKeyError` / `PyvoaDbError` / `PyvoaWhereError` / `PyvoaLookupError` / `PyvoaConnectionError` / `PyvoaNotManagedError` names no longer exist. It is a real `Exception` subclass and must always be **raised**, never called as a bare statement (a bare call constructs the object, prints the banner and then does nothing). It renders its coloured banner at construction time, so the message still reaches the end user when the traceback is hidden, as in a notebook.

`PyvoaWarning` and `PyvoaInfo` are *not* exceptions: they are display functions gated on the verbosity (`> 0` and `> 1` respectively).

### Verbosity

Global `_verbose_mode`: 0 = silent, 1 = info, 2 = debug. Use `verb()` / `info()` from `tools.py` for conditional output — do not use bare `print()` in library code.

### Visualization backends

Backends are optional imports that fail gracefully. `AllVisu` discovers available plot methods via `dir()` + `callable()`. Matplotlib backend uses a decorator (`decomatplotlib`) to inject logos and titles.

## Version

Single source of truth: `pyvoa/__version__.py`. `pyproject.toml` reads it through `[tool.setuptools.dynamic]`, `pyvoa/__init__.py` re-exports it (so `import pyvoa; pyvoa.__version__` works without pulling in the heavy dependencies), and the `front` class welcome message prints it. There is no `setup.py` any more — packaging is PEP 621.
