# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PyVOA (Python Virus Open Analysis) is a Python library for accessing, standardizing, and visualizing COVID-19 and other viral epidemiological datasets from 25 databases (JHU, OWID, PHE, RKI, DPC, etc.). It targets non-specialist audiences (students, journalists, researchers).

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

`HANDOFF.md` at the repo root tracks the publication-readiness plan and its current task status. The target journal is SoftwareX (it was JOSS until 2026-08-13).

## Lint

`ruff check .` must be clean — it is enforced by CI, and the tree is currently at zero findings. The configuration lives in `[tool.ruff]` in `pyproject.toml`: ruff's own default rule set plus `E4`/`E7`/`E9`, with `*.ipynb` excluded (the example notebooks are documentation, not library code). The ruff version is **pinned** in the `dev` extra and in the workflow, because ruff widens its default selection between releases and an unpinned gate would start failing on its own.

Four exceptions are deliberate, and the reasoning is recorded next to them in `pyproject.toml` — do not "fix" the underlying code to satisfy these rules:

- **BLE001** — `except Exception:` followed by `raise PyvoaError(...)` is the intended pattern, since `PyvoaError` is the library's single documented exception type.
- **DTZ001 / DTZ007 / DTZ011** — epidemiological series are indexed by calendar dates, which have no timezone. Making them tz-aware would shift dates near midnight.
- **E402, `pyvoa/front.py` only** — the module sets a `FutureWarning` filter before importing pandas/geopandas so those imports stay quiet for notebook users, and it exposes the singleton's methods at module level after instantiating it.

`# noqa: F401` on the optional-backend probes in `visualizer.py` and on `import google.colab` in `tools.py` is also intentional: importing *is* the availability test there.

Dead assignments are commented out rather than deleted, so the original intent stays readable.

## Continuous integration

`.github/workflows/ci.yml` runs four jobs on push to `main` and on every pull request:

- `lint` — pinned ruff, installed alone so the job does not build geopandas.
- `test` — python 3.10/3.11/3.12/3.13 (matching the classifiers), the offline suite, coverage written to the GitHub Actions job summary and uploaded as a `coverage.xml` artefact. There is no third-party coverage service, hence a CI badge in `README.md` but no coverage badge.
- `minimum` — the same offline suite on python 3.10 with every direct dependency pinned to the lower bound declared in `pyproject.toml` (`uv pip install --resolution lowest-direct`). `test` always resolves to the newest release, so without this job the floors would be unverified claims. If you raise a floor, this is what proves it was necessary; if you lower one, this is what proves it works.
- `network` — the `@pytest.mark.network` tests, restricted to the weekly cron and manual dispatch, so an upstream outage can never block a pull request.

## Architecture

### Database configuration

Each supported database is described by a JSON file in `pyvoa/data/`. These files specify: data URLs, column definitions with aliases, granularity (country/region/subregion), and parsing rules. Two dataset keys are easy to confuse: `names` declares the columns of a CSV shipped **without** a header line (`ebolardc`), while `namedata` marks a *wide* file whose columns are dates and triggers a melt to long form (`jhu`, `jpnmhlw`) — a file that is already long must not carry it. `splitwhere` (`{"separator": ",", "keep": -1}`) cuts a composite location such as `"Gaines, Texas"` down to the part the database is indexed by; the parser then sums the rows that collapse onto the same `(date, where)`, which is how `measles-usa` and `jhu-usa` aggregate counties into states.

Two column keys handle sources that report *increments* rather than totals, as `measles-usa` does. `cumulative: true` runs a `cumsum()` per location at parse time, since pyvoa's `what` has no cumulating step and every `tot_*` series is expected to be cumulative already. That sum stops at the first missing day, so a sparse source must also carry `fillmissing: true`, which turns the days `fill_missing_dates()` inserted into zeros first. Both are opt-in per column: the six databases that used `cumulative` before are dense and unaffected. Adding a new database means adding a JSON file and no Python changes in most cases. `CONTRIBUTING.md` §6 has the checklist for new-database PRs (open licence, stable URL, ISO 3166-resolvable geography, documented caveats).

### Caching

Downloaded files are cached under `~/.cache/pyvoa.data_<username>/`. Files smaller than 1000 characters are considered corrupt/empty and re-downloaded. Cache invalidation is CRC32-based (in `tools.py`).

### Data source mode: archive vs live

`get_local_from_url()` in `tools.py` serves **every** download — database payloads *and* the ~20 reference pages `geo.py` scrapes — from a frozen Zenodo record by default: any non-Zenodo url is rewritten to `https://zenodo.org/api/records/18784098/files/<netloc>_<crc32>/content`, and the caller's `expiration_time` is forced to 0 so an archived file is fetched once and never again. That is what makes a given release reproducible.

The global `_live_mode` (`get_live_mode()` / `set_live_mode()` in `tools.py`, same shape as `_verbose_mode`) turns that off. When it is on:

- the Zenodo rewrite is skipped, so the original url is fetched;
- the caller's `expiration_time` is honoured again (`jsondb_parser` passes 10000 s);
- `jsondb_parser.get_parsing()` reads `datasets['urlparent']` — the upstream source declared in the JSON description — instead of `datasets['urldata']`, which is the Zenodo mirror.

The cache filename is `netloc + crc32(url)`, so the archived and the live copy of the same dataset land in different files and switching mode cannot corrupt either.

The user-facing switch is `front.setlive(live=True)` / `front.getlive()`, exported at module level like everything else on the singleton (`pv.setlive(True)`). Changing the mode resets `self.db = ''`, because `setwhom()` early-returns when the requested database is already the current one and would otherwise keep serving the frame parsed from the other source.

**URL fields in the JSON descriptions.** Three keys, with one meaning each:

- `urldata` — what is actually downloaded by default: the Zenodo mirror. Mandatory (`checkmetadatastructure`).
- `urlparent` — the live data *file* upstream, used in live mode. All 41 datasets carry one, and `tests/test_jsondb_parser.py::test_every_shipped_dataset_declares_a_live_source` keeps it that way.
- `urlmaster` — the human-readable page of the provider (a GitHub repo, a data.gouv.fr dataset page). Optional, purely informative, never fetched.

A database added after the last archive run has no Zenodo copy at all (`ebolardc` is the first). `get_local_from_url()` handles that by itself: if the mirror answers with an error or with less than 1000 characters, it falls back to the original URL, so a new database works in both modes without a Zenodo deposit.

`spf.json` and `sumeau.json` used to hold the opposite convention (live file in `urlmaster`, landing page in `urlparent`); they were swapped to match `sentinellesIRA.json` and the rest. A dataset with no `urlparent` still falls back to `urldata` with a `PyvoaWarning`, but none is in that case today.

**Four databases are dead upstream** and therefore only work from the archive, whatever `urlparent` says: `phe` (all five datasets — `api.coronavirus.data.gov.uk` no longer resolves; UKHSA moved to `api.ukhsa-dashboard.data.gov.uk`, whose API is not a drop-in replacement), `minciencia` (404), and `moh` datasets #1 and #3 (the upstream repo renamed the files to `epidemic/deaths_state.csv` and `vaccination/vax_state.csv`, whose columns still need checking against the JSON). Their `urlparent` values are the historical ones and have deliberately not been touched.

### Geographic normalization

All location names are normalized through `tostdstring()` (a module-level function in `tools.py`, not a `GeoManager` method), which strips accents via `unidecode`, collapses whitespace and hyphens, and upper-cases. Country names, ISO3 codes, regions, and subregions are all supported. Mappings use `pycountry` and `pycountry_convert`.

### Country geographies (`GeoCountry`)

`_country_info_dict` maps an ISO3 code to one geometry file, `_source_dict` adds the auxiliary sources, and one `elif self._country == 'XXX':` branch in `__init__` normalises whatever that file ships into `name_subregion` / `code_subregion` / `name_region` / `code_region` / `geometry` (plus optional `population_subregion`, `flag_subregion`, …). Everything downstream — `get_subregion_list()`, the region dissolve in `get_data(True)`, `jsondb_parser` — only ever sees those normalised names.

`COD` (Democratic Republic of the Congo) is the geography of the Ebola database: 519 health zones (*zones de santé*) from the INRB/UMIE build, grouped in the 26 provinces. The provinces carry no code upstream, so they are resolved to their ISO 3166-2:CD code through `pycountry` keyed on `tostdstring(name)` — all 26 match. Population comes from the WorldPop count shipped by the same repository. The geojson also embeds the whole epidemiological payload as nested properties; the branch keeps the geographic columns only.

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


