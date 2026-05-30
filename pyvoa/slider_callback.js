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
    color_mapperjs.low = Math.min(...values);
    color_mapperjs.high = Math.max(...values);
}

sourcemap.change.emit();

// ====================================================
// HISTOGRAM
// ====================================================

const len = sourcehisto.data[which].length;

const sorted_rows = [...rows].sort(
    (a, b) => (Number(b[which]) || 0) - (Number(a[which]) || 0)
);

const limited = sorted_rows.slice(0, len);

const allColumns = Object.keys(sourcehisto.data);

for (const col of allColumns) {

    if (!(col in limited[0])) {
        continue;
    }

    sourcehisto.data[col] = limited.map(r => r[col]);
}

// ====================================================
// Labels and derived quantities
// ====================================================

const labelMap = {};

const total = sourcehisto.data[which]
    .map(v => Number(v) || 0)
    .reduce((a, b) => a + b, 0);

for (let j = 0; j < len; j++) {

    const value = Number(sourcehisto.data[which][j]) || 0;

    const w = String(sourcehisto.data["where"][j] || "");

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

    sourcehisto.data["top_pos"][j] = top_pos;
    sourcehisto.data["bottom_pos"][j] = bottom_pos;

    sourcehisto.data["horihistotexty"][j] =
        bottom_pos + 0.5 * ymax / maxcountrydisplay;

    const pos = parseInt(ymax * (len - j) / len);

    if (Number.isFinite(pos)) {
        labelMap[pos] = where_val;
    }

    sourcehisto.data["angle"][j] =
        total > 0 ? (value / total) * 2 * Math.PI : 0;

    sourcehisto.data["textdisplayed"][j] =
        String(w).padStart(36, " ");

    const percent =
        total > 0 ? 100 * value / total : 0;

    sourcehisto.data["textdisplayed2"][j] =
        percent.toFixed(1) + "%";
}

// ====================================================
// Axis labels
// ====================================================

ylabellinear.major_label_overrides = labelMap;
ylabellog.major_label_overrides = labelMap;

// ====================================================
// Refresh
// ====================================================

sourcehisto.change.emit();

div.text = "<b>" + dates[i] + "</b>";
