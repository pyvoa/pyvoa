const i = cb_obj.value;
const frame = frames[i];
const keys = Object.keys(frame);

// ====================================================
// Build rows
// ====================================================
const rows = [];
for (let j = 0; j < frame[which].length; j++) {
    let r = {};
    for (const k of keys) {
        r[k] = frame[k][j];
    }
    rows.push(r);
}

// ====================================================
// MAP
// ====================================================
for (const k of keys) {
    sourcemap.data[k] = rows.map(r => r[k]);
}
sourcemap.data["cases"] = sourcemap.data[which];
const values = sourcemap.data["cases"].filter(v =>
    Number.isFinite(Number(v))
);
if (values.length > 0) {
    color_mapperjs.low  = Math.min(...values);
    color_mapperjs.high = Math.max(...values);
}
sourcemap.change.emit();

// ====================================================
// HISTOGRAM — tri et slice
// ====================================================
const len = sourcehisto.data[which].length;
const sorted_rows = [...rows].sort(
    (a, b) => (Number(b[which]) || 0) - (Number(a[which]) || 0)
);
const limited = sorted_rows.slice(0, len);

if (limited.length === 0) return;

// 1. Colonnes qui viennent de la frame (where, which, etc.)
const frameColumns = Object.keys(frame);
for (const col of frameColumns) {
    sourcehisto.data[col] = limited.map(r => r[col]);
}
const newTicks = limited.map((r, j) =>
    Math.round(ymax * (maxcountrydisplay - j) / maxcountrydisplay)
);

ticker_linear.ticks = newTicks;
ticker_log.ticks    = newTicks;

// ====================================================
// Labels and derived quantities
// ====================================================
const labelMap = {};
const total = limited
    .map(r => Number(r[which]) || 0)
    .reduce((a, b) => a + b, 0);

for (let j = 0; j < limited.length; j++) {
    const value = Number(limited[j][which]) || 0;
    const w = String(limited[j]["where"] || "");
    const where_val =
        w.length > maxlettersdisplay
            ? w.slice(0, maxlettersdisplay) + "..."
            : w;

    const top_pos =
        ymax * (maxcountrydisplay - j) / maxcountrydisplay +
        0.5 * ymax / maxcountrydisplay;
    const bottom_pos =
        ymax * (maxcountrydisplay - j) / maxcountrydisplay -
        0.5 * ymax / maxcountrydisplay;

    sourcehisto.data["top"][j]            = top_pos;
    sourcehisto.data["bottom"][j]         = bottom_pos;
    sourcehisto.data["horihistotexty"][j] = bottom_pos + 0.5 * ymax / maxcountrydisplay;
    sourcehisto.data["angle"][j]          = total > 0 ? (value / total) * 2 * Math.PI : 0;
    sourcehisto.data["textdisplayed"][j]  = String(w).padStart(36, " ");
    sourcehisto.data["textdisplayed2"][j] = total > 0
        ? (100 * value / total).toFixed(1) + "%"
        : "0.0%";

    const pos = parseInt(ymax * (limited.length - j) / limited.length);
    if (Number.isFinite(pos)) labelMap[String(pos)] = where_val;
}

// ====================================================
// Axis labels
// ====================================================
ylabellinear.major_label_overrides = labelMap;
ylabellog.major_label_overrides    = labelMap;

// ====================================================
// Refresh
// ====================================================
sourcehisto.change.emit();
console.log("sourcehisto.data['where'] après écriture:", sourcehisto.data["where"].slice(0,5));
console.log("sourcehisto.data[which] après écriture:", sourcehisto.data[which].slice(0,5));
div.text = "<b>" + dates[i] + "</b>";
