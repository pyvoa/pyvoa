"""The pyvoa package.

Deliberately thin: it re-exports ``__version__`` and nothing else, so that
``import pyvoa`` stays cheap and does not drag in pandas or geopandas. The
library itself is reached through ``import pyvoa.front as pf``, which exposes
every method of the front singleton at module level.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
"""
from pyvoa.__version__ import __version__

__all__ = ["__version__"]
