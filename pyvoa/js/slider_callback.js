/*
The date slider of the bokeh maps, histograms and pie charts.

On a map, each value of the selected frame goes to the shape of its location
and the colour scale is fitted to them. On a histogram or a pie chart, the
locations are ranked as ``tools.rank_locations`` ranks them, the first
``maxcountrydisplayed`` drawn, the others gathered into one ``SumOthers``
slice of a pie. The title and the date label follow the date drawn.

Parameters
----------
cb_obj : Slider
    the date slider, whose value is the index of the date drawn.
frames : list of dict
    one frame per date, a column name to its list of values, holding every
    location of that date.
sourcemap : ColumnDataSource
    on a map, the source of the shapes, one per location; on a histogram or
    a pie chart, the same object as ``sourcehisto``, which is how the callback
    tells the two apart.
sourcehisto : ColumnDataSource
    the source of the bars or of the slices.
which : str
    the column drawn.
dates : list of str
    the dates, in the order of ``frames``.
div : Div
    the label showing the date drawn, under the slider.
maxcountrydisplayed : int
    the number of locations drawn on a histogram or a pie chart.
ylabellinear, ylabellog : Axis
    the y axes of the linear and the log figures, whose ticks carry the names
    of the locations of a horizontal histogram.
ymax : float
    the height the bars of a horizontal histogram are spread over.
color_mapperjs : ColorMapper
    the colour scale of a map.
titlefigs : list of figure
    the figures whose title follows the date.
ispie : bool
    whether the chart is a pie chart, the only one to gather the others.
titleprefix : str
    the default title less its trailing ``(date)``, or empty when the caller
    gave a title of their own, which is then left as it is.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
*/

const i = cb_obj.value;
const frame = frames[i];
const keys = Object.keys(frame);

// the default title, 'SPF database (31/12/2020)', follows the date drawn
if (titleprefix) {
    for (const f of titlefigs) {
        f.title.text = titleprefix + "(" + dates[i] + ")";
    }
}

// ====================================================
// Build rows
// ====================================================
// the frame is column-wise, as a ColumnDataSource is: turned into one object
// per location, it can be matched to the shapes and ranked
const rows = [];
for (let j = 0; j < frame[which].length; j++) {
    let r = {};
    for (const k of keys) r[k] = frame[k][j];
    rows.push(r);
}

// ====================================================
// MAP
// ====================================================
// a histogram or a pie chart is handed its own source as 'sourcemap' too:
// the map part only applies to a map
if (sourcemap !== sourcehisto) {
    // the source holds one shape per location, in its own order: each value
    // of the frame goes to the shape of its location, not to the row of the
    // same rank, and a location the frame lacks is left without a value
    const where = sourcemap.data["where"];
    const pos = new Map();
    for (let j = 0; j < where.length; j++) pos.set(where[j], j);
    const data = {...sourcemap.data};
    for (const k of keys) {
        if (k === "where") continue;
        const col = new Array(where.length).fill(NaN);
        for (const r of rows) {
            const j = pos.get(r["where"]);
            if (j !== undefined) col[j] = r[k];
        }
        data[k] = col;
    }
    // the colour of the shapes is read from 'cases', not from 'which'
    data["cases"] = data[which];
    sourcemap.data = data;
    // the colour scale spans the values of the date drawn, the missing ones
    // left out
    const values = data["cases"].filter(v => Number.isFinite(Number(v)));
    if (values.length > 0) {
        color_mapperjs.low  = Math.min(...values);
        color_mapperjs.high = Math.max(...values);
    }
    sourcemap.change.emit();
    // the title is set already: the histogram part below is skipped
    div.text = "<b>" + dates[i] + "</b>";
    return;
}

// ====================================================
// HISTOGRAM AND PIE — ranked, capped at maxcountrydisplayed
// ====================================================
// the frame holds every location of the date: only the first
// maxcountrydisplayed of them by value are drawn, so that none is left
// stacked on the slots of the others
// ranked as tools.rank_locations ranks them without the slider: decreasing
// value, a missing one last, ties by location name compared as strings, so
// that the locations kept at equal values are the same ones
const val = r => { const n = Number(r[which]); return Number.isFinite(n) ? n : -Infinity; };
const byname = (a, b) => {
    const x = String(a["where"]), y = String(b["where"]);
    return x < y ? -1 : (x > y ? 1 : 0);
};
const rank = (a, b) => (val(b) - val(a)) || byname(a, b);
const sorted_rows = [...rows].sort(rank);
let limited = sorted_rows.slice(0, maxcountrydisplayed);
const others = sorted_rows.slice(maxcountrydisplayed);
if (ispie && others.length > 0) {
    // the other locations make one slice, as without the slider, so that the
    // shares are those of the whole
    const rest = {...limited[0]};
    rest["where"] = "SumOthers";
    rest["code"] = "SumOthers";
    rest[which] = others.reduce((a, r) => a + (Number.isFinite(Number(r[which])) ? Number(r[which]) : 0), 0);
    rest["colors"] = "#FFFFFF";
    // ranked with the others, as gather_others ranks it in Python
    limited = [...limited, rest].sort(rank);
}
const len = limited.length;
// no location has a value at this date: the chart is left as it is
if (len === 0) return;

// every column gets a new array of the same length: the frame's own columns,
// then the drawing ones computed below, then whatever else the source holds
const data = {};
for (const col of keys) {
    data[col] = limited.map(r => r[col]);
}

// the columns the drawing methods read, computed as addcolumnshisto and
// addcolumnspie compute them in Python: the slot of each bar, from the top
// down, its extent, and the share and angle of each slice
const total = limited
    .map(r => Number(r[which]) || 0)
    .reduce((a, b) => a + b, 0);
const step = ymax / maxcountrydisplayed;
// the text of a bar's value label, as _fmt in addcolumnshisto writes it:
// '0' for zero, three significant figures in Python's '.3g' for a value of
// 10000 or more or below 0.01, str(round(v, 2)) otherwise
const fmt = v => {
    if (v === 0) return "0";
    if (Math.abs(v) >= 1e4 || Math.abs(v) < 0.01) {
        // '.3g' writes 5.49e+07 for a large value but 0.005 for a small one:
        // the exponent form only outside [1e-4, 1e3), trailing zeros dropped
        const [m, e] = v.toExponential(2).split("e");
        const exp = Number(e);
        if (exp < -4 || exp >= 3) {
            const mant = m.replace(/\.?0+$/, "");
            return mant + "e" + (exp < 0 ? "-" : "+") + String(Math.abs(exp)).padStart(2, "0");
        }
        return String(Number(v.toPrecision(3)));
    }
    // str() of a float keeps one decimal at least: 5.0, not 5
    const r = Math.round(v * 100) / 100;
    return Number.isInteger(r) ? r.toFixed(1) : String(r);
};
data["top"] = [];
data["bottom"] = [];
data["horihistotexty"] = [];
data["left"] = [];
data["right"] = [];
data["horihistotextx"] = [];
data["horihistotext"] = [];
data["percentage"] = [];
data["angle"] = [];
data["textdisplayed"] = [];
data["textdisplayed2"] = [];

const labelMap = new Map();
const ytick_loc = [];
for (let j = 0; j < len; j++) {
    const value = Number(limited[j][which]) || 0;
    // 'where' is cut to maxlettersdisplayed already, by decohistomap
    const w = String(limited[j]["where"] || "");

    // the j-th location takes the j-th slot from the top, one step high; the
    // SumOthers slice of a pie, one past the last slot, wraps round to the
    // first, as in addcolumnshisto (a pie draws no bar: only the columns agree)
    const slot       = j % maxcountrydisplayed;
    const top_pos    = ymax * (maxcountrydisplayed - slot) / maxcountrydisplayed + 0.5 * step;
    const bottom_pos = ymax * (maxcountrydisplayed - slot) / maxcountrydisplayed - 0.5 * step;
    const tick_pos   = parseInt(bottom_pos + 0.5 * step);

    data["top"].push(top_pos);
    data["bottom"].push(bottom_pos);
    data["horihistotexty"].push(tick_pos);
    data["left"].push(Math.min(value, 0));
    data["right"].push(Math.max(value, 0));
    data["horihistotextx"].push(Math.max(value, 0));
    data["horihistotext"].push(fmt(value));
    data["percentage"].push(total > 0 ? value / total : 0);
    data["angle"].push(total > 0 ? (value / total) * 2 * Math.PI : 0);
    // the labels of a pie slice: its name, padded on the left as
    // addcolumnspie pads it, and its share
    data["textdisplayed"].push(w.padStart(36, " "));
    data["textdisplayed2"].push("      " + (total > 0 ? (100 * value / total).toFixed(1) : "0.0") + "%");

    // a tick at the middle of each bar, labelled with its location
    ytick_loc.push(tick_pos);
    labelMap.set(tick_pos, w);
}
// a column the source holds and nothing above recomputes keeps its values,
// the last one repeated when there are more rows than before: every column of
// a ColumnDataSource must have the same length
for (const col of Object.keys(sourcehisto.data)) {
    if (!(col in data)) {
        const old = sourcehisto.data[col];
        data[col] = Array.from({length: len}, (_, j) => old[Math.min(j, old.length - 1)]);
    }
}
sourcehisto.data = data;

// ====================================================
// Axis update
// ====================================================
// the y ticks of a horizontal histogram carry the names of the locations: they
// follow the new ranking, on both figures
ylabellinear.ticker.ticks          = ytick_loc;
ylabellog.ticker.ticks             = ytick_loc;
ylabellinear.major_label_overrides = labelMap;
ylabellog.major_label_overrides    = labelMap;

div.text = "<b>" + dates[i] + "</b>";
