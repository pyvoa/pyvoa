# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PyVOA (Python Virus Open Analysis) is a Python library for accessing, standardizing, and visualizing COVID-19 and other viral epidemiological datasets from 23 databases (JHU, OWID, PHE, RKI, DPC, etc.). It targets non-specialist audiences (students, journalists, researchers).

## Development Commands

```bash
# Install in editable mode, with the test dependencies
pip install -e ".[dev]"

# Run the test suite (offline tests only — network tests are deselected)
pytest

# Run the tests that genuinely hit upstream servers
pytest -m network

# Lint (must be clean: this is what the CI lint job runs)
ruff check .

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

`HANDOFF.md` at the repo root tracks the JOSS-readiness plan and its current task status.

## Lint

`ruff check .` must be clean — it is enforced by CI, and the tree is currently at zero findings. The configuration lives in `[tool.ruff]` in `pyproject.toml`: ruff's own default rule set plus `E4`/`E7`/`E9`, with `*.ipynb` excluded (the example notebooks are documentation, not library code). The ruff version is **pinned** in the `dev` extra and in the workflow, because ruff widens its default selection between releases and an unpinned gate would start failing on its own.

Four exceptions are deliberate, and the reasoning is recorded next to them in `pyproject.toml` — do not "fix" the underlying code to satisfy these rules:

- **BLE001** — `except Exception:` followed by `raise PyvoaError(...)` is the intended pattern, since `PyvoaError` is the library's single documented exception type.
- **DTZ001 / DTZ007 / DTZ011** — epidemiological series are indexed by calendar dates, which have no timezone. Making them tz-aware would shift dates near midnight.
- **E402, `pyvoa/front.py` only** — the module sets a `FutureWarning` filter before importing pandas/geopandas so those imports stay quiet for notebook users, and it exposes the singleton's methods at module level after instantiating it.

`# noqa: F401` on the optional-backend probes in `visualizer.py` and on `import google.colab` in `tools.py` is also intentional: importing *is* the availability test there.

Dead assignments are commented out rather than deleted, so the original intent stays readable.

## Continuous integration

`.github/workflows/ci.yml` runs three jobs on push to `main` and on every pull request:

- `lint` — pinned ruff, installed alone so the job does not build geopandas.
- `test` — python 3.10/3.11/3.12/3.13 (matching the classifiers), the offline suite, coverage written to the GitHub Actions job summary and uploaded as a `coverage.xml` artefact. There is no third-party coverage service, hence a CI badge in `README.md` but no coverage badge.
- `network` — the `@pytest.mark.network` tests, restricted to the weekly cron and manual dispatch, so an upstream outage can never block a pull request.

## Architecture

### Database configuration

Each supported database is described by a JSON file in `pyvoa/data/`. These files specify: data URLs, column definitions with aliases, granularity (country/region/subregion), and parsing rules. Adding a new database means adding a JSON file and no Python changes in most cases. `CONTRIBUTING.md` §6 has the checklist for new-database PRs (open licence, stable URL, ISO 3166-resolvable geography, documented caveats).

### Caching

Downloaded files are cached under `~/.cache/pyvoa.data_<username>/`. Files smaller than 1000 characters are considered corrupt/empty and re-downloaded. Cache invalidation is CRC32-based (in `tools.py`).

### Geographic normalization

All location names are normalized through `tostdstring()` (a module-level function in `tools.py`, not a `GeoManager` method), which strips accents via `unidecode`, collapses whitespace and hyphens, and upper-cases. Country names, ISO3 codes, regions, and subregions are all supported. Mappings use `pycountry` and `pycountry_convert`.

### Error handling

`PyvoaError` (in `tools.py`) is the single exception type of the library — there is no hierarchy, and the older `PyvoaTypeError` / `PyvoaKeyError` / `PyvoaDbError` / `PyvoaWhereError` / `PyvoaLookupError` / `PyvoaConnectionError` / `PyvoaNotManagedError` names no longer exist. It is a real `Exception` subclass and must always be **raised**, never called as a bare statement (a bare call constructs the object, prints the banner and then does nothing). It renders its coloured banner at construction time, so the message still reaches the end user when the traceback is hidden, as in a notebook.

`PyvoaWarning` and `PyvoaInfo` are *not* exceptions: they are display functions gated on the verbosity (`> 0` and `> 1` respectively).

### Known dead API

`front.merger()` calls `self.gpdbuilder.merger(...)`, but no `merger` method exists on `GPDBuilder` or anywhere else in the package — the method has never been callable. It either needs an implementation or removal; do not assume it works.

### Verbosity

Global `_verbose_mode`: 0 = silent, 1 = info, 2 = debug. Use `verb()` / `info()` from `tools.py` for conditional output — do not use bare `print()` in library code.

### Visualization backends

Backends are optional imports that fail gracefully. `AllVisu` discovers available plot methods via `dir()` + `callable()`. Matplotlib backend uses a decorator (`decomatplotlib`) to inject logos and titles.

## Version

Single source of truth: `pyvoa/__version__.py`. `pyproject.toml` reads it through `[tool.setuptools.dynamic]`, `pyvoa/__init__.py` re-exports it (so `import pyvoa; pyvoa.__version__` works without pulling in the heavy dependencies), and the `front` class welcome message prints it. There is no `setup.py` any more — packaging is PEP 621.
