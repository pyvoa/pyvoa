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


def test_matplotlib_show_values_skips_a_location_without_geometry():
    # owid's continents and world carry an empty geometry: its representative
    # point is empty too, and reading its x raised a GEOSException
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from shapely.geometry import Polygon

    from pyvoa.visu_matplotlib import visu_matplotlib

    frame = gpd.GeoDataFrame({
        "where": ["A", "B", "World"],
        "cases": [12.0, 570.0, 582.0],
        "from_db": [True, True, True],
        "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                     Polygon([(2, 0), (3, 0), (3, 1), (2, 1)]),
                     Polygon()],
    }, crs="EPSG:4326")
    # no __init__: it would switch matplotlib to TkAgg
    visu = visu_matplotlib.__new__(visu_matplotlib)
    ax = visu.matplotlib_map(input=frame, which="cases", title="", tile=None,
                             typeofmap=["dense", "show_values"],
                             return_pltaxis=True, pyvoalogo=False)
    assert sorted(t.get_text() for t in ax.texts) == ["12", "570"]
    plt.close("all")
