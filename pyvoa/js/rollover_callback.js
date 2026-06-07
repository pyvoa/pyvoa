/*
Project : PyvoA
Date :    april 2020 - november 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_org
License: See joint LICENSE file
https://pyvoa.org/

Module : js/rollover_callback.js

About :
-------
*/
// rollover_callback.js
const v = Number(value);
if (!isFinite(v)) return "";

const abs = Math.abs(v);
if (abs !== 0 && (abs > 10_000 || abs < 0.01)) {
    return v.toExponential(2);
}

const [int, dec] = v.toFixed(2).split(".");
return int.replace(/\B(?=(\d{3})+(?!\d))/g, "\u202f") + "." + dec;
