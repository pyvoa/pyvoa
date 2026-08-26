"""Sphinx configuration for the pyvoa documentation.

The API pages are generated from the docstrings in ``pyvoa/`` by autodoc, and
read by the napoleon extension, which understands the NumPy convention the
package is written to (see CONTRIBUTING.md section 5).
"""

import os
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _dist_version

# The package is documented from the working tree, not from an installed copy,
# so that the docs always describe the checkout they are built in.
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "pyvoa"
author = "Tristan Beau, Julien Browaeys, Olivier Dadoun"
copyright = "2020-2026, the pyvoa team"

try:
    release = _dist_version("pyvoa")
except PackageNotFoundError:
    # Not installed: read the single source of truth directly, the way
    # pyproject.toml does.
    from pyvoa.__version__ import __version__ as release
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- napoleon ----------------------------------------------------------------
# pyvoa writes NumPy-style docstrings and ruff enforces it, so the Google
# parser is switched off: leaving it on would let a Google-style docstring
# render correctly here while still failing the lint gate.
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True

# -- autodoc -----------------------------------------------------------------

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
autodoc_preserve_defaults = True

# The visualisation backends are optional dependencies: pyvoa imports them at
# module level and fails gracefully at runtime when one is absent. None of them
# is in `dependencies`, so none is present in the environment the workflow
# builds from; mocking all four is what lets the docs cover every backend
# without installing bokeh, seaborn and folium just to read their docstrings.
# autodoc still reads the real pyvoa modules -- only the third-party names they
# import are stubbed.
autodoc_mock_imports = ["bokeh", "seaborn", "folium", "branca"]

# -- intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "geopandas": ("https://geopandas.org/en/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

# -- HTML output -------------------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = f"pyvoa {release}"
html_baseurl = "https://pyvoa.github.io/pyvoa/"


# -- The decorated front methods ---------------------------------------------
# get(), plot(), hist() and map() are defined with the signature of the
# innermost function of a decorator chain -- ``plot(self, fig)`` -- while the
# callable a user reaches takes keyword arguments only. autodoc reads the
# source signature and would advertise ``fig``, a parameter no caller can
# pass. The docstrings say so in their Notes, but the signature line is what a
# reader skims, so it is corrected here.
_KWARGS_ONLY = {
    "pyvoa.front.front.get",
    "pyvoa.front.front.plot",
    "pyvoa.front.front.hist",
    "pyvoa.front.front.map",
}


def _fix_decorated_signature(app, what, name, obj, options, signature, return_annotation):
    """Advertise the keyword-only signature the decorators actually accept."""
    if name in _KWARGS_ONLY:
        return "(**kwargs)", return_annotation
    return None


def setup(app):
    """Register the Sphinx hooks this project needs."""
    app.connect("autodoc-process-signature", _fix_decorated_signature)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
