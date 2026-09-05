
"""The catalogue of keyword arguments pyvoa accepts.

``InputOption`` holds the data-selection arguments (``where``, ``which``,
``what``, ``when``, ``option``, ``input``, ``output``) and the drawing ones
(``vis``, ``typeofplot``, ``typeofhist``, ``typeofmap``, ``tile`` and the
rest), each mapped to the values it accepts, the first of which is the default.
``front`` validates every user call against these two dictionaries.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
"""
import importlib

import pandas as pd

from pyvoa.tools import kwargs_keystesting

__all__ = ['InputOption']

class InputOption:
    """The catalogue of keyword arguments, and the values each one accepts.

    front validates every user call against the two dictionaries built here.
    """

    def __init__(self):
        """Build the catalogue of every keyword argument pyvoa accepts.

        Fills two dictionaries that the front class validates user input against:
        d_batchinput_args, the data selection ('where', 'which', 'what', 'when',
        'option', 'input', 'output'), and d_graphicsinput_args, the drawing
        options ('vis', 'typeofplot', 'typeofhist', 'typeofmap', 'tile', ...).
        Each entry maps a keyword to its accepted values, the first of which is
        the default. pdcharts records which backend supports which chart type,
        and dictpop the population scales used by the 'normalize:' options.
        """
        self.dictpop = {'pop':1.,'pop100':100,'pop1k':1e3,'pop10k':1e4,'pop100k':1e5,'pop1M':1e6}
        self.lpop = ['normalize:'+k for k in self.dictpop]
        self.d_batchinput_args  = {
                        'where':[''],\
                        'option':['','nonneg','smooth7','sumall']+\
                        [f'normalize:{k}' for k in self.dictpop],\
                        'which':'',\
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
                        'typeofplot':['date','compare','versus','spiral','yearly'],
                        'typeofmap':[None,'not dense','dense','folium'],\
                        'bins':10,\
                        'vis':['matplotlib','bokeh','seaborn'],\
                        'tile' : ['openstreet','esri','positron','stamen'],\
                        'orientation':['horizontal','vertical'],\
                        'dateslider':[False,True],\
                        'guideline':[False,True],\
                         #does None need here 'scale':[None,'linear','log']
                        'scale':['linear','log'],\
                        'maxlettersdisplayed':10
                        }

        self.pdcharts = pd.DataFrame({
            'matplotlib': ["'typeofplot'=['date', 'versus', 'yearly']","'typeofhist'=['location','value','pie']",\
                "'typeofmap'=[None,'not dense','dense']" ],
            'seaborn': ["'typeofplot'=['date', 'versus','yearly']","'typeofhist'=['location','value','pie']",False],
            'bokeh': ["'typeofplot'=['date', 'compare', 'versus', 'spiral', 'yearly']","'typeofhist'=['location','value','pie']",
            "'typeofmap'=[None,'not dense','dense']"]
            }, index=['plot', 'hist','map'])

        self.windows = {' daily':1,' weekly':7}
        self.listviskargskeys = list(self.d_graphicsinput_args.keys())
        self.dicokfront = {}

    def test_add_graphics_libraries(self,libraries):
        """Tests the presence of the specified graphical libraries."""
        results = {}
        for lib in libraries:
            try:
                importlib.import_module(lib)
                results[lib] = True
            except ImportError:
                results[lib] = False
        return results

    def setkwargsfront(self,kw):
        """Store the drawing options to apply to the following charts.

        Parameters
        ----------
        kw : dict
            the options to keep, checked against
            d_graphicsinput_args. An unknown key raises PyvoaError.
        """
        kwargs_keystesting(kw, list(self.d_graphicsinput_args.keys())+list(self.d_graphicsinput_args.keys()), 'Error with this resquest (not available in setoptvis)')
        self.dicokfront = kw

    def getkwargsfront(self):
        """Return the drawing options set by setkwargsfront().

        Returns
        -------
        dict
            the stored options, empty until setkwargsfront() is called.
        """
        return self.dicokfront
