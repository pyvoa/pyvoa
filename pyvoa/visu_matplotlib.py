# -*- coding: utf-8 -*-

"""
Project : PyvoA
Date :    april 2020 - december 2025
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
from pyvoa.kwarg_options import InputOption
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

class visu_matplotlib:
    '''
        MATPLOTLIB chart drawing methods ...
    '''
    def __init__(self,):
        import matplotlib
        self.av = InputOption()
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
        def wrapper(self, **kwargs):
            title = kwargs.get('title')
            im = mpimg.imread(kwargs['logo'])
            h, w = im.shape[:2]

            fig, ax = plt.subplots(1, 1, figsize=(10, 5))
            ax.set_title(title)

            # Scale logo to ~15% of figure width
            logo_width = int(0.40 * fig.get_figwidth() * fig.dpi)
            logo_height = int(logo_width * h / w)  # Maintain aspect ratio

            fig_w, fig_h = fig.get_size_inches() * fig.dpi
            xo = int(fig_w - logo_width - 20)    # 20px margin from right
            yo = int(fig_h - logo_height - 20)   # 20px margin from top

            # Resize the image to match calculated dimensions
            from PIL import Image
            pil_im = Image.fromarray((im * 255).astype('uint8'))
            im_resized = pil_im.resize((logo_width, logo_height))
            im_resized = np.array(im_resized) / 255.0

            fig.figimage(im_resized, xo=0, yo=0.5*yo, alpha=0.1)

            kwargs['fig'] = fig
            kwargs['ax'] = ax
            kwargs['plt'] = plt
            return func(self, **kwargs)
        return wrapper

    @decomatplotlib
    def matplotlib_date_plot(self,**kwargs):
        input = kwargs.get('input')
        what = kwargs.get('what')
        ax = kwargs['ax']
        legend = kwargs.get('legend',None)
        kwargs['dicodisplayloc']
        ax.set_xlabel("date", fontsize=10)
        ax.set_ylabel(what[0], fontsize=10)
        st=['-','--',':']
        for idx, i in enumerate(what):
            df = pd.pivot_table(input, index='date', columns='where', values=i)
            for where in df.columns:
                if legend:
                    label = legend
                else:
                    label = f"{kwargs['dicodisplayloc'][where]}"
                if len(what)>1:
                    label =f"{kwargs['dicodisplayloc'][where]} — {i}"
                ax.plot(
                    df.index,
                    df[where],
                    label=label,
                    linestyle=st[idx]
                )

        ax.legend(loc="upper right", fontsize=8, title_fontsize=10, title=", ".join(what),ncol=len(what))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))
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
            ax.plot(df.index,df,label=f'{i}')
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
        if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
            input['where'] = 'sum all location'
        input['where']= [kwargs['dicodisplayloc'][w] for w in input['where']]
        input = input.set_index('where')
        return input.plot(kind="pie",y=what, autopct='%1.1f%%', legend=True,
        title=title, ylabel='', labeldistance=None,ax=ax)


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

        input_sorted = input.sort_values(by=what,ascending=True)
        ax.set_title(title)
        ax.set_xlabel(what)
        if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
            input_sorted['where'] = 'sum all location'
        return ax.barh(input_sorted['where'], input_sorted[what],color=cmap.colors,label = legend)


    @decomatplotlib
    def matplotlib_histo(self,**kwargs):
        what = kwargs.get('what')
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        ax = kwargs.get('ax')
        input_df = kwargs.get('input').copy()
        bins = kwargs.get('bins', self.av.d_graphicsinput_args['bins'])
        which = kwargs.get('which')

        if isinstance(which, list):
            which = which[0]

        # bins
        min_val = input_df[which].min()
        max_val = input_df[which].max()

        if not bins:
            bins = 11

        edges = np.linspace(min_val, max_val, bins + 1)

        # assign bins
        input_df["bin"] = pd.cut(input_df[which], bins=edges, include_lowest=True)

        # pivot: bin x country
        pivot = (
            input_df
            .groupby(["bin", "where"])
            .size()
            .unstack(fill_value=0)
            .sort_index()
        )

        countries = pivot.columns
        colors = plt.cm.tab20(np.linspace(0, 1, len(countries)))

        x = np.arange(len(pivot))
        bottom = np.zeros(len(pivot))

        for i, country in enumerate(countries):
            ax.bar(
                x,
                pivot[country].values,
                bottom=bottom,
                label=country,
                color=colors[i],
                alpha=0.85
            )
            bottom += pivot[country].values

        # -------------------------
        # AXE X en LOG (puissance de 10)
        # -------------------------
        def format_sci(x):
            if x <= 0:
                return ""

            exp = int(np.floor(np.log10(x)))
            mant = x / 10**exp

            # arrondi propre
            mant = np.round(mant, 1)

            if mant == 1:
                return rf"$10^{{{exp}}}$"
            else:
                return rf"${mant:g}\times10^{{{exp}}}$"

        centers = np.array([(edges[i] + edges[i+1]) / 2 for i in range(len(edges)-1)])
        mask = centers > 0
        ax.set_xticks(x[mask])

        ax.set_xticklabels([format_sci(c) for c in centers[mask]])

        ax.set_xlabel(which)
        ax.set_ylabel("frequency")

        # -------------------------
        # LÉGENDE À L'EXTÉRIEUR
        # -------------------------
        ax.legend(
            title="Country",
            bbox_to_anchor=(1.05, 1),
            loc="upper left",
            borderaxespad=0
        )

        #plt.tight_layout()
        return ax

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
                                'orientation': "horizontal","pad": 0.01, 'shrink': 0.5})
        ax.set_axis_off()
        ax.set_title(title)
        input = input.to_crs(epsg=3857)
        if tile == 'openstreet':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.OpenStreetMap.Mapnik)
        elif tile == 'esri':
            PyvoaWarning("Problem occurs wiht esri and matplolib use default tile ....")
            #cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.Esri.WorldImagery)
        elif tile == 'stamen':
            #cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.Stamen.TonerLite)
            PyvoaWarning("Couldn't find stamen for matplolib use default tile ....")
        elif tile == 'positron':
            cx.add_basemap(ax, crs=input.crs.to_string(), source=cx.providers.CartoDB.PositronNoLabels)
        else:
            PyvoaError("Don't know what kind of tile is it ...")

        return ax
