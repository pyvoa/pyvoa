
const i = cb_obj.value;
const frame = frames[i];
const keys = Object.keys(frame);

// ====================================================
// Build rows
// ====================================================
const rows = [];

for (let j = 0; j < frame[which].length; j++) {
    const r = {};
    for (const k of keys) {
        r[k] = frame[k][j];
    }
    rows.push(r);
}

// ====================================================
// MAP
// ====================================================
if (sourcemap !== sourcehisto) {
    const mapData = {};

    for (const k of keys) {
        mapData[k] = rows.map(r => r[k]);
    }

    mapData["cases"] = [...mapData[which]];

    sourcemap.data = mapData;

    const values = mapData["cases"]
        .map(Number)
        .filter(Number.isFinite);

    if (values.length > 0) {
        color_mapperjs.low = Math.min(...values);
        color_mapperjs.high = Math.max(...values);
    }
}

// ====================================================
// HISTOGRAM — sort and limit
// ====================================================
const limited = [...rows]
    .sort((a, b) =>
        (Number(b[which]) || 0) -
        (Number(a[which]) || 0)
    )
    .slice(0, maxcountrydisplayed);

const n = limited.length;
if (n === 0) return;

const histoData = {};

for (const col of keys) {
    histoData[col] = limited.map(r => r[col]);
}

// ====================================================
// Labels and geometry
// ====================================================
const labelMap = new Map();
const ytick_loc = [];

const total = limited.reduce(
    (sum, r) => sum + (Number(r[which]) || 0),
    0
);

const step = ymax / maxcountrydisplayed;

for (let j = 0; j < n; j++) {
    const value = Number(limited[j][which]) || 0;
    const w = String(limited[j]["where"] || "");

    const tick_pos = ymax - j * step;
    const top_pos = tick_pos + 0.5 * step;
    const bottom_pos = tick_pos - 0.5 * step;

    histoData["top"][j] = top_pos;
    histoData["bottom"][j] = bottom_pos;
    histoData["horihistotexty"][j] = tick_pos;

    histoData["angle"][j] =
        total > 0 ? (value / total) * 2 * Math.PI : 0;

    histoData["textdisplayed"][j] =
        w.padStart(36, " ");

    histoData["textdisplayed2"][j] =
        total > 0
            ? (100 * value / total).toFixed(1) + "%"
            : "0.0%";

    ytick_loc.push(tick_pos);
    labelMap.set(tick_pos, w);
}
// ====================================================
// Update histogram
// ====================================================
sourcehisto.data = histoData;

// ====================================================
// Axis update
// ====================================================
ylabellinear.ticker.ticks          = ytick_loc;
ylabellog.ticker.ticks             = ytick_loc;
ylabellinear.major_label_overrides = labelMap;
console.log(labelMap);
