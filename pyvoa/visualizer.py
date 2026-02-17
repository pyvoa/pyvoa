# -*- coding: utf-8 -*-

"""
Project : PyvoA
Date :    april 2020 - november 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_org
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.visualizer

About :
-------

An interface module to easily plot pyvoa_data with bokeh

"""
from functools import wraps
import datetime as dt
from pyvoa.tools import (
    kwargs_keystesting,
    extract_dates,
    verb,
    fill_missing_dates
)
import geopandas as gpd
import pandas as pd
from pyvoa.jsondb_parser import MetaInfo
from pyvoa.kwarg_options import InputOption
from pyvoa.error import *

try:
    import bokeh
    BOKEH_AVAILABLE = True
except ImportError:
    BOKEH_AVAILABLE = False

try:
    import matplotlib
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import seaborn
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

try:
    import folium
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
    """
        All visualisation should be implemented here !
    """
    def __init__(self, db_name = None, kindgeo = None):
        self.lcolors = ['red', 'blue', 'green', 'orange', 'purple',
                        'brown', 'pink', 'gray', 'yellow', 'cyan']
        self.scolors = self.lcolors[:5]

        if kindgeo is None:
            pass
        else:
            self.kindgeo = kindgeo

        self.database_name = None
        verb("Init of AllVisu() with db=" + str(db_name))
        self.database_name = db_name
        self.currentmetadata = MetaInfo().getcurrentmetadata(db_name)
        self.setchartsfunctions = [method for method in dir(AllVisu) if callable(getattr(AllVisu, method)) and method.startswith("pyvoa_") and not method.startswith("__")]
        self.geopan = gpd.GeoDataFrame()
        self.pyvoa_geopandas = False
        self.geom = []
        self.listfigs = []
        self.dchartkargs = {}
        self.dvisukargs = {}
        self.uptitle, self.subtitle = ' ',' '
        self.code = self.currentmetadata['geoinfo']['iso3']
        self.granularity = self.currentmetadata['geoinfo']['granularity']
        self.namecountry = self.currentmetadata['geoinfo']['iso3']
        self.maxcountrydisplay  = 12
        self.maxlettersdisplay = 5
        pathmetadb = str(pkg_resources.files(pyvoa).joinpath("data"))
        self.logo = pathmetadb+'/logo-pyvoa.png'

    ''' DECORATORS FOR PLOT: DATE, VERSUS, SCROLLINGMENU '''
    def decoplot(func):
        """
        decorator for plot purpose
        """
        @wraps(func)
        def inner_plot(self ,**kwargs):
            input = kwargs.get('input')
            which = kwargs.get('which')
            what = kwargs.get('what')
            when = kwargs.get('when')
            kwargs['maxlettersdisplay'] = self.maxlettersdisplay

            kwargs['logo'] = self.logo
            #input = input.sort_values(by=['date']).reset_index(drop=True)
            locunique = kwargs['whereordered']
            input = input.loc[input['where'].isin(locunique)]
            #input['where'] = input['where'].cat.remove_unused_categories()
            if kwargs['what'] in ['daily','weekly']:
               cols = [c for c in input.columns if c.endswith(kwargs['what'])]
               kwargs['what'] = cols
            kwargs['legend'] = None
            if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
                kwargs['legend'] = 'sum all location'
            if func.__name__ == 'plot':
                kwargs['title'] = self.database_name.upper() +', '+ str(which) + ' time evolution between ' + str(when)
            loc=list(input['where'].unique())
            kwargs['dicodisplayloc'] = { w:(w[:self.maxlettersdisplay] + '…') if len(w) > self.maxlettersdisplay else w for w in loc }

            kwargs['input'] = input.loc[input['where'].isin(loc[:self.maxcountrydisplay])]
            kwargs['maxcountrydisplay'] = self.maxcountrydisplay

            if kwargs['kwargsuser']['what'] != 'current':
                kwargs['which'] = kwargs['what']

            return func(self, **kwargs)
        return inner_plot

    ''' DECORATORS FOR HISTO VERTICAL, HISTO HORIZONTAL, PIE & MAP'''
    def decohistomap(func):
        """
        Decorator function used for histogram and map
        """
        @wraps(func)
        def inner_hm(self, **kwargs):
            input = kwargs.get('input')
            which = kwargs.get('which')
            which = which[0]
            what = kwargs.get('what')
            when = kwargs.get('when')
            kwargs['logo'] = self.logo
            kwargs['maxlettersdisplay'] = self.maxlettersdisplay
            windows =  InputOption().windows
            if not kwargs['dateslider'] and func.__name__ != 'map':
                input = input[input.date==input.date.max()].sort_values(by = which, ascending=False).reset_index(drop=True)
                if func.__name__ != 'map' and  kwargs['typeofhist'] != 'value':
                    input = input.head(self.maxcountrydisplay)
                if kwargs['typeofhist'] == 'value':
                    top = input.iloc[:self.maxcountrydisplay]
                    others = input.iloc[self.maxcountrydisplay:]
                    rest = {col: ['SumOthers'] for col in top.columns}
                    if 'normalize' in which:
                        windows_which = [ which.replace(' ',i+' ') for i in windows.keys() ]
                    else:
                        windows_which = [ which + i for i in windows.keys() ]
                    for i in [which]+windows_which:
                        total = others[i].apply(
                            lambda x: x[0] if isinstance(x, list) else x
                            ).sum()
                        rest[i] = [total]
                    if kwargs['kwargsuser']['vis'] == 'bokeh':
                        rest["where"] = ["_".join(others["where"].astype(str).unique())]
                    rest['date'] = [input['date'].iloc[0]]
                    rest['colors'] = ['#FFFFFF']
                    rest = pd.DataFrame(rest)
                    input = pd.concat([top, rest], ignore_index=True)
                    input = input.sort_values(by=which, ascending=False).reset_index(drop=True)

            if len(kwargs['which'])>1:
                PyvoaInfo("Only one variable could be displayed, take the first one ...")
            if kwargs['what'] in ['daily','weekly']:
               cols = [c for c in input.columns if c.endswith(kwargs['what'])]
               kwargs['what'] = cols
            if isinstance(kwargs['what'],list):
                 kwargs['what'] = kwargs['what'][0]
            if (input[kwargs['what']] == 0.0).all():
                print("All values seems to be null ... nothing to plot")
                return
            kwargs['legend'] = None
            typeofhist=kwargs.get('typeofhist',None)
            if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
                kwargs['legend'] = 'sum all location'
            kwargs['title'] = self.database_name.upper() + ' database, ' + str(kwargs['which']) + '(' + str(when[0].split(':')[1]) +')'
            kwargs['maxcountrydisplay'] = self.maxcountrydisplay
            kwargs['input'] = input
            if kwargs['kwargsuser']['what'] != 'current':
                kwargs['which'] = kwargs['what']

            loc = list(input['where'].unique())
            kwargs['dicodisplayloc'] = { w:(w[:self.maxlettersdisplay] + '…') if len(w) > self.maxlettersdisplay else w for w in loc }
            return func(self, **kwargs)
        return inner_hm
    ''' DECORATORS FOR HISTO VERTICAL, HISTO HORIZONTAL, PIE '''
    def decohistopie(func):
        @wraps(func)
        def inner_decohistopie(self, **kwargs):
            """
            Decorator for Horizontal histogram & Pie Chart
            It put in the kwargs:
            kwargs['geopdwd']-> pandas for which asked (all dates)
            kwargs['geopdwd_filtered']-> pandas for which asked last dates
            """
            input = kwargs.get('input')
            which = kwargs.get('which')
            locunique = input['where'].unique()
            vis = kwargs.get('vis')
            input = input.sort_values(by=which, ascending=False).reset_index(drop=True)
            kwargs['input'] = input
            if kwargs['dateslider'] and vis != 'bokeh':
                raise PyvoaError('dateslider available only visu Bokeh')
            if kwargs['what'] in ['daily','weekly']:
               cols = [c for c in input.columns if c.endswith(kwargs['what'])]
               kwargs['what'] = cols
            if isinstance(kwargs['what'],list):
                 kwargs['what'] = kwargs['what'][0]
            kwargs['input'] = input
            return func(self,**kwargs)
        return inner_decohistopie

    @decoplot
    def plot(self,**kwargs):
        input = kwargs.get('input')
        typeofplot = kwargs.get('typeofplot')
        if input.date.max() == input.date.min():
            raise PyvoaError("Only one date ! Plot is meaning less here")
        vis = kwargs.get('vis')
        fig = None
        if (typeofplot == 'yearly' or typeofplot == 'spiral') and \
           (len(kwargs['input']['where'].unique())>1 or len(kwargs['which'])>1):
            raise PyvoaError('Yearly or spiral plots can display only one country and/or one value.')
        if typeofplot == 'versus':
            if len(kwargs.get('which')) != 2:
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
        '''
        FILL IT
        '''
        typeofhist = kwargs.get('typeofhist')
        vis = kwargs.get('vis')
        if vis == 'matplotlib':
            if typeofhist == 'location':
                fig = visu_matplotlib().matplotlib_horizontal_histo(**kwargs)
            elif typeofhist == 'value':
                fig = visu_matplotlib().matplotlib_histo(**kwargs)
            elif typeofhist == 'pie':
                fig = visu_matplotlib().matplotlib_pie(**kwargs)
            else:
                raise PyvoaError(typeofhist + ' not implemented in ' + vis)
        elif vis == 'bokeh' and BOKEH_AVAILABLE:
            if typeofhist == 'location':
                fig = visu_bokeh().bokeh_horizonhisto(**kwargs)
            elif typeofhist == 'value':
                fig = visu_bokeh().bokeh_histo(**kwargs)
            elif typeofhist == 'pie':
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
        '''
        FILL IT
        '''
        vis = kwargs.get('vis')
        input = kwargs.get('input')
        if vis != 'bokeh' and kwargs['dateslider']:
            kwargs.pop("dateslider")
            PyvoaWarning("Only avalaible for vis='bokeh' dummy argument")
        if 'geometry' not in list(input.columns):
            raise PyvoaError('No geometry in you pandas, map can not be called ...')
        if vis == 'matplotlib':
            fig = visu_matplotlib().matplotlib_map(**kwargs)
        elif vis == 'seaborn':
            fig = visu_seaborn().seaborn_heatmap(**kwargs)
        elif vis == 'bokeh' and BOKEH_AVAILABLE:
                fig = visu_bokeh().bokeh_map(**kwargs)
        elif vis == 'folium':
            fig = visu_folium().folium_map(**kwargs)
        else:
            raise PyvoaError('Waiting for a valid visualisation. So far: \'bokeh\', \'folium\' or \'matplotlib\' \
            aka matplotlib .See help.')
        return fig
