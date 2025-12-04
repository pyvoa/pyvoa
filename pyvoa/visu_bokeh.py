# -*- coding: utf-8 -*-

"""
Project : PyvoA
Date :    april 2020 - november 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_org
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.visu_bokeh

About :
-------


"""
from pyvoa.tools import (
    extract_dates,
    verb,
    fill_missing_dates
)
from pyvoa.error import *
import math
import pandas as pd
import geopandas as gpd
import numpy as np

from collections import defaultdict
import itertools
import json
import io
from io import BytesIO
import base64
import copy
import inspect
import importlib

import shapely.geometry as sg

import datetime as dt
import bisect
from functools import wraps
import datetime as dt
from pyvoa.jsondb_parser import MetaInfo
from bokeh.models import (
ColumnDataSource,
TableColumn,
DataTable,
ColorBar,
LogTicker,
HoverTool,
CrosshairTool,
BasicTicker,
GeoJSONDataSource,
LinearColorMapper,
LogColorMapper,
Label,
PrintfTickFormatter,
BasicTickFormatter,
NumeralTickFormatter,
Slider,
CustomJS,
CustomJSHover,
Select,
Range1d,
DatetimeTickFormatter,
Legend,
LegendItem,
Text,
Div,
Row
)
from bokeh.models import (
    Toggle
)
from bokeh.models.layouts import TabPanel, Tabs
from bokeh.models import Panel
from bokeh.plotting import figure
from bokeh.io import output_notebook
from pyvoa.kwarg_options import InputOption

def safe_output_notebook():
    try:
        from IPython import get_ipython
        ipy = get_ipython()
        if ipy is not None and 'IPKernelApp' in ipy.config:
            output_notebook()
    except Exception:
        pass
safe_output_notebook()

#output_notebook(hide_banner=True)
from bokeh.layouts import (
row,
column,
gridplot
)
from bokeh.palettes import (
Category10,
Category20,
Viridis256
)
from bokeh.models import Title

from bokeh.io import export_png
from bokeh import events
from bokeh.models.widgets import DateSlider
from bokeh.models import (
LabelSet,
WMTSTileSource
)
from bokeh.transform import (
transform,
cumsum
)

class visu_bokeh:
    def __init__(self,):
        self.av = InputOption()
        self.lcolors = Category20[20]
        self.scolors = Category10[5]
        self.figure_height = 400
        self.figure_width = 490
        self.listfigs = None

    @staticmethod
    def min_max_range(a_min, a_max):
        """ Return a cleverly rounded min and max giving raw min and raw max of data.
        Usefull for hist range and colormap
        """
        min_p = 0
        max_p = 0
        if a_min != 0:
            min_p = math.floor(math.log10(math.fabs(a_min)))  # power
        if a_max != 0:
            max_p = math.floor(math.log10(math.fabs(a_max)))

        if a_min == 0:
            if a_max == 0:
                p = 0
            else:
                p = max_p
        else:
            if a_max == 0:
                p = min_p
            else:
                p = max(min_p, max_p)

        if a_min != 0:
            min_r = math.floor(a_min / 10 ** (p - 1)) * 10 ** (p - 1)  # min range rounded
        else:
            min_r = 0

        if a_max != 0:
            max_r = math.ceil(a_max / 10 ** (p - 1)) * 10 ** (p - 1)
        else:
            max_r = 0

        if min_r == max_r:
            if min_r == 0:
                min_r = -1
                max_r = 1
                k = 0
            elif max_r > 0:
                k = 0.1
            else:
                k = -0.1
            max_r = (1 + k) * max_r
            min_r = (1 - k) * min_r

        return (min_r, max_r)

    @staticmethod
    def rollerJS():
        from bokeh.models import CustomJSHover
        return CustomJSHover(code="""
                var value;
                 //   if(Math.abs(value)>100000 || Math.abs(value)<0.001)
                 //       return value.toExponential(2);
                 //   else
                 //       return value.toFixed(2);
                 if(value>10000 || value <0.01)
                    value =  Number.parseFloat(value).toExponential(2);
                 else
                     value = Number.parseFloat(value).toFixed(2);
                return value.toString();
                /*  var s = value;
                  var s0=s;
                  var sp1=s.split(".");
                  var p1=sp1[0].length
                  if (sp1.length>1) {
                    var sp2=s.split("e");
                    var p2=sp2[0].length
                    var p3=p2
                    while(s[p2-1]=="0" && p2>p1) {
                        p2=p2-1;
                    }
                    s=s0.substring(0,p2)+s0.substring(p3,s0.length);
                  }
                  if (s.split(".")[0].length==s.length-1) {
                    s=s.substring(0,s.length-1);
                  }
                  return s;*/
                """)

    @staticmethod
    def pyvoalogo(logo):
        with open(logo, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        url = f"data:image/png;base64,{b64}"
        return url

    def deco_bokeh(func):
        @wraps(func)
        def innerdeco_bokeh(self,**kwargs):
            input = kwargs.get('input')
            unique_where = input['where'].unique()
            color_map = {w: self.lcolors[i % 20] for i, w in enumerate(unique_where)}
            input['colors'] = input['where'].map(color_map)
            kwargs['input'] = input
            logo = kwargs['logo']
            which = kwargs['which']
            title = kwargs['title']
            width  = kwargs.get('width', self.figure_width)
            height = kwargs.get('height',self.figure_height)
            input = kwargs['input']

            dicfig = {}
            dicfig['bokeh_figure_linear']      = figure(x_axis_type='linear', y_axis_type='linear', width=width, height=height)
            dicfig['bokeh_figure_log']         = figure(x_axis_type='log', y_axis_type='linear', width=width, height=height)
            dicfig['bokeh_figure_loglog']      = figure(x_axis_type='log', y_axis_type='log', width=width, height=height)
            dicfig['bokeh_figure_map']         = figure(x_axis_type='mercator', y_axis_type='mercator',width=width, height=height, match_aspect=False)
            dicfig['bokeh_figure_linear_date'] = figure(x_axis_type='datetime', y_axis_type='linear', width=width, height=height)
            dicfig['bokeh_figure_log_date']    = figure(x_axis_type='datetime', y_axis_type='log', width=width, height=height)
            dicfig['bokeh_figure_yearly']      = figure(x_axis_type='linear', y_axis_type='linear',  width=width, height=height)

            logo_url = visu_bokeh.pyvoalogo(logo)
            for key, fig in dicfig.items():
                fig.title = title
                #if (key == "bokeh_figure_map" or func.__name__ == 'bokeh_horizonhisto' or func.__name__ == 'bokeh_pie') and kwargs['dateslider']:
                #    fig.title = title
                #else:
                #    fig.title = title + str(kwargs['kwargsuser']['when'])
                dicfig[key]=fig
            d = Div(text = '<div style="position: absolute; left:-400px; top:100px"><img src=' + logo_url + ' style="width:280px; height:110px; opacity: 0.1"></div>')
            #d = Div(text = '<div style="position: absolute; left:-400px; top:100px"> <p style="background-image: url("+img_girl.jpg+");"> </div>')
            kwargs['watermark'] = d
            kwargs = { **kwargs, **dicfig }
            return func(self, **kwargs)
        return innerdeco_bokeh

    def decodateslider(func):
        @wraps(func)
        def inner_decodateslider(self, **kwargs):
            input = kwargs['input']
            which  = kwargs.get('which')
            if isinstance(which,list):
                which = which[0]
                kwargs['which'] = which

            bokeh_figure_linear = kwargs.get('bokeh_figure_linear')
            bokeh_figure_log = kwargs.get('bokeh_figure_log')
            bokeh_figure_map = kwargs.get('bokeh_figure_map')

            dateslider = kwargs.get('dateslider')
            if func.__name__ == 'bokeh_histo' and dateslider == True:
                print('dateslider not implemented in this current version ...')
                dateslider = False

            maxcountrydisplay = kwargs['maxcountrydisplay']
            maxlettersdisplay = kwargs['maxlettersdisplay']

            lhist = ['bokeh_pie','bokeh_horizonhisto']

            ymax = self.figure_height

            if func.__name__ in lhist:
                input = self.addcolumnshisto(input,which,maxcountrydisplay)
                yrange = Range1d(min(input['bottom']), max(input['top']))

            input_uniquecountries = input.loc[input.date==input.date.max()].drop(columns=['date']).reset_index(drop=True)
            input_uniquecountries['right'] = len(input_uniquecountries.index)*[0.]

            if 'geometry' in list(input_uniquecountries.columns):
                if func.__name__ in lhist:
                    input_uniquecountries = input_uniquecountries.head(maxcountrydisplay)
                input_uniquecountries['cases']=input_uniquecountries[which]
                passinput_uniquecountries = input_uniquecountries.to_crs(epsg=4326)
                convertgeo = visu_bokeh().convertmercator(input_uniquecountries)
                geocolumndatasrc = GeoJSONDataSource(geojson = convertgeo.to_json())

            if 'geometry' in list(input.columns):
                input_dates = input.drop(columns='geometry').copy()
            else:
                input_dates = input.copy()

            invViridis256 = Viridis256[::-1]
            color_mapper = LinearColorMapper(palette=invViridis256, low=0, high=max(input_dates[which]), nan_color='#ffffff')
            color_bar = ColorBar(color_mapper=color_mapper, label_standoff=4, bar_line_cap='round',\
                        border_line_color=None, location=(0, 0), orientation='horizontal', ticker=BasicTicker())
            if dateslider:
                input_dates = input_dates.sort_values(by=['date', 'where'])
                input_dates['date'] = input_dates['date'].dt.strftime("%d/%m/%Y")
                unique_dates = input_dates['date'].drop_duplicates().tolist()
                unique_where = input_dates['where'].unique().tolist()
                #unique_dates = [i.strftime("%d/%m/%Y") for i in unique_dates]
                frames = []
                cols = list(input_dates.columns)
                frames = []
                #unique_dates = unique_dates[::-1]

                for d in unique_dates:
                    df_d = input_dates[input_dates['date'] == d].copy()
                    df_d['where'] = pd.Categorical(
                        df_d['where'],
                        categories=unique_where,
                        ordered=True
                    )
                    df_d = df_d.sort_values('where')
                    df_d = df_d[cols]
                    if df_d.empty:
                        frame = {c: [] for c in cols}
                        frames.append(frame)
                        continue

                    frame = {}
                    for c in list(df_d.columns):
                        if c in df_d.columns:
                            frame[c] = df_d[c].tolist()
                        else:
                            frame[c] = []
                    frames.append(frame)

                input_dates =  input_dates.loc[input_dates.date==input_dates.date.max()].head(maxcountrydisplay).reset_index(drop=True)
                if func.__name__ in lhist:
                    input_dates = self.addcolumnshisto(input_dates,which,maxcountrydisplay)
                    input_dates = self.addcolumnspie(input_dates,which)
                    yrange = Range1d(min(input_dates['bottom']), max(input_dates['top']))
                columndatasrc = ColumnDataSource(data = input_dates)

                from bokeh.models import Slider, CustomJS, Div
                slider = Slider(start=0, end=max(0, len(frames)-1), value=0, step=1, title="Date index", width=300)
                date_display = Div(text=f"<b>{unique_dates[0]}</b>", width=300)
                from bokeh.models import CustomJS

                slider_callback = CustomJS(
                        args=dict(
                            frames=frames,
                            sourcemap=geocolumndatasrc,
                            sourcehisto=columndatasrc,
                            which=which,
                            dates=unique_dates,
                            div=date_display,
                            maxcountrydisplay=maxcountrydisplay,
                            maxlettersdisplay=maxlettersdisplay,
                            ylabellinear=bokeh_figure_linear.yaxis[0],
                            ylabellog=bokeh_figure_log.yaxis[0],
                            ymax = ymax,
                            color_mapperjs = color_mapper
                        ),
                        code="""
                            const i = cb_obj.value;
                            const frame = frames[i];
                            const keys = Object.keys(frame);
                            const rows = [];

                            //FOR MAP
                            for (let j = 0; j < frame[which].length; j++) {
                                let r = {};
                                for (const k of keys) {
                                    r[k] = frame[k][j];
                                }
                                rows.push(r);
                            }

                            for (const k of keys) {
                                sourcemap.data[k] = rows.map(r => r[k]);
                                sourcemap.data['cases'] = sourcemap.data[which];
                            }
                            const values = sourcemap.data['cases'].filter(v => Number.isFinite(v));
                            color_mapperjs.low=Math.min.apply(Math, values);
                            color_mapperjs.high=Math.max.apply(Math, values);
                            sourcemap.change.emit();
                            console.log(sourcemap.data['cases'],Math.max.apply(Math, sourcemap.data['cases']));
                            // For HISTO
                            const len = sourcehisto.data[which].length;
                            const sorted_rows = rows.sort((a, b) => b[which] - a[which]);
                            const limited = sorted_rows.slice(0, maxcountrydisplay);
                            const allColumns = Object.keys(sourcehisto.data);

                             for (const col of allColumns) {
                                const limited_col = limited.map(r => r[col]);
                                sourcehisto.data[col] = limited_col;
                            }

                            const labelMap = new Map();
                            const total = sourcehisto.data[which].map(Number).reduce((a, b) => a + b, 0);
                            const angles = new Array(len);

                            for (let j = 0; j < len; j++) {
                                const where_val = sourcehisto.data['where'][j].slice(0, maxlettersdisplay);
                                sourcehisto.data['top'][j]    = ymax * (maxcountrydisplay - j) / maxcountrydisplay + 0.5 * ymax / maxcountrydisplay;
                                sourcehisto.data['bottom'][j] = ymax * (maxcountrydisplay - j) / maxcountrydisplay - 0.5 * ymax / maxcountrydisplay;
                                sourcehisto.data['horihistotexty'] = sourcehisto.data['bottom'][j] + 0.5 * ymax / maxcountrydisplay;

                                let pos = parseInt(ymax * (len - j) / len);
                                if (!Number.isFinite(pos)) continue;
                                labelMap.set(pos, String(where_val));

                                sourcehisto.data['angle'][j] =  (sourcehisto.data[which][j] / total) * 2 * Math.PI;
                                sourcehisto.data['textdisplayed'][j] = sourcehisto.data['where'].map(w =>
                                String(w).padStart(36, " "))[j];
                                const value = sourcehisto.data[which][j];
                                const percent = (total === 0) ? 0 : (100 * value / total);
                                sourcehisto.data['textdisplayed2'][j] = percent.toFixed(1) + "%";
                            }
                            ylabellinear.major_label_overrides = labelMap;
                            ylabellog.major_label_overrides    = labelMap;
                            sourcehisto.change.emit();

                            div.text = '<b>' + dates[i] + '</b>';
                        """
                    )

                slider.js_on_change('value', slider_callback)
                toggl = Toggle(label='► Play', active=False, button_type="success", height=30, width=70)
                # CustomJS pour démarrer/arrêter l'animation

                toggle_callback = CustomJS(args=dict(slider=slider, frames=frames), code="""
                    if (cb_obj.active) {
                        // play: démarrer interval si pas déjà présent
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
                """)
                toggl.js_on_change('active', toggle_callback)

                from bokeh.models import Div
                date_display = Div(text=f"<b>{unique_dates[-1]}</b>", width=300)
                # Mettre à jour le Div depuis le slider (JS)
                slider_date_div_cb = CustomJS(args=dict(div=date_display, dates=unique_dates),
                code="""
                  const i = cb_obj.value;      // index choisi
                  div.text = "<b>" + dates[i] + "</b>";
                  """)

                slider.js_on_change('value', slider_date_div_cb)
                controls = column(toggl, slider, date_display)
                kwargs['controls'] = controls
            else:
                input_dates = input_dates.loc[input_dates.date==input_dates.date.max()]
                input_dates = self.addcolumnspie(input_dates,which)
                columndatasrc = ColumnDataSource(data = input_dates)

            def geosource_bounds(geosource):
                import json
                from shapely.geometry import shape
                data = json.loads(geosource.geojson)
                xs, ys = [], []
                for feature in data["features"]:
                    geom = shape(feature["geometry"])
                    x_min, y_min, x_max, y_max = geom.bounds
                    xs += [x_min, x_max]
                    ys += [y_min, y_max]
                return min(xs), min(ys), max(xs), max(ys)


            xmin, ymin, xmax, ymax = geosource_bounds(geocolumndatasrc)
            pad_x = (xmax - xmin) * 0.05
            pad_y = (ymax - ymin) * 0.05
            bokeh_figure_map.x_range.bounds = (xmin - pad_x, xmax + pad_x)
            bokeh_figure_map.y_range.bounds = (ymin - pad_y, ymax + pad_y)
            ratio = (ymax + pad_y - (ymin - pad_y)) / (xmax + pad_x - (xmin - pad_x))
            bokeh_figure_map.min_border = 0

            bokeh_figure_map.x_range.start = xmin - pad_x
            bokeh_figure_map.x_range.end   = xmax + pad_x
            bokeh_figure_map.y_range.start = ymin - pad_y
            bokeh_figure_map.y_range.end   = ymax + pad_y

            min_col, max_col = visu_bokeh().min_max_range(np.nanmin(input_dates[which]),np.nanmax(input_dates[which]))

            bokeh_figure_map.patches('xs', 'ys', source = geocolumndatasrc,
                            fill_color = {'field': 'cases', 'transform': color_mapper},
                            line_color = 'black', line_width = 0.25, fill_alpha = 1)

            if func.__name__ in lhist:
                kwargs['yrange']=yrange
            if 'geometry' in list(input_uniquecountries.columns):
                kwargs['geocolumndatasrc'] = geocolumndatasrc
            kwargs['columndatasrc'] = columndatasrc
            kwargs['color_mapper']=color_mapper
            kwargs['input'] = input
            return func(self, **kwargs)
        return inner_decodateslider

    @staticmethod
    def bokeh_legend(bkfigure):
        from bokeh.models import CustomJS
        from bokeh import events
        toggle_legend_js = CustomJS(args=dict(leg=bkfigure.legend[0]),
        code="""
        if(leg.visible)
        {
            leg.visible = false;
        }
        else
        {
            leg.visible = true;
        }
        """)
        bkfigure.js_on_event(events.DoubleTap, toggle_legend_js)

    def get_listfigures(self):
        return  self.listfigs

    def set_listfigures(self,fig):
            if not isinstance(fig,list):
                fig = [fig]
            self.listfigs = fig

    def bokeh_resume_data(self,**kwargs):
        loc=list(input['where'].unique())
        input['cases'] = input[which]
        resumetype = kwargs.get('resumetype','spiral')
        if resumetype == 'spiral':
            dspiral={i:AllVisu.spiral(input.loc[ (input['where']==i) &
                        (input.date >= self.when_beg) &
                        (input.date <= self.when_end)].sort_values(by='date')) for i in loc}
            input['resume']=input['where'].map(dspiral)
        elif resumetype == 'spark':
            spark={i:AllVisu.sparkline(input.loc[ (input['where']==i) &
                        (input.date >= self.when_beg) &
                        (input.date <= self.when_end)].sort_values(by='date')) for i in loc}
            input['resume']=input['where'].map(spark)
        else:
            raise PyvoaError('bokeh_resume_data can use spiral or spark ... here what ?')
        input = input.loc[input.date==input.date.max()].reset_index(drop=True)
        def path_to_image_html(path):
            return '<img pyvoa="'+ path + '" width="60" >'

        input=input.apply(lambda x: x.round(2) if x.name in [which,'daily','weekly'] else x)
        if isinstance(input['where'][0], list):
            col=[i for i in list(input.columns) if i not in ['where','where','code']]
            col.insert(0,'where')
            input = input[col]
            input=input.set_index('where')
        else:
           input = input.drop(columns='where')
           input=input.set_index('where')

        return input.to_html(escape=False,formatters=dict(resume=path_to_image_html))

    def bokeh_plot(func):
        @wraps(func)
        def inner_bokeh_plot(self, **kwargs):
            input=kwargs['input']
            nb = kwargs['maxlettersdisplay']
            input['where'] = [ (w[:nb] + '…') if len(w) > nb else w for w in input['where']]
            if 'geometry' in list(input.columns):
                kwargs['input'] = input.drop(columns='geometry')
            return func(self, **kwargs)
        return  inner_bokeh_plot

    ''' PLOT VERSUS '''
    @deco_bokeh
    @bokeh_plot
    def bokeh_versus_plot(self,**kwargs):
        '''
        -----------------
        Create a versus plot according to arguments.
        See help(bokeh_versus_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pypyvoa.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
        - which = if None take second element. It should be a list dim=2. Moreover the 2 variables must be present
        in the DataFrame considered.
        - plot_heigh = Width_Height_Default[1]
        - graph_width = Width_Height_Default[0]
        - title = None
        - copyright = default
        - mode = mouse
        - dateslider = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''
        input = kwargs.get('input')
        which = kwargs.get('which')
        copyright = kwargs.get('copyright')
        mode = kwargs.get('mode')
        bokeh_figure = kwargs.get('bokeh_figure')
        panels = []
        cases_custom = visu_bokeh().rollerJS()
        if self.get_listfigures():
            self.set_listfigures([])
        listfigs=[]
        dbokeh_figure = {
            'linear': kwargs.get('bokeh_figure_linear'),
            'log': kwargs.get('bokeh_figure_log')
        }
        dicof={'title':kwargs.get('title')}
        for axis_type in self.av.d_graphicsinput_args['ax_type']:
            fig = dbokeh_figure[axis_type]
            dicof['x_axis_label'] = which[0]
            dicof['y_axis_label'] = which[1]
            dicof['y_axis_type' ] = axis_type


            fig.add_tools(HoverTool(
                tooltips=[('where', '@where'), ('date', '@date{%F}'),
                          (which[0], '@{casesx}' + '{custom}'),
                          (which[1], '@{casesy}' + '{custom}')],
                formatters={'where': 'printf', '@{casesx}': cases_custom, '@{casesy}': cases_custom,
                            '@date': 'datetime'}, mode = mode,
                point_policy="snap_to_data"))  # ,PanTool())

            for loc in input['where'].unique():
                pandaloc = input.loc[input['where'] == loc].sort_values(by='date', ascending=True)
                #pandaloc.rename(columns={what[0]: 'casesx', what[1]: 'casesy'}, inplace=True)
                fig.line(x=which[0], y=which[1],
                                 source=ColumnDataSource(pandaloc), legend_label=f"{loc}",
                                 color=pandaloc.colors.iloc[0], line_width=3, hover_line_width=4)

            fig.legend.label_text_font_size = "12px"
            panel = TabPanel(child=Row(fig,kwargs['watermark']), title=axis_type)
            panels.append(panel)
            fig.legend.background_fill_alpha = 0.6

            fig.legend.location = "top_right"
            listfigs.append(fig)
            visu_bokeh().bokeh_legend(fig)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs=panels)
        return tabs

    ''' DATE PLOT '''
    @deco_bokeh
    @bokeh_plot
    def bokeh_date_plot(self,**kwargs):
        '''
        -----------------
        Create a date plot according to arguments. See help(bokeh_date_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pypyvoa.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
        - which = if None take second element could be a list
        - plot_heigh= Width_Height_Default[1]
        - graph_width = Width_Height_Default[0]
        - title = None
        - copyright = default
        - mode = mouse
        - guideline = False
        - dateslider = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''
        input = kwargs.get('input')

        which = kwargs.get('which')
        mode = kwargs.get('mode')
        guideline = kwargs.get('guideline')
        title = kwargs.get('title',None)
        panels = []
        listfigs = []
        cases_custom = visu_bokeh().rollerJS()
        dbokeh_figure = {
            'linear': kwargs.get('bokeh_figure_linear_date'),
            'log': kwargs.get('bokeh_figure_log_date')
        }
        dicof={'title':kwargs.get('title')}

        legend = kwargs.get('legend', None)

        for axis_type in self.av.d_graphicsinput_args['ax_type']:
            fig = dbokeh_figure[axis_type]
            dicof['x_axis_type'] = 'datetime'
            dicof['y_axis_type'] = axis_type
            i = 0
            r_list=[]
            maxi=-1000
            line_style = ['solid', 'dashed', 'dotted', 'dotdash','dashdot']
            maxi, mini=0, 0
            tooltips=[]
            colors = list(input['colors'].unique())
            for idx,val in enumerate(which):
                for ldx,loc in enumerate(list(input['where'].unique())):
                    pyvoa = ColumnDataSource(input.loc[input['where'].isin([loc])])
                    if legend:
                        label = legend
                    else:
                        label = f"{loc}"
                        if len(which)>1:
                            label=f"{loc}, {val}"
                    r = fig.line(x = 'date', y = val, source = pyvoa,
                                     line_width = 3,
                                     color=colors[ldx],
                                     legend_label=label,
                                     hover_line_width = 4, name = val, line_dash=line_style[idx])
                    r_list.append(r)
                    maxi=max(maxi,np.nanmax(input[val]))
                    mini=max(mini,np.nanmin(input[val]))

                    if mini <0.01:
                        tooltips.append([('where', '@where'), ('date', '@date{%F}'), (r.name, '@$name')])
                    else:
                        tooltips.append([('where', '@where'), ('date', '@date{%F}'), (r.name, '@$name{0,0.0}')])
                    if isinstance(tooltips,tuple):
                        tooltips = tooltips[0]
                i += 1
            for i,r in enumerate(r_list):
                label = r.name
                tt = tooltips[i]
                formatters = {'where': 'printf', '@date': 'datetime', '@name': 'printf'}
                hover=HoverTool(tooltips = tt, formatters = formatters, point_policy = "snap_to_data", mode = mode, renderers=[r])  # ,PanTool())
                fig.add_tools(hover)

                if guideline:
                    cross= CrosshairTool()
                    fig.add_tools(cross)

            if axis_type == 'linear':
                if maxi  < 1e4 :
                    fig.yaxis.formatter = BasicTickFormatter(use_scientific=False)
            fig.legend.title=", ".join(which)
            fig.legend.ncols = len(which)
            fig.legend.visible = True
            fig.legend.background_fill_alpha = 0.6
            fig.legend.click_policy="hide"
            fig.legend.label_text_font_size = '8pt'
            fig.legend.spacing = 5
            fig.legend.location = "top_left"
            panel = TabPanel(child=Row(fig,kwargs['watermark']), title = axis_type)
            panels.append(panel)
            fig.xaxis.formatter = DatetimeTickFormatter(
                days = "%d/%m/%y", months = "%d/%m/%y", years = "%b %Y")
            visu_bokeh().bokeh_legend(fig)

            listfigs.append(fig)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs = panels)
        return tabs

    ''' SPIRAL PLOT '''
    @deco_bokeh
    @bokeh_plot
    def bokeh_spiral_plot(self, **kwargs):
        panels = []
        listfigs = []
        input = kwargs.get('input')
        which = kwargs.get('which')
        borne = 300
        dicof={'title':kwargs.get('title')}
        dicof['match_aspect']=True

        bokeh_figure = kwargs.get('bokeh_figure_linear')#(x_range=[-borne, borne], y_range=[-borne, borne], **dicof)
        bokeh_figure.xaxis.visible = False
        bokeh_figure.yaxis.visible = False

        if len(input['where'].unique()) > 1 :
            print('Can only display spiral for ONE location. I took the first one:', input['where'][0])
            input = input.loc[input['where'] == input['where'][0]].copy()
        input["dayofyear"]=input.date.dt.dayofyear
        input['year']=input.date.dt.year
        input['cases'] = input[which]

        K = 2*input[which].max()
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input["dayofyear_angle"] = input["dayofyear"]*2 * np.pi/365
        input["r_baseline"] = input.apply(lambda x : ((x["year"]-2020)*2 * np.pi + x["dayofyear_angle"])*K,axis=1)
        size_factor = 16
        input["r_cas_sup"] = input.apply(lambda x : x["r_baseline"] + 0.5*x[which]*size_factor,axis=1)
        input["r_cas_inf"] = input.apply(lambda x : x["r_baseline"] - 0.5*x[which]*size_factor,axis=1)

        radius = 200
        def polar(theta,r,norm=radius/input["r_baseline"].max()):
            x = norm*r*np.cos(theta)
            y = norm*r*np.sin(theta)
            return x,y
        x_base,y_base=polar(input["dayofyear_angle"],input["r_baseline"])
        x_cas_sup,y_cas_sup=polar(input["dayofyear_angle"],input["r_cas_sup"])
        x_cas_inf,y_cas_inf=polar(input["dayofyear_angle"],input["r_cas_inf"])

        xcol,ycol=[],[]
        [ xcol.append([i,j]) for i,j in zip(x_cas_inf,x_cas_sup)]
        [ ycol.append([i,j]) for i,j in zip(y_cas_inf,y_cas_sup)]
        bokeh_figure.patches(xcol,ycol,color='blue',fill_alpha = 0.5)

        pyvoa = ColumnDataSource(data=dict(
        x=x_base,
        y=y_base,
        date=input['date'],
        cases=input['cases']
        ))
        bokeh_figure.line( x = 'x', y = 'y', source = pyvoa, legend_label = which[0] +', '+ input['where'][0],
                        line_width = 3, line_color = 'blue')
        circle = bokeh_figure.circle('x', 'y', size=2, source=pyvoa)

        cases_custom = visu_bokeh().rollerJS()
        hover_tool = HoverTool(tooltips=[('Cases', '@cases{0,0.0}'), ('date', '@date{%F}')],
                               formatters={'Cases': 'printf', '@{cases}': cases_custom, '@date': 'datetime'},
                               renderers=[circle],
                               point_policy="snap_to_data")
        bokeh_figure.add_tools(hover_tool)

        outer_radius=250
        [bokeh_figure.annular_wedge(
            x=0, y=0, inner_radius=0, outer_radius=outer_radius, start_angle=i*np.pi/6,\
            end_angle=(i+1)*np.pi/6,fill_color=None,line_color='black',line_dash='dotted')
        for i in range(12)]

        label = ['January','February','March','April','May','June','July','August','September','October','November','December']
        xr,yr = polar(np.linspace(0, 2 * np.pi, 13),outer_radius,1)
        bokeh_figure.text(xr[:-1], yr[:-1], label,text_font_size="9pt", text_align="center", text_baseline="middle")

        bokeh_figure.legend.background_fill_alpha = 0.6
        bokeh_figure.legend.location = "top_left"
        bokeh_figure.legend.click_policy="hide"
        panel = TabPanel(child=Row(bokeh_figure,kwargs['watermark']))
        tabs = Tabs(tabs = [panel])
        return tabs

    ''' SCROLLINGMENU PLOT '''
    @deco_bokeh
    @bokeh_plot
    def bokeh_menu_plot(self, **kwargs):
        '''
        -----------------
        Create a date plot, with a scrolling menu location, according to arguments.
        See help(bokeh_menu_plot).
        Keyword arguments
        -----------------
        len(location) > 2
        - input = None : if None take first element. A DataFrame with a Pypyvoa.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
        - which = if None take second element could be a list
        - plot_heigh= Width_Height_Default[1]
        - graph_width = Width_Height_Default[0]
        - title = None
        - copyright = default
        - mode = mouse
        - guideline = False
        - dateslider = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''

        input = kwargs.get('input')
        which= kwargs.get('which')
        guideline = kwargs.get('guideline',self.av.d_graphicsinput_args['guideline'][0])
        mode = kwargs.get('mode',self.av.d_graphicsinput_args['mode'][0])
        if isinstance(which,list):
            which=which[0]

        dbokeh_figure = {
            'linear': kwargs.get('bokeh_figure_linear_date'),
            'log': kwargs.get('bokeh_figure_log_date')
        }

        uniqloc = list(input['where'].unique())
        uniqloc.sort()
        if 'where' in input.columns:
            if len(uniqloc) < 2:
                raise PyvoaTypeError('What do you want me to do ? You have selected, only one country.'
                                   'There is no sens to use this method. See help.')
        input = input[['date', 'where', which]]
        input = input.sort_values(by='where', ascending = True).reset_index(drop=True)

        mypivot = pd.pivot_table(input, index='date', columns='where', values=which)
        column_order = uniqloc
        mypivot = mypivot.reindex(column_order, axis=1)
        source = ColumnDataSource(mypivot)

        filter_data1 = mypivot[[uniqloc[0]]].rename(columns={uniqloc[0]: 'cases'})
        pyvoa1 = ColumnDataSource(filter_data1)

        filter_data2 = mypivot[[uniqloc[1]]].rename(columns={uniqloc[1]: 'cases'})
        pyvoa2 = ColumnDataSource(filter_data2)

        cases_custom = visu_bokeh().rollerJS()
        #hover_tool = HoverTool(tooltips=[(which, '@which{0,0.0}'), ('date', '@date{%F}')],
        #                       formatters={which: 'printf', '@{which}': cases_custom, '@date': 'datetime'},
        #                       mode = mode, point_policy="snap_to_data")  # ,PanTool())

        panels = []
        for axis_type in self.av.d_graphicsinput_args['ax_type']:
            fig = dbokeh_figure[axis_type]
            fig.yaxis[0].formatter = PrintfTickFormatter(format = "%4.2e")
            fig.xaxis.formatter = DatetimeTickFormatter(
                days = "%d/%m/%y", months = "%d/%m/%y", years = "%b %Y")

        #    bokeh_figure.add_tools(hover_tool)
            if guideline:
                cross= CrosshairTool()
                fig.add_tools(cross)
            def add_line(pyvoa, options, init, color):
                s = Select(options = options, value = init)
                r = fig.line(x = 'date', y = 'cases', source = pyvoa, line_width = 3, line_color = color)
                li = LegendItem(label = init, renderers = [r])
                s.js_on_change('value', CustomJS(args=dict(s0=source, s1=pyvoa, li=li),
                                                 code="""
                                            var c = cb_obj.value;
                                            var y = s0.data[c];
                                            s1.data['cases'] = y;
                                            li.label = {value: cb_obj.value};
                                            s1.change.emit();
                                     """))
                return s, li

            s1, li1 = add_line(pyvoa1, uniqloc, uniqloc[0], self.scolors[0])
            s2, li2 = add_line(pyvoa2, uniqloc, uniqloc[1], self.scolors[1])
            fig.add_layout(Legend(items = [li1, li2]))
            fig.legend.location = 'top_left'
            layout = row(column(row(s1, s2), row(fig)))
            panel = TabPanel(child=Row(layout,kwargs['watermark']), title = axis_type)
            panels.append(panel)

        tabs = Tabs(tabs = panels)
        label = fig.title
        return tabs

    ''' YEARLY PLOT '''
    @deco_bokeh
    @bokeh_plot
    def bokeh_yearly_plot(self,**kwargs):
        '''
        -----------------
        Create a date plot according to arguments. See help(bokeh_date_plot).
        Keyword arguments
        -----------------
        - input = None : if None take first element. A DataFrame with a Pypyvoa.struture is mandatory
        |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
        - which = if None take second element could be a list
        - plot_heigh= Width_Height_Default[1]
        - graph_width = Width_Height_Default[0]
        - title = None
        - copyright = default
        - mode = mouse
        - guideline = False
        - dateslider = None if True
                - orientation = horizontal
        - when : default min and max according to the inpude DataFrame.
                 Dates are given under the format dd/mm/yyyy.
                 when format [dd/mm/yyyy : dd/mm/yyyy]
                 if [:dd/mm/yyyy] min date up to
                 if [dd/mm/yyyy:] up to max date
        '''
        input = kwargs['input']
        which = kwargs['which']
        guideline = kwargs.get('guideline',self.av.d_graphicsinput_args['guideline'][0])
        mode = kwargs.get('mode',self.av.d_graphicsinput_args['mode'][0])
        dbokeh_figure = {
            'linear': kwargs.get('bokeh_figure_yearly'),
            'log': kwargs.get('bokeh_figure_yearly')
        }

        input = input.loc[input['where'] == input['where'][0]].copy()

        panels = []
        listfigs = []
        cases_custom = visu_bokeh().rollerJS()
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)
        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)
        allyears = list(input.allyears.unique())

        for axis_type in  self.av.d_graphicsinput_args['ax_type']:
            fig = dbokeh_figure[axis_type]
            i = 0
            r_list=[]
            maxi=-1000
            input['cases']=input[which]
            line_style = ['solid', 'dashed', 'dotted', 'dotdash']
            colors = itertools.cycle(self.lcolors)
            for loc in list(input['where'].unique()):
                for year in allyears:
                    df = input.loc[(input['where'] == loc) & (input['date'].dt.year.eq(year))].reset_index(drop=True)
                    if df.empty:
                        continue
                    pyvoa = ColumnDataSource(df)
                    leg = f"{year} {loc}"
                    r = fig.line(
                        x='dayofyear', y='cases', source=pyvoa,
                        color=next(colors), line_width=3,
                        legend_label=leg, hover_line_width=4, name='cases'
                    )
                    #maxi=max(maxi,np.nanmax(pyvoa.data['cases']))

            label = which
            tooltips = [('where', '@rolloverdisplay'), ('date', '@date{%F}'), ('Cases', '@cases{0,0.0}')]
            formatters = {'where': 'printf', '@date': 'datetime', '@name': 'printf'}
            hover=HoverTool(tooltips = tooltips, formatters = formatters, point_policy = "snap_to_data", mode = mode)  # ,PanTool())
            fig.add_tools(hover)
            if guideline:
                cross= CrosshairTool()
                fig.add_tools(cross)


            fig.yaxis.formatter = BasicTickFormatter(use_scientific=False)

            fig.legend.label_text_font_size = "12px"
            panel = TabPanel(child=Row(fig,kwargs['watermark']), title = axis_type)
            panels.append(panel)
            fig.legend.background_fill_alpha = 0.6

            fig.legend.location = "top_left"
            fig.legend.click_policy="hide"

            minyear=input.date.min().year

            months = pd.date_range("2023-01-01", "2023-12-01", freq="MS")
            month_doys = months.dayofyear
            month_labels = months.strftime("%b")
            fig.xaxis.ticker = list(month_doys)
            fig.xaxis.major_label_overrides = dict(zip(month_doys, month_labels))
            visu_bokeh().bokeh_legend(fig)
            listfigs.append(fig)

        tooltips = [('where', '@rolloverdisplay'), ('date', '@date{%F}'), (r.name, '@$name{0,0.0}')]
        formatters = {'where': 'printf', '@date': 'datetime', '@name': 'printf'}
        hover=HoverTool(tooltips = tooltips, formatters = formatters, point_policy = "snap_to_data", mode = mode, renderers=[r])  # ,PanTool())
        fig.add_tools(hover)
        if guideline:
            cross= CrosshairTool()
            fig.add_tools(cross)
        self.set_listfigures(listfigs)
        tabs = Tabs(tabs = panels)
        return tabs

    ''' VERTICAL HISTO '''

    @deco_bokeh
    def bokeh_histo(self, **kwargs):
        '''
            -----------------
            Create 1D histogramme by value according to arguments.
            See help(bokeh_histo).
            Keyword arguments
            -----------------
            - input : A DataFrame with a Pypyvoa.struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
            - which = if None take second element could be a list
            - plot_heigh= Width_Height_Default[1]
            - graph_width = Width_Height_Default[0]
            - title = None
            - copyright = default
            - when : default min and max according to the inpude DataFrame.
                     Dates are given under the format dd/mm/yyyy.
                     when format [dd/mm/yyyy : dd/mm/yyyy]
                     if [:dd/mm/yyyy] min date up to
                     if [dd/mm/yyyy:] up to max date
        '''

        input = kwargs.get('input')
        bins = kwargs.get('bins', self.av.d_graphicsinput_args['bins'])
        uniqloc = list(input['where'].unique())
        which  = kwargs.get('which')
        if isinstance(which,list):
            which = which[0]

        dfigures = {
                    'linear':kwargs.get('bokeh_figure_linear'),
                    'loglog':kwargs.get('bokeh_figure_loglog')
                    }

        min_val = input[which].min()
        max_val =  input[which].max()

        if not bins:
            if len(input[which].unique()) == 1:
                bins = 2
                min_val = 0.
            else:
                bins = 11

        delta = (max_val - min_val ) / bins
        interval = [ min_val + i*delta for i in range(bins+1)]

        contributors = {  i : [] for i in range(bins+1)}
        for i in range(len(input)):
            rank = bisect.bisect_left(interval, input.iloc[i][which])
            if rank >= bins:
                rank = bins - 1
            contributors[rank].append(input.iloc[i]['where'])

        lcolors = iter(self.lcolors)

        contributors = dict(sorted(contributors.items()))

        frame_histo = pd.DataFrame({
                          'left': [0]+interval[:-1],
                          'right':interval,
                          'middle_bin': [format((i+j)/2, ".1f") for i,j in zip([0]+interval[:-1],interval)],
                          'top': [len(i) for i in list(contributors.values())],
                          'contributors': [', '.join(i) for i in contributors.values()],
                          'colors': [next(lcolors) for i in range(len(interval)) ]})
        #tooltips = """
        #<div style="width: 400px">
        #<b>Middle value:</b> @middle_bin <br>
        #<b>Contributors:</b> @contributors{safe} <br>
        #</div>
        #"""
        tooltips = """
        <b>Middle value:</b> @middle_bin <br>
        <b>Contributors:</b> @contributors{safe} <br>
        """
        hover_tool = HoverTool(tooltips = tooltips)
        panels = []
        bottom = 0
        x_axis_type, y_axis_type, axis_type_title = 3 * ['linear']
        for axis_type in ["linear", "loglog"]:
            fig = dfigures[axis_type]
            if axis_type == 'loglog':
                x_axis_type, y_axis_type = 'log', 'log'
                axis_type_title = 'loglog'

            fig.add_tools(hover_tool)
            fig.x_range = Range1d(interval[0], interval[-1])
            fig.y_range = Range1d(0, 1.05 * frame_histo['top'].max())
            if x_axis_type == "log":
                left = 0.8
                if frame_histo['left'][0] <= 0:
                    frame_histo.at[0, 'left'] = left
                else:
                    left  = frame_histo['left'][0]
                fig.x_range = Range1d(left, 10 * interval[-1])

            if y_axis_type == "log":
                bottom = 0.0001
                fig.y_range = Range1d(0.001, 10 * frame_histo['top'].max())

            fig.quad(source=ColumnDataSource(frame_histo), top='top', bottom=bottom, left='left', \
                             right='right', fill_color='colors')
            panel = TabPanel(child=Row(fig,kwargs['watermark']), title=axis_type_title)
            panels.append(panel)
        tabs = Tabs(tabs=panels)
        return tabs

    ''' VERTICAL HISTO '''
    @deco_bokeh
    @decodateslider
    def bokeh_horizonhisto(self, **kwargs):
        mode = kwargs.get('mode')
        dateslider = kwargs.get('dateslider')
        columndatasrc = kwargs.get('columndatasrc')
        controls = kwargs.get('controls', None)
        maxletters = kwargs['maxlettersdisplay']
        title = kwargs['title']
        dbokeh_figure = {
            'linear': kwargs.get('bokeh_figure_linear'),
            'log': kwargs.get('bokeh_figure_log')
        }

        new_panels = []
        from bokeh.models import LogScale, LinearScale

        for axis_type in self.av.d_graphicsinput_args['ax_type']:
            fig = dbokeh_figure[axis_type]
            fig.y_range = kwargs['yrange']

            ytick_loc = [int(i) for i in columndatasrc.data['horihistotexty']]
            fig.yaxis[0].ticker = ytick_loc
            label_dict = dict(zip(ytick_loc, [x[:maxletters] for x in columndatasrc.data['where']]))
            if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
                label_dict = {ytick_loc[0]:'sum all location'}

            fig.yaxis[0].major_label_overrides = label_dict
            fig.yaxis[0].formatter = NumeralTickFormatter(format="0.0")

            factor = 20.0 if axis_type == 'log' else 1.2
            left = 0.01 if axis_type == 'log' else 'left'
            epslion = 0.01 if axis_type == 'log' and min(columndatasrc.data['left']) == 0 else 0.0
            minn = min(columndatasrc.data['left']) + epslion
            maxx = 1.15*max(columndatasrc.data['right'])
            fig.x_range.start = minn
            fig.x_range.end = maxx
            fig.title = title
            fig.quad(
                source=columndatasrc,
                top='top',
                bottom='bottom',
                left=left,
                right='right',
                color='colors',
                line_color='black',
                line_width=1,
                hover_line_width=2,
            )

            labels = LabelSet(
                x='horihistotextx',
                y='horihistotexty',
                x_offset=5,
                y_offset=-4,
                text='horihistotext',
                source=columndatasrc,
                text_font_size='10px',
                text_color='black'
            )
            fig.add_layout(labels)

            cases_custom = visu_bokeh().rollerJS()
            hover_tool = HoverTool(
                tooltips=[
                    ('where', '@where'),
                    ('cases', '@right')
                ],
                formatters={'where': 'printf', '@{' + 'right' + '}': cases_custom, '%': 'printf'},
                mode=mode,
                point_policy="snap_to_data"
            )
            fig.add_tools(hover_tool)
            panel = TabPanel(child=Row(fig,kwargs['watermark']), title=axis_type)
            new_panels.append(panel)

        tabs = Tabs(tabs=new_panels)

        if dateslider:
            layout = column(controls, tabs)
            tabs = layout
        return tabs

    def addcolumnshisto(self,mypd,which,maxcountrydisplay):
        ymax = self.figure_height
        mypd['left'] = mypd[which]
        mypd['right'] = mypd[which]
        def _fmt(v):
            fv = float(v)
            if fv == 0:
                return '0'
            if abs(fv) >= 1.e4 or (abs(fv) > 0 and abs(fv) < 0.01):
                return '{:.3g}'.format(fv)
            return str(round(fv, 2))

        mypd['horihistotext'] = mypd['right'].apply(_fmt)
        mypd['horihistotext'] = [str(i) for i in mypd['horihistotext']]
        mypd['left'] = mypd['left'].apply(lambda x: 0 if x > 0 else x)
        mypd['right'] = mypd['right'].apply(lambda x: 0 if x < 0 else x)
        mypd['horihistotextx'] = mypd['right']
        indices = [i % maxcountrydisplay for i in range(len(mypd))]
        mypd['top'] = [ymax * (maxcountrydisplay - i) / maxcountrydisplay + 0.5 * ymax / maxcountrydisplay for i in indices]
        mypd['bottom'] = [ymax * (maxcountrydisplay - i) / maxcountrydisplay - 0.5 * ymax / maxcountrydisplay for i in indices]
        mypd['horihistotexty'] = mypd['bottom'] + 0.5*ymax/maxcountrydisplay
        mypd['horihistotextx'] = mypd['right']
        return mypd

    ''' PIE '''
    def addcolumnspie(self,df,column_name):
        df = df.copy()
        column_sum = df[column_name].sum()
        df['percentage'] = df[column_name]/column_sum

        percentages = [0]  + df['percentage'].cumsum().tolist()
        df['angle'] = (df[column_name]/column_sum)*2 * np.pi
        df['starts'] = [p * 2 * np.pi for p in percentages[:-1]]
        df['ends'] = [p * 2 * np.pi for p in percentages[1:]]
        df['diff'] = (df['ends'] - df['starts'])
        df['middle'] = df['starts']+np.abs(df['ends']-df['starts'])/2.
        df['cos'] = np.cos(df['middle']) * 0.9
        df['sin'] = np.sin(df['middle']) * 0.9

        df['text_size'] = '8pt'

        df['textdisplayed'] = df['where'].str.pad(36, side = "left")
        df['textdisplayed2'] =  ['      '+str(round(100*i,1))+'%' for i in df['percentage']]
        #df.loc[df['diff'] <= np.pi/20,'textdisplayed']=''
        #df.loc[df['diff'] <= np.pi/20,'textdisplayed2']=''
        return df

    @deco_bokeh
    @decodateslider
    def bokeh_pie(self, **kwargs):
        '''
            -----------------
            Create a pie chart according to arguments.
            See help(bokeh_pie).
            Keyword arguments
            -----------------
            - pyvoafiltered : A DataFrame with a Pypyvoa.struture is mandatory
            |location|date|Variable desired|daily|cumul|weekly|code|clustername|rolloverdisplay|
            - which = if None take second element could be a list
            - plot_heigh= Width_Height_Default[1]
            - graph_width = Width_Height_Default[0]
            - title = None
            - copyright = default
            - mode = mouse
            - dateslider = None if True
                    - orientation = horizontal
        '''
        columndatasrc = kwargs.get('columndatasrc')  # doit être ColumnDataSource
        fig = kwargs.get('bokeh_figure_linear')
        controls = kwargs.get('controls', None)
        dateslider = kwargs.get('dateslider')
        mode = kwargs.get('mode')

        # taille et apparence
        fig.height = 450
        fig.width = 450
        fig.x_range = Range1d(-1.1, 1.1)
        fig.y_range = Range1d(-1.1, 1.1)

        for ax in fig.axis:
            ax.visible = False

        fig.xgrid.grid_line_color = None
        fig.ygrid.grid_line_color = None

        fig.wedge(
            x=0, y=0, radius=1.0, line_color='#E8E8E8',
            start_angle=cumsum('angle', include_zero=True),
            end_angle=cumsum('angle'),
            fill_color='colors',
            legend_field='where',
            source=columndatasrc
        )
        fig.legend.visible = False

        labels = LabelSet(
            x=0, y=0,
            text='textdisplayed',
            angle=cumsum('angle', include_zero=True),
            text_font_size="10pt",
            source=columndatasrc
        )

        labels2 = LabelSet(
            x=0, y=0,
            text='textdisplayed2',
            angle=cumsum('angle', include_zero=True),
            text_font_size="8pt",
            source=columndatasrc
        )

        cases_custom = visu_bokeh().rollerJS()
        hover_tool = HoverTool(
            tooltips=[('where', '@where'), ('cases', '@right{0,0.0}')],
            formatters={'where': 'printf', '@{cases}': cases_custom},
            mode=mode, point_policy="snap_to_data"
        )
        fig.add_tools(hover_tool)

        fig.add_layout(labels)
        fig.add_layout(labels2)
        fig = Row(bokeh_figure,kwargs['watermark'])
        if dateslider:
            layout = column(controls, fig)
            return layout
        return fig

    @deco_bokeh
    @decodateslider
    def bokeh_map(self,**kwargs):
        input = kwargs.get('input')
        geocolumndatasrc = kwargs.get('geocolumndatasrc')
        which = kwargs.get('which')
        color_mapper = kwargs['color_mapper']
        bokeh_figure = kwargs['bokeh_figure_map']
        tile = kwargs.get('tile')
        if kwargs['typeofmap']!='dense':
            tile = visu_bokeh.convert_tile(tile, 'bokeh')
            wmt = WMTSTileSource(url = tile)
            bokeh_figure.add_tile(wmt, retina=True)

        logo = kwargs['logo']
        logo_url = visu_bokeh.pyvoalogo(logo)

        bokeh_figure.image_url(
            url=[logo_url],
            x=0.25*bokeh_figure.width,
            y=0.25*bokeh_figure.height,
            w=bokeh_figure.width, w_units="screen",
            h=bokeh_figure.height, h_units="screen",
            anchor="center",
            alpha=0.05
        )

        dateslider = kwargs.get('dateslider')
        controls = kwargs.get('controls', None)

        min_col, max_col = visu_bokeh().min_max_range(np.nanmin(input[which]), np.nanmax(input[which]))

        invViridis256 = Viridis256[::-1]
        color_bar = ColorBar(color_mapper=color_mapper, label_standoff=4, bar_line_cap='round',
                             border_line_color=None, location=(0, 0), orientation='horizontal', ticker=BasicTicker())
        color_bar.formatter = BasicTickFormatter(use_scientific=True, precision=1, power_limit_low=int(max_col))

        bokeh_figure.add_layout(color_bar, 'below')
        bokeh_figure.xaxis.visible = False
        bokeh_figure.yaxis.visible = False
        bokeh_figure.xgrid.grid_line_color = None
        bokeh_figure.ygrid.grid_line_color = None

        bokeh_figure.patches('xs', 'ys', source = geocolumndatasrc,
        fill_color = {'field': which, 'transform': color_mapper},
        line_color = 'black', line_width = 0.25)

        tooltips = f"""
                    <b>location: @where<br>
                    cases: @cases </b>
                    """

        bokeh_figure.add_tools(HoverTool(tooltips = tooltips,
        formatters = {'where': 'printf', '@right': 'printf',})),

        bokeh_figure = Row(bokeh_figure,kwargs['watermark'])
        if dateslider:
             layout = column(controls, bokeh_figure)
             return layout
        return bokeh_figure

    @staticmethod
    def bokeh_savefig(fig,name):
        from bokeh.io import export_png
        export_png(fig, filename = name)

    @staticmethod
    def get_polycoords(geopandasrow):
        """
        Take a row of a geopandas as an input (i.e : for index, row in geopdwd.iterrows():...)
            and returns a tuple (if the geometry is a Polygon) or a list (if the geometry is a multipolygon)
            of an exterior.coords
        """
        geometry = geopandasrow['geometry']
        all = []
        if geometry.type == 'Polygon':
            return list(geometry.exterior.coords)
        if geometry.type == 'MultiPolygon':
            for ea in geometry.geoms:
                all.append(list(ea.exterior.coords))
        return all

    @staticmethod
    def convertmercator(gdf):
        '''
        trick found by dadoun to solve this problem
        see https://discourse.bokeh.org/t/bokeh-tile-antimeridian-problem/6978
        '''
        rows = []

        for idx, row in gdf.iterrows():
            new_poly = []

            # Convertir les polygones / multipolygones
            if row["geometry"]:
                for pt in visu_bokeh().get_polycoords(row):
                    if isinstance(pt, tuple):
                        # Un point = tuple (lon, lat)
                        new_poly.append(visu_bokeh().wgs84_to_web_mercator(pt))
                    elif isinstance(pt, list):
                        # Liste de points = ring de polygone
                        shifted = [visu_bokeh().wgs84_to_web_mercator(p) for p in pt]
                        new_poly.append(sg.Polygon(shifted))
                    else:
                        raise TypeError("Unknown geometry element type")

                # Construire la géométrie finale
                if isinstance(new_poly[0], tuple):
                    geom = sg.Polygon(new_poly)
                else:
                    geom = sg.MultiPolygon(new_poly)

                # Copier toutes les colonnes d’origine
                new_row = row.copy()
                new_row["geometry"] = geom
                rows.append(new_row)

        # Reconstruire un GeoDataFrame complet
        new_gdf = gpd.GeoDataFrame(rows, crs="epsg:3857")
        return new_gdf

    @staticmethod
    def wgs84_to_web_mercator(tuple_xy):
        """
        Take a tuple (longitude,latitude) from a coordinate reference system crs=EPSG:4326
         and converts it to a  longitude/latitude tuple from to Web Mercator format
        """
        k = 6378137
        x = tuple_xy[0] * (k * np.pi / 180.0)
        if tuple_xy[1] == -90:
            lat = -89.99
        else:
            lat = tuple_xy[1]
        y = np.log(np.tan((90 + lat) * np.pi / 360.0)) * k
        return x, y

    @staticmethod
    def convert_tile(tilename, which = 'bokeh'):
        ''' Return tiles url according to folium or bokeh resquested'''
        tile = 'openstreet'
        if tilename == 'openstreet':
            if which == 'folium':
                tile = r'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
            else:
                tile = r'http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png'
        elif tilename == 'positron':
            #print('Problem with positron tile (huge http resquest need to check), esri is then used ...')
            #tile = r'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}.png'
            tile = 'https://tiles.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'
        elif tilename == 'esri':
            tile = r'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}.png'
        elif tilename == 'stamen':
            tile = r'http://tile.stamen.com/toner/{z}/{x}/{y}.png'
        else:
            print('Don\'t know you tile ... take default one: ')
        return tile
