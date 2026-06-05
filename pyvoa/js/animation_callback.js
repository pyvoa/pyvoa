/*
Project : PyvoA
Date :    april 2020 - november 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_org
License: See joint LICENSE file
https://pyvoa.org/

Module : js/animation_callback.js

About :
-------


*/
if (cb_obj.active) {
	if (!window._bokeh_play_interval) {
		window._bokeh_play_interval = setInterval(function() {
			let v = slider.value + 1;

			if (v > slider.end) {
				// Stopper à la fin
				clearInterval(window._bokeh_play_interval);
				window._bokeh_play_interval = null;
				cb_obj.active = false;
				cb_obj.label = '► Play';
				return;
			}
			slider.value = v; // déclenche slider_callback
		}, 100);
		cb_obj.label = '❚❚ Pause';
	}
} else {
	// pause: clear interval
	if (window._bokeh_play_interval) {
		clearInterval(window._bokeh_play_interval);
		window._bokeh_play_interval = null;
	}
	cb_obj.label = '► Play';
}
