Visualisation backends
======================

Three backends draw the charts, and they do not all offer the same ones:
``compare`` and ``spiral`` plots and the date slider exist only in bokeh, and
seaborn has no map. :class:`pyvoa.visualizer.AllVisu` routes each request to
the right one according to the ``vis`` argument.

pyvoa.visu_matplotlib
---------------------

.. automodule:: pyvoa.visu_matplotlib
   :members:
   :show-inheritance:

pyvoa.visu_bokeh
----------------

.. automodule:: pyvoa.visu_bokeh
   :members:
   :show-inheritance:

pyvoa.visu_seaborn
------------------

.. automodule:: pyvoa.visu_seaborn
   :members:
   :show-inheritance:

pyvoa.visu_folium
-----------------

.. automodule:: pyvoa.visu_folium
   :members:
   :show-inheritance:
