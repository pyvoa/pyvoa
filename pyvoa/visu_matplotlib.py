# -*- coding: utf-8 -*-

"""
Project : PyvoA
Date :    april 2020 - november 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_org
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
            title = kwargs.get('title')
            im = mpimg.imread(kwargs['logo'])
            h, w = im.shape[:2]
            fig, ax = plt.subplots(1, 1,figsize=(10, 5))
            ax.set_title(title)
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
        nb = kwargs['maxlettersdisplay']
        input['where'] = [k[:nb] for k in input['where']]
        what = kwargs.get('what')
        ax = kwargs['ax']
        legend = kwargs.get('legend',None)
        ax.set_xlabel("date", fontsize=10)
        ax.set_ylabel(what[0], fontsize=10)
        st=['-','--',':']
        for idx, i in enumerate(what):
            df = pd.pivot_table(input, index='date', columns='where', values=i)
            for where in df.columns:
                label = f"{where}"
                if len(what)>1:
                    label =f"{where} — {i}"
                ax.plot(
                    df.index,
                    df[where],
                    label=label,
                    linestyle=st[idx]
                )

        ax.legend(loc="upper right", fontsize=8, title_fontsize=10, title=", ".join(what),ncol=len(what))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        return ax

    @decomatplotlib
    def matplotlib_versus_plot(self,**kwargs):
        input = kwargs.get('input')
        what = kwargs.get('what')
        ax = kwargs['ax']
        loc = list(input['where'].unique())
        ax.set_xlabel()(what[0], fontsize=10)
        ax.set_ylabel()(what[1], fontsize=10)
        leg=[]
        for col in loc:
            pandy=input.loc[input['where']==col]
            ax.plot(pandy[what[0]], pandy[what[1]])
            leg.append(col)
        ax.legend(leg)
        return ax

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
            ax = ax.plot(df.index,df,label=f'{i}')
        ax.legend(d)
        return ax

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
        nb = kwargs.get('maxlettersdisplay')
        if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
            input['where'] = 'sum all location'
        input['where'] = [ (w[:nb] + '…') if len(w) > nb else w for w in input['where']]
        input = input.set_index('where')
        return input.plot(kind="pie",y=what, autopct='%1.1f%%', legend=True,
        title=title, ylabel='where', labeldistance=None,ax=ax)


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
        ax.set_title(title)
        ax.set_xlabel(what)
        if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
            input_sorted['where'] = 'sum all location'
        input_sorted['where'] = [ (w[:maxletters] + '…') if len(w) > maxletters else w for w in input_sorted['where']]
        return ax.barh(input_sorted['where'], input_sorted[what],color=cmap.colors,label = legend)


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

        maxletters = kwargs['maxlettersdisplay']
        input['where'] = [ (w[:maxletters] + '…') if len(w) > maxletters else w for w in input['where']]

        input = pd.pivot_table(input,index='date', columns='where', values=what)
        return input.plot.hist(bins=bins, alpha=0.5,title = title,ax=ax)

    @decomatplotlib
    def matplotlib_map(self,**kwargs):
        '''
         matplotlib map display
        '''
        import contextily as cx
        ax = kwargs.get('ax')
        ax.axis('off')
        input = kwargs.get('input')
        what = kwargs.get('what')
        title = kwargs.get('title')
        tile = kwargs.get('tile')
        input.plot(column = what, ax=ax,legend=True,
                                legend_kwds={'label': what,
                                'orientation': "horizontal","pad": 0.001})
        ax.set_axis_off()
        ax.set_title(title)

        input = input.to_crs(epsg=3857)
        if tile == 'openstreet':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.OpenStreetMap.Mapnik)
        elif tile == 'esri':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.Esri.WorldImagery)
        elif tile == 'stamen':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.Stamen.TonerLite)
            PyvoaWarning("Couldn't find stamen for matplolib use esri ....")
        elif tile == 'positron':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.CartoDB.PositronNoLabels)
        else:
            PyvoaError("Don't know what kind of tile is it ...")

        return ax
