# -*- coding: utf-8 -*-

"""
Project : PyvoA
Date :    april 2020 - march 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_fr
License: See joint LICENSE file
https://pyvoa.org/

Module : pyvoa.kwarg_options

About :
-------

An interface module to easily plot pycoa_data with bokeh

"""
from pyvoa.tools import kwargs_keystesting
from pyvoa.error import *
import math
import pandas as pd
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

import bisect
from functools import wraps

__all__ = ['InputOption']

class InputOption():
    """
        Option visualisation !
    """
    def __init__(self):
        self.dictpop = {'pop':1.,'pop100':100,'pop1k':1e3,'pop100k':1e5,'pop1M':1e6}
        self.lpop = ['normalize:'+k for k in self.dictpop.keys()]
        self.d_batchinput_args  = {
                        'where':[''],\
                        'option':['','nonneg','smooth7','sumall']+\
                        [f'normalize:{k}' for k in self.dictpop.keys()],\
                        'which':[''],\
                        'what':['current','daily','weekly'],\
                        'when':'',\
                        'input':pd.DataFrame(),\
                        'output':['geopandas','pandas','list','dict','array']
                        }
        self.listargument = list(self.d_batchinput_args.keys())
        self.listargumentvalue = list(self.d_batchinput_args.values())

        self.d_graphicsinput_args = {
                        'title':'Pyvoa charts',\
                        'copyright': 'pyvoa',\
                        'mode':['mouse','vline','hline'],\
                        'typeofhist':['location','value','pie'],\
                        'typeofplot':['date','compare','versus','spiral','yearly'],\
                        'bins':10,\
                        'vis':['matplotlib','bokeh','folium','seaborn'],\
                        'tile' : ['openstreet','esri','stamen','positron'],\
                        'orientation':['horizontal','vertical'],\
                        'dateslider':[False,True],\
                        'mapoption':['text','textinteger','spark','label%','log','unsorted','dense'],\
                        'guideline':[False,True],\
                        'ax_type':['linear', 'log']
                        }

        self.pdcharts = pd.DataFrame({
            'matplotlib': ["'typeofplot'=['date', 'versus', 'yearly']","'typeofhist'=['location','value','pie']",\
                "['dense']" ],
            'seaborn': ["'typeofplot'=['date', 'versus','yearly']","'typeofhist'=['location','value','pie']",False],
            'bokeh': ["'typeofplot'=['date', 'compare', 'versus', 'spiral', 'yearly']","'typeofhist'=['location','value','pie']",
            "['text','textinteger','spark','label%','log','unsorted','dense']"]
            }, index=['plot', 'hist','map'])

        self.listviskargskeys = list(self.d_graphicsinput_args.keys())
        self.dicokfront = {}

    def test_add_graphics_libraries(self,libraries):
        '''
            Tests the presence of the specified graphical libraries
        '''
        results = {}
        for lib in libraries:
            try:
                importlib.import_module(lib)
                results[lib] = True
            except ImportError:
                results[lib] = False
        return results

    def setkwargsfront(self,kw):
        kwargs_keystesting(kw, list(self.d_graphicsinput_args.keys())+list(self.d_graphicsinput_args.keys()), 'Error with this resquest (not available in setoptvis)')
        self.dicokfront = kw

    def getkwargsfront(self):
        return self.dicokfront
