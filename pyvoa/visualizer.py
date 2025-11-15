# -*- coding: utf-8 -*-

"""
Project : PyvoA
Date :    april 2020 - march 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_fr
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.visualizer

About :
-------

An interface module to easily plot pycoa_data with bokeh

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
from pyvoa.visu_matplotlib import visu_matplotlib
from pyvoa.visu_seaborn import visu_seaborn
from pyvoa.error import *

try:
    import bokeh
    BOKEH_AVAILABLE = True
except ImportError:
    BOKEH_AVAILABLE = False

if BOKEH_AVAILABLE:
    from pyvoa.visu_bokeh import visu_bokeh

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
        self.when_beg, self.when_end = dt.date(1, 1, 1), dt.date(1, 1, 1)

        self.database_name = None
        verb("Init of AllVisu() with db=" + str(db_name))
        self.database_name = db_name
        self.currentmetadata = MetaInfo().getcurrentmetadata(db_name)
        self.setchartsfunctions = [method for method in dir(AllVisu) if callable(getattr(AllVisu, method)) and method.startswith("pycoa_") and not method.startswith("__")]
        self.geopan = gpd.GeoDataFrame()
        self.pycoa_geopandas = False
        self.geom = []
        self.listfigs = []
        self.dchartkargs = {}
        self.dvisukargs = {}
        self.uptitle, self.subtitle = ' ',' '
        self.code = self.currentmetadata['geoinfo']['iso3']
        self.granularity = self.currentmetadata['geoinfo']['granularity']
        self.namecountry = self.currentmetadata['geoinfo']['iso3']
        self.maxcountrydisplay  = 12
        self.maxlettersdisplay = 10
        pathmetadb = str(pkg_resources.files(pyvoa).joinpath("data"))
        self.logo = pathmetadb+'/pyvoa_logo2.jpg'

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
            kwargs['logo'] = self.logo
            input = input.sort_values(by=['date']).reset_index(drop=True)
            locunique = list(input['where'].unique())[:self.maxcountrydisplay]
            input = input.loc[input['where'].isin(locunique)]
            input['where'] = input['where'].cat.remove_unused_categories()
            if kwargs['what'] in ['daily','weekly']:
               cols = [c for c in input.columns if c.endswith(kwargs['what'])]
               kwargs['what'] = cols
            kwargs['legend'] = None
            if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
                kwargs['legend'] = 'sum all location'
            if kwargs['kwargsuser']['typeofplot'] == 'date':
                kwargs['title'] = what[0] + ' time evolution'
            kwargs['title'] = self.database_name + ' time evolution between ' + str(when[0])
            kwargs['input'] = input
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
            what = kwargs.get('what')
            when = kwargs.get('when')
            kwargs['logo'] = self.logo
            kwargs['maxlettersdisplay'] = self.maxlettersdisplay
            if not kwargs['dateslider']:
                input = input[input.date==input.date.max()].sort_values(by = which, ascending=False).reset_index(drop=True)
                if func.__name__ != 'map':
                    input = input.head(self.maxcountrydisplay)
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
            kwargs['title'] = self.database_name + ' database at ' + when[0].split(':')[1]
            kwargs['maxcountrydisplay'] = self.maxcountrydisplay
            kwargs['input'] = input
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
            input = input.sort_values(by=which, ascending=False).reset_index(drop=True)
            kwargs['input'] = input
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
        mapoption = kwargs.get('mapoption')
        input = kwargs.get('input')
        if vis == 'matplotlib':
            if mapoption:
                PyvoaWarning("No mapoption is avalaible for matplotlib")
            fig = visu_matplotlib().matplotlib_map(**kwargs)
        elif vis == 'seaborn':
            if mapoption:
                print("No map is avalaible for seaborn")
            fig = visu_seaborn().seaborn_heatmap(**kwargs)
        elif vis == 'bokeh' and BOKEH_AVAILABLE:
            if mapoption:
                if 'spark' in mapoption or 'spiral' in mapoption:
                    fig = visu_bokeh().pycoa_pimpmap(**kwargs)
                elif 'text' or 'exploded' or 'dense' in mapoption:
                    fig = visu_bokeh().bokeh_map(**kwargs)
                else:
                    PyvoaWarning("What kind of pimp map you want ?!")
            else:
                fig = visu_bokeh().bokeh_map(**kwargs)
        elif vis == 'folium':
            fig = visu_matplotlib().bokeh_mapfolium(**kwargs)
        else:
            raise PyvoaError('Waiting for a valid visualisation. So far: \'bokeh\', \'folium\' or \'matplotlib\' \
            aka matplotlib .See help.')
        return fig
