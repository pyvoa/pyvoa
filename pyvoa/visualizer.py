"""Dispatch of chart requests to the visualisation backends.

``AllVisu`` holds the drawing settings that do not depend on the backend -- the
colour cycle, the logos, how many locations a chart shows and how long a name
may be -- then routes each request to matplotlib, bokeh or seaborn according to
``vis``, and to the routine matching ``typeofplot``, ``typeofhist`` or
``typeofmap``. The backends do not all offer the same charts.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
"""

import datetime as dt
from functools import wraps

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pyvoa.jsondb_parser import MetaInfo
from pyvoa.kwargs_options import InputOption
from pyvoa.tools import PyvoaError, PyvoaWarning, shorten_locations, verb

# The four imports below only probe whether an optional backend is installed;
# the backends themselves are imported lazily, hence the noqa on three of them.
# matplotlib needs none, being imported at the top of the module anyway (and a
# hard dependency through contextily), so its probe always succeeds.
try:
    import bokeh  # noqa: F401
    BOKEH_AVAILABLE = True
except ImportError:
    BOKEH_AVAILABLE = False

try:
    import matplotlib
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import seaborn  # noqa: F401
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

try:
    import folium  # noqa: F401
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

if MATPLOTLIB_AVAILABLE:
    from pyvoa.visu_matplotlib import visu_matplotlib

if SEABORN_AVAILABLE:
    from pyvoa.visu_seaborn import visu_seaborn

if BOKEH_AVAILABLE:
    from pyvoa.visu_bokeh import visu_bokeh

if FOLIUM_AVAILABLE:
    from pyvoa.visu_folium import visu_folium

import importlib.resources as pkg_resources

import pyvoa


class AllVisu:
    """Dispatcher routing a chart request to the backend that draws it.

    Every visualisation is implemented here or in one of the backend modules
    it delegates to.
    """

    def __init__(self, db_name = None, kindgeo = None):
        """Prepare the dispatcher for one database.

        Reads the geographic metadata of db_name -- its ISO3 code and its
        granularity -- unless the data is user supplied ('in-house data'),
        collects the chart methods the class exposes, and settles the drawing
        defaults: the colour cycle, how many locations a chart shows at most
        when ``maxcountrydisplayed`` is not given (12; see :meth:`maxcountry`),
        and the paths to the two logo files
        stamped on the figures. How long a location name may be before it is
        cut is not settled here: each chart reads ``maxlettersdisplayed`` from
        its keyword arguments.

        Parameters
        ----------
        db_name : str
            the database the charts will describe.
        kindgeo : gpd.GeoDataFrame
            the geometry to draw the locations with.
        """
        if kindgeo is None:
            pass
        else:
            self.kindgeo = kindgeo

        self.database_name = None
        verb("Init of AllVisu() with db=" + str(db_name))
        self.database_name = db_name
        if db_name != 'in-house data':
            self.currentmetadata = MetaInfo().getcurrentmetadata(db_name)
            self.code = self.currentmetadata['geoinfo']['iso3']
            self.granularity = self.currentmetadata['geoinfo']['granularity']
            self.namecountry = self.currentmetadata['geoinfo']['iso3']

        self.setchartsfunctions = [method for method in dir(AllVisu) if callable(getattr(AllVisu, method)) and method.startswith("pyvoa_") and not method.startswith("__")]
        self.geopan = gpd.GeoDataFrame()
        self.pyvoa_geopandas = False
        self.geom = []
        self.listfigs = []
        self.dchartkargs = {}
        self.dvisukargs = {}
        self.uptitle, self.subtitle = ' ',' '
        self.maxcountrydisplayed  = InputOption().d_graphicsinput_args['maxcountrydisplayed']
        self.colors = plt.cm.tab20(np.linspace(0, 1,self.maxcountrydisplayed))

        pathmetadb = str(pkg_resources.files(pyvoa).joinpath("data"))
        self.logo = pathmetadb+'/logo-pyvoa.png'
        self.logosmall = pathmetadb+'/logo-pyvoa_small.png'

    def maxcountry(self, kwargs):
        """Return how many locations a chart may show, as asked for.

        Parameters
        ----------
        kwargs : dict
            The drawing arguments; 'maxcountrydisplayed' is read from them, and
            the default of 12 used when it is missing.

        Returns
        -------
        int
            The cap.

        Raises
        ------
        PyvoaError
            If the value is not a positive integer.
        """
        n = kwargs.get('maxcountrydisplayed', self.maxcountrydisplayed)
        if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or n < 1:
            raise PyvoaError('maxcountrydisplayed must be a positive integer, not '+repr(n))
        return int(n)

    ''' DECORATORS FOR PLOT: DATE, VERSUS, SCROLLINGMENU '''
    def decoplot(func):
        """Decorate preparing the data of a time-series plot.

        Keeps the first ``maxcountrydisplayed`` locations, cuts their names to
        ``maxlettersdisplayed`` for the labels, legends and tooltips, and sets
        the title, the logo and the legend of a 'sumall' plot.
        """
        @wraps(func)
        def inner_plot(self ,**kwargs):
            """Prepare the keyword arguments shared by every time-series plot.

            Adds the title, the logo, the colour cycle and the shortened location
            labels before handing over to the plotting routine.
            """
            input = kwargs.get('input')
            # what = kwargs.get('what')
            title = kwargs.get('title')
            kwargs['logo'] = self.logosmall

            #input = input.loc[input['where'].isin(locunique)]
            kwargs['legend'] = None
            if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
                kwargs['legend'] = 'sum all location'
            if func.__name__ == 'plot' and title == InputOption().d_graphicsinput_args['title']:
                kwargs['title'] = self.database_name.upper() + ' database'

            maxcountry = self.maxcountry(kwargs)
            loc=list(input['where'].unique())
            input = input.loc[input['where'].isin(loc[:maxcountry])].copy()
            # the names are cut for the chart only: labels, legends and tooltips
            input['where'] = shorten_locations(input['where'], kwargs['maxlettersdisplayed'])
            kwargs['input'] = input
            kwargs['maxcountrydisplayed'] = maxcountry
            return func(self, **kwargs)
        return inner_plot

    ''' DECORATORS FOR HISTO VERTICAL, HISTO HORIZONTAL, PIE & MAP'''
    def decohistomap(func):
        """Decorate preparing the data of a histogram, a pie chart or a map.

        Cuts the location names to ``maxlettersdisplayed`` for the labels,
        legends and tooltips, keeps the last date (unless a date slider is
        asked for), ranks the locations, caps a histogram by location at
        ``maxcountrydisplayed`` of them, and gathers the rest into a
        'SumOthers' slice for a histogram by value or a pie chart.
        """
        @wraps(func)
        def inner_hm(self, **kwargs):
            """Prepare the keyword arguments shared by histograms and maps.

            Adds the title, the date actually drawn, the logo and the shortened
            location labels before handing over to the drawing routine.
            """
            input = kwargs.get('input').copy()
            # the names are cut for the chart only: labels, legends and tooltips,
            # including the list of the locations gathered into 'SumOthers'
            input['where'] = shorten_locations(input['where'], kwargs['maxlettersdisplayed'])
            kwargs['input'] = input
            which = kwargs.get('which')
            # where = kwargs['input']['where']
            if isinstance(which, list):
                which = which[0]
                kwargs['which'] = which
            if kwargs['input'][which].values.sum()==0.:
                raise PyvoaError('All value are null for '+str(which)+ 'at the date of ' +str(kwargs['when']))
            title = kwargs['title']
            drawn = input['date'].max()
            # what = kwargs.get('what')
            # when = kwargs.get('when') : the title now reads the date drawn
            typeofhist = kwargs.get('typeofhist')

            kwargs['logo'] = self.logo
            # windows =  InputOption().windows
            if title == InputOption().d_graphicsinput_args['title']:
                kwargs['title'] = self.database_name.upper() + ' database' + ' ('+drawn.strftime('%d/%m/%Y')+')'
            maxcountry = self.maxcountry(kwargs)
            if not kwargs['dateslider']:
                input = input[input.date==input.date.max()].sort_values(by = which, ascending=False).reset_index(drop=True)
                if func.__name__ != 'map' and kwargs['typeofhist'] == 'location':
                    input = input.head(maxcountry)

                if typeofhist == 'value' or typeofhist == 'pie':
                    top = input.iloc[:maxcountry].copy()
                    # one colour per slice, as many as the cap asked for, and
                    # fewer locations than that when few are asked for
                    colors = plt.cm.tab20(np.linspace(0, 1, maxcountry))
                    top['colors'] = [matplotlib.colors.rgb2hex(c) for c in colors[:len(top)]]
                    others = input.iloc[maxcountry:]
                    rest = {col: ['SumOthers'] for col in top.columns}

                    total = others[which].apply(
                        lambda x: x[0] if isinstance(x, list) else x
                        ).sum()
                    rest[which] = [total]
                    if kwargs['kwargsuser']['vis'] == 'bokeh':
                        rest["where"] = ["_".join(others["where"].astype(str).unique())]
                    rest['date'] = [input['date'].iloc[0]]
                    rest['colors'] = ['#FFFFFF']
                    rest = pd.DataFrame(rest)
                    input = pd.concat([top, rest], ignore_index=True)
                    input = input.sort_values(by=which, ascending=False).reset_index(drop=True)

            if kwargs['what'] in ['daily','weekly']:
               cols = [c for c in input.columns if c.endswith(kwargs['what'])]
               kwargs['what'] = cols
            kwargs['legend'] = None
            typeofhist=kwargs.get('typeofhist',None)
            if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
                kwargs['legend'] = 'sum all location'
            kwargs['maxcountrydisplayed'] = maxcountry
            kwargs['input'] = input

            return func(self, **kwargs)
        return inner_hm
    ''' DECORATORS FOR HISTO VERTICAL, HISTO HORIZONTAL, PIE '''
    def decohistopie(func):
        """Decorate preparing the data of a histogram or a pie chart.

        Sorts the locations by decreasing value so the chart is drawn in rank
        order, and resolves 'what' to the single column the chart needs when a
        daily or weekly series was asked for.
        """
        @wraps(func)
        def inner_decohistopie(self, **kwargs):
            """Prepare the data of a horizontal histogram or a pie chart.

            Puts into the kwargs ``geopdwd``, the pandas of the variable asked for
            over all dates, and ``geopdwd_filtered``, the same for the last date only.
            """
            input = kwargs.get('input')
            which = kwargs.get('which')
            # vis = kwargs.get('vis')
            input['where'].unique()
            input = input.sort_values(by=which, ascending=False).reset_index(drop=True)
            kwargs['input'] = input
            return func(self,**kwargs)
        return inner_decohistopie

    @decoplot
    def plot(self,**kwargs):
        """Draw a time series with whichever backend is selected.

        Dispatches to matplotlib, bokeh or seaborn according to 'vis', and
        within each to the routine matching 'typeofplot'. The backends do not
        all offer the same plots: 'compare' and 'spiral' exist only in bokeh.

        Parameters
        ----------
        **kwargs
            the drawing arguments prepared by front, including
            'input', 'which', 'what', 'vis' and 'typeofplot'.

        Returns
        -------
        The figure built by the backend.

        Raises
        ------
        PyvoaError
            if the selection holds a single date, if 'yearly' or
            'spiral' is asked for with more than one location or variable,
            or if 'versus' is not given exactly two variables.
        """
        input = kwargs.get('input')
        typeofplot = kwargs.get('typeofplot')
        if input.date.max() == input.date.min():
            raise PyvoaError("Only one date ! Plot is meaning less here")
        vis = kwargs.get('vis')
        fig = None

        if (typeofplot == 'yearly' or typeofplot == 'spiral') and \
           (len(kwargs['input']['where'].unique())>1 or len(kwargs['which'])>1):
            raise PyvoaError('Yearly or spiral plots can display only one country and/or one value.')
        if typeofplot == 'versus' and len(kwargs.get('which')) != 2:
            raise PyvoaError("Can't make versus plot in this condition len("+str(kwargs.get('which'))+")!=2")
        if vis == 'matplotlib':
            if typeofplot == 'date':
                fig = visu_matplotlib().matplotlib_date_plot(**kwargs)
            elif typeofplot == 'versus':
                fig = visu_matplotlib().matplotlib_versus_plot(**kwargs)
            elif typeofplot == 'yearly':
                fig = visu_matplotlib().matplotlib_yearly_plot(**kwargs)
            else:
                raise PyvoaError('For display: '+ vis +' unknown typeofplot '+typeofplot)
        elif vis =='seaborn':
            if typeofplot == 'date':
                fig = visu_seaborn().seaborn_date_plot(**kwargs)
            elif  typeofplot == 'versus':
                fig = visu_seaborn().seaborn_versus_plot(**kwargs)
            elif  typeofplot == 'yearly':
                fig = visu_seaborn().seaborn_yearly_plot(**kwargs)
            else:
                raise PyvoaError(typeofplot + ' not implemented in ' + vis)
        elif vis == 'bokeh' and BOKEH_AVAILABLE:
            if typeofplot == 'date':
                fig = visu_bokeh().bokeh_date_plot(**kwargs)
            elif typeofplot == 'spiral':
                fig = visu_bokeh().bokeh_spiral_plot(**kwargs)
            elif typeofplot == 'versus':
                fig = visu_bokeh().bokeh_versus_plot(**kwargs)
            elif typeofplot == 'compare':
                if self.granularity == 'nation' and self.granularity != 'World':
                    print('typeofplot is compare with a national DB granularity, use date plot instead ...')
                    fig = visu_bokeh().plot(*kwargs)
                else:
                    if len(kwargs['which']) > 1:
                        PyvoaWarning('typeofplot is compare but dim(which)>1, take first one '+kwargs['which'][0])
                    fig = visu_bokeh().bokeh_menu_plot(**kwargs)
            elif typeofplot == 'yearly':
                if input.date.max()-input.date.min() <= dt.timedelta(days=365):
                    print("Yearly will not be used since the time covered is less than 1 year")
                    fig =  visu_bokeh().bokeh_date_plot(**kwargs)
                else:
                    fig =  visu_bokeh().bokeh_yearly_plot(**kwargs)
        else:
            print(" Not implemented yet ")
        return fig

    @decohistomap
    @decohistopie
    def hist(self,**kwargs):
        """Draw a histogram or a pie chart with whichever backend is selected.

        Dispatches to matplotlib, bokeh or seaborn according to 'vis', and
        within each to the routine matching 'typeofhist': 'location' (one bar
        per location), 'value' (the locations binned by value) or 'pie'.

        Parameters
        ----------
        **kwargs
            the drawing arguments prepared by front, including 'input',
            'which', 'vis' and 'typeofhist'.

        Returns
        -------
        The figure built by the backend.

        Raises
        ------
        PyvoaError
            If matplotlib is asked for a 'typeofhist' it does not draw.
        """
        typeofhist = kwargs.get('typeofhist')
        vis = kwargs.get('vis')
        if vis == 'matplotlib':
            if typeofhist == 'location':
                fig = visu_matplotlib().matplotlib_horizontal_histo(**kwargs)
            elif typeofhist == 'value':
                fig = visu_matplotlib().matplotlib_histo(**kwargs)
            elif typeofhist == 'pie':
                kwargs['logo'] = self.logosmall
                fig = visu_matplotlib().matplotlib_pie(**kwargs)
            else:
                raise PyvoaError(typeofhist + ' not implemented in ' + vis)
        elif vis == 'bokeh' and BOKEH_AVAILABLE:
            if typeofhist == 'location':
                fig = visu_bokeh().bokeh_horizonhisto(**kwargs)
            elif typeofhist == 'value':
                fig = visu_bokeh().bokeh_histo(**kwargs)
            elif typeofhist == 'pie':
                kwargs['logo'] = self.logosmall
                fig = visu_bokeh().bokeh_pie(**kwargs)
        elif vis == 'seaborn':
            if typeofhist == 'location':
                fig = visu_seaborn().seaborn_hist_horizontal(**kwargs)
            elif typeofhist == 'pie':
                fig = visu_seaborn().seaborn_pie(**kwargs)
            elif typeofhist == 'value':
                fig = visu_seaborn().seaborn_hist_value( **kwargs)
            else:
                print(typeofhist + ' not implemented in ' + vis)
        else:
            print( "\n not yet implemented \n")
        return fig

    @decohistomap
    @decohistopie
    def map(self,**kwargs):
        """Draw a map with whichever backend is selected.

        Dispatches to matplotlib, bokeh, seaborn or folium according to 'vis'.
        A single variable is drawn: a list given as 'which' is reduced to its
        first element.

        Parameters
        ----------
        **kwargs
            the drawing arguments prepared by front, including 'input' with its
            'geometry' column, 'which', 'vis', 'typeofmap' and 'tile'.

        Returns
        -------
        The map built by the backend.

        Raises
        ------
        PyvoaError
            If 'dateslider' is asked for outside bokeh, if 'input' has no
            geometry, or if 'vis' names no backend that draws maps.
        """
        vis = kwargs.get('vis')
        input = kwargs.get('input')
        which = kwargs.get('which')
        if isinstance(which, list):
            which = which[0]
            kwargs['which'] = which

        if vis != 'bokeh' and kwargs['dateslider']:
            kwargs.pop("dateslider")
            raise PyvoaError("Only avalaible for vis='bokeh' dummy argument")
        if 'geometry' not in list(input.columns):
            raise PyvoaError('No geometry in you pandas, map can not be called ...')
        if vis == 'matplotlib':
            fig = visu_matplotlib().matplotlib_map(**kwargs)
        elif vis == 'seaborn':
            fig = visu_seaborn().seaborn_heatmap(**kwargs)
        elif vis == 'bokeh' and BOKEH_AVAILABLE:
                # a location with no geometry of its own carries an empty one,
                # serialised as null in the GeoJSON, which BokehJS fails on
                # ("Cannot read properties of null"), drawing no map at all
                drawable = ~gpd.GeoSeries(input['geometry']).is_empty.to_numpy()
                kwargs['input'] = input.loc[drawable]
                fig = visu_bokeh().bokeh_map(**kwargs)
        elif vis == 'folium':
            # folium serialises GeoJSON too: same care as for bokeh
            drawable = ~gpd.GeoSeries(input['geometry']).is_empty.to_numpy()
            kwargs['input'] = input.loc[drawable]
            fig = visu_folium().folium_map(**kwargs)
        else:
            raise PyvoaError('Waiting for a valid visualisation. So far: \'bokeh\', \'folium\' or \'matplotlib\' \
            aka matplotlib .See help.')
        return fig
