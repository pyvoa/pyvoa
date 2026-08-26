pyvoa
=====

**pyvoa** (Python Virus Open Analysis) is an open-source Python library giving
unified access to epidemiological databases, a standardised data format,
transparent joins with geolocation data, and built-in time-series and
cartographic visualisation.

It is meant to be usable by non-specialists — high-school and university
students, science journalists, researchers unfamiliar with data extraction —
while remaining scriptable for advanced Python users.

.. code-block:: python

   import pyvoa.front as pf

   pf.setwhom('owid')
   pf.plot(where=['France', 'Italy'], which='tot_cases', what='daily')

Install with ``pip install pyvoa``, or ``pip install pyvoa-full`` for every
visualisation backend.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   api/index

Links
-----

* Project site: https://pyvoa.org
* Source: https://github.com/pyvoa/pyvoa
* Package: https://pypi.org/project/pyvoa/

Indices
-------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
