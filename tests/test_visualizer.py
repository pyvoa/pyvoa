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


def test_visu_matplotlib_keeps_the_backend_mplbackend_names():
    # it used to switch to TkAgg, and the plots of test_front.py then opened
    # windows a terminal run had to close by hand
    import matplotlib

    from pyvoa.visu_matplotlib import visu_matplotlib

    visu_matplotlib()
    assert matplotlib.get_backend().lower() == "agg"


def test_bokeh_dateslider_histogram_opens_ranked_capped_on_the_last_date():
    # the source drawn before the slider moves used to hold every location in
    # alphabetical order, stacked on the maxcountrydisplayed slots, on the
    # date whose '%d/%m/%Y' string sorts last (31/08 over 09/10)
    pytest.importorskip("bokeh")
    from importlib.resources import files

    import pandas as pd
    from bokeh.models import ColumnDataSource, Slider

    from pyvoa.visu_bokeh import visu_bokeh

    dates = pd.to_datetime(["2026-08-31", "2026-10-09"])
    where = [f"L{i:02d}" for i in range(15)]
    frame = pd.DataFrame([
        {"date": d, "where": w, "code": w, "from_db": True,
         "tot_deaths": float(k * (i + 1)), "colors": "#000000"}
        for k, d in enumerate(dates, 1) for i, w in enumerate(where)
    ]).sort_values("tot_deaths", ascending=False).reset_index(drop=True)
    fig = visu_bokeh().bokeh_horizonhisto(
        input=frame, which="tot_deaths", title="", pyvoalogo=False,
        logo=str(files("pyvoa") / "data" / "logo-pyvoa.png"),
        dateslider=True, maxcountrydisplayed=12, typeofmap=["not dense"])
    source = next(m for m in fig.select({"type": ColumnDataSource}) if "top" in m.data)
    assert list(source.data["where"]) == [f"L{i:02d}" for i in range(14, 2, -1)]
    assert set(source.data["date"]) == {"09/10/2026"}
    # the slider opens on that date, the last one
    assert [s.value for s in fig.select({"type": Slider})] == [1]
