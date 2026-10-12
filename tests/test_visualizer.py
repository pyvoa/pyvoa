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


def test_bokeh_dateslider_pie_gathers_the_other_locations():
    # with the slider, the pie used to keep the first maxcountrydisplayed
    # locations only, and its shares were those of their own total
    pytest.importorskip("bokeh")
    from importlib.resources import files

    import pandas as pd
    from bokeh.models import ColumnDataSource

    from pyvoa.visu_bokeh import visu_bokeh

    dates = pd.to_datetime(["2026-08-31", "2026-10-09"])
    where = [f"L{i:02d}" for i in range(15)]
    frame = pd.DataFrame([
        {"date": d, "where": w, "code": w, "from_db": True,
         "tot_deaths": float(k * (i + 1)), "colors": "#000000"}
        for k, d in enumerate(dates, 1) for i, w in enumerate(where)
    ])
    fig = visu_bokeh().bokeh_pie(
        input=frame, which="tot_deaths", title="", pyvoalogo=False,
        logo=str(files("pyvoa") / "data" / "logo-pyvoa.png"),
        dateslider=True, maxcountrydisplayed=12, typeofmap=["not dense"],
        mode="mouse")
    source = next(m for m in fig.references()
                  if isinstance(m, ColumnDataSource) and "angle" in m.data)
    values = dict(zip(source.data["where"], source.data["tot_deaths"]))
    # L00 to L02, 2 + 4 + 6 on the last date, make the thirteenth slice
    assert len(values) == 13 and values["SumOthers"] == 12.0
    assert abs(sum(source.data["percentage"]) - 1) < 1e-9


def test_bokeh_pie_paints_sumothers_white():
    # deco_bokeh gave the 'SumOthers' slice a colour of the cycle, over the
    # white decohistomap and the slider callback give it, and recoloured the
    # locations after the order of the rows
    pytest.importorskip("bokeh")
    from importlib.resources import files

    import pandas as pd
    from bokeh.models import ColumnDataSource

    from pyvoa.visu_bokeh import visu_bokeh

    frame = pd.DataFrame({
        "date": pd.to_datetime(["2026-10-09"] * 3), "where": ["A_B", "C", "D"],
        "code": ["SumOthers", "C", "D"], "from_db": True,
        "tot_deaths": [5.0, 4.0, 3.0], "colors": ["#123456", "#ff7f0e", "#2ca02c"],
    })
    fig = visu_bokeh().bokeh_pie(
        input=frame, which="tot_deaths", title="", pyvoalogo=False,
        logo=str(files("pyvoa") / "data" / "logo-pyvoa.png"),
        dateslider=False, maxcountrydisplayed=12, typeofmap=["not dense"],
        mode="mouse")
    source = next(m for m in fig.references()
                  if isinstance(m, ColumnDataSource) and "angle" in m.data)
    colors = dict(zip(source.data["code"], source.data["colors"]))
    assert colors["SumOthers"] == "#FFFFFF"
    # the locations keep the colours they come with, one per location
    assert colors["C"] == "#ff7f0e" and colors["D"] == "#2ca02c"


def test_bokeh_dateslider_histogram_by_value_bins_every_date_as_without():
    # the histogram by value took dateslider, drew no slider and binned every
    # date of every location together
    pytest.importorskip("bokeh")
    from importlib.resources import files

    import pandas as pd
    from bokeh.models import CustomJS, Slider

    from pyvoa.tools import gather_others
    from pyvoa.visu_bokeh import visu_bokeh

    dates = pd.to_datetime(["2026-08-31", "2026-10-09"])
    where = [f"L{i:02d}" for i in range(15)]
    frame = pd.DataFrame([
        {"date": d, "where": w, "code": w, "from_db": True,
         "tot_deaths": float(k * (i + 1) ** 2), "colors": "#000000"}
        for k, d in enumerate(dates, 1) for i, w in enumerate(where)
    ])
    fig = visu_bokeh().bokeh_histo(
        input=frame, which="tot_deaths", title="T (09/10/2026)", pyvoalogo=False,
        logo=str(files("pyvoa") / "data" / "logo-pyvoa.png"), bins=None,
        dateslider=True, maxcountrydisplayed=12, typeofmap=["not dense"])
    callback = next(m for m in fig.references()
                    if isinstance(m, CustomJS) and "frames" in m.args and "source" in m.args)
    frames = callback.args["frames"]
    assert callback.args["dates"] == ["31/08/2026", "09/10/2026"]
    assert callback.args["titleprefix"] == "T "
    for d, got in zip(dates, frames):
        expected = visu_bokeh().value_histo(
            gather_others(frame[frame["date"] == d], "tot_deaths", 12), "tot_deaths", None)
        assert got == expected.to_dict(orient="list")
    # the chart opens on the last date
    assert callback.args["source"].data["top"].tolist() == frames[-1]["top"]
    assert [s.value for s in fig.select({"type": Slider})] == [1]


def test_bokeh_dateslider_map_holds_one_shape_per_location():
    # every location was serialised with its geometry at every date, pink ones
    # included: hundreds of megabytes for spf, and a source the slider callback
    # could not match its frames against
    pytest.importorskip("bokeh")
    import json
    from importlib.resources import files

    import geopandas as gpd
    import pandas as pd
    from bokeh.models import CustomJS, GeoJSONDataSource
    from shapely.geometry import Polygon

    from pyvoa.visu_bokeh import visu_bokeh

    dates = pd.to_datetime(["2026-08-31", "2026-09-30", "2026-10-09"])
    frame = gpd.GeoDataFrame([
        {"date": d, "where": w, "code": w, "from_db": w != "C",
         "tot_deaths": float(k + i),
         "geometry": Polygon([(i, 0), (i + 1, 0), (i + 1, 1), (i, 1)])}
        for k, d in enumerate(dates) for i, w in enumerate("ABC")
    ], crs="EPSG:4326")
    fig = visu_bokeh().bokeh_map(
        input=frame, which="tot_deaths", title="T (09/10/2026)", pyvoalogo=False,
        logo=str(files("pyvoa") / "data" / "logo-pyvoa.png"),
        dateslider=True, maxcountrydisplayed=12, typeofmap=["dense"],
        tile="openstreet")
    shapes = {}
    for source in fig.references():
        if isinstance(source, GeoJSONDataSource):
            for feature in json.loads(source.geojson)["features"]:
                shapes.setdefault(feature["properties"]["where"], []).append(
                    feature["properties"].get("tot_deaths"))
    # one shape each, the pink C included; A and B carry the last date's value
    assert {w: len(v) for w, v in shapes.items()} == {"A": 1, "B": 1, "C": 1}
    assert (shapes["A"], shapes["B"]) == ([2.0], [3.0])
    # the default title follows the slider: what precedes its date
    callback = next(m for m in fig.references()
                    if isinstance(m, CustomJS) and "titleprefix" in m.args)
    assert callback.args["titleprefix"] == "T "
