API reference
=============

Every page below is generated from the docstrings in ``pyvoa/``. They follow
the NumPy convention, which ruff enforces, and are read here by
:mod:`sphinx.ext.napoleon`.

The user-facing entry point is :mod:`pyvoa.front`: importing it as ``pf``
exposes every method of the front singleton at module level, so ``pf.get()``,
``pf.plot()``, ``pf.hist()`` and ``pf.map()`` are called directly.

.. toctree::
   :maxdepth: 1

   front
   geo
   geopd_builder
   jsondb_parser
   tools
   kwargs_options
   visualizer
   backends
   help
