/*
The Play / Pause button of the bokeh date slider.

Toggled on, it advances the slider by one date every 100 ms, restarting from
the first date when it stands on the last, and turns itself off at the end;
toggled off, it stops there. Each step moves the slider, which fires the
slider's own callback.

Parameters
----------
cb_obj : Toggle
    the button itself, handed by bokeh to the callback it fires.
slider : Slider
    the date slider the button drives.

Notes
-----
The timer is kept on the button itself, as ``cb_obj._pyvoa_play``: a second
click must find the one the first click started, and a CustomJS callback
keeps no state of its own between two calls. On ``window`` it would be shared
by every Play button of the page, so that with two charts in one notebook,
pausing one would stop the other.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
*/

if (cb_obj.active) {
	// toggled on: start a timer, unless one is running already
	if (!cb_obj._pyvoa_play) {
		// started on the last date, where the slider opens: play from the first
		if (slider.value >= slider.end) {
			slider.value = slider.start;
		}
		cb_obj._pyvoa_play = setInterval(function() {
			let v = slider.value + 1;

			if (v > slider.end) {
				// past the last date: stop, and set the button back to Play
				clearInterval(cb_obj._pyvoa_play);
				cb_obj._pyvoa_play = null;
				cb_obj.active = false;
				cb_obj.label = '► Play';
				return;
			}
			// moving the slider fires its own callback, which redraws the chart
			slider.value = v;
		}, 100);
		cb_obj.label = '❚❚ Pause';
	}
} else {
	// toggled off: stop the timer, the slider stays on the date reached
	if (cb_obj._pyvoa_play) {
		clearInterval(cb_obj._pyvoa_play);
		cb_obj._pyvoa_play = null;
	}
	cb_obj.label = '► Play';
}
