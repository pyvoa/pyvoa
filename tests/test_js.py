"""The bokeh callbacks of pyvoa/js/, run in node.

Nothing else in the suite runs them: bokeh reads them as text and BokehJS only
executes them in a browser, so a typo would pass every other job. They run here
as BokehJS runs them, the code of a file being the body of a function whose
parameters are the names the callback is handed, against plain objects standing
for the bokeh models.

The slider callback repeats in javascript what the Python side draws before the
slider moves -- rank_locations, gather_others, addcolumnshisto, addcolumnspie --
and the tests check that the two agree on the same frame.

node comes from the PATH or, failing that, from the nodejs-wheel-binaries
package of the dev extra. Without either, the tests skip, except on CI, where
they fail.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pyvoa.tools import gather_others, rank_locations
from pyvoa.visu_bokeh import visu_bokeh

JS = Path(__file__).resolve().parents[1] / "pyvoa" / "js"


def node_executable() -> str | None:
    """Return a node binary, from the PATH or from nodejs-wheel-binaries."""
    found = shutil.which("node")
    if found:
        return found
    try:
        from nodejs_wheel.executable import ROOT_DIR
    except ImportError:
        return None
    if os.name == "nt":
        return str(Path(ROOT_DIR) / "node.exe")
    return str(Path(ROOT_DIR) / "bin" / "node")


NODE = node_executable()
if NODE is None:
    if os.environ.get("CI"):
        raise RuntimeError("node is needed on CI: install the dev extra")
    pytestmark = pytest.mark.skip(reason="no node: pip install -e '.[dev]'")

# Defines callback(file, names): the code of pyvoa/js/<file> as a function of
# the given names, which is how BokehJS compiles a CustomJS. out() prints what
# the test reads back.
PRELUDE = "const JSDIR = " + json.dumps(str(JS)) + ";" + """
const fs = require("fs");
const path = require("path");
function callback(file, names) {
    return new Function(...names, fs.readFileSync(path.join(JSDIR, file), "utf8"));
}
function out(x) { process.stdout.write(JSON.stringify(x)); }
"""


def run(script: str):
    """Run a script in node after the prelude and return what it printed, as JSON."""
    done = subprocess.run(
        [NODE, "-e", PRELUDE + script], capture_output=True, text=True, timeout=60, check=False,
    )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout) if done.stdout else None


# ---------------------------------------------------------------------------
# Syntax
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", sorted(JS.glob("*.js")), ids=lambda p: p.name)
def test_js_compiles_as_a_callback_body(path: Path):
    # `node --check` would refuse the top-level return the callbacks use: they
    # are function bodies. new Function() compiles one without running it, and
    # the names it is handed are free variables to the compiler.
    run(f"new Function(fs.readFileSync({json.dumps(str(path))}, 'utf8')); out(true);")


# ---------------------------------------------------------------------------
# rollover_callback.js
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value, expected", [
    (0, "0,00"),
    (12.345678, "12,35"),
    (1234.567, "1 234,57"),
    (-0.5, "-0,50"),
    (10000, "10 000,00"),
    (54_900_000, "5.49e+7"),
    (0.00123, "1.23e-3"),
    ("42", "42,00"),
])
def test_rollover_formats_a_value(value, expected):
    got = run(f"out(callback('rollover_callback.js', ['value'])({json.dumps(value)}));")
    assert got == expected


# ---------------------------------------------------------------------------
# animation_callback.js
# ---------------------------------------------------------------------------

def test_play_buttons_keep_a_timer_each():
    # setInterval and clearInterval are handed in, which shadows node's own, so
    # that the test advances the timers itself, one tick at a time.
    got = run("""
    const timers = new Map();
    let next = 1;
    const setInterval = (f) => { timers.set(next, f); return next++; };
    const clearInterval = (id) => { timers.delete(id); };
    const tick = () => { for (const f of [...timers.values()]) f(); };
    const cb = callback("animation_callback.js", ["cb_obj", "slider", "setInterval", "clearInterval"]);
    const make = () => ({toggle: {active: false, label: "► Play"},
                         slider: {start: 0, end: 5, value: 5}});
    const a = make(), b = make();
    const press = (x, on) => { x.toggle.active = on; cb(x.toggle, x.slider, setInterval, clearInterval); };
    const log = {};
    press(a, true); press(b, true);
    log.restart = [a.slider.value, b.slider.value];
    tick(); tick();
    log.both = [a.slider.value, b.slider.value, a.toggle.label, b.toggle.label];
    press(b, false);
    tick();
    log.one_paused = [a.slider.value, b.slider.value, b.toggle.label];
    tick(); tick(); tick();
    log.end = [a.slider.value, a.toggle.active, a.toggle.label, timers.size];
    out(log);
    """)
    assert got["restart"] == [0, 0], "Play on the last date starts from the first"
    assert got["both"] == [2, 2, "❚❚ Pause", "❚❚ Pause"]
    assert got["one_paused"] == [3, 2, "► Play"], "pausing one chart stopped the other"
    assert got["end"] == [5, False, "► Play", 0], "the timer outlived the last date"


# ---------------------------------------------------------------------------
# histo_value_callback.js
# ---------------------------------------------------------------------------

def test_histo_value_swaps_the_bins_and_fits_the_axes():
    got = run("""
    const fig = () => ({x_range: {}, y_range: {}, title: {text: "old"}});
    const a = {figlinear: fig(), figlog: fig(), source: {data: {}}, div: {text: ""}};
    const frames = [
        {left: [0, 1], right: [1, 2], top: [3, 4]},
        {left: [5, 7], right: [7, 9], top: [8, 2]},
    ];
    callback("histo_value_callback.js",
             ["cb_obj", "frames", "source", "dates", "div", "figlinear", "figlog", "titleprefix"])
        ({value: 1}, frames, a.source, ["d0", "d1"], a.div, a.figlinear, a.figlog, "SPF database ");
    out({data: a.source.data, x: [a.figlinear.x_range, a.figlog.x_range],
         y: [a.figlinear.y_range.end, a.figlog.y_range.end],
         title: a.figlog.title.text, div: a.div.text,
         copied: a.source.data !== frames[1]});
    """)
    assert got["data"] == {"left": [5, 7], "right": [7, 9], "top": [8, 2]}
    assert got["copied"], "the frame itself was handed over, not a copy"
    assert got["x"] == [{"start": 5, "end": 9}] * 2
    assert got["y"] == pytest.approx([1.05 * 8, 10 * 8])
    assert got["title"] == "SPF database (d1)"
    assert got["div"] == "<b>d1</b>"


# ---------------------------------------------------------------------------
# slider_callback.js
# ---------------------------------------------------------------------------

SLIDER_NAMES = ["cb_obj", "frames", "sourcemap", "sourcehisto", "which", "dates", "div",
                "maxcountrydisplayed", "ylabellinear", "ylabellog", "ymax",
                "color_mapperjs", "titlefigs", "ispie", "titleprefix"]

# the columns the slider callback computes, which must be the Python ones
DRAWN = ["where", "tot", "colors", "top", "bottom", "left", "right",
         "horihistotextx", "horihistotexty", "horihistotext",
         "percentage", "angle", "textdisplayed", "textdisplayed2"]


def one_date() -> pd.DataFrame:
    """Return the frame of one date: ties, a missing value, every _fmt branch."""
    return pd.DataFrame({
        "where": ["Nord", "Ain", "Paris", "Cher", "Gers", "Aube", "Lot", "Var"],
        "code": ["59", "01", "75", "18", "32", "10", "46", "83"],
        "tot": [54_900_000.0, 5.0, 5.0, 12.3456, 0.005, 0.0, np.nan, 2.0e-5],
        "colors": ["#a", "#b", "#c", "#d", "#e", "#f", "#g", "#h"],
    })


def columns(frame: pd.DataFrame) -> dict:
    """Return a frame column-wise, as decodateslider hands it, a NaN as null."""
    return frame.astype(object).where(frame.notna(), None).to_dict(orient="list")


def slider(frame: pd.DataFrame, maxcountrydisplayed: int, ispie: bool) -> dict:
    """Run the slider callback on one frame of a histogram or a pie chart."""
    consts = (f"const NAMES = {json.dumps(SLIDER_NAMES)};"
              f"const FRAME = {json.dumps(columns(frame))};"
              f"const MAX = {maxcountrydisplayed}; const ISPIE = {json.dumps(ispie)};")
    return run(consts + """
    const axis = () => ({ticker: {}});
    const src = {data: {colors: ["#000"], extra: ["kept", "kept too"]}};
    const a = {div: {text: ""}, ylin: axis(), ylog: axis()};
    callback("slider_callback.js", NAMES)(
        {value: 0}, [FRAME], src, src, "tot", ["01/02/2021"], a.div, MAX,
        a.ylin, a.ylog, 400, {}, [], ISPIE, "");
    out({data: src.data, ticks: a.ylin.ticker.ticks,
         labels: Object.fromEntries(a.ylin.major_label_overrides), div: a.div.text});
    """)


def python_side(frame: pd.DataFrame, maxcountrydisplayed: int, ispie: bool) -> pd.DataFrame:
    """Return what decodateslider draws before the slider moves, on the same frame."""
    if ispie:
        drawn = gather_others(frame, "tot", maxcountrydisplayed)
    else:
        drawn = rank_locations(frame, "tot").head(maxcountrydisplayed)
    v = visu_bokeh()
    drawn = v.addcolumnshisto(drawn, "tot", maxcountrydisplayed)
    return v.addcolumnspie(drawn, "tot")


def same(a, b) -> bool:
    """Compare two cell values, a missing value and NaN being equal."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    return a == b


@pytest.mark.parametrize("ispie", [False, True], ids=["histogram", "pie"])
def test_slider_draws_a_date_as_python_draws_it(ispie):
    frame = one_date().dropna(subset=["tot"])
    js = slider(frame, 4, ispie)["data"]
    py = python_side(frame, 4, ispie)
    for col in DRAWN:
        got, want = js[col], py[col].tolist()
        assert len(got) == len(want), f"{col}: {got} != {want}"
        assert all(same(g, w) for g, w in zip(got, want)), f"{col}: {got} != {want}"
    assert js["extra"] == ["kept"] + ["kept too"] * (len(js["where"]) - 1), (
        "a column nothing recomputes must keep its values, padded to the new length")


def test_slider_ranks_a_missing_value_last():
    # Python's addcolumnspie cannot take a NaN (the total would be NaN), so the
    # parity test drops it; the ranking alone is checked with it here
    js = slider(one_date(), 8, False)["data"]
    assert js["where"] == rank_locations(one_date(), "tot")["where"].tolist()
    assert js["where"][-1] == "Lot"


def test_slider_puts_the_location_names_on_the_ticks():
    got = slider(one_date().dropna(subset=["tot"]), 3, False)
    assert got["ticks"] == [int(t) for t in got["data"]["horihistotexty"]]
    # a JSON object sorts integer keys: read the labels in the order of the ticks.
    # Ain and Paris are tied at 5: Ain, first by name, takes the last slot
    assert [got["labels"][str(t)] for t in got["ticks"]] == ["Nord", "Cher", "Ain"]
    assert got["div"] == "<b>01/02/2021</b>"


def test_slider_maps_each_value_to_its_own_shape():
    got = run(f"const NAMES = {json.dumps(SLIDER_NAMES)};" + """
    const sourcemap = {data: {where: ["A", "B", "C"], geometry: ["g1", "g2", "g3"]},
                       change: {emit() { this.emitted = true; }}};
    const mapper = {};
    const fig = {title: {text: ""}};
    const div = {text: ""};
    callback("slider_callback.js", NAMES)(
        {value: 1}, [{where: ["C"], tot: [1]}, {where: ["C", "A"], tot: [30, 10]}],
        sourcemap, {data: {}}, "tot", ["d0", "d1"], div, 10, null, null, 400,
        mapper, [fig], false, "SPF database ");
    out({data: sourcemap.data, low: mapper.low, high: mapper.high,
         emitted: sourcemap.change.emitted === true, title: fig.title.text, div: div.text});
    """)
    # B is in no frame of this date: left without a value, which JSON writes null
    assert got["data"]["where"] == ["A", "B", "C"]
    assert got["data"]["geometry"] == ["g1", "g2", "g3"]
    assert got["data"]["tot"] == [10, None, 30]
    assert got["data"]["cases"] == [10, None, 30]
    assert (got["low"], got["high"]) == (10, 30)
    assert got["emitted"]
    assert got["title"] == "SPF database (d1)"
    assert got["div"] == "<b>d1</b>"
