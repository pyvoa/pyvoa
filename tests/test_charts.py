"""Draw every chart for real, offline, and write it to a file.

The other tests check what pyvoa computes. These check that matplotlib,
bokeh, contextily and pandas still take what pyvoa hands them: a release of
one of them that renames a keyword or tightens a type breaks a chart only
when it is drawn, as contextily before 1.7 did with ``headers=`` (aab95a0),
or as a Categorical refusing the white of 'SumOthers' did with every bokeh
time series (aaf0a9b). The ``test`` job runs them at the newest releases,
the ``minimum`` job at the declared floors. Only the map tiles, which are
downloads, are stubbed out.
"""

import json

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Polygon

import pyvoa.front as pf

WHERE = ["Ain", "Aisne", "Allier"]


@pytest.fixture
def frame(cache_dir):
    """Return eighteen months of two daily series for three locations."""
    days = pd.date_range("2020-01-01", "2021-06-30")
    rng = np.random.default_rng(0)
    yield pd.DataFrame({
        "date": days.repeat(len(WHERE)),
        "where": WHERE * len(days),
        "cur_rea": rng.uniform(0, 100, len(days) * len(WHERE)),
        "cur_hosp": rng.uniform(0, 500, len(days) * len(WHERE)),
    })
    plt.close("all")


def _saved(tmp_path, vis):
    """Write the last chart through front.savefig() and return the file."""
    name = tmp_path / "chart.png"
    pf.savefig(str(name))
    # bokeh writes an html page, and appends the extension itself
    saved = tmp_path / "chart.png.html" if vis == "bokeh" else name
    assert saved.stat().st_size > 0
    return saved


# --------------------------------------------------------------------------
# time series and histograms, through front
# --------------------------------------------------------------------------

PLOTS = [
    ("matplotlib", {"which": "cur_rea"}),
    ("matplotlib", {"which": ["cur_rea", "cur_hosp"], "typeofplot": "versus"}),
    ("matplotlib", {"which": "cur_rea", "typeofplot": "yearly", "single": True}),
    ("bokeh", {"which": "cur_rea"}),
    ("bokeh", {"which": ["cur_rea", "cur_hosp"], "typeofplot": "versus"}),
    ("bokeh", {"which": "cur_rea", "typeofplot": "yearly", "single": True}),
    ("bokeh", {"which": "cur_rea", "typeofplot": "spiral", "single": True}),
    # its menu picks one location among those of the frame
    ("bokeh", {"which": "cur_rea", "typeofplot": "compare"}),
]


@pytest.mark.parametrize(("vis", "kwargs"), PLOTS)
def test_plot_is_drawn_and_saved(frame, tmp_path, vis, kwargs):
    kwargs = dict(kwargs)
    if kwargs.pop("single", False):
        # yearly and spiral plots draw one location only
        frame = frame[frame["where"] == WHERE[0]]
    pf.setvis(vis)
    # from get(), as a user would: 'where' then comes out as a Categorical
    pf.plot(input=pf.get(input=frame, which=kwargs["which"]), **kwargs)
    _saved(tmp_path, vis)


@pytest.mark.parametrize("vis", ["matplotlib", "bokeh"])
@pytest.mark.parametrize("typeofhist", ["location", "value", "pie"])
def test_hist_is_drawn_and_saved(frame, tmp_path, vis, typeofhist):
    pf.setvis(vis)
    pf.hist(input=pf.get(input=frame, which="cur_rea"), which="cur_rea",
            typeofhist=typeofhist)
    _saved(tmp_path, vis)


def test_bokeh_hist_with_its_date_slider_is_saved(frame, tmp_path):
    pf.setvis("bokeh")
    pf.hist(input=pf.get(input=frame, which="cur_rea"), which="cur_rea",
            dateslider=True)
    _saved(tmp_path, "bokeh")


# --------------------------------------------------------------------------
# maps
# --------------------------------------------------------------------------

def _map_frame(dates):
    """Return a GeoDataFrame of three squares in France, one row per date."""
    return gpd.GeoDataFrame([
        {"date": d, "where": w, "code": w, "from_db": True,
         "cur_rea": float(10 * k + i + 1),
         "geometry": Polygon([(2 + i, 45), (3 + i, 45), (3 + i, 46), (2 + i, 46)])}
        for k, d in enumerate(dates) for i, w in enumerate(WHERE)
    ], crs="EPSG:4326")


@pytest.fixture
def no_tile_download(monkeypatch):
    """Hand contextily a blank tile instead of downloading one."""
    import contextily.plotting

    def blank(left, bottom, right, top, **kwargs):
        return np.zeros((4, 4, 3), dtype=np.uint8), (left, right, bottom, top)

    monkeypatch.setattr(contextily.plotting, "bounds2img", blank)
    monkeypatch.setattr(contextily.plotting, "warp_tiles",
                        lambda image, extent, **kwargs: (image, extent))


@pytest.mark.parametrize("projection", ["eckert4", "mercator"])
@pytest.mark.parametrize(("typeofmap", "tile"), [
    (["not dense"], "openstreet"),
    (["not dense"], "esri"),
    (["dense"], None),
    (["dense", "show_values"], None),
])
def test_matplotlib_map_is_drawn_and_saved(no_tile_download, tmp_path,
                                           typeofmap, tile, projection):
    from pyvoa.visu_matplotlib import visu_matplotlib

    ax = visu_matplotlib().matplotlib_map(
        input=_map_frame(["2021-03-01"]), which="cur_rea", title="",
        tile=tile, typeofmap=typeofmap, projection=projection,
        return_pltaxis=True, pyvoalogo=False)
    # a tile, when asked for, is drawn under the shapes
    assert len(ax.images) == (1 if tile else 0)
    name = tmp_path / "map.png"
    ax.figure.savefig(name, bbox_inches="tight")
    assert name.stat().st_size > 0
    plt.close("all")


@pytest.mark.parametrize("dateslider", [False, True])
@pytest.mark.parametrize(("typeofmap", "tile"), [
    (["not dense"], "openstreet"),
    (["not dense"], "esri"),
    (["dense"], "openstreet"),
    (["dense", "show_values"], "openstreet"),
])
def test_bokeh_map_is_drawn_and_saved(tmp_path, typeofmap, tile, dateslider):
    from importlib.resources import files

    from bokeh.embed import file_html
    from bokeh.resources import CDN

    from pyvoa.visu_bokeh import visu_bokeh

    fig = visu_bokeh().bokeh_map(
        input=_map_frame(pd.to_datetime(["2021-03-01", "2021-03-02"])),
        which="cur_rea", title="", pyvoalogo=False,
        logo=str(files("pyvoa") / "data" / "logo-pyvoa.png"),
        dateslider=dateslider, maxcountrydisplayed=12, typeofmap=typeofmap,
        tile=tile)
    # serialising validates every model and property against this bokeh,
    # which building the figure in python does not
    page = file_html(fig, CDN)
    name = tmp_path / "map.html"
    name.write_text(page, encoding="utf-8")
    # the page carries the document, its three shapes included
    assert json.dumps("Allier")[1:-1] in page


@pytest.mark.parametrize("vis", ["matplotlib", "bokeh"])
def test_map_of_an_in_house_frame_needs_no_database(no_tile_download, cache_dir,
                                                    monkeypatch, tmp_path, vis):
    """Draw a GeoDataFrame of one's own, as the docstring of map() offers.

    With no database loaded, map() read the geography of the database, None,
    and failed with an AttributeError.
    """
    monkeypatch.setattr(pf.__pyvoafront_instance__, "gpdbuilder", None)
    pf.setvis(vis)
    frame = _map_frame(pd.to_datetime(["2021-03-01", "2021-03-02"]))
    pf.map(input=frame.drop(columns="code"), which="cur_rea")
    _saved(tmp_path, vis)


def test_savefig_leaves_the_next_bokeh_chart_out_of_its_file(frame, tmp_path):
    """Write the file savefig() names, and that one only.

    It went through output_file(), which names the file of every chart
    shown afterwards in the session: the next one was written over it.
    """
    from bokeh.io.state import curstate

    pf.setvis("bokeh")
    pf.plot(input=pf.get(input=frame, which="cur_rea"), which="cur_rea")
    before = curstate().file
    saved = _saved(tmp_path, "bokeh")
    assert curstate().file == before
    assert "cur_rea" in saved.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# histograms of values that do not spread
# --------------------------------------------------------------------------

def _last_date_frame(values):
    """Return two dates of 'cur_rea', the last one holding the given values."""
    where = WHERE[:len(values)]
    return pd.DataFrame({
        "date": pd.to_datetime(["2021-03-01"] * len(where) + ["2021-03-02"] * len(where)),
        "where": where * 2,
        "cur_rea": [1.0] * len(where) + list(values),
    })


@pytest.mark.parametrize("vis", ["matplotlib", "bokeh"])
@pytest.mark.parametrize("values", [[35.0], [7.0, 7.0, 7.0], [0.0, 0.0, 0.0], [-155.0]],
                         ids=["one location", "all equal", "all zero", "negative"])
def test_hist_by_value_draws_values_that_are_all_equal(cache_dir, tmp_path, vis, values):
    # matplotlib's bins then had edges that all coincided, which pd.cut refused
    pf.setvis(vis)
    pf.hist(input=_last_date_frame(values), which="cur_rea", typeofhist="value")
    _saved(tmp_path, vis)
    plt.close("all")


@pytest.mark.parametrize("vis", ["matplotlib", "bokeh"])
@pytest.mark.parametrize(("values", "message"), [
    ([0.0, 0.0, 0.0], "zero or missing"),
    ([10.0, -5.0, 3.0], "cannot show negative values"),
])
def test_pie_refuses_what_it_cannot_share(cache_dir, vis, values, message):
    # matplotlib failed on both, and bokeh drew a wrong pie, or none
    pf.setvis(vis)
    with pytest.raises(pf.PyvoaError, match=message):
        pf.hist(input=_last_date_frame(values), which="cur_rea", typeofhist="pie")
    plt.close("all")
