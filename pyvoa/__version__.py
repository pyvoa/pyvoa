"""
Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.__version__

About : the single source of truth for the package version.

`pyproject.toml` reads `__version__` from here at build time, so the number is
written down exactly once:

    [tool.setuptools.dynamic]
    version = { attr = "pyvoa.__version__.__version__" }

setuptools reads this module *statically* — it parses it rather than importing
it — and `tests/test_paper.py` reads it as text. Keep it free of imports and of
any computed value: a plain literal assignment is what both of them can see, and
it is what keeps `import pyvoa` cheap, since `pyvoa/__init__.py` re-exports
`__version__` without pulling in pandas or geopandas.

Releasing: bump `__version__` here and nowhere else, then follow the checklist
in CONTRIBUTING.md §9. The value must be a valid PEP 440 version.

See https://packaging.python.org/en/latest/guides/single-sourcing-package-version/
"""

__version__ = '0.5.0'

# Neither of these is standardised: distribution metadata belongs in
# pyproject.toml, and AUTHORS and CITATION.cff are the canonical record of
# authorship. They are mirrored here because pyvoa.help and the front singleton
# expose them (`pf.__author__`), so update AUTHORS first and this file after.
__author__ = 'Tristan Beau, Julien Browaeys, Olivier Dadoun'
__email__ = 'contact@pyvoa.org'

__all__ = ['__author__', '__email__', '__version__']
