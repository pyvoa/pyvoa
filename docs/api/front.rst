pyvoa.front
===========

.. module:: pyvoa.front

The user-facing entry point. Importing the module instantiates the ``front``
class once and copies every public method of that singleton onto the module
itself, so the two spellings below are the same object:

.. code-block:: python

   import pyvoa.front as pf

   pf.setwhom('owid')          # the module-level name
   pf.plot(where='France')

Each method is documented once, on the class. The module-level name is a
reference to the same bound method, so ``help(pf.plot)`` shows what is written
here.

.. autoclass:: pyvoa.front.front
   :members:
   :show-inheritance:
   :member-order: bysource

Module-level helpers
--------------------

.. autofunction:: pyvoa.front.getversion
