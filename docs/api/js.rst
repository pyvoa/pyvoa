Bokeh callbacks
===============

The interactive parts of the bokeh charts -- the date slider, its Play button,
the hover tooltips -- run in the browser, as javascript. Each callback is a
file of ``pyvoa/js/``, which :mod:`pyvoa.visu_bokeh` reads and hands to a
bokeh ``CustomJS`` (or ``CustomJSHover``) along with the objects it acts on.

The code of a file is the body of a function: its parameters, listed below,
are those objects, the keys of the ``args`` of the ``CustomJS``, and
``cb_obj``, the widget whose change fires it. Some of them repeat in
javascript what the python side draws before the slider moves, and are tested
against it in ``tests/test_js.py``.

Every callback is part of pyvoa, by Tristan Beau, Julien Browaeys and Olivier
Dadoun, under the licence of the package.

.. jscallbacks::
