/*
Format a value shown by a bokeh hover tooltip.

A value above 10000 or below 0.01 in absolute terms, zero aside, is written in
scientific notation with two decimals; any other in the French locale, with
two decimals.

Parameters
----------
value : number or str
    the value of the hovered field, handed by bokeh to a CustomJSHover.

Returns
-------
str
    the text the tooltip shows, e.g. ``5.49e+7`` or ``1 234,57``.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
*/

let v = Number(value);

// very large and very small values go to scientific notation: with two
// decimals, the first would run long and the second would read '0,00'.
// Zero itself stays '0,00'
if (Math.abs(v) > 10000 || (Math.abs(v) < 0.01 && v !== 0)) {
    return v.toExponential(2);
} else {
    // the others in the French locale: a comma for the decimal point, a
    // space between the thousands
    return v.toLocaleString('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}
