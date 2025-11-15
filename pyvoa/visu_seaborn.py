# -*- coding: utf-8 -*-

"""
Project : PyvoA
Date :    april 2020 - march 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_fr
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.visu_seaborn

About :
-------

An interface module to easily plot pycoa_data with bokeh

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
import locale
import inspect
import importlib

import shapely.geometry as sg

import datetime as dt
import bisect
from functools import wraps

from pyvoa.jsondb_parser import MetaInfo

class visu_seaborn:
    ######SEABORN#########
    ######################
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

    def decoplotseaborn(func):
        """
        decorator for seaborn plot
        """
        @wraps(func)
        def inner_plot(self, **kwargs):
            import matplotlib.pyplot as plt
            import seaborn as sns
            fig, ax = plt.subplots(1, 1,figsize=(8, 6))
            title = kwargs.get('title')
            plt.title(title)
            input = kwargs.get('input')
            which = kwargs.get('which')
            kwargs['plt'] = plt
            kwargs['sns'] = sns
            return func(self, **kwargs)
        return inner_plot

    def decohistseaborn(func):
        """
        decorator for seaborn histogram
        """
        @wraps(func)
        def inner_hist(self,**kwargs):
            input = kwargs.get('input')
            which = kwargs.get('which')
            if isinstance(which, list):
                which = which[0]

            input = (input.sort_values('date')
                  .drop_duplicates('where', keep='last')
                  .drop_duplicates(['where', which])
                  .sort_values(by=which, ascending=False)
                  .reset_index(drop=True))

            kwargs['input'] = input
            return func(self, **kwargs)
        return inner_hist

    #####SEABORN PLOT#########
    @decoplotseaborn
    def seaborn_date_plot(self, **kwargs):
        """
        Create a seaborn line plot with date on x-axis and which on y-axis.
        """
        input = kwargs['input']
        what = kwargs['what']
        plt = kwargs.get('plt')
        legend = kwargs.get('legend',None)
        sns = kwargs.get('sns')
        st=['-','--',':']
        df = input.copy()
        for idx, i in enumerate(what):
            label_col = f'where_{i}'
            df[label_col] = df['where'].astype(str) + ', ' + i
            label_name = legend.get(i, i) if legend else i
            if st and idx < len(st):
                dashes = st[idx]

            sns.lineplot(
                data=df,
                x='date',
                y=i,
                hue=label_col,
                style=label_col,
                legend='full',
            )
        plt.legend(title=what[0])
        plt.xlabel('Date')
        plt.xticks(rotation=45)

    @decoplotseaborn
    def seaborn_yearly_plot(self, **kwargs):
        input = kwargs['input']
        what = kwargs['what'][0]
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        input = input.loc[~(input['date'].dt.month.eq(2) & input['date'].dt.day.eq(29))].reset_index(drop=True)
        input = input.copy()
        input.loc[:,'allyears']=input['date'].apply(lambda x : x.year)
        input['allyears'] = input['allyears'].astype(int)
        input.loc[:,'dayofyear']= input['date'].apply(lambda x : x.dayofyear)

        years = sorted(input["allyears"].unique())
        palette = sns.color_palette("husl", n_colors=len(years))
        for color, i in zip(palette, years):
            subset = input.loc[input["allyears"] == i]
            sns.lineplot(
                data=subset,
                x="dayofyear",
                y=what,
                label=str(i),    # la légende affichera les années
                color=color
            )
        plt.title(title)
        plt.xlabel("Jour de l'année ")
        plt.ylabel(what)
        plt.legend(title="Anneé", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

    @decoplotseaborn
    def seaborn_versus_plot(self, **kwargs):
        input = kwargs['input']
        what = kwargs['what']
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        sns.set_theme(style="whitegrid")
        sns.lineplot(data=input, x=what[0], y=what[1], hue='where',color='colors')
        plt.legend(title = "where", loc= "upper right",bbox_to_anchor=(1.04, 1))
        plt.xlabel(what[0])
        plt.ylabel(what[1])

    @decoplotseaborn
    @decohistseaborn
    def seaborn_hist_value(self, **kwargs):
        """
        Create a seaborn vertical histogram where the x-axis represents a numerical field.
        """
        input = kwargs['input']
        what = kwargs['what']
        sns = kwargs.get('sns')
        plt = kwargs.get('plt')
        sns.set_theme(style="whitegrid")
        sns.histplot(data=input, x=what, bins=24, color='blue', kde=True)
        plt.xlabel(what)
        plt.ylabel('Frequency')

    ######SEABORN HIST HORIZONTALE#########
    @decoplotseaborn
    @decohistseaborn
    def seaborn_hist_horizontal(self, **kwargs):
        """
        Create a seaborn horizontal histogram with which on x-axis.
        """
        input = kwargs['input']
        what = kwargs['what']
        title = kwargs.get('title')
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        legend = kwargs.get('legend',None)
        sns.set_theme(style="whitegrid")
        if kwargs['kwargsuser']['where']==[''] and 'sumall' in kwargs['kwargsuser']['option']:
            input['where'] = 'sum all location'
        input['where'] = [ (w[:10] + '…') if len(w) > 10 else w for w in input['where']]
        sns.barplot(data=input, x=what, y='where', palette="viridis", errorbar=None)
        #plt.title(title)
        plt.xlabel(what)
        plt.ylabel('')
        plt.xticks(rotation=45)


    ######SEABORN BOXPLOT#########
    @decoplotseaborn
    def seaborn_pie(self, **kwargs):
        """
        Create a seaborn pairplot
        """
        input = kwargs['input']
        what = kwargs['what']
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')
        sns.set_theme(style="whitegrid")
        plt.pie(input[what], labels=input['where'], autopct='%1.1f%%')
        plt.xlabel(what)
        plt.ylabel('')
        plt.xticks(rotation=45)

    ######SEABORN heatmap#########
    @decoplotseaborn
    def seaborn_heatmap(self, **kwargs):
        """
        Create a seaborn heatmap
        """
        PyvoaWarning("BEWARE !!! THIS visualisation need to be checked !!!")
        input = kwargs.get('input')
        what = kwargs['what']
        plt = kwargs.get('plt')
        sns = kwargs.get('sns')

        input['month'] = [m.month for m in input['date']]
        input['year'] = [m.year for m in input['date']]

        data_pivot = input.pivot_table(index='month', columns='year', values=what)

        total = data_pivot.sum().sum()

        sns.heatmap(data_pivot, annot=True, fmt=".1f", linewidths=.5, cmap='plasma')
        plt.xlabel('Year')
        plt.ylabel('Month')

        # Afficher le total en dehors du graphique
        plt.text(0, data_pivot.shape[0] + 1, f'Total: {total}', fontsize=12)
