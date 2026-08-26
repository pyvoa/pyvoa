"""The folium visualisation backend.

Interactive leaflet maps. Only maps are implemented here, folium having no
time-series or histogram equivalent, so ``AllVisu`` falls back to another
backend for plots and histograms. Reached through
``map(typeofmap='folium')``.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
"""
import json

import folium
import numpy as np
from branca.colormap import LinearColormap
from branca.element import Element, Figure


class visu_folium:
    """The folium backend, drawing interactive leaflet maps.

    Only maps are implemented here: folium has no time-series or histogram
    equivalent, which is why AllVisu falls back to another backend for
    plot() and hist(). Selected through map(typeofmap='folium').
    """

    def __init__(self,):
        """Set the size, in pixels, of the figure the maps are drawn in."""
        self.folium_width = 800
        self.folium_height = 400

    def folium_map(self, **kwargs):
        """Draw a choropleth map of one variable with folium.

        Colours each location by its value using a four-stop viridis-like scale
        between the smallest and the largest value present, greys out the ones
        with no value, and attaches a tooltip giving the location and its value
        in scientific notation. The colour bar is relabelled through a snippet
        of javascript so that its ticks are shown in scientific notation too.

        Parameters
        ----------
        **kwargs
            the drawing arguments prepared by AllVisu.
            - input (gpd.GeoDataFrame): the data to draw, carrying a 'where'
            column, a geometry and the column named by 'what'.
            - what (str): the column to colour by.
            - title (str): the caption of the colour bar.

        Returns
        -------
        folium.Map
            the map, ready to be displayed in a notebook.
        """
        title=kwargs.get('title')
        input = kwargs.get('input')
        input=input.drop(columns=['date'])
        what = kwargs.get('what')
        #tile = AllVisu.convert_tile(kwargs.get('tile',self.dicovisuargs['tile']), 'folium')
        # plabel = kwargs.get('label')
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
        colormap.get_name()

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
            ([f'{i:.5g}' for i in input[what]])
        # (['{:.3g}'.format(i) if i>100000 else i for i in geopdwd_filter[input_field]])

        map_dict = input.set_index('where')[what].to_dict()
        #if np.nanmin(geopdwd_filtered[input_field]) == np.nanmax(geopdwd_filtered[input_field]):
        #    map_dict['FakeCountry'] = 0.

        def get_color(feature):
            """Return the fill colour of one geojson feature.

            Grey (#8c8c8c) when the location has no value, its place on the
            colour map otherwise.
            """
            value = map_dict.get(feature['properties']['where'])
            if value is None or np.isnan(value):
                return '#8c8c8c'  # MISSING -> gray
            else:
                return colormap(value)

        #displayed = 'rolloverdisplay'
        json.dumps(json.loads(input.to_json()))

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
