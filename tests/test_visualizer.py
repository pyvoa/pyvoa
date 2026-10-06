"""Offline tests of the chart dispatcher, AllVisu."""

import pytest

from pyvoa.tools import PyvoaError
from pyvoa.visualizer import AllVisu


@pytest.fixture
def allvisu():
    """Build an AllVisu with its default cap, without any database."""
    visu = AllVisu.__new__(AllVisu)
    visu.maxcountrydisplayed = 12
    return visu


def test_maxcountry_defaults_to_twelve(allvisu):
    assert allvisu.maxcountry({}) == 12


def test_maxcountry_takes_the_value_asked_for(allvisu):
    assert allvisu.maxcountry({"maxcountrydisplayed": 15}) == 15


@pytest.mark.parametrize("bad", [0, -3, 2.5, "ten", True, None])
def test_maxcountry_refuses_anything_but_a_positive_integer(allvisu, bad):
    with pytest.raises(PyvoaError):
        allvisu.maxcountry({"maxcountrydisplayed": bad})
