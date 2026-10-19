/*
The date slider of the bokeh histogram by value.

Each frame holds the bins of one date, computed in Python as the histogram
without the slider computes them. The callback swaps them in, and fits the
axes to them.

Parameters
----------
cb_obj : Slider
    the date slider, whose value is the index of the date drawn.
frames : list of dict
    one frame per date, a column name to its list of values: the bins
    ``left`` and ``right``, their height ``top``, and the other columns the
    quads read.
source : ColumnDataSource
    the source the quads of both figures are drawn from.
dates : list of str
    the dates, in the order of ``frames``.
div : Div
    the label showing the date drawn, under the slider.
figlinear, figlog : figure
    the linear and the log-log figures, one per tab.
titleprefix : str
    the default title less its trailing ``(date)``, or empty when the caller
    gave a title of their own, which is then left as it is.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
*/

// a shallow copy: assigning a new object is what makes bokeh redraw
const i = cb_obj.value;
const frame = frames[i];
source.data = {...frame};

// the bins differ from one date to the next: the x axis spans the bins of the
// date drawn, the y axis its tallest bin, with the same margins as in Python
// (5% above in linear, a decade above in log)
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
