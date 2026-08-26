
"""The bokeh visualisation backend.

The most complete of the three backends: the only one offering the ``compare``
and ``spiral`` plots and the date slider, alongside the plots, histograms and
maps the others share. Figures are returned as bokeh objects.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
"""
import base64
import bisect
import itertools
import json
from functools import wraps
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh import events
from bokeh.io import export_png, output_notebook
from bokeh.layouts import column, row
from bokeh.models import (
    BasicTicker,
    BasicTickFormatter,
    ColorBar,
    ColumnDataSource,
    CrosshairTool,
    CustomJS,
    CustomJSHover,
    CustomJSTickFormatter,
    DatetimeTickFormatter,
    Div,
    GeoJSONDataSource,
    HoverTool,
    LabelSet,
    Legend,
    LegendItem,
    LinearColorMapper,
    PrintfTickFormatter,
    Range1d,
    Row,
    Select,
    Toggle,
    WMTSTileSource,
)
from bokeh.models.layouts import TabPanel, Tabs
from bokeh.palettes import Category10, Category20, Viridis256
from bokeh.plotting import figure
from bokeh.transform import cumsum

from pyvoa.kwargs_options import InputOption
from pyvoa.tools import PyvoaError, min_max_range, verb


def safe_output_notebook():
    """Enable bokeh's notebook output, but only inside a notebook.

    Calling output_notebook() from a plain interpreter emits a warning and
    achieves nothing, so the environment is detected first and the failure
    reported through verb() rather than raised.
    """
    try:
        from IPython import get_ipython
        ipy = get_ipython()
        if ipy is not None and 'IPKernelApp' in ipy.config:
            output_notebook()
    except Exception as e:
        verb('Not running inside a notebook, bokeh output_notebook() skipped: '+str(e))
safe_output_notebook()

#output_notebook(hide_banner=True)



class visu_bokeh:
    """The bokeh backend, drawing interactive charts.

    The most complete of the three: it is the only one offering the
    'compare' and 'spiral' plots and the date slider, alongside the plots,
    histograms and maps the others share. Figures are returned as bokeh
    objects and shown in the notebook by front.
    """

    def __init__(self,):
        """Set the colour cycles and the default figure size.

        Category20 gives the twenty colours locations are cycled through, and
        Category10 the five used where fewer are needed.
        """
        self.av = InputOption()
        self.lcolors = Category20[20]
        self.scolors = Category10[5]
        self.figure_height = 400
        self.figure_width = 490
        self.listfigs = None

    @staticmethod
    def rollerJS():
        """Return the hover formatter shared by the bokeh charts.

        Reads pyvoa/js/rollover_callback.js and wraps it in a CustomJSHover, so
        that the tooltip formatting lives in a javascript file rather than in a
        string here.

        Returns
        -------
        CustomJSHover
            the formatter.
        """
        from pathlib import Path
        jsfile = Path(__file__).parent / "js/rollover_callback.js"
        return CustomJSHover(code=jsfile.read_text(encoding="utf-8"))

    @staticmethod
    def pyvoalogo(logo):
        """Read a logo file and return it as a data: URL.

        Embedding the image in the document rather than linking it keeps a
        saved chart self-contained.

        Parameters
        ----------
        logo : str
            path to the png.

        Returns
        -------
        str
            a 'data:image/png;base64,...' URL.
        """
        with open(logo, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode("utf-8")
        url = f"data:image/png;base64,{b64}"
        return url

    def deco_bokeh(func):
        """Decorate building the bokeh figure a chart is drawn on.

        Gives each location a stable colour from the Category20 cycle, then
        creates the figure, its title and the logo watermark, and passes them
        on to the drawing method.
        """
        @wraps(func)
        def innerdeco_bokeh(self,**kwargs):
            """Assign the location colours, build the figure, then draw."""
            input = kwargs.get('input')
            unique_where = input['where'].unique()
            color_map = {w: self.lcolors[i % 20] for i, w in enumerate(unique_where)}
            input['colors'] = input['where'].map(color_map)
            kwargs['input'] = input
            logo = kwargs['logo']
            kwargs['which']
            title = kwargs['title']
            width  = kwargs.get('width', self.figure_width)
            height = kwargs.get('height',self.figure_height)
            input = kwargs['input']

            dicfig = {}
            dicfig['bokeh_figure_linear']      = figure(x_axis_type='linear', y_axis_type='linear', width=width, height=height)
            dicfig['bokeh_figure_log']         = figure(x_axis_type='log', y_axis_type='linear', width=width, height=height)
            dicfig['bokeh_figure_loglog']      = figure(x_axis_type='log', y_axis_type='log', width=width, height=height)
            dicfig['bokeh_figure_map']         = figure(x_axis_type='mercator', y_axis_type='mercator',width=350, height=350, match_aspect=True)
            dicfig['bokeh_figure_linear_date'] = figure(x_axis_type='datetime', y_axis_type='linear', width=width, height=height)
            dicfig['bokeh_figure_log_date']    = figure(x_axis_type='datetime', y_axis_type='log', width=width, height=height)
            dicfig['bokeh_figure_yearly']      = figure(x_axis_type='linear', y_axis_type='linear',  width=width, height=height)
            dicfig['bokeh_figure_yearly_log']  = figure(x_axis_type='linear', y_axis_type='log',  width=width, height=height)

            logo_url = visu_bokeh.pyvoalogo(logo)
            for key, fig in dicfig.items():
                fig.title = title
                #if (key == "bokeh_figure_map" or func.__name__ == 'bokeh_horizonhisto' or func.__name__ == 'bokeh_pie') and kwargs['dateslider']:
                #    fig.title = title
                #else:
                #    fig.title = title + str(kwargs['kwargsuser']['when'])
                dicfig[key]=fig
            d = Div(text = '<div style="position: absolute; left:-300px; top:100px"><img src=' + logo_url + ' style="width:100px; height:40px; opacity: 0.1"></div>')
            #d = Div(text = '<div style="position: absolute; left:-400px; top:100px"> <p style="background-image: url("+img_girl.jpg+");"> </div>')
            kwargs['watermark'] = d
            kwargs = { **kwargs, **dicfig }
            return func(self, **kwargs)
        return innerdeco_bokeh

    @staticmethod
    def geosource_bounds(geosource):
        """Return the bounding box of every geometry in a GeoJSON source.

        Parameters
        ----------
        geosource : GeoJSONDataSource
            the source to measure.

        Returns
        -------
        tuple
            (x_min, y_min, x_max, y_max).

        Raises
        ------
        ValueError
            if the source holds no usable geometry.
        """
        from shapely.geometry import shape

        data = json.loads(geosource.geojson)
        xs, ys = [], []
        for feature in data["features"]:
            geom_json = feature.get("geometry")
            if geom_json is None:
                continue
            geom = shape(geom_json)
            if geom.is_empty:
                continue
            x_min, y_min, x_max, y_max = geom.bounds
            xs.extend([x_min, x_max])
            ys.extend([y_min, y_max])
        if not xs:
            raise ValueError("No valid geometries found in GeoJSONDataSource")
        return min(xs), min(ys), max(xs), max(ys)

    @staticmethod
    def bokeh_legend(bkfigure):
        """Make a double-click on the figure hide and show the legend.

        Parameters
        ----------
        bkfigure
            the bokeh figure to attach the callback to.
        """
        from bokeh.models import CustomJS
        toggle_legend_js = CustomJS(args={'leg': bkfigure.legend[0]},
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
        """Return the figures built by the last call."""
        return  self.listfigs

    def set_listfigures(self,fig):
            """Record the figures built, wrapping a single one in a list."""
            if not isinstance(fig,list):
                fig = [fig]
            self.listfigs = fig

    def bokeh_plot(func):
        """Decorate shortening the location labels before a chart is drawn.

        Replaces each location by its display name, and drops the geometry
        column, which the non-map charts have no use for.
        """
        @wraps(func)
        def inner_bokeh_plot(self, **kwargs):
            """Shorten the location labels and drop the geometry, then draw."""
            input=kwargs['input']
            kwargs['maxlettersdisplay']
            input['where'] = [kwargs['dicodisplayloc'][w] for w in input['where']]
            if 'geometry' in list(input.columns):
                kwargs['input'] = input.drop(columns='geometry')
            return func(self, **kwargs)
        return  inner_bokeh_plot

    ''' PLOT VERSUS '''
    @deco_bokeh
    @bokeh_plot
    def bokeh_versus_plot(self,**kwargs):
        """Create a versus plot according to arguments.

        Parameters
        ----------
        input : pd.DataFrame
            If None, take the first element. A DataFrame with a pyvoa structure is
            mandatory: ``|location|date|Variable desired|daily|cumul|weekly|code|
            clustername|rolloverdisplay|``.
        which : list
            If None, take the second element. It must be a list of dimension 2, and
            both variables must be present in the DataFrame considered.
        plot_heigh : int
            Default is Width_Height_Default[1].
        graph_width : int
            Default is Width_Height_Default[0].
        title : str
            Default is None.
        copyright : str
            Default is the pyvoa copyright.
        mode : str
            Default is 'mouse'.
        dateslider : bool
            Default is None. If True, orientation is horizontal.
        when : str
            Default is the min and the max of the input DataFrame. Dates are given
            under the format dd/mm/yyyy: ``[dd/mm/yyyy : dd/mm/yyyy]`` for a range,
            ``[:dd/mm/yyyy]`` from the min date up to, ``[dd/mm/yyyy:]`` up to the
            max date.
        """
        input = kwargs.get('input')
        which = kwargs.get('which')
        # copyright = kwargs.get('copyright')
        mode = kwargs.get('mode')
        # bokeh_figure = kwargs.get('bokeh_figure')
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
        for axis_type in self.av.d_graphicsinput_args['scale']:
            fig = dbokeh_figure[axis_type]
            dicof['x_axis_label'] = which[0]
            dicof['y_axis_label'] = which[1]
            dicof['y_axis_type' ] = axis_type
            fig.xaxis.axis_label = which[0]
            fig.yaxis.axis_label = which[1]
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
        """Create a date plot according to arguments.

        Parameters
        ----------
        input : pd.DataFrame
            If None, take the first element. A DataFrame with a pyvoa structure is
            mandatory: ``|location|date|Variable desired|daily|cumul|weekly|code|
            clustername|rolloverdisplay|``.
        which : list
            If None, take the second element. It could be a list.
        plot_heigh : int
            Default is Width_Height_Default[1].
        graph_width : int
            Default is Width_Height_Default[0].
        title : str
            Default is None.
        copyright : str
            Default is the pyvoa copyright.
        mode : str
            Default is 'mouse'.
        guideline : bool
            Default is False.
        dateslider : bool
            Default is None. If True, orientation is horizontal.
        when : str
            Default is the min and the max of the input DataFrame. Dates are given
            under the format dd/mm/yyyy: ``[dd/mm/yyyy : dd/mm/yyyy]`` for a range,
            ``[:dd/mm/yyyy]`` from the min date up to, ``[dd/mm/yyyy:]`` up to the
            max date.
        """
        input = kwargs.get('input')

        which = kwargs.get('which')
        mode = kwargs.get('mode')
        guideline = kwargs.get('guideline')
        panels = []
        listfigs = []
        visu_bokeh().rollerJS()
        dbokeh_figure = {
            'linear': kwargs.get('bokeh_figure_linear_date'),
            'log': kwargs.get('bokeh_figure_log_date')
        }
        dicof={'title':kwargs.get('title')}
        legend = kwargs.get('legend', None)

        ay_type = kwargs.get('scale', None)
        self.av.d_graphicsinput_args['scale']

        if ay_type is None:
            ay_type = [i for i in self.av.d_graphicsinput_args['scale'] if i]
        if not isinstance(ay_type,list):
            ay_type = [ay_type]

        for axis_type in ay_type:
            fig = dbokeh_figure[axis_type]
            dicof['x_axis_type'] = 'datetime'
            dicof['y_axis_type'] = axis_type
            # i = 0
            r_list=[]
            maxi=-1000
            line_style = ['solid', 'dashed', 'dotted', 'dotdash','dashdot']
            maxi, mini=0, 0
            tooltips=[]
            colors = list(input['colors'].unique())
            for idx,val in enumerate(which):
                fig.yaxis.axis_label = val
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
                    tooltips.append([('where', '@where'), ('date', '@date{%F}'), (r.name, '@$name{0,0.0}')])
                    '''
                    if mini <0.01:
                        tooltips.append([('where', '@where'), ('date', '@date{%F}'), (r.name, '@$name')])
                    else:
                        tooltips.append([('where', '@where'), ('date', '@date{%F}'), (r.name, '@$name{0,0.0}')])
                    if isinstance(tooltips,tuple):
                        tooltips = tooltips[0]
                    '''
                # i += 1
            visu_bokeh().rollerJS()

            for i,r in enumerate(r_list):
                label = r.name
                tt = tooltips[i]
                formatters = {'where': 'printf', '@date': 'datetime', '@name':  'numeral'}
                hover=HoverTool(tooltips = tt, formatters = formatters, point_policy = "snap_to_data", mode = mode, renderers=[r])  # ,PanTool())
                fig.add_tools(hover)

                if guideline:
                    cross= CrosshairTool()
                    fig.add_tools(cross)

            if axis_type == 'linear' and maxi < 1e4 :
                fig.yaxis.formatter = BasicTickFormatter(use_scientific=False)
            #fig.legend.title=", ".join(which)
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
        """Draw one location's series as an Archimedean spiral.

        Each year is one turn, the day of the year giving the angle, so that
        seasonality shows up as alignment between successive turns. The value
        is drawn as a ribbon whose width straddles the baseline. The 29th of
        February is dropped so that a day number means the same date every
        year.

        Parameters
        ----------
        **kwargs
            the drawing arguments, including 'input' (a single
            location) and 'which'.

        Raises
        ------
        PyvoaError
            if the selection holds more than one location.
        """
        input = kwargs.get('input')
        which = kwargs.get('which')
        dicof={'title':kwargs.get('title')}
        dicof['match_aspect']=True

        bokeh_figure = kwargs.get('bokeh_figure_linear')#(x_range=[-borne, borne], y_range=[-borne, borne], **dicof)
        bokeh_figure.xaxis.visible = False
        bokeh_figure.yaxis.visible = False

        if len(input['where'].unique()) > 1 :
            raise PyvoaError('Can only display spiral for ONE location. I took the first one:', input['where'][0])
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
        polar_norm = radius/input["r_baseline"].max()
        def polar(theta,r,norm=polar_norm):
            """Convert an angle and a radius to x, y, scaled to the figure."""
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

        pyvoa = ColumnDataSource(data={
        'x': x_base,
        'y': y_base,
        'date': input['date'],
        'cases': input['cases']
        })
        bokeh_figure.line( x = 'x', y = 'y', source = pyvoa, legend_label = which[0] +', '+ input['where'][0],
                        line_width = 3, line_color = 'blue')
        circle = bokeh_figure.scatter(
                x='x',
                y='y',
                size=2,
                color='red',
                marker='circle',
                source=pyvoa
            )

        cases_custom = visu_bokeh().rollerJS()
        hover_tool = HoverTool(tooltips=[('Cases', '@cases{0,0}'), ('date', '@date{%F}')],
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
        """Create a date plot with a scrolling menu of locations.

        Requires more than two locations.

        Parameters
        ----------
        input : pd.DataFrame
            If None, take the first element. A DataFrame with a pyvoa structure is
            mandatory: ``|location|date|Variable desired|daily|cumul|weekly|code|
            clustername|rolloverdisplay|``.
        which : list
            If None, take the second element. It could be a list.
        plot_heigh : int
            Default is Width_Height_Default[1].
        graph_width : int
            Default is Width_Height_Default[0].
        title : str
            Default is None.
        copyright : str
            Default is the pyvoa copyright.
        mode : str
            Default is 'mouse'.
        guideline : bool
            Default is False.
        dateslider : bool
            Default is None. If True, orientation is horizontal.
        when : str
            Default is the min and the max of the input DataFrame. Dates are given
            under the format dd/mm/yyyy: ``[dd/mm/yyyy : dd/mm/yyyy]`` for a range,
            ``[:dd/mm/yyyy]`` from the min date up to, ``[dd/mm/yyyy:]`` up to the
            max date.
        """
        input = kwargs.get('input')
        which= kwargs.get('which')
        guideline = kwargs.get('guideline',self.av.d_graphicsinput_args['guideline'][0])
        # mode = kwargs.get('mode',self.av.d_graphicsinput_args['mode'][0])
        if isinstance(which,list):
            which=which[0]

        dbokeh_figure = {
            'linear': kwargs.get('bokeh_figure_linear_date'),
            'log': kwargs.get('bokeh_figure_log_date')
        }

        uniqloc = list(input['where'].unique())
        uniqloc.sort()
        if 'where' in input.columns and len(uniqloc) < 2:
            raise PyvoaError('What do you want me to do ? You have selected, only one country.'
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

        visu_bokeh().rollerJS()
        #hover_tool = HoverTool(tooltips=[(which, '@which{0,0.0}'), ('date', '@date{%F}')],
        #                       formatters={which: 'printf', '@{which}': cases_custom, '@date': 'datetime'},
        #                       mode = mode, point_policy="snap_to_data")  # ,PanTool())

        panels = []
        for axis_type in self.av.d_graphicsinput_args['scale']:
            fig = dbokeh_figure[axis_type]
            fig.yaxis[0].formatter = PrintfTickFormatter(format = "%4.2e")
            fig.xaxis.formatter = DatetimeTickFormatter(
                days = "%d/%m/%y", months = "%d/%m/%y", years = "%b %Y")

        #    bokeh_figure.add_tools(hover_tool)
            if guideline:
                cross= CrosshairTool()
                fig.add_tools(cross)
            def add_line(pyvoa, options, init, color, fig=fig):
                """Add one selectable series to the figure.

                Builds the Select widget and the line it drives, wired together by a
                javascript callback so that changing the selection swaps the data
                without a round trip to python.

                Returns
                -------
                tuple
                    (the Select widget, its legend item).
                """
                s = Select(options = options, value = init)
                r = fig.line(x = 'date', y = 'cases', source = pyvoa, line_width = 3, line_color = color)
                li = LegendItem(label = init, renderers = [r])
                s.js_on_change('value', CustomJS(args={'s0': source, 's1': pyvoa, 'li': li},
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
        return tabs

    ''' YEARLY PLOT '''
    @deco_bokeh
    @bokeh_plot
    def bokeh_yearly_plot(self,**kwargs):
        """Create a yearly plot according to arguments.

        Parameters
        ----------
        input : pd.DataFrame
            If None, take the first element. A DataFrame with a pyvoa structure is
            mandatory: ``|location|date|Variable desired|daily|cumul|weekly|code|
            clustername|rolloverdisplay|``.
        which : list
            If None, take the second element. It could be a list.
        plot_heigh : int
            Default is Width_Height_Default[1].
        graph_width : int
            Default is Width_Height_Default[0].
        title : str
            Default is None.
        copyright : str
            Default is the pyvoa copyright.
        mode : str
            Default is 'mouse'.
        guideline : bool
            Default is False.
        dateslider : bool
            Default is None. If True, orientation is horizontal.
        when : str
            Default is the min and the max of the input DataFrame. Dates are given
            under the format dd/mm/yyyy: ``[dd/mm/yyyy : dd/mm/yyyy]`` for a range,
            ``[:dd/mm/yyyy]`` from the min date up to, ``[dd/mm/yyyy:]`` up to the
            max date.
        """
        input = kwargs['input']
        which = kwargs['which']
        guideline = kwargs.get('guideline',self.av.d_graphicsinput_args['guideline'][0])
        mode = kwargs.get('mode',self.av.d_graphicsinput_args['mode'][0])
        dbokeh_figure = {
            'linear': kwargs.get('bokeh_figure_yearly'),
            'log': kwargs.get('bokeh_figure_yearly_log')
        }

        input = input.loc[input['where'] == input['where'][0]].copy()

        panels = []
        listfigs = []
        visu_bokeh().rollerJS()
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)
        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)
        allyears = list(input.allyears.unique())

        for axis_type in self.av.d_graphicsinput_args['scale']:

            fig = dbokeh_figure[axis_type]
            input['cases']=input[which]
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

            tooltips = [('where', '@rolloverdisplay'), ('date', '@date{%F}'), ('Cases', '@cases{0,0}')]
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

            # minyear = input.date.min().year

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
    def decodateslider(func):
        """Decorate adding a date slider to a chart.

        Wires a slider to the figure so the drawn date can be moved through the
        series. Histograms are not covered: the slider is declined there, with
        a message. Bokeh only; front refuses 'dateslider' for other backends.
        """
        @wraps(func)
        def inner_decodateslider(self, **kwargs):
            """Attach the slider to the figure, then draw."""
            input = kwargs['input']
            which  = kwargs.get('which')
            if isinstance(which,list):
                which = which[0]
                kwargs['which'] = which

            bokeh_figure_linear = kwargs.get('bokeh_figure_linear')
            bokeh_figure_log = kwargs.get('bokeh_figure_log')
            bokeh_figure_map = kwargs.get('bokeh_figure_map')

            dateslider = kwargs.get('dateslider')
            if func.__name__ == 'bokeh_histo' and dateslider:
                print('dateslider not implemented in this current version ...')
                dateslider = False

            maxcountrydisplay = kwargs['maxcountrydisplay']

            lhist = ['bokeh_pie','bokeh_horizonhisto']

            ymax = self.figure_height

            if func.__name__ in lhist:
                input = self.addcolumnshisto(input,which,maxcountrydisplay)
                yrange = Range1d(min(input['bottom']), max(input['top']))

            input_uniquecountries = input.loc[input.date==input.date.max()].drop(columns=['date']).reset_index(drop=True)
            input_uniquecountries['right'] = len(input_uniquecountries.index)*[0.]

            if func.__name__ == 'bokeh_map':
                if func.__name__ in lhist:
                    input_uniquecountries = input_uniquecountries.head(maxcountrydisplay)
                input_uniquecountries['cases']=input_uniquecountries[which]
                geocolumndatasrc = GeoJSONDataSource(geojson = input_uniquecountries.to_json())
                input_dates = input.drop(columns='geometry').copy()
            else:
                input_dates = input.copy()

            invViridis256 = Viridis256[::-1]
            color_mapper = LinearColorMapper(palette = invViridis256, low=0, high=max(input_dates[which]), nan_color='#ffffff')
            ColorBar(color_mapper=color_mapper, label_standoff=4, bar_line_cap='round',\
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

                from bokeh.models import CustomJS, Div, Slider
                slider = Slider(start=0, end=max(0, len(frames)-1), value=0, step=1, title="Date index", width=300)
                date_display = Div(text=f"<b>{unique_dates[0]}</b>", width=300)

                jsfile = Path(__file__).parent / "js/slider_callback.js"
                with open(jsfile) as f:
                    slider_code = f.read()

                slider_callback = CustomJS(
                        args={
                            'frames': frames,
                            'sourcemap': geocolumndatasrc if func.__name__ == 'bokeh_map' else columndatasrc,
                            'sourcehisto': columndatasrc,
                            'which': which,
                            'dates': unique_dates,
                            'div': date_display,
                            'maxcountrydisplay': maxcountrydisplay,
                            'ylabellinear': bokeh_figure_linear.yaxis[0],
                            'ylabellog': bokeh_figure_log.yaxis[0],
                            'ymax': ymax,
                            'color_mapperjs': color_mapper
                        },
                        code=slider_code)

                slider.js_on_change('value', slider_callback)
                toggl = Toggle(label='► Play', active=False, button_type="success", height=30, width=70)
                # CustomJS pour démarrer/arrêter l'animation
                jsfile = Path(__file__).parent / "js/animation_callback.js"
                with open(jsfile) as f:
                    animation_code = f.read()
                toggle_callback = CustomJS(args={'slider': slider, 'frames': frames}, code=animation_code)
                toggl.js_on_change('active', toggle_callback)

                from bokeh.models import Div
                date_display = Div(text=f"<b>{unique_dates[-1]}</b>", width=300)
                # Mettre à jour le Div depuis le slider (JS)
                slider_date_div_cb = CustomJS(args={'div': date_display, 'dates': unique_dates},
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

            if func.__name__ == 'bokeh_map':
                xmin, ymin, xmax, ymax = visu_bokeh().geosource_bounds(geocolumndatasrc)
                gdf = input.to_crs(epsg=3857)
                pad_x,pad_y=0.,0.
                if len(gdf) > 10:
                    pad_x = (xmax - xmin) * 0.05
                    pad_y = (ymax - ymin) * 0.05
                    bokeh_figure_map.x_range.bounds = (xmin - pad_x, xmax + pad_x)
                    bokeh_figure_map.y_range.bounds = (ymin - pad_y, ymax + pad_y)
                    ratio = (ymax + pad_y - (ymin - pad_y)) / (xmax + pad_x - (xmin - pad_x))
                    if ratio < 1:  # Wider than tall
                        bokeh_figure_map.width = int(bokeh_figure_map.height / ratio)
                    else:  # Taller than wide
                        bokeh_figure_map.height = int(bokeh_figure_map.width * ratio)
                else:
                    zoom = 2
                    dx = (xmax - xmin)
                    dy = (ymax - ymin)
                    padding_x = dx * zoom
                    padding_y = dy * zoom
                    xmin -= padding_x
                    xmax += padding_x
                    ymin -= padding_y
                    ymax += padding_y

                bokeh_figure_map.x_range.start = xmin - pad_x
                bokeh_figure_map.x_range.end   = xmax + pad_x
                bokeh_figure_map.y_range.start = ymin - pad_y
                bokeh_figure_map.y_range.end   = ymax + pad_y

                _min_col, _max_col = min_max_range(np.nanmin(input_dates[which]),np.nanmax(input_dates[which]))

                bokeh_figure_map.patches('xs', 'ys', source = geocolumndatasrc,
                                fill_color = {'field': 'cases', 'transform': color_mapper},
                                line_color = 'black', line_width = 0.25, fill_alpha = 1)
                kwargs['geocolumndatasrc'] = geocolumndatasrc

            if func.__name__ in lhist:
                kwargs['yrange']=yrange

            kwargs['columndatasrc'] = columndatasrc
            kwargs['color_mapper'] = color_mapper
            kwargs['input'] = input
            return func(self, **kwargs)
        return inner_decodateslider

    @deco_bokeh
    def bokeh_histo(self, **kwargs):
        """Create a 1D histogram by value according to arguments.

        Parameters
        ----------
        input : pd.DataFrame
            A DataFrame with a pyvoa structure is
            mandatory: ``|location|date|Variable desired|daily|cumul|weekly|code|
            clustername|rolloverdisplay|``.
        which : list
            If None, take the second element. It could be a list.
        plot_heigh : int
            Default is Width_Height_Default[1].
        graph_width : int
            Default is Width_Height_Default[0].
        title : str
            Default is None.
        copyright : str
            Default is the pyvoa copyright.
        when : str
            Default is the min and the max of the input DataFrame. Dates are given
            under the format dd/mm/yyyy: ``[dd/mm/yyyy : dd/mm/yyyy]`` for a range,
            ``[:dd/mm/yyyy]`` from the min date up to, ``[dd/mm/yyyy:]`` up to the
            max date.
        """
        input = kwargs.get('input')
        bins = kwargs.get('bins', self.av.d_graphicsinput_args['bins'])
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

        # Dead assignment kept for the record: the bin width is implied by the
        # linspace below, which is what the histogram actually uses.
        # delta = (max_val - min_val) / bins

        interval = np.linspace(
            min_val,
            max_val,
            bins + 1
        )

        contributors = {i: [] for i in range(bins)}

        for i in range(len(input)):
            value = input.iloc[i][which]

            rank = bisect.bisect_right(interval, value) - 1

            if rank < 0:
                rank = 0
            elif rank >= bins:
                rank = bins - 1

            contributors[rank].append(
                input.iloc[i]['where']
            )

        lcolors = iter(self.lcolors)

        contributors = dict(sorted(contributors.items()))

        frame_histo = pd.DataFrame({
                'left': interval[:-1],
                'right': interval[1:],
                'middle_bin': [
                    format((i + j) / 2, ".1f")
                    for i, j in itertools.pairwise(interval)
                ],
                'top': [
                    len(contributors[i])
                    for i in range(bins)
                ],
                'contributors': [
                    ', '.join(contributors[i])
                    for i in range(bins)
                ],
                'colors': [
                    next(lcolors)
                    for _ in range(bins)
                ]
            })
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
        _x_axis_type, y_axis_type, axis_type_title = 3 * ['linear']
        axis_t = ["linear", "loglog"]

        for axis_type in axis_t:
            fig = dfigures[axis_type]
            fig.yaxis.axis_label = 'frequency'
            fig.xaxis.axis_label = which
            if axis_type == 'loglog':
                _x_axis_type, y_axis_type = 'log', 'log'
                axis_type_title = 'loglog'

            fig.add_tools(hover_tool)
            fig.x_range = Range1d(interval[0], interval[-1])
            fig.y_range = Range1d(0, 1.05 * frame_histo['top'].max())

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
        # input = kwargs.get('input')
        """Draw a horizontal bar chart, one bar per location.

        Bars are ranked by value and labelled with it. Only maxcountrydisplay
        locations are shown at a time, the rest reachable through the widget.

        Parameters
        ----------
        **kwargs
            the drawing arguments, including 'which', the column
            data source, and optionally 'dateslider'.

        Returns
        -------
        The bokeh figure.
        """
        which=kwargs['which']
        columndatasrc = kwargs.get('columndatasrc')
        # which = kwargs.get('which')

        # mode = kwargs.get('mode')
        dateslider = kwargs.get('dateslider')
        controls = kwargs.get('controls', None)
        title = kwargs['title']
        dbokeh_figure = {
            'linear': kwargs.get('bokeh_figure_linear'),
            'log': kwargs.get('bokeh_figure_log')
        }

        new_panels = []

        for axis_type in self.av.d_graphicsinput_args['scale']:
            fig = dbokeh_figure[axis_type]
            fig.y_range = kwargs['yrange']
            fig.xaxis.axis_label = which

            ytick_loc = [int(i) for i in columndatasrc.data['horihistotexty']]
            fig.yaxis[0].ticker = ytick_loc
            label_dict = dict(zip(ytick_loc,[x for x in columndatasrc.data['shortenwhere']]))

            #if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
            #    label_dict = {ytick_loc[0]:'sum all location'}

            fig.yaxis[0].major_label_overrides = label_dict


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
            '''
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
            '''
            visu_bokeh().rollerJS()
            hover_tool = HoverTool(
                tooltips=[('where', '@where'), ('cases', '@right{0,0}')]
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
        """Add the geometry columns a horizontal bar chart needs.

        Computes each bar's left, right, top and bottom edges, and the position
        and text of its label, so the chart can be drawn from plain rectangles.

        Parameters
        ----------
        mypd : pd.DataFrame
            one row per location.
        which : str
            the column holding the value.
        maxcountrydisplay : int
            how many bars fit on screen at once.

        Returns
        -------
        pd.DataFrame
            mypd with the drawing columns added.
        """
        ymax = self.figure_height
        mypd['left'] = mypd[which]
        mypd['right'] = mypd[which]
        def _fmt(v):
            """Format a bar label.

            Three significant digits for very large or very small values, two decimals
            otherwise.
            """
            fv = float(v)
            if fv == 0:
                return '0'
            if abs(fv) >= 1.e4 or (abs(fv) > 0 and abs(fv) < 0.01):
                return f'{fv:.3g}'
            return str(round(fv, 2))

        mypd['horihistotext'] = mypd['right'].apply(_fmt)
        mypd['horihistotext'] = [str(i) for i in mypd['horihistotext']]
        mypd['left'] = mypd['left'].apply(lambda x: min(x, 0))
        mypd['right'] = mypd['right'].apply(lambda x: max(x, 0))
        mypd['horihistotextx'] = mypd['right']
        indices = [i % maxcountrydisplay for i in range(len(mypd))]
        mypd['top'] = [ymax * (maxcountrydisplay - i) / maxcountrydisplay + 0.5 * ymax / maxcountrydisplay for i in indices]
        mypd['bottom'] = [ymax * (maxcountrydisplay - i) / maxcountrydisplay - 0.5 * ymax / maxcountrydisplay for i in indices]
        mypd['horihistotexty'] = mypd['bottom'] + 0.5*ymax/maxcountrydisplay
        mypd['horihistotextx'] = mypd['right']
        return mypd

    ''' PIE '''
    def addcolumnspie(self,df,column_name):
        """Add the angle columns a pie chart needs.

        Turns each value into its share of the total and into the start and end
        angles of its wedge.

        Parameters
        ----------
        df : pd.DataFrame
            one row per location.
        column_name : str
            the column holding the value.

        Returns
        -------
        pd.DataFrame
            df with 'percentage', 'angle', 'starts' and 'ends'.
        """
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
        """Create a pie chart according to arguments.

        Parameters
        ----------
        pyvoafiltered : pd.DataFrame
            A DataFrame with a pyvoa structure is
            mandatory: ``|location|date|Variable desired|daily|cumul|weekly|code|
            clustername|rolloverdisplay|``.
        which : list
            If None, take the second element. It could be a list.
        plot_heigh : int
            Default is Width_Height_Default[1].
        graph_width : int
            Default is Width_Height_Default[0].
        title : str
            Default is None.
        copyright : str
            Default is the pyvoa copyright.
        mode : str
            Default is 'mouse'.
        dateslider : bool
            Default is None. If True, orientation is horizontal.
        """
        columndatasrc = kwargs.get('columndatasrc')
        fig = kwargs.get('bokeh_figure_linear')
        controls = kwargs.get('controls', None)
        dateslider = kwargs.get('dateslider')
        mode = kwargs.get('mode')
        which=kwargs.get('which')

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
        from bokeh.models import Label
        labeltitre = Label(
            x=0.8, y=0.95,
            text=which,
            text_align="right",
            text_font_size="12px",
            text_font_style="bold",
            text_color="black"
        )

        cases_custom = visu_bokeh().rollerJS()
        hover_tool = HoverTool(
            tooltips=[('where', '@where'), ('cases', '@right{0,0}')],
            formatters={'where': 'printf', '@{cases}': cases_custom},
            mode=mode, point_policy="snap_to_data"
        )
        fig.add_tools(hover_tool)

        fig.add_layout(labels)
        fig.add_layout(labeltitre)
        #fig.add_layout(labels2)
        fig = Row(fig,kwargs['watermark'])
        if dateslider:
            layout = column(controls, fig)
            return layout
        return fig

    @deco_bokeh
    @decodateslider
    def bokeh_map(self,**kwargs):
        """Draw a choropleth map of one variable.

        Colours each location by its value and, unless the map is drawn dense,
        lays it over the background tiles named by 'tile'. The pyvoa logo is
        stamped in a corner.

        Parameters
        ----------
        **kwargs
            the drawing arguments, including the GeoJSON source, the
            colour mapper, 'which', 'typeofmap' and 'tile'.

        Returns
        -------
        The bokeh figure holding the map.
        """
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
            x=0.2*bokeh_figure.width,
            y=0.2*bokeh_figure.height,
            w=bokeh_figure.width, w_units="screen",
            h=bokeh_figure.height, h_units="screen",
            anchor="center",
            alpha=0.05,
            level='overlay'
        )

        dateslider = kwargs.get('dateslider')
        controls = kwargs.get('controls', None)

        _min_col, max_col = min_max_range(np.nanmin(input[which]), np.nanmax(input[which]))

        color_bar = ColorBar(title=which,color_mapper=color_mapper, label_standoff=4, bar_line_cap='round',
                             border_line_color=None, location=(0, 0), orientation='horizontal',
                             ticker=BasicTicker())
        color_bar.formatter = BasicTickFormatter(use_scientific=True, precision=1, power_limit_low=int(max_col))

        max_val = np.nanmax(input[which])

        if max_val > 0 and not np.isnan(max_val):
            exp = int(np.floor(np.log10(abs(max_val))))
            divisor = 10 ** exp
        else:
            exp = 0
            divisor = 1

        color_bar.formatter = CustomJSTickFormatter(
            args={'divisor': divisor, 'exp': exp},
            code="""
            const val = (tick / divisor).toFixed(1);
            return val + " ×10" + exp.toString().split('').map(d => '⁰¹²³⁴⁵⁶⁷⁸⁹'[d] || d).join('');
        """
        )
        bokeh_figure.add_layout(color_bar, 'below')
        bokeh_figure.xaxis.visible = False
        bokeh_figure.yaxis.visible = False
        bokeh_figure.xgrid.grid_line_color = None
        bokeh_figure.ygrid.grid_line_color = None
        bokeh_figure.patches('xs', 'ys', source = geocolumndatasrc,
        fill_color = {'field': which, 'transform': color_mapper},
        line_color = 'black', line_width = 0.25)

        bokeh_figure.add_tools(HoverTool(tooltips=[('location', '@where'), ('cases', '@cases{0,0}')]))

        #bokeh_figure = Row(bokeh_figure,kwargs['watermark'])
        if dateslider:
             layout = column(controls, bokeh_figure)
             return layout
        return bokeh_figure

    @staticmethod
    def bokeh_savefig(fig,name):
        """Write a bokeh figure to a png file.

        Parameters
        ----------
        fig
            the figure to export.
        name : str
            the destination file name.
        """
        export_png(fig, filename = name)

    @staticmethod
    def convert_tile(tilename, which = 'bokeh'):
        """Return tiles url according to folium or bokeh resquested."""
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
