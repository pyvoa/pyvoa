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

let v = Number(value);

if (Math.abs(v) > 10000 || (Math.abs(v) < 0.01 && v !== 0)) {
    return v.toExponential(2);
} else {
    return v.toLocaleString('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

