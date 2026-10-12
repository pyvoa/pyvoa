/*
Project : PyvoA
Date :    april 2020 - october 2026
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_org
License: See joint LICENSE file
https://pyvoa.org/

Module : js/histo_value_callback.js

About :
-------
The date slider of the histogram by value: each frame holds the bins of one
date, computed in Python as the histogram without the slider computes them.
The callback swaps them in, and fits the axes to them.
*/

const i = cb_obj.value;
const frame = frames[i];
source.data = {...frame};

const tops = frame["top"].map(Number);
const highest = tops.length > 0 ? Math.max(...tops) : 1;
for (const fig of [figlinear, figlog]) {
    fig.x_range.start = frame["left"][0];
    fig.x_range.end   = frame["right"][frame["right"].length - 1];
}
figlinear.y_range.end = 1.05 * highest;
figlog.y_range.end    = 10 * highest;

// the default title, 'EBOLARDC database (09/10/2026)', follows the date drawn
if (titleprefix) {
    for (const fig of [figlinear, figlog]) {
        fig.title.text = titleprefix + "(" + dates[i] + ")";
    }
}
div.text = "<b>" + dates[i] + "</b>";
