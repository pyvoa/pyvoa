"""
Project : PyvoA
Date :    april 2020 - march 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_fr
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.visu_folium

About :
-------

An interface module to easily plot pycoa_data with bokeh

"""
import folium
import branca.colormap
from branca.colormap import LinearColormap
from branca.element import (
    Element,
    Figure
)
import json
import numpy as np

class visu_folium:
    def __init__(self,):
        self.folium_width = 800
        self.folium_height = 400
        pass

    def folium_map(self, **kwargs):
        title=kwargs.get('title')
        input = kwargs.get('input')
        input=input.drop(columns=['date'])
        what = kwargs.get('what')
        #tile = AllVisu.convert_tile(kwargs.get('tile',self.dicovisuargs['tile']), 'folium')
        plabel = kwargs.get('label')
        #mapa = folium.Map(tiles=tile, attr='<a href=\"http://pyvoa.org\"> ©pyvoa </a>' + msg)
        mapa = folium.Map(attr='<a href=\"http://pyvoa.org\"> ©pyvoa </a>')
        fig = Figure(width=self.folium_width, height=self.folium_height)
        fig.add_child(mapa)
        min_col, max_col = min(input[what]),max(input[what])

        colormap = LinearColormap(
            ['#440154', '#31688e', '#35b779', '#fdee60'],
            vmin=min_col,
            vmax=max_col
        )
        colormap.caption =  title
        colormap.add_to(mapa)
        map_id = colormap.get_name()

        custom_label_colorbar_js = """
        var div = document.getElementById('legend');
        var ticks = document.getElementsByClassName('tick')
        for(var i = 0; i < ticks.length; i++){
        var values = ticks[i].textContent.replace(',','')
        val = parseFloat(values).toExponential(1).toString().replace("+", "")
        if(parseFloat(ticks[i].textContent) == 0) val = 0.
        div.innerHTML = div.innerHTML.replace(ticks[i].textContent,val);
        }
        """
        e = Element(custom_label_colorbar_js)
        html = colormap.get_root()
        html.script.get_root().render()
        html.script._children[e.get_name()] = e
        input[what + 'scientific_format'] = \
            (['{:.5g}'.format(i) for i in input[what]])
        # (['{:.3g}'.format(i) if i>100000 else i for i in geopdwd_filter[input_field]])

        map_dict = input.set_index('where')[what].to_dict()
        #if np.nanmin(geopdwd_filtered[input_field]) == np.nanmax(geopdwd_filtered[input_field]):
        #    map_dict['FakeCountry'] = 0.

        def get_color(feature):
            value = map_dict.get(feature['properties']['where'])
            if value is None or np.isnan(value):
                return '#8c8c8c'  # MISSING -> gray
            else:
                return colormap(value)

        #displayed = 'rolloverdisplay'
        json_data = json.dumps(json.loads(input.to_json()))

        folium.GeoJson(
            input,
            style_function=lambda x:
            {
                'fillColor': get_color(x),
                'fillOpacity': 0.8,
                'color': None
            },
            highlight_function=lambda x: {'weight': 2, 'color': 'green'},
            tooltip=folium.features.GeoJsonTooltip(fields=['where', what + 'scientific_format'],
                                                   aliases=['where' + ':', what + ":"],
                                                   style="""
                        background-color: #F0EFEF;
                        border: 2px solid black;
                        border-radius: 3px;
                        box-shadow: 3px;
                        opacity: 0.2;
                        """),
        ).add_to(mapa)


        return mapa
