# Unreleased
- fix: the four `GeoInfo` tests built a real `GeoInfo(0)`, which builds a
  `GeoManager` and downloads about ten pages, so they failed on CI and passed
  locally only on a warm cache. They now use `GeoInfo.__new__`, like the
  `GeoManager` tests next to them.
- `README.md` now documents installation (`pip install pyvoa`, `pyvoa-full`), a
  first example, and a table of the 23 supported databases with their coverage,
  granularity and source.

# version 0.5.0
Publication-readiness release: no change to the analysis API, but the package,
its error handling and its development process are now those expected of a
citable piece of research software.

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
