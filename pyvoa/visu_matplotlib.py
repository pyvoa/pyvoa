# -*- coding: utf-8 -*-

"""
Project : PyvoA
Date :    april 2020 - march 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_fr
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.visu_matplotlib

About :
-------


"""
from pyvoa.tools import (
    extract_dates,
    debug,
    verb,
    fill_missing_dates
)
from pyvoa.error import *
import math
import pandas as pd
import geopandas as gpd
import numpy as np

import json
import io
import copy

import datetime as dt
import matplotlib.dates as mdates
from pyvoa.jsondb_parser import MetaInfo
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

class visu_matplotlib:
    '''
        MATPLOTLIB chart drawing methods ...
    '''
    def __init__(self,):
        import matplotlib
        def set_matplotlib_backend():
            try:
                from IPython import get_ipython
                ipy = get_ipython()
                if ipy is None:
                    # For classic terminal  (python)
                    matplotlib.use("TkAgg")
                elif "IPKernelApp" in ipy.config:
                    # For Jupyter notebook
                    matplotlib.use("module://matplotlib_inline.backend_inline")
                else:
                    # Cas IPython shell (ex : ipython en console)
                    matplotlib.use("TkAgg")
            except Exception:
                #in other case fallback vers TkAgg (fenêtre graphique)
                matplotlib.use("TkAgg")
        set_matplotlib_backend()

    def decomatplotlib(func):
        def wrapper(self,**kwargs):
            im = mpimg.imread(kwargs['logo'])
            h, w = im.shape[:2]
            fig, ax = plt.subplots(1, 1,figsize=(10, 5))
            fig_w, fig_h = fig.get_size_inches() * fig.dpi
            xo = int(0.25*(fig_w-w))
            yo = int(0.3 * fig_h)
            fig.figimage(im, xo=xo, yo=yo, alpha=.1)
            kwargs['fig'] = fig
            kwargs['ax'] = ax
            kwargs['plt'] = plt
            return func(self,**kwargs)
        return wrapper

    @decomatplotlib
    def matplotlib_date_plot(self,**kwargs):
        input = kwargs.get('input')
        what = kwargs.get('what')
        title = kwargs.get('title')
        plt = kwargs['plt']
        ax = kwargs['ax']
        legend = kwargs.get('legend',None)
        plt.xlabel("date", fontsize=10)
        plt.ylabel(what[0], fontsize=10)
        df = pd.pivot_table(input,index='date', columns='where', values=what)
        leg=[]
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(1)
        for col in df.columns:
            label = legend if legend else col
            lines = plt.plot(df.index, df[col],label=label)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        plt.legend(title="where", loc="upper left", fontsize=8, title_fontsize=10)
        plt.title(title)
        #return plt.gcf()

    @decomatplotlib
    def matplotlib_versus_plot(self,**kwargs):
        input = kwargs.get('input')
        what = kwargs.get('what')
        title = kwargs.get('title')
        plt = kwargs['plt']
        ax = kwargs['ax']
        loc = list(input['where'].unique())
        plt.xlabel(what[0], fontsize=10)
        plt.ylabel(what[1], fontsize=10)
        leg=[]
        for col in loc:
            pandy=input.loc[input['where']==col]
            lines=plt.plot(pandy[what[0]], pandy[what[1]])
            leg.append(col)
        plt.legend(leg)
        plt.title(title)
        return plt.gcf()

    @decomatplotlib
    def matplotlib_yearly_plot(self,**kwargs):
        '''
         matplotlib date yearly plot chart
         Max display defined by Max_Countries_Default
        '''
        input = kwargs.get('input')
        what = kwargs.get('what')
        title = kwargs.get('title')
        plt = kwargs['plt']
        ax = kwargs['ax']
        #drop bissextile fine tuning in needed in the future
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input = input.copy()
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)

        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)

        loc = input['where'][0]
        d = input.allyears.unique()
        for i in d:
            df = pd.pivot_table(input.loc[input.allyears==i],index='dayofyear', columns='where', values=what)
            ax = plt.plot(df.index,df,label=f'{i}')
        plt.legend(d)
        plt.title(title)
        return plt.gcf()

    @decomatplotlib
    def matplotlib_pie(self,**kwargs):
        '''
         matplotlib pie chart
         Max display defined by Max_Countries_Default
        '''
        input = kwargs.get('input')
        what = kwargs.get('what')
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        ax = kwargs.get('ax')
        ax.legend(bbox_to_anchor=(0.75, 1.2), loc='upper left')
        ax.set_title(title)
        input = input.set_index('where')
        input.plot(kind="pie",y=what, autopct='%1.1f%%', legend=True,
        title=title, ylabel='where', labeldistance=None,ax=ax)
        return plt.gcf()

    @decomatplotlib
    def matplotlib_horizontal_histo(self,**kwargs):
        '''
        matplotlib horizon histo
        '''
        input = kwargs.get('input')
        what = kwargs.get('what')
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        cmap = plt.get_cmap('Paired')
        ax = kwargs.get('ax')
        fig = kwargs.get('fig')
        legend = kwargs.get('legend',None)
        maxletters = kwargs['maxlettersdisplay']

        input_sorted = input.sort_values(by=what,ascending=True)
        if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
            input_sorted['where'] = 'sum all location'
        input_sorted['where'] = [ (w[:10] + '…') if len(w) > 10 else w for w in input_sorted['where']]
        ax.barh(input_sorted['where'], input_sorted[what],color=cmap.colors,label = legend)
        ax.set_title(title)
        plt.xlabel(what)
        #return plt.gcf()

    @decomatplotlib
    def matplotlib_histo(self,**kwargs):
        '''
        matplotlib vertical histo
        '''
        input = kwargs.get('input')
        what = kwargs.get('what')
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        ax = kwargs.get('ax')
        bins=len(input['where'])+1
        input = pd.pivot_table(input,index='date', columns='where', values=what)
        input.plot.hist(bins=bins, alpha=0.5,title = title,ax=ax)
        #return plt.gcf()

    @decomatplotlib
    def matplotlib_map(self,**kwargs):
        '''
         matplotlib map display
        '''
        from matplotlib.colors import Normalize
        from matplotlib import cm
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        import contextily as cx
        import xyzservices
        plt = kwargs.get('plt')
        ax = kwargs.get('ax')
        plt.axis('off')
        input = kwargs.get('input')
        what = kwargs.get('what')
        mapoption = kwargs.get('mapoption')
        title = kwargs.get('title')
        tile = kwargs.get('tile')
        input.plot(column = what, ax=ax,legend=True,
                                legend_kwds={'label': what,
                                'orientation': "horizontal","pad": 0.001})

        if tile == 'openstreet':
            input = input.to_crs(epsg=3857)
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.OpenStreetMap.Mapnik)
        elif tile == 'esri':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.Esri.WorldImagery)
        elif tile == 'stamen':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.Esri.WorldImagery)
            PyvoaWarning("Couldn't find stamen for matplolib use esri ....")
            input = input.to_crs(epsg=4326)
        elif tile == 'positron':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.CartoDB.PositronNoLabels)
        else:
            PyvoaError("Don't know what kind of tile is it ...")

        if 'text' in mapoption:
            centroids = input['geometry'].centroid
            for idx, centroid in enumerate(centroids):
                if centroid:
                    x, y = centroid.x, centroid.y
                    annotation = input.iloc[idx][what]
                    annotation =  annotation.round(2)

        ax.set_axis_off()
        ax.set_title(title)
        #return plt.gcf()
