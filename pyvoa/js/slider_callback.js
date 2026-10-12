/*
Project : PyvoA
Date :    april 2020 - november 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_org
License: See joint LICENSE file
https://pyvoa.org/

Module : js/slider_callback.js

About :
-------


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
    data["cases"] = data[which];
    sourcemap.data = data;
    const values = data["cases"].filter(v => Number.isFinite(Number(v)));
    if (values.length > 0) {
        color_mapperjs.low  = Math.min(...values);
        color_mapperjs.high = Math.max(...values);
    }
    sourcemap.change.emit();
    div.text = "<b>" + dates[i] + "</b>";
    return;
}

// ====================================================
// HISTOGRAM AND PIE — ranked, capped at maxcountrydisplayed
// ====================================================
// the frame holds every location of the date: only the first
// maxcountrydisplayed of them by value are drawn, so that none is left
// stacked on the slots of the others
const sorted_rows = [...rows].sort(
    (a, b) => (Number(b[which]) || 0) - (Number(a[which]) || 0)
);
const len = Math.min(maxcountrydisplayed, sorted_rows.length);
const limited = sorted_rows.slice(0, len);
if (len === 0) return;

// every column gets a new array of the same length: the frame's own columns,
// then the drawing ones computed below, then whatever else the source holds
const data = {};
for (const col of keys) {
    data[col] = limited.map(r => r[col]);
}

const total = limited
    .map(r => Number(r[which]) || 0)
    .reduce((a, b) => a + b, 0);
const step = ymax / maxcountrydisplayed;
data["top"] = [];
data["bottom"] = [];
data["horihistotexty"] = [];
data["left"] = [];
data["right"] = [];
data["horihistotextx"] = [];
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

    const top_pos    = ymax * (maxcountrydisplayed - j) / maxcountrydisplayed + 0.5 * step;
    const bottom_pos = ymax * (maxcountrydisplayed - j) / maxcountrydisplayed - 0.5 * step;
    const tick_pos   = parseInt(bottom_pos + 0.5 * step);

    data["top"].push(top_pos);
    data["bottom"].push(bottom_pos);
    data["horihistotexty"].push(tick_pos);
    data["left"].push(Math.min(value, 0));
    data["right"].push(Math.max(value, 0));
    data["horihistotextx"].push(Math.max(value, 0));
    data["percentage"].push(total > 0 ? value / total : 0);
    data["angle"].push(total > 0 ? (value / total) * 2 * Math.PI : 0);
    data["textdisplayed"].push(w.padStart(36, " "));   // this is for pie
    data["textdisplayed2"].push(total > 0 ? (100 * value / total).toFixed(1) + "%" : "0.0%");

    ytick_loc.push(tick_pos);
    labelMap.set(tick_pos, w);
}
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
ylabellinear.ticker.ticks          = ytick_loc;
ylabellog.ticker.ticks             = ytick_loc;
ylabellinear.major_label_overrides = labelMap;
ylabellog.major_label_overrides    = labelMap;

div.text = "<b>" + dates[i] + "</b>";
