# Unreleased
- `GeoCountry` gained four converters between codes and names:
  `from_subregion_codes_to_names`, `from_subregion_names_to_codes`,
  `from_region_names_to_codes` and `from_region_codes_to_names`. Each takes a
  list and answers in the same order, so the two lists can be zipped, and
  translates a repeated entry as many times as it appears. A non-list
  argument, or an entry absent from the country data, raises a `PyvoaError`
  that names the offending entries.
- Python 3.13 is declared as supported and added to the CI test matrix, which
  now covers 3.10, 3.11, 3.12 and 3.13.
- fix: the four `GeoInfo` tests built a real `GeoInfo(0)`, which builds a
  `GeoManager` and downloads about ten pages, so they failed on CI and passed
  locally only on a warm cache. They now use `GeoInfo.__new__`, like the
  `GeoManager` tests next to them.
- `README.md` now documents installation (`pip install pyvoa`, `pyvoa-full`), a
  first example, and a table of the 23 supported databases with their coverage,
  granularity and source.

# version 0.5.0
Eight months and 236 commits since 0.4.2 (2025-12-12 to 2026-08-06), in two
strands: the data and visualization work that occupied most of the period, and
the publication-readiness push of the last few days. A handful of names
changed, so this is not a drop-in upgrade from 0.4.2 — see the renames below.

Data sources and caching:

- eleven database descriptions were added, taking the catalogue from 12 to 23:
  `covid19india`, `covidtracking`, `dgs`, `dpc`, `escovid19data`, `jpnmhlw`,
  `minciencia`, `moh`, `phe`, `risklayer` and `rki`. `listwhom()` now answers
  in alphabetical order.
- the databases read from the project's own Zenodo deposits rather than from
  the original upstream sites, which had grown unreliable. The downloader
  identifies itself as wget, and a file under 1000 characters is treated as a
  failed download and fetched again.
- the download cache moved out of the system temporary directory to
  `~/.cache/pyvoa.data_<user>`, so it survives a reboot.
- `html5lib` became a mandatory dependency.

Geography:

- `where` is forced to a string internally, so numeric département or state
  codes no longer have to be cast at the call site.
- fix: USA subregions gained a three-character `code_region`; the ESP subregion
  naming was homogenised on `Coruña, A`; DEU data is cast to geopandas;
  Belgium's mixture of NaN and None in the geo data no longer breaks a lookup.
- fix: Canada, Chile, Greece and Norway could be drawn individually but not
  under `sumall`, an invalid-geometry problem worked around with `buffer(0)`.
  Portugal needed a different CRS.
- fix: the `europa` database declared its geography as `EUR` while its data is
  world-wide; it is described as `WLD` now.

Visualization:

- `setvisu()` is now `setvis()`, and `get_echoinfo()` moved to the front module.
- the axis-type option is now `scale` (`linear` or `log`), and it applies to
  both the matplotlib and the bokeh backends.
- the bokeh callbacks left the Python sources for `pyvoa/js/`: slider, rollover
  and animation are now three JavaScript files.
- location labels are truncated to a common length, decided in one place, with
  a `dicodisplayloc` keyword to override the displayed name.
- fix: a long list of plotting defects — log scales on histograms and on the
  yearly plot, missing histogram axis labels, the date slider, autozoom for
  maps with few points, country borders, 10⁸ tick notation on bokeh maps,
  colour maps that disagreed between the two backends, `savefig`, and the size
  and placement of the logo.

Data handling:

- fix: cumulative series were reworked throughout — the cumulative sum is taken
  after the missing values are filled, the first `tot_*` variable is selected
  by default, and several databases carried a cumulation they should not have.
- fix: the non-negative filter broke against newer pandas and numpy.
- a pandas or geopandas frame can be plotted through `input=` without calling
  `setwhom()` first, and a session can move between the two in either
  direction.

Errors, warnings and verbosity:

- `PyvoaError` is a real `Exception` subclass and is raised everywhere, instead
  of being called as a bare statement. It is the single exception type of the
  library; the former `PyvoaTypeError`, `PyvoaKeyError`, `PyvoaDbError`,
  `PyvoaWhereError`, `PyvoaLookupError`, `PyvoaConnectionError` and
  `PyvoaNotManagedError` names are gone.
- fix: a missing `import shutil` made every error raise `UnboundLocalError`
  instead of `PyvoaError` when running outside a terminal (script, cron, CI).
- fix: an unknown database name passed to `setwhom()` is reported as a
  `PyvoaError` rather than a `KeyError` from the JSON parser.
- fix: `return_nonan_dates_pandas` trims the leading all-NaN dates.
- `pyvoa/error.py` is gone: the error and warning helpers live in `tools.py`,
  which is also where the geometry helper `wgs84_to_web_mercator` moved, so
  both backends share one copy.
- `set_verbose_mode()` is exposed on the front module. Warnings are quiet at
  verbosity 1, and the noise that external modules print when a French map
  archive or a datetime column is read is swallowed below verbosity 2.

Packaging, tests and process:

- packaging moved to PEP 621: `setup.py` is deleted, `pyproject.toml` reads the
  version from `pyvoa/__version__.py`, and `import pyvoa` exposes
  `pyvoa.__version__` without pulling in the heavy dependencies.
- minimum Python is now 3.10; 3.10, 3.11 and 3.12 are tested.
- a pytest suite that never touches the network by default: any test needing an
  upstream server is marked `@pytest.mark.network` and deselected.
- continuous integration on GitHub Actions: lint, the test matrix, and a weekly
  job for the network tests.
- `ruff check .` is clean and enforced by CI.
- community files for citation and contribution: `AUTHORS`, `CITATION.cff`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md` and the issue forms.
- `__pycache__` is no longer tracked.

# versions 0.4.1, 0.4.2
- cosmetic changes

# version 0.4.0
- Most of the work consisted in adding decorators to the classes.
- Jupyter is not mandatory to use pyvoa; it can be used from a console. 
- add json description of the database
- we use one class per visualization

# version 0.3.1
- cosmetic and docstrings
- version for pip, first full version 

# version 0.3.0
- import of the whole former pycoa software into pyvoa
- using matplotlib as graphical output

# version 0.2.2
- nothing (pip troubles with previous version)

# version 0.2.1
- Structure of the package to deal with pip
- data file can be access now. See test1.py 

# version 0.2.0
Adding geo and a python example

# version 0.1.0
First import, scheleton only
