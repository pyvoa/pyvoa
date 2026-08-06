# -*- coding: utf-8 -*-
"""Unit tests for pyvoa.tools.

Every public function of the module is exercised here. None of these tests
touches the network: the conftest ``no_network`` fixture makes any socket
creation fail.
"""

import datetime
import subprocess
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import shapely.geometry as sg

import pyvoa.tools as tools
from pyvoa.tools import PyvoaError


# --------------------------------------------------------------------------
# verbosity
# --------------------------------------------------------------------------

def test_set_verbose_mode_returns_the_new_value():
    assert tools.set_verbose_mode(2) == 2
    assert tools.get_verbose_mode() == 2


@pytest.mark.parametrize(
    "mode, expect_info, expect_verb",
    [(0, False, False), (1, True, False), (2, True, True)],
)
def test_info_and_verb_honour_the_verbosity(capsys, mode, expect_info, expect_verb):
    tools.set_verbose_mode(mode)
    tools.info("an info message")
    tools.verb("a debug message")
    out = capsys.readouterr().out
    assert ("an info message" in out) is expect_info
    assert ("a debug message" in out) is expect_verb


# --------------------------------------------------------------------------
# kwargs validation
# --------------------------------------------------------------------------

def test_kwargs_keystesting_accepts_known_keys():
    assert tools.kwargs_keystesting({"a": 1}, ["a", "b"], "ctx.") is True


def test_kwargs_keystesting_rejects_unknown_keys():
    with pytest.raises(PyvoaError) as excinfo:
        tools.kwargs_keystesting({"nope": 1}, ["a"], "ctx.")
    assert "nope" in str(excinfo.value)


@pytest.mark.parametrize(
    "given, expected",
    [(["not a dict"], ["a"]), ({"a": 1}, "not a list")],
)
def test_kwargs_keystesting_rejects_wrong_container_types(given, expected):
    with pytest.raises(PyvoaError):
        tools.kwargs_keystesting(given, expected, "ctx.")


def test_kwargs_test_behaves_like_kwargs_keystesting():
    assert tools.kwargs_test({"a": 1}, ["a"], "ctx.") is True
    with pytest.raises(PyvoaError):
        tools.kwargs_test({"b": 1}, ["a"], "ctx.")


def test_kwargs_values_testing_accepts_allowed_values():
    assert tools.kwargs_values_testing("a", ["a", "b"], "ctx") is None
    assert tools.kwargs_values_testing(["a", "b"], ["a", "b"], "ctx") is None
    assert tools.kwargs_values_testing([["a"], ["b"]], ["a", "b"], "ctx") is None


def test_kwargs_values_testing_is_a_noop_without_a_reference_list():
    assert tools.kwargs_values_testing(None, ["a"], "ctx") is None
    assert tools.kwargs_values_testing("a", None, "ctx") is None
    assert tools.kwargs_values_testing("a", "not a container", "ctx") is None


@pytest.mark.parametrize("given", ["z", ["a", "z"], [["a"], ["z"]]])
def test_kwargs_values_testing_rejects_unknown_values(given):
    with pytest.raises(PyvoaError):
        tools.kwargs_values_testing(given, ["a", "b"], "ctx")


def test_kwargs_keyvaluestesting_accepts_matching_pairs():
    assert tools.kwargs_keyvaluestesting({"a": "x"}, {"a": "x"}, None, "ctx.") is True


def test_kwargs_keyvaluestesting_rejects_unknown_key_or_value():
    with pytest.raises(PyvoaError):
        tools.kwargs_keyvaluestesting({"zz": "x"}, {"a": "x"}, None, "ctx.")
    with pytest.raises(PyvoaError):
        tools.kwargs_keyvaluestesting({"a": "zz"}, {"a": "x"}, None, "ctx.")


def test_kwargs_keyvaluestesting_rejects_non_dict_arguments():
    with pytest.raises(PyvoaError):
        tools.kwargs_keyvaluestesting(["a"], {"a": "x"}, None, "ctx.")


def test_kwargs_keyvaluestesting_ignores_hidden_keys():
    given = {"a": "x", "secret": "whatever"}
    expected = {"a": "x", "secret": "something else"}
    assert tools.kwargs_keyvaluestesting(given, expected, ["secret"], "ctx.") is True


# --------------------------------------------------------------------------
# strings
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "given, expected",
    [
        ("France", "FRANCE"),
        ("Côte d'Ivoire", "COTE D'IVOIRE"),
        ("Guinea-Bissau", "GUINEA BISSAU"),
        ("  United   Kingdom  ", "UNITED KINGDOM"),
    ],
)
def test_tostdstring(given, expected):
    assert tools.tostdstring(given) == expected


# --------------------------------------------------------------------------
# dates
# --------------------------------------------------------------------------

def test_check_valid_date_returns_a_date():
    assert tools.check_valid_date("01/05/2020") == datetime.date(2020, 5, 1)


def test_check_valid_date_rejects_non_string():
    with pytest.raises(PyvoaError):
        tools.check_valid_date(20200501)


@pytest.mark.parametrize("given", ["2020-05-01", "1/5/2020", "01/05/20", "01/05"])
def test_check_valid_date_rejects_wrong_format(given):
    with pytest.raises(PyvoaError):
        tools.check_valid_date(given)


@pytest.mark.parametrize("given", ["31/02/2020", "01/13/2020", "32/01/2020"])
def test_check_valid_date_rejects_impossible_dates(given):
    with pytest.raises(PyvoaError):
        tools.check_valid_date(given)


def test_extract_dates_without_argument_spans_everything():
    first, last = tools.extract_dates(None)
    assert first == datetime.date(1, 1, 1)
    assert last == datetime.date.today()


def test_extract_dates_with_a_single_date_returns_it_twice():
    assert tools.extract_dates("01/05/2020") == (
        datetime.date(2020, 5, 1),
        datetime.date(2020, 5, 1),
    )


def test_extract_dates_with_a_range():
    assert tools.extract_dates("01/05/2020:04/05/2020") == (
        datetime.date(2020, 5, 1),
        datetime.date(2020, 5, 4),
    )


def test_extract_dates_with_an_open_range():
    first, last = tools.extract_dates(":04/05/2020")
    assert first == datetime.date(1, 1, 1)
    assert last == datetime.date(2020, 5, 4)

    first, last = tools.extract_dates("01/05/2020:")
    assert first == datetime.date(2020, 5, 1)
    assert last == datetime.date.today()


def test_extract_dates_rejects_reversed_range():
    with pytest.raises(PyvoaError):
        tools.extract_dates("04/05/2020:01/05/2020")


def test_extract_dates_rejects_more_than_two_dates():
    with pytest.raises(PyvoaError):
        tools.extract_dates("01/05/2020:02/05/2020:03/05/2020")


def test_extract_dates_rejects_non_string():
    with pytest.raises(PyvoaError):
        tools.extract_dates(20200501)


def test_week_to_date_rolling_week_returns_the_middle_day():
    assert tools.week_to_date("2020-01-01-2020-01-11") == datetime.date(2020, 1, 6)


def test_week_to_date_single_day_returns_the_middle_of_the_week():
    assert tools.week_to_date("2020-01-01") == datetime.date(2020, 1, 4)


def test_week_to_date_compact_week_number():
    assert tools.week_to_date("202001") == datetime.datetime(2020, 1, 6)


def test_week_to_date_iso_week_number():
    assert tools.week_to_date("2020-S01") == datetime.datetime(2020, 1, 6)


def test_fill_missing_dates_inserts_the_missing_days():
    given = pd.DataFrame(
        {
            "date": [datetime.date(2020, 1, 1), datetime.date(2020, 1, 4)],
            "where": ["a", "a"],
            "v": [1, 2],
        }
    )
    filled = tools.fill_missing_dates(given)
    assert len(filled) == 4
    assert list(filled["where"]) == ["a"] * 4
    assert filled["v"].isna().sum() == 2


def test_fill_missing_dates_handles_several_locations():
    given = pd.DataFrame(
        {
            "date": [datetime.date(2020, 1, 1), datetime.date(2020, 1, 3)],
            "where": ["a", "b"],
            "v": [1, 2],
        }
    )
    filled = tools.fill_missing_dates(given)
    assert len(filled) == 6
    assert set(filled["where"]) == {"a", "b"}


def test_fill_missing_dates_rejects_a_non_dataframe():
    with pytest.raises(PyvoaError):
        tools.fill_missing_dates("not a dataframe")


@pytest.mark.parametrize("kwargs", [{"date_field": "nope"}, {"loc_field": "nope"}])
def test_fill_missing_dates_rejects_unknown_columns(kwargs):
    given = pd.DataFrame(
        {"date": [datetime.date(2020, 1, 1)], "where": ["a"], "v": [1]}
    )
    with pytest.raises(PyvoaError):
        tools.fill_missing_dates(given, **kwargs)


def test_fill_missing_dates_rejects_reversed_boundaries():
    given = pd.DataFrame(
        {"date": [datetime.date(2020, 1, 1)], "where": ["a"], "v": [1]}
    )
    with pytest.raises(PyvoaError):
        tools.fill_missing_dates(
            given, d1=datetime.date(2020, 1, 4), d2=datetime.date(2020, 1, 1)
        )


def test_return_nonan_dates_pandas_drops_trailing_empty_dates():
    given = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
            "v": [1.0, 2.0, np.nan],
        }
    )
    trimmed = tools.return_nonan_dates_pandas(given, "v")
    assert trimmed["date"].max() == pd.Timestamp("2020-01-02")


@pytest.mark.xfail(
    reason="sign error in the leading-edge loop of return_nonan_dates_pandas: it "
           "computes 'watchdate - timedelta(j-1)' where the trailing loop needs "
           "'+', so leading all-NaN dates are never dropped",
    strict=True,
)
def test_return_nonan_dates_pandas_drops_leading_empty_dates():
    given = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
            "v": [np.nan, 1.0, 2.0],
        }
    )
    trimmed = tools.return_nonan_dates_pandas(given, "v")
    assert trimmed["date"].min() == pd.Timestamp("2020-01-02")


# --------------------------------------------------------------------------
# list helpers
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "lst1, lst2, expected",
    [
        (["a"], ["a", "b"], True),
        (["a", "b"], ["a", "b"], True),
        (["a", "z"], ["a", "b"], False),
        ([], ["a"], True),
    ],
)
def test_testsublist(lst1, lst2, expected):
    assert tools.testsublist(lst1, lst2) is expected


def test_flat_list_flattens_one_level_and_keeps_scalars():
    assert tools.flat_list([["a", "b"], "c", ["d"]]) == ["a", "b", "c", "d"]


@pytest.mark.parametrize(
    "given, expected",
    [([1, 2], True), ([[1], [2]], True), ([[1], 2], False), ([], True)],
)
def test_all_or_none_lists(given, expected):
    assert tools.all_or_none_lists(given) is expected


# --------------------------------------------------------------------------
# numeric / geometric helpers
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "a_min, a_max, expected",
    [
        (3, 7, (3.0, 7.0)),
        (0, 0, (-1, 1)),
        (-5, 120, (-10, 120)),
    ],
)
def test_min_max_range(a_min, a_max, expected):
    assert tools.min_max_range(a_min, a_max) == expected


def test_min_max_range_widens_a_degenerate_interval():
    low, high = tools.min_max_range(5, 5)
    assert low < 5 < high


def test_wgs84_to_web_mercator_maps_the_origin_to_the_origin():
    x, y = tools.wgs84_to_web_mercator((0, 0))
    assert x == 0
    assert y == pytest.approx(0, abs=1e-6)


def test_wgs84_to_web_mercator_clamps_the_south_pole():
    """Latitude -90 is infinite in Mercator, the code clamps it to -89.99."""
    _, y_pole = tools.wgs84_to_web_mercator((0, -90))
    _, y_clamp = tools.wgs84_to_web_mercator((0, -89.99))
    assert np.isfinite(y_pole)
    assert y_pole == pytest.approx(y_clamp)


def test_get_polycoords_returns_a_ring_for_a_polygon():
    polygon = sg.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    coords = tools.get_polycoords({"geometry": polygon})
    assert isinstance(coords[0], tuple)
    assert coords[0] == coords[-1]  # closed ring


def test_get_polycoords_returns_one_ring_per_part_for_a_multipolygon():
    multi = sg.MultiPolygon(
        [
            sg.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            sg.Polygon([(2, 2), (3, 2), (3, 3), (2, 3)]),
        ]
    )
    coords = tools.get_polycoords({"geometry": multi})
    assert len(coords) == 2
    assert all(isinstance(ring, list) for ring in coords)


def test_convertmercator_reprojects_and_keeps_the_attributes():
    frame = gpd.GeoDataFrame(
        {"name": ["x", "y"]},
        geometry=[
            sg.Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            sg.MultiPolygon(
                [
                    sg.Polygon([(2, 2), (3, 2), (3, 3), (2, 3)]),
                    sg.Polygon([(4, 4), (5, 4), (5, 5), (4, 5)]),
                ]
            ),
        ],
        crs="epsg:4326",
    )
    converted = tools.convertmercator(frame)
    assert converted.crs == "epsg:3857"
    assert list(converted["name"]) == ["x", "y"]
    assert converted.geometry.iloc[0].bounds[0] == pytest.approx(0)


def test_getnonnegfunc_leaves_a_monotonic_series_untouched():
    given = pd.DataFrame({"where": ["a"] * 4, "v": [0.0, 5.0, 10.0, 20.0]})
    assert list(tools.getnonnegfunc(given, "v")["v"]) == [0.0, 5.0, 10.0, 20.0]


def test_getnonnegfunc_rewrites_a_series_containing_a_drop():
    given = pd.DataFrame({"where": ["a"] * 4, "v": [0.0, 10.0, 5.0, 20.0]})
    rebuilt = tools.getnonnegfunc(given, "v")
    assert len(rebuilt) == 4
    # the trailing value is an anchor and must be preserved
    assert rebuilt["v"].iloc[-1] == 20.0
    assert list(rebuilt["v"]) != [0.0, 10.0, 5.0, 20.0]


def test_getnonnegfunc_handles_several_locations():
    given = pd.DataFrame(
        {"where": ["a", "a", "b", "b"], "v": [0.0, 5.0, 0.0, 7.0]}
    )
    rebuilt = tools.getnonnegfunc(given, "v")
    assert set(rebuilt["where"]) == {"a", "b"}


def test_getnonnegfunc_rejects_a_list_of_variables():
    given = pd.DataFrame({"where": ["a"], "v": [1.0]})
    with pytest.raises(PyvoaError):
        tools.getnonnegfunc(given, ["v", "w"])


# --------------------------------------------------------------------------
# caching : pickles and downloads
# --------------------------------------------------------------------------

def test_dumppkl_then_readpkl_round_trip(cache_dir):
    payload = {"a": [1, 2, 3]}
    tools.dumppkl("sample.pkl", payload)
    assert (cache_dir / "sample.pkl").exists()
    assert tools.readpkl("sample.pkl") == payload


def test_dumppkl_creates_the_cache_directory(tmp_path, monkeypatch):
    target = tmp_path / "does-not-exist-yet"
    monkeypatch.setattr(tools, "pklpath", str(target))
    tools.dumppkl("sample.pkl", [1])
    assert (target / "sample.pkl").exists()


def test_dumppkl_requires_both_arguments(cache_dir):
    with pytest.raises(PyvoaError):
        tools.dumppkl(None, [1])
    with pytest.raises(PyvoaError):
        tools.dumppkl("sample.pkl", None)


def test_readpkl_requires_a_filename(cache_dir):
    with pytest.raises(PyvoaError):
        tools.readpkl(None)


def test_readpkl_reports_a_missing_file(cache_dir):
    with pytest.raises(PyvoaError) as excinfo:
        tools.readpkl("never-written.pkl")
    assert "not found" in str(excinfo.value)


def test_readpkl_reports_a_corrupted_file(cache_dir):
    (cache_dir / "broken.pkl").write_bytes(b"this is not a pickle")
    with pytest.raises(PyvoaError):
        tools.readpkl("broken.pkl")


class _FakeResponse:
    def __init__(self, content):
        self.content = content


def test_get_local_from_url_downloads_and_caches(cache_dir, monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeResponse(b"x" * 2000)

    monkeypatch.setattr(tools.requests, "get", fake_get)

    first = tools.get_local_from_url("https://example.org/data.csv")
    assert len(calls) == 1
    with open(first, "rb") as handle:
        assert handle.read() == b"x" * 2000

    # second call is served from the cache, no further download
    second = tools.get_local_from_url("https://example.org/data.csv")
    assert second == first
    assert len(calls) == 1


def test_get_local_from_url_redownloads_a_too_small_cached_file(cache_dir, monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeResponse(b"y" * 2000)

    monkeypatch.setattr(tools.requests, "get", fake_get)

    # a cached file below the 1000 characters threshold is considered empty
    tools.get_local_from_url("https://example.org/small.csv")
    calls.clear()
    monkeypatch.setattr(
        tools.requests, "get", lambda url, **kwargs: _FakeResponse(b"z" * 2000)
    )
    path = tools.get_local_from_url("https://example.org/small.csv")
    with open(path, "wb") as handle:
        handle.write(b"tiny")

    tools.get_local_from_url("https://example.org/small.csv")
    with open(path, "rb") as handle:
        assert len(handle.read()) == 2000


def test_get_local_from_url_uses_a_distinct_file_per_url(cache_dir, monkeypatch):
    monkeypatch.setattr(
        tools.requests, "get", lambda url, **kwargs: _FakeResponse(b"x" * 2000)
    )
    first = tools.get_local_from_url("https://example.org/a.csv")
    second = tools.get_local_from_url("https://example.org/b.csv")
    assert first != second


def test_get_local_from_url_reports_a_connection_failure(cache_dir, monkeypatch):
    def fake_get(url, **kwargs):
        raise tools.requests.exceptions.RequestException("no route to host")

    monkeypatch.setattr(tools.requests, "get", fake_get)
    with pytest.raises(PyvoaError) as excinfo:
        tools.get_local_from_url("https://example.org/unreachable.csv")
    assert "Cannot access" in str(excinfo.value)


# --------------------------------------------------------------------------
# messages and error display
# --------------------------------------------------------------------------

def test_dotdict_supports_attribute_access():
    d = tools.dotdict({"a": 1})
    assert d.a == 1
    d.b = 2
    assert d["b"] == 2
    del d.b
    assert "b" not in d
    assert d.missing is None


def test_pyvoaerror_is_a_real_exception():
    assert issubclass(PyvoaError, Exception)


def test_pyvoaerror_keeps_its_message():
    error = PyvoaError("something went wrong")
    assert str(error) == "something went wrong"


def test_pyvoaerror_joins_several_arguments():
    error = PyvoaError("bad location:", "France")
    assert str(error) == "bad location: France"


def test_pyvoaerror_displays_a_banner(capsys):
    PyvoaError("visible message")
    out = capsys.readouterr().out
    assert "PYVOA Error" in out
    assert "visible message" in out


def test_pyvoawarning_is_shown_only_when_verbose(capsys):
    tools.set_verbose_mode(0)
    tools.PyvoaWarning("hidden warning")
    assert "hidden warning" not in capsys.readouterr().out

    tools.set_verbose_mode(1)
    tools.PyvoaWarning("shown warning")
    assert "shown warning" in capsys.readouterr().out


def test_pyvoainfo_is_shown_only_in_debug_mode(capsys):
    tools.set_verbose_mode(1)
    tools.PyvoaInfo("hidden info")
    assert "hidden info" not in capsys.readouterr().out

    tools.set_verbose_mode(2)
    tools.PyvoaInfo("shown info")
    assert "shown info" in capsys.readouterr().out


def test_blinking_centered_text_falls_back_to_a_default_width(capsys, monkeypatch):
    def no_terminal(*args, **kwargs):
        raise OSError("not a terminal")

    monkeypatch.setattr(tools.shutil, "get_terminal_size", no_terminal)
    tools.blinking_centered_text("TITLE", "body")
    assert "body" in capsys.readouterr().out


def test_error_display_works_without_a_tty():
    """Regression test for the missing ``shutil`` import.

    Outside a TTY the terminal-size lookup takes its fallback branch. It used
    to raise ``UnboundLocalError: cannot access local variable 'shutil'``,
    hiding the real error. Run in a subprocess with the streams redirected so
    that there is genuinely no controlling terminal.
    """
    script = (
        "import pyvoa.tools as t\n"
        "try:\n"
        "    t.check_valid_date('2020-05-01')\n"
        "except t.PyvoaError as e:\n"
        "    print('CAUGHT', e)\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "UnboundLocalError" not in completed.stderr
    assert "NameError" not in completed.stderr
    assert "CAUGHT" in completed.stdout
    assert "PYVOA Error" in completed.stdout


# --------------------------------------------------------------------------
# remaining public helpers and branches
# --------------------------------------------------------------------------

def test_debug_prints_the_value_and_the_message(capsys):
    tools.debug([1, 2], "a label")
    out = capsys.readouterr().out
    assert "a label" in out
    assert "[1, 2]" in out


def test_debug_works_without_a_message(capsys):
    tools.debug("a value")
    assert "a value" in capsys.readouterr().out


def test_kwargs_keyvaluestesting_accepts_a_list_of_values():
    given = {"a": ["x", "y"]}
    expected = {"a": ["x", "y"], "b": ""}
    assert tools.kwargs_keyvaluestesting(given, expected, None, "ctx.") is True


def test_kwargs_keyvaluestesting_rejects_a_bad_value_inside_a_list():
    given = {"a": ["x", "unknown"]}
    expected = {"a": ["x", "y"], "b": ""}
    with pytest.raises(PyvoaError):
        tools.kwargs_keyvaluestesting(given, expected, None, "ctx.")


class _FakeHead:
    def __init__(self, status_code):
        self.status_code = status_code


def test_exists_from_url_is_true_for_a_reachable_url(monkeypatch):
    monkeypatch.setattr(tools.requests, "head", lambda url: _FakeHead(200))
    assert tools.exists_from_url("https://example.org/data.csv") is True


def test_exists_from_url_is_false_for_a_missing_url(monkeypatch):
    monkeypatch.setattr(tools.requests, "head", lambda url: _FakeHead(404))
    assert tools.exists_from_url("https://example.org/nope.csv") is False


@pytest.mark.parametrize(
    "a_min, a_max",
    [(0, 250), (-250, 0), (-90, -10), (0.002, 0.05)],
)
def test_min_max_range_brackets_the_data(a_min, a_max):
    low, high = tools.min_max_range(a_min, a_max)
    assert low <= a_min
    assert high >= a_max


def test_blinking_centered_text_renders_html_in_a_notebook(monkeypatch):
    """In a notebook the banner is displayed as HTML rather than ANSI."""
    displayed = []

    class _Shell:
        pass

    _Shell.__name__ = "ZMQInteractiveShell"

    monkeypatch.setattr(tools, "get_ipython", lambda: _Shell(), raising=False)

    import IPython.display

    monkeypatch.setattr(
        IPython.display, "display", lambda obj: displayed.append(obj)
    )

    tools.blinking_centered_text(
        "PYVOA Error !", "a notebook message", blinking=True, bg_color="red"
    )

    assert len(displayed) == 1
    html = displayed[0].data
    assert "a notebook message" in html
    assert "animation: blink" in html
    assert "#C0392B" in html  # the red of the colour map


def test_blinking_centered_text_html_has_no_animation_when_not_blinking(monkeypatch):
    displayed = []

    class _Shell:
        pass

    _Shell.__name__ = "ZMQInteractiveShell"

    monkeypatch.setattr(tools, "get_ipython", lambda: _Shell(), raising=False)

    import IPython.display

    monkeypatch.setattr(
        IPython.display, "display", lambda obj: displayed.append(obj)
    )

    tools.blinking_centered_text("PYVOA Info !", "calm message", blinking=False)

    assert "animation: blink" not in displayed[0].data
