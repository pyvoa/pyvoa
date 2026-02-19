
'''

# -*- coding: utf-8 -*-
Project : Pyvoa
Date :    april 2020 - november 2025
Authors : Olivier Dadoun, Julien Browaeys, Tristan Beau
Copyright ©pyvoa_org
License: See joint LICENSE file
https://pyvoa.org/

Date :    April 2020 - November 2025
'''

# --- Imports ----------------------------------------------------------
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
from functools import wraps
import numpy as np

import datetime as dt
from pyvoa.tools import (
    kwargs_keystesting,
    kwargs_valuestesting,
    debug,
    info,
    flat_list,
    all_or_none_lists,
    readpkl,
    set_verbose_mode
)

import pyvoa.geopd_builder as coco
from pyvoa.jsondb_parser import MetaInfo
from pyvoa.error import *
import pyvoa.geo as coge

import geopandas as gpd
from pyvoa.kwarg_options import InputOption
from pyvoa.visualizer import AllVisu
import pyvoa.help as h

from importlib import import_module
import ast

def getversion():
    try:
        version_module = import_module("pyvoa.__version__")
        return getattr(version_module, "__version__", "unknown")
    except Exception:
        return "unknown"

print(f"\033[1m\033[92m ✨ Welcome to PyVOA (version {getversion()}) ✨\033[0m")
print("See https://pyvoa.org")


class front:
    """Class for managing graphical data visualization and processing.

    This class provides methods to configure and utilize various graphical libraries for data visualization. It allows users to set visualization options, retrieve data in different formats, and manage the underlying database for graphical data.

    Attributes:
        meta (MetaInfo): Metadata information for the graphical data.
        av (InputOption): Input options for graphical input arguments.
        lvisu (list): List of available visualizations.
        available_libs (dict): Dictionary of available graphical libraries.
        lwhat (list): List of available 'what' options for data processing.
        lhist (list): List of available histogram types.
        loption (list): List of available options for data processing.
        ltiles (list): List of available tile options for maps.
        largument (list): List of available keyword argument keys for chart functions.
        listchartkargsvalues (list): List of available keyword argument values for chart functions.
        listviskargskeys (list): List of available visualization keyword argument keys.
        db (str): Current database name.
        gpdbuilder: Current GPDBuilder instance.
        vis: Current visualization setting.
        allvisu: All available visualizations.
        charts: Current chart settings.
        namefunction (str): Name of the currently set function.
        _setkwargsvisu (dict): Dictionary for visualization options.

    Methods:
        whattodo(): Generates a DataFrame summarizing available methods and their options.
        setwhom(base, **kwargs): Sets the current GPDBuilder database and optionally reloads it.
        get(**kwargs): Retrieves and processes data based on the specified output format.
        listoutput(): Returns the list of currently available output types for the get() function.
        listvis(): Returns the list of currently available visualizations for the map() function.
        listwhom(detailed=False): Returns the list of currently available GPDBuilders for geopd_builder data in Pyvoa.
        listwhat(): Returns the list of currently available types of series.
        listhist(): Returns the list of currently available types of histograms.
        listplot(): Returns the list of currently available types of plots.
        listoption(): Returns the list of currently available options applied to data.
        listtile(): Returns the list of currently available tile options for maps.
        listwhich(dbname=None): Gets the available fields for the specified database.
        listwhere(clustered=False): Gets the list of available regions/subregions managed by the current GPDBuilder.
        getdatabase(): Returns the main pandas DataFrame with all values loaded from the selected GPDBuilder.
        saveoutput(**kwargs): Exports pandas DataFrame as an output file.
        merger(**kwargs): Merges two or more pandas DataFrames from get_stats operation.
        savefig(name): Saves the current figure to a file.
    """

    def __init__(self):
        self.meta = MetaInfo()
        self.av = InputOption()
        self.lvisu = list(self.av.d_graphicsinput_args['vis'])
        self.lvisu.sort()
        available_libs = self.av.test_add_graphics_libraries(self.lvisu)
        for lib, available in available_libs.items():
            if not available:
                self.lvisu.remove(lib)
        PyvoaInfo("Available graphical librairies : " + str(self.lvisu))

        self.lwhat = list(self.av.d_batchinput_args['what'])
        self.lplot = list(self.av.d_graphicsinput_args['typeofplot'])
        self.loption = list(self.av.d_batchinput_args['option'])

        self.ltiles = list(self.av.d_graphicsinput_args['tile'])

        self.largument = self.av.listargument
        self.largumentvalue = self.av.listargumentvalue
        self.listviskargskeys = self.av.listviskargskeys

        self.lpop = self.av.lpop

        self.db = ''
        self.gpdbuilder = ''
        self.vis = None
        self.allvisu = None
        self.charts = None
        self.namefunction = None
        self._setkwargsvisu = None
        self.batch = False
        self.outcome = None

    def whattodo(self,):
        """Generates a DataFrame summarizing available methods and their options.

        This method constructs a DataFrame that combines information from two dictionaries:
        one containing graphics input arguments and another with visualization options.
        The resulting DataFrame is organized by method names and their corresponding
        available options.

        Returns:
            pd.DataFrame: A DataFrame with methods as the index and their available
            options listed in the columns. The DataFrame is sorted by the 'Arguments'
            column in descending order.

        Raises:
            None: This method does not raise any exceptions.
        """
        dico1 = {k:str(v) for k,v in self.av.d_batchinput_args.items()}
        dico2 = {k:str(v) for k,v in self.av.d_graphicsinput_args.items()}
        dico2['vis'] = self.lvisu
        def df(d,k):
            m = pd.DataFrame.from_dict(d.items())
            m['index'] = len(m)*[k]
            m=m.set_index('index')
            m.columns = ['Arguments', 'Available options']
            return m
        pd1 = df(dico1,'get, hist, map, plot, ')
        pd1.index = np.where(pd1.Arguments=='dateslider','hist, map', pd1.index)
        pd1.index = np.where(pd1.Arguments=='output','get', pd1.index)
        pd1.index = np.where(pd1.Arguments=='typeofhist','hist',pd1.index)
        pd1.index = np.where(pd1.Arguments=='typeofplot','plot', pd1.index)
        pd2 = df(dico2,'setoptvis')
        pd1=pd.concat([pd1,pd2])
        pd1.index = pd1.index.rename('Methods')
        pd1 = pd1.sort_values(by='Arguments',ascending = False)
        return pd1

    def setwhom(self,base,**kwargs):
        """Sets the current GPDBuilder database and optionally reloads it.

        This method updates the current database to the specified base if it is supported.
        If the `reload` parameter is set to True, it will reload the database; otherwise, it will read from a cached file.

        Args:
            base (str): The name of the GPDBuilder database to set as the current database.
            **kwargs: Additional keyword arguments that may be used for further customization.

        Raises:
            PyvoaError: If the `reload` parameter is not a boolean (0 or 1).
            PyvoaDbError: If the specified `base` is not in the list of supported GPDBuilders.

        Returns:
            None: This method does not return a value.
        """
        reload = kwargs.get('reload', True)
        if reload not in [0,1]:
            raise PyvoaError('reload must be a boolean ... ')
        if base not in self.listwhom():
            raise PyvoaDbError(base + ' is not a supported GPDBuilder. '
                                    'See pyvoa.fron.listwhom() for the full list.')
        # Check if the current base is already set to the requested base
        visu = self.getvis()
        if self.db == base:
            info(f"The GPDBuilder '{base}' is already set as the current database")
            print('Available key-words, which ∈', self.listwhich())
            return
        else:
            if reload:
                self.gpdbuilder, self.allvisu = coco.GPDBuilder.factory(db_name=base,reload=reload,vis=visu)
            else:
                self.gpdbuilder = readpkl(base + '.pkl')
                if self.gpdbuilder is None:
                   self.gpdbuilder, self.allvisu = coco.GPDBuilder.factory(db_name=base,reload=True,vis=visu)
                pandy = self.gpdbuilder.getwheregeometrydescription()
                self.allvisu = AllVisu(base, pandy)
                coge.GeoManager('name')
        self.db = base

    def help(self,):
        return h.display_full_help()

    def input_wrapper(func):
        """
        Decorator for handling input argument testing and formatting for
        geopandas builder methods. This decorator ensures that the input
        arguments are properly formatted and validated before passing them
        to the decorated function. It also handles specific cases for certain
        arguments, such as 'where', 'which', and 'option', by transforming
        them into lists if they are not already. The decorator also checks
        for compatibility between different visualization options and the
        requested function (e.g., 'get', 'plot', 'hist', 'map').
        Parameters
        ----------
        func : function
            The function to be decorated. This should be a callable function
            that takes the input arguments and performs the desired operation.
        Returns
        -------
        function
            The decorated function with input argument handling and validation.
        Raises
        PyvoaError
            If the input arguments are not properly formatted or if there
            are compatibility issues between different visualization options
            and the requested function.
        """
        @wraps(func)
        def wrapper(self,**kwargs):
            '''
                Wrapper input function .
                Wrap and format the user input argument for geopd_builder class
                if argument is missing fill with the default value
                Transforms 'where', 'which', and 'option' into lists if they are not already.
                order position of the items in 'option'
            '''

            if self.gpdbuilder == '' and kwargs['input'] is None and kwargs['which'] is None:
                raise PyvoaError("Does setwhom has been defined ???")

            if func.__name__ == 'get':
                if 'typeofhist' in list(kwargs.keys()) or 'typeofplot' in list(kwargs.keys()):
                    raise PyvoaError("Argument ERROR")
            elif func.__name__ == 'plot':
              if 'typeofhist' in list(kwargs.keys()):
                    raise PyvoaError("Argument ERROR")
            elif func.__name__ == 'hist':
              if 'typeofplot' in list(kwargs.keys()):
                    raise PyvoaError("Argument ERROR")
            elif func.__name__ == 'map':
              if 'typeofhist' in list(kwargs.keys()) or 'typeofplot' in list(kwargs.keys()):
                    raise PyvoaError("Argument ERROR")
            else:
                raise PyvoaError("What function is this "+func.__name__)

            if self.db == '' and kwargs['input'] is None:
                PyvoaError('Something went wrong ... does a db has been loaded ? (setwhom)')

            mustbealist = ['where','which','option']

            kwargs_keystesting(kwargs,self.largument + self.listviskargskeys,' kwargs keys not recognized ...')
            default = { k:[v[0]] if isinstance(v,list) else v for k,v in self.av.d_batchinput_args.items()}
            default['output'] = default['output'][0]
            default['input'] = kwargs.get('input')
            dicovisu = {k:kwargs.get(k,v[0]) if isinstance(v,list) else kwargs.get(k,v) for k,v in self.av.d_graphicsinput_args.items()}
            [kwargs_valuestesting(dicovisu[i],self.av.d_graphicsinput_args[i],'value of '+ i +' not correct') for i in ['typeofhist','typeofplot']]
            for k,v in default.items():
                if k in kwargs.keys() and k not in ['when','input']:
                    if isinstance(kwargs[k],list):
                        default[k] = kwargs[k]
                    else:
                        default[k] = [kwargs[k]]
                default['when'] = kwargs.get('when')
                default['input'] = kwargs.get('input',pd.DataFrame())

            kwargs = {**default, **dicovisu}
            kwargs['what'] = kwargs.get('what',kwargs['what'][0])
            if isinstance(kwargs['what'],list):
                kwargs['what'] = kwargs['what'][0]
            input = kwargs.get('input',pd.DataFrame())
            kwargs['kwargsuser'] = kwargs.copy()

            where =  kwargs['where']

            if kwargs['where'][0] == '':
                if input.empty:
                    if self.gpdbuilder:
                        kwargs['where'] = list(self.gpdbuilder.get_fulldb()['where'].unique())
                else:
                    kwargs['where'] = list(input['where'].unique())

            if not all_or_none_lists(kwargs['where']):
                raise PyvoaError('For coherence all the element in where must have the same type list or not list ...')

            if 'sumall' in kwargs['option']:
                kwargs['option'].remove('sumall')
                kwargs['option'].append('sumall')

            if 'sumall' in kwargs['option'] and len(kwargs['which'])>1:
                raise PyvoaError('sumall option incompatible with multiple variables... please keep only one variable!')

            if not input.empty:
                PyvoaWarning("In your DataFrame : the date must be in pd.to_datetime format !")
                if not all(i in input.columns for i in ['where', 'date']):
                    raise PyvoaError("Minimal requierement for your input pandas : 'where' AND 'date'  must be in the columns name")

                when = kwargs.get('when')

                #if not when:
                #    kwargs['when'] = input.date.min().strftime("%d/%m/%Y")+':'+input.date.max().strftime("%d/%m/%Y")
                #input = input.loc[input['where'].isin(kwargs['where'])]
                #kwargs['input'] = input
                kwargs['kwargsuser']['input'] = input

            if self.gpdbuilder != '':
                kwargs = self.gpdbuilder.get_stats(**kwargs)

            if self.db == '':
                    self.allvisu = AllVisu('', kwargs['input'])

            found_bypop = None
            for w in kwargs['option']:
                if w.startswith('normalize:'):
                    found_bypop = w
                    if kwargs['what'] == 'current':
                        ext =' '
                    else:
                        ext = ' '+kwargs['what']+' '
                    kwargs['what'] = [i+ ext +found_bypop for i in kwargs['which']]
                    kwargs['which'] = [i+ ' ' +found_bypop for i in kwargs['which']]
            if kwargs['what'] == 'current':
                kwargs['what'] = kwargs['which']

            return func(self,**kwargs)
        return wrapper

    def input_visuwrapper(func):
        """
        Decorator for ensuring single-variable input for histograms and maps.
        This decorator checks if the input arguments for the decorated function
        are properly formatted and validated before passing them to the
        decorated function. It ensures that the input arguments are compatible
        with the requested function (e.g., 'hist', 'map') and raises errors
        if there are compatibility issues.
        Parameters
        ----------
        func : function
            The function to be decorated. This should be a callable function
            that takes the input arguments and performs the desired operation.
            Returns
            -------
            function
                The decorated function with input argument handling and validation.
                Raises
                PyvoaError
                    If the input arguments are not properly formatted or if there
                    are compatibility issues between different visualization options
                    and the requested function.
        """
        @wraps(func)
        def inner(self,**kwargs):
            if self._setkwargsvisu is None:
                raise PyvoaError("vis is not set can you can not use charts functions  ...")
            kwargs['vis'] = self.vis
            if not 'get' in func.__name__:
                z = { **self.getkwargsvisu(), **kwargs }
            if self.getvis() is not None:
                if func.__name__ in ['hist','map']:
                    if isinstance(z['which'],list) and len(z['which'])>1:
                        raise PyvoaError("Histo and map available only for ONE variable ...")

                    #z['input'] = z['input'].sort_values(by=kwargs['which'], ascending=False).reset_index(drop=True)
                    if func.__name__ == 'map':
                            z.pop('typeofhist')
                            z.pop('typeofplot')
                            z.pop('bins')
                return func(self,**z)
            else:
                PyvoaWarning("Graphics asked can't be displayed, no visualization has been setted")
        return inner

    def decoget(func):
        @wraps(func)
        def inner(self,**kwargs):
            """Retrieve and process data based on the specified output format.

            This method accepts a pandas DataFrame as input and converts it into various formats
            such as pandas DataFrame, GeoPandas DataFrame, dictionary, list, or numpy array
            based on the 'output' keyword argument. It also logs memory usage for the DataFrame
            if the output is set to 'pandas'.

            Args:
                **kwargs: Arbitrary keyword arguments. Expected keys include:
                    - 'input': A pandas DataFrame to be processed.
                    - 'output': A string indicating the desired output format.
                                Options include 'pandas', 'geopandas', 'dict', 'list', or 'array'.

            Returns:
                The processed data in the specified output format.

            Raises:
                PyvoaError: If the specified output format is unknown.

            Notes:
                - If the output is 'pandas', the method will log the memory usage of the DataFrame.
                - If the output is 'geopandas', it merges the input DataFrame with geometry data.
                - If the output is 'dict', it converts the DataFrame to a dictionary.
                - If the output is 'list' or 'array', it converts the DataFrame to a list or numpy array respectively.
            """
            output = kwargs.get('output')
            pandy = kwargs.get('input')
            which = kwargs.get('which')[0]

            if 'geometry' not in list(pandy.columns):
                output = 'pandas'
            if isinstance(output,list):
                output=output[0]
            self.setnamefunction(self.get)
            if output == 'pandas':
                def color_df(val):
                    if val.columns=='date':
                        return 'blue'
                    elif val.columns=='where':
                        return 'red'
                    else:
                        return black

                if 'geometry' in list(pandy.columns):
                    pandy = pandy.drop(columns='geometry')
                casted_data = pandy
                col=list(pandy.columns)
                mem='{:,}'.format(pandy[col].memory_usage(deep=True).sum())
                info('Memory usage of all columns: ' + mem + ' bytes')
            elif output == 'geopandas':
                if 'geometry' in list(pandy.columns):
                    casted_data = pandy
                else:
                    casted_data = pd.merge(pandy, self.gpdbuilder.getwheregeometrydescription(), on='where')
                    casted_data = gpd.GeoDataFrame(casted_data)
            elif output == 'dict':
                casted_data = pandy.to_dict('split')
            elif output == 'list' or output == 'array':
                my_list = []
                for keys, values in pandy.items():
                    vc = [i for i in values]
                    my_list.append(vc)
                casted_data = my_list
                if output == 'array':
                    casted_data = np.array(pandy)
            else:
                raise PyvoaError('Unknown output.')

            last_rows = casted_data[ casted_data.date == casted_data.date.max() ]
            last_rows = last_rows.sort_values(by=kwargs["which"][0], ascending=False)
            where_ordered_bylastvalues = last_rows['where'].tolist()
            casted_data['where'] = pd.Categorical(
                casted_data['where'],
                categories=where_ordered_bylastvalues,
                ordered=True
            )
            kwargs['whereordered'] = where_ordered_bylastvalues
            casted_data = casted_data.sort_values(['where','date']).reset_index(drop=True)
            kwargs['input'] = casted_data
            return func(self,**kwargs)
        return inner

    @input_wrapper
    @decoget
    def get(self,**kwargs):
        return kwargs['input']

    def decomap(func):
        @wraps(func)
        def inner(self,**kwargs):
            """Inner function to process input parameters and modify geometry settings.

            Args:
                self: The instance of the class.
                **kwargs: Additional keyword arguments that may include:
                    - where (str): A condition to filter data.
                    - output: Optional output parameter (ignored in processing).
                    - bypop: Optional population parameter (ignored in processing).
                    - dateslider: Optional date slider parameter (default is None).
                    - input (DataFrame): Input data that may be modified based on geometry settings.

            Returns:
                The result of the function `func` after processing the input parameters.

            Raises:
                Any exceptions raised by the `func` or during the processing of geometry settings.
            """
            input = kwargs.get('input')
            originalinput = input.copy()
            if 'geometry' not in list(input.columns):
                raise PyvoaError('No geometry inside your pandas, map can not be asked')
            where = kwargs.get('where')

            mapoption = kwargs.get('typeofmap',None)

            if isinstance(self.gpdbuilder.gettypeofgeometry(), coge.GeoCountry):
                mapoption = kwargs.get('typeofmap','not dense')
            else:
                PyvoaWarning('typeofmap not compatible with this db, dummy argument')
                mapoption = None

            if 'output' in kwargs:
                kwargs.pop('output')
            if 'pop' in kwargs:
                kwargs.pop('pop')
            dateslider = kwargs.get('dateslider', None)

            if mapoption:
                if 'folium' in mapoption:
                    mapoption.remove('folium')
                    print(self.av.test_add_graphics_libraries(['folium']))
                    #self.setvis('folium')
                if mapoption == 'dense':
                    self.gpdbuilder.gettypeofgeometry().set_dense_geometry()
                    new_geo = self.gpdbuilder.geo.get_data()
                    granularity = self.meta.getcurrentmetadata(self.db)['geoinfo']['granularity']
                    new_geo = new_geo.rename(columns={'name_'+granularity:'where'})
                    new_geo['where'] = new_geo['where'].apply(lambda x: x.upper())
                    new_geo = new_geo.set_index('where')['geometry'].to_dict()
                    input['geometry'] = input['where'].apply(lambda x: x.upper()).map(new_geo)
                    input['where'] = input['where'].apply(lambda x: x.title())
                    kwargs['input'] = input
                else:
                    #if not self.gpdbuilder.gettypeofgeometry().is_exploded_geometry():
                    kwargs['input'] = input
            return func(self,**kwargs)
        return inner

    def decohist(func):
        @wraps(func)
        def inner(self,**kwargs):
            """Inner method to generate a histogram visualization based on provided keyword arguments.

            Args:
                **kwargs: Arbitrary keyword arguments that may include:
                    - typeofhist: The type of histogram to generate.
                    - output: This argument is removed from kwargs and not used.
                    - pop: If present, this argument is removed from kwargs and not used.

            Raises:
                PyvoaError: If no visualization has been set up.

            Returns:
                The result of the visualization function applied to the generated histogram outcome.
            """
            dateslider = kwargs.get('dateslider')
            typeofhist = kwargs.get('typeofhist')
            if self.getvis() == 'bokeh' and 'geometry' in kwargs['input'].columns:
                kwargs['input'] = kwargs['input'].drop(columns='geometry')
            if kwargs.get('pop'):
              kwargs.pop('pop')
            if self.getvis():
                z = { **self.getkwargsvisu(), **kwargs  }
                if self.getvis() != 'bokeh' and typeofhist == 'location' :
                    return func(self,self.allvisu.hist(**z)[0])
                else:
                    print(z)
                    return func(self,self.allvisu.hist(**z))
            else:
                raise PyvoaError(" No visualization has been set up !")
        return inner

    @input_wrapper
    @input_visuwrapper
    @decoget
    @decomap
    def map(self,**kwargs):
        """Maps the visualization with the provided keyword arguments.

        This method checks if a display is set up. If it is, it combines the visualization keyword arguments with the provided keyword arguments and applies the mapping. If no display is set up, it raises a `PyvoaError`.

        Args:
            **kwargs: Additional keyword arguments to be passed to the mapping function.

        Returns:
            The outcome of the mapping operation.

        Raises:
            PyvoaError: If no visualization has been set up.
        """
        self.setnamefunction(self.map)
        if self.getvis():
            z = {**kwargs , **self.getkwargsvisu()}
            fig = self.allvisu.map(**z)
            #return self.outcome
        else:
            raise PyvoaError(" No visualization has been set up !")
        #fig = self.outcome
        if self.getvis() == 'bokeh':
            from bokeh.io import (
            show,
            )
            if not self.batch:
                show(fig)
        else:
            import matplotlib.pyplot as plt
            if not self.batch:
                plt.show()
            self.outcome = fig
            return fig

    @input_wrapper
    @input_visuwrapper
    @decoget
    @decohist
    def hist(self,fig):
        """Generates and displays a histogram figure.

        This method sets the function name, stores the provided figure, and displays it using the appropriate visualization library based on the current display setting.

        Args:
            fig: The figure object to be displayed, typically a histogram.

        Returns:
            The figure object if the display setting is not 'bokeh'.

        Raises:
            ImportError: If 'bokeh' is specified but the library is not installed.
        """
        self.setnamefunction(self.hist)
        if self.getvis() == 'bokeh':
            from bokeh.io import (
            show,
            )
            if not self.batch:
                if fig:
                    show(fig)
        else:
            import matplotlib.pyplot as plt
            if not self.batch:
                plt.show()
            self.outcome = fig
            return fig

    def decoplot(func):
        @wraps(func)
        def inner(self,**kwargs):
            """Inner method to plot visualization based on provided keyword arguments.

            This method checks if a display is set up and, if so, merges the visualization keyword arguments with any additional keyword arguments provided. It then calls the plotting function and returns the outcome. If no display is set up, it raises a PyvoaError.

            Args:
                **kwargs: Additional keyword arguments to be passed to the plotting function.

            Returns:
                The outcome of the plotting function.

            Raises:
                PyvoaError: If no visualization has been set up.
            """
            input=kwargs['input']

            which = kwargs.get('which')
            typeofplot = kwargs.get('typeofplot',self.listplot()[0])
            if kwargs.get('output'):
                kwargs.pop('output')

            if typeofplot == 'versus' and len(which)>2:
                PyvoaError(" versu can be used with 2 variables and only 2 !")
            if kwargs.get('pop'):
                kwargs.pop('pop')
            if self.getvis():
                z = {**self.getkwargsvisu(),**kwargs}
                return func(self,self.allvisu.plot(**z))
            else:
                PyvoaError(" No visualization has been set up !")
        return inner

    @input_wrapper
    @input_visuwrapper
    @decoget
    @decoplot
    def plot(self,fig):
        """Plots the given figure using the appropriate display method.

        This method checks the current display setting and uses Bokeh to show the plot if the display is set to 'bokeh'. If the display is not set to 'bokeh', it simply returns the figure.

        Args:
            fig: The figure to be plotted.

        Returns:
            If the display is not 'bokeh', returns the input figure. Otherwise, displays the figure using Bokeh.
        """
        self.setnamefunction(self.plot)
        ''' show plot '''
        if self.getvis() == 'bokeh':
            from bokeh.io import (
            show,
            )
            if not self.batch:
                show(fig)
        else:
            import matplotlib.pyplot as plt
            if not self.batch:
                plt.show()
                self.outcome = fig
            return fig

    def setnamefunction(self,name):
        """Sets the name of the function.

        This method assigns the name of the provided function to the instance variable `namefunction`.

        Args:
            name (function): The function whose name will be assigned to `namefunction`.

        Returns:
            None
        """
        # self.namefunction = name : it updates the visu + redraws the last chart
        self.namefunction = name.__name__

    def getnamefunction(self,):
        """Retrieves the name of the function.

        Returns:
            str: The name of the function associated with the instance.
        """

        return self.namefunction

    def listoutput(self,):
        """Returns a list of output values from the batch input arguments.

        This method retrieves the 'output' key from the `d_batchinput_args` dictionary
        of the `av` attribute and converts it into a list.

        Returns:
            list: A list containing the output values.
        """
        return list(self.av.d_batchinput_args['output'])

    def listvis(self,):
        """Returns the visualization list.

        This method retrieves the visualization list associated with the instance.

        Returns:
            list: The visualization list.
        """
        if 'seaborn' in self.lvisu:
            self.lvisu.remove('seaborn')
        return self.lvisu

    def listmap(self,):
        optmap = [ i for i in list(self.av.d_graphicsinput_args['typeofmap']) if i ]
        if 'folium' in optmap:
            optmap.remove('folium')
        return optmap

    def listwhom(self, detailed = False):
        """Lists the names of databases and their associated metadata.

        Args:
            detailed (bool, optional): If True, returns a detailed DataFrame containing database names, ISO3 codes, granularity, and variables. Defaults to False.

        Returns:
            list or pd.DataFrame:
                - If detailed is False, returns a list of database names.
                - If detailed is True, returns a DataFrame with columns for database names, ISO3 codes, granularity, and variables.

        Raises:
            PyvoaError: If the detailed argument is not a boolean.
        """
        allpd  = self.meta.getallmetadata()
        namedb = allpd.name.to_list()
        namedb.sort()

        if detailed:
            dico = {}
            namels, iso3ls, grls, varls = [],[],[],[]
            for i in namedb:

                mypd = allpd.loc[allpd.name.isin([i])]
                if mypd.validejson.values  == 'GOOD':
                    namels.append(i)
                    iso3 = mypd.parsingjson.values[0]['geoinfo']['iso3']
                    iso3ls.append(iso3)
                    gr = mypd.parsingjson.values[0]['geoinfo']['granularity']
                    grls.append(gr)
                    for datasets in mypd.parsingjson.values[0]['datasets']:
                        pdata = pd.DataFrame(datasets['columns'])
                    varls.append(self.listwhich(i))

            dico.update({'dbname': namels})
            dico.update({'iso3': iso3ls})
            dico.update({'granularity': grls})
            dico.update({'variables': varls})
            return pd.DataFrame.from_dict(dico, orient='index').T.reset_index(drop=True).set_index('dbname')
        else:
            return namedb

    def listwhat(self,):
        """Returns the value of the lwhat attribute.

        This method retrieves the current value of the lwhat attribute from the instance.

        Returns:
            The value of the lwhat attribute.
        """
        return self.lwhat

    def listchart(self,):
        if self.vis == None:
            raise PyvoaError('Vis has not be set !')
        return self.av.pdcharts[self.vis]

    def listhist(self,):
        """Returns the list histogram.

        This method retrieves the histogram of the list stored in the instance.

        Returns:
            list: The list histogram.
        """
        if self.vis == None:
            raise PyvoaError('Vis has not be set !')
        self.lhist = self.av.pdcharts[self.vis]['hist']
        self.lhist = ast.literal_eval(self.lhist.split("=", 1)[1])
        return self.lhist

    def listplot(self,):
        """Returns a list of the types of plots from the graphics input arguments.

        This method retrieves the 'typeofplot' key from the
        'd_graphicsinput_args' attribute of the 'av' object and
        returns it as a list.

        Returns:
            list: A list containing the types of plots.
        """
        if self.vis == None:
            raise PyvoaError('Vis has not be set !')
        self.lplot = self.av.pdcharts[self.vis]['plot']
        self.lplot = ast.literal_eval(self.lplot.split("=", 1)[1])
        return self.lplot

    def listoption(self,):
        """Returns the value of the loption attribute.

        This method retrieves the current value of the loption attribute from the instance.

        Returns:
            The value of the loption attribute.
        """
        return [x for x in self.loption if x != '']

    def listargument(self,):
        """Returns the keys of the largument attribute.

        This method retrieves the keys stored in the largument attribute of the instance.

        Returns:
            list: A list of keys from the largument attribute.
        """
        return self.largument

    def listargumentvalue(self,):
        """Returns the values of the lchartkargs attribute.

        This method retrieves the values stored in the lchartkargsvalues attribute of the instance.

        Returns:
            list: The values of the lchartkargsvalues attribute.
        """
        return self.largumentvalue

    def listtile(self,):
        """Returns the list of tiles.

        This method retrieves the current list of tiles stored in the instance.

        Returns:
            list: A list containing the tiles.
        """
        if self.av.pdcharts[self.vis]['map']:
            return self.ltiles
        else:
            raise PyvoaError(self.vis+ ' : has not map function !')

    def listwhich(self,dbname=None):
        """Lists the current metadata for a specified database.

        This method retrieves the current metadata for the given database name. If no database name is provided, it uses the default database associated with the instance. If neither is available, it raises an error.

        Args:
            dbname (str, optional): The name of the database for which to list the metadata. If not provided, the default database will be used.

        Returns:
            list: A sorted list of metadata associated with the specified database.

        Raises:
            PyvoaError: If no database name is provided and no default database is set.
        """
        if dbname:
            dic = self.meta.getcurrentmetadata(dbname)

        elif self.db:
            dic = self.meta.getcurrentmetadata(self.db)
        else:
            raise PyvoaError('listwhich for which database ? I am lost ... are you ?')
        return sorted(self.meta.getcurrentmetadatawhich(dic))

    def listwhere(self,clustered = False):
        """Lists regions or countries based on the current metadata and specified granularity.

        Args:
            clustered (bool): If True, returns a clustered list of regions. Defaults to False.

        Returns:
            list or str: A list of region names or a single country code, depending on the granularity and the clustered flag.

        Raises:
            PyvoaError: If the granularity of the database is not recognized.

        Notes:
            The function retrieves the current metadata to determine the granularity and ISO3 code.
            If the granularity is 'country' and the code is not 'WLD' or 'EUR', it returns the country code.
            If clustered is True, it returns a list of regions based on the ISO3 code.
            If clustered is False, it returns a list of countries based on the granularity and the current database settings.
        """
        granularity = self.meta.getcurrentmetadata(self.db)['geoinfo']['granularity']
        code = self.meta.getcurrentmetadata(self.db)['geoinfo']['iso3']
        def clust():
            if granularity == 'country' and code not in ['WLD','EUR']:
                return  self.gpdbuilder.geo.to_standard(code)
            else:
                r = self.gpdbuilder.geo.get_region_list()
                if not isinstance(r, list):
                    r=sorted(r['name_region'].to_list())
                r.append(code)
                if code  == 'EUR':
                    r.append('European Union')
                return r

        if granularity == 'country' and code not in ['WLD','EUR']:
            return code
        if clustered:
            return clust()
        else:
            if self.gpdbuilder.db_world == True:
                if granularity == 'country' and code not in ['WLD','EUR'] :
                    r =  self.gpdbuilder.to_standard(code)
                else:
                    if code == 'WLD':
                        r = self.gpdbuilder.geo.get_GeoRegion().get_countries_from_region('World')
                    else:
                        r = self.gpdbuilder.geo.get_GeoRegion().get_countries_from_region('Europe')
                    r = [self.gpdbuilder.geo.to_standard(c)[0] for c in r]
            else:
                if granularity == 'subregion':
                    pan = self.gpdbuilder.geo.get_subregion_list()
                    r = list(pan.name_subregion.unique())
                elif granularity == 'region':
                    pan = self.gpdbuilder.geo.get_region_list()
                    r = list(pan.name_region.unique())
                elif granularity == 'country':
                    r = clust()
                    r.append(code)
                else:
                    raise PyvoaError('What is the granularity of your DB ?')
            return r

    def listpop(self):
        """
        Returns a list of keys from the dictionary `lpop`.
        """
        return self.lpop

    def getwhom(self, db = None, detailed=False,return_error=True):
        """Retrieves the database instance associated with the current object.

        Args:
            return_error (bool): A flag indicating whether to return an error if the database instance is not available. Defaults to True.
            detailed (bool): If True, displays detailed information about the database instance. Defaults to False.

        Returns:
            The database instance associated with the current object.
        """
        if db:
            if detailed:
                l=self.listwhom(True)
                print(l[l.index == db])
                return None
        else:
            if self.db=='':
                if return_error:
                    raise PyvoaError('Something went wrong ... does a db has been loaded ? (setwhom)')
                else:
                    return None
            if detailed:
                l=self.listwhom(True)
                print(l[l.index==self.db])
            return self.db

    def getdbmetadata(self,db=None):
        if db:
            if db in self.listwhom():
               return self.meta.getcurrentmetadata(db)
            else:
                PyvoaError('Database is not in the pyvoa listing, please have a look ...')

        else:
            raise PyvoaError('Database has not been defined')

    def getwhichinfo(self, which=None):
        """Retrieves information based on the specified keyword.

        Args:
            which (str, optional): The keyword for which information is to be retrieved.
                If provided, the function will print the keyword's definition and its associated URL.
                If not provided, the function will return the database description.

        Raises:
            PyvoaError: If the provided keyword does not exist in the database.

        Returns:
            DataFrame: The database description if no keyword is specified.
        """
        if which:
            if which in self.listwhich(self.db):
                print(self.gpdbuilder.get_parserdb().get_keyword_definition(which))
                print('Parsed from this url:',self.gpdbuilder.get_parserdb().get_keyword_url(which))
            else:
                raise PyvoaError('This value do not exist please check.'+'Available variable so far in this db ' + str(self.listwhich()))
        else:
            df = self.gpdbuilder.get_parserdb().get_dbdescription()
            return df

    def getdatabase(self):
        """Retrieves the full database and logs its memory usage.

        This method fetches the complete database from the `gpdbuilder` object, calculates the total memory usage of all columns, and logs this information. It then returns the full database as a DataFrame.

        Returns:
            pandas.DataFrame: The full database retrieved from the `gpdbuilder`.
        """
        col = list(self.gpdbuilder.get_fulldb().columns)
        mem='{:,}'.format(self.gpdbuilder.get_fulldb()[col].memory_usage(deep=True).sum())
        info('Memory usage of all columns: ' + mem + ' bytes')
        df = self.gpdbuilder.get_fulldb()
        return df

    def setkwargsvisu(self,**kwargs):
        """Sets visualization parameters using keyword arguments.

        This method updates the internal dictionary of visualization parameters.
        If the internal dictionary `_setkwargsvisu` already exists, it updates
        the existing keys with the provided values only if the values are truthy.
        If `_setkwargsvisu` does not exist, it initializes it with the provided
        keyword arguments.

        Args:
            **kwargs: Arbitrary keyword arguments representing visualization parameters.
                       Only keys with truthy values will be set in the internal dictionary.

        Returns:
            None
        """
        if self._setkwargsvisu:
            for k,v in kwargs.items():
                if v:
                    self._setkwargsvisu[k] = v
        else:
            self._setkwargsvisu = kwargs

    def getkwargsvisu(self,):
        return self._setkwargsvisu

    def setvis(self,vis=' '):
        """Sets the visualization and updates the keyword arguments for the visualization settings.

        Args:
            **kwargs: Arbitrary keyword arguments that may include visualization settings.

        Raises:
            PyvoaError: If the specified visualization is not implemented.

        Notes:
            This method retrieves default visualization settings from the object's graphics input arguments,
            updates them with any provided keyword arguments, and checks if the specified visualization is
            available. If it is, the visualization is set, and a confirmation message is logged. Otherwise,
            an error is raised.

        Example:
            setvis('example_visualization')
        """
        if vis not in self.lvisu:
            raise PyvoaError("Sorry but " + vis + " visualisation isn't installed ")
        else:
            self.vis = vis
            PyvoaInfo(f"The visualization has been set correctly to: {vis}")
        self.setkwargsvisu(**{'vis':vis})

    def setbatch(self,):
        self.batch = True

    def getvis(self,):
        """Returns the display attribute of the instance.

        This method retrieves the value of the `vis` attribute from the instance.

        Returns:
            The value of the `vis` attribute.
        """
        return self.vis

    def saveoutput(self,**kwargs):
        """Save output to a specified format.

        This method saves a pandas DataFrame to a file in the specified format. It requires a pandas DataFrame to be provided and allows for customization of the save format and file name.

        Args:
            **kwargs: Keyword arguments that can include:
                - pandas (pd.DataFrame): The DataFrame to save. This is mandatory.
                - saveformat (str): The format to save the DataFrame in. Default is 'excel'.
                - savename (str): The name of the file to save the DataFrame as. Default is an empty string.

        Raises:
            PyvoaError: If the provided DataFrame is empty or if mandatory arguments are not provided.

        Returns:
            None
        """
        global _db
        kwargs_keystesting(kwargs, ['pandas','saveformat','savename'], 'Bad args used in the pyvoa.saveoutput function.')
        pandy = kwargs.get('pandas', pd.DataFrame())
        saveformat = kwargs.get('saveformat', 'excel')
        savename = kwargs.get('savename', '')
        if pandy.empty:
            raise PyvoaError('Pandas to save is mandatory there is not default !')
        else:
            _db.saveoutput(pandas=pandy,saveformat=saveformat,savename=savename)

    def merger(self,**kwargs):
        """Merger function that integrates provided data into the database.

        This function takes keyword arguments and specifically looks for a key
        named 'coapandas'. It validates the arguments and then calls the
        database merger function with the provided data.

        Args:
            **kwargs: Arbitrary keyword arguments. Must include:
                - 'coapandas' (list): A list of data to be merged into the database.

        Raises:
            ValueError: If invalid arguments are provided.

        Returns:
            The result of the database merger operation.
        """
        global _db
        kwargs_keystesting(kwargs,['coapandas'], 'Bad args used in the pyvoa.merger function.')
        listpandy = kwargs.get('coapandas',[])
        return _db.merger(coapandas = listpandy)

    def savefig(self,name):
        """Saves the current figure to a file.

        This method checks the display type and saves the figure accordingly. If the display type is 'bokeh', it uses the Bokeh library to export the figure as a PNG file. Otherwise, it uses the standard savefig method. If the name function is 'get', it raises a PyvoaError indicating that saving is not allowed for a pandas DataFrame.

        Args:
            name (str): The name of the file to save the figure as.

        Raises:
            PyvoaError: If the name function is 'get', indicating that saving a pandas DataFrame is not permitted.
        """
        if  self.getnamefunction() != 'get':
            if self.getvis() == 'bokeh':
                ''' Not so easy to save a png with bokeh ... error from geckodriver and Chromium
                from bokeh.io import export_png
                try:
                    import bokeh
                except:
                    raise PyvoaError('selenium is needed ... pip install selenium')
                export_png(self.outcome, filename=name)
                '''
                from bokeh.plotting import figure, output_file, save
                output_file(name+'.html')
                save(self.outcome)
                #
            else:
                    self.outcome.figure.savefig(name)
            print('Figure :', name, ' has been saved ')
        else:
            PyvoaError('savefig can\'t be used to store a panda DataFrame')

# this trick allow you to do
# import pyvoa.front as pv
# pv.setwhom(...)
# pv.map(...)

__pyvoafront_instance__ = front()

from pyvoa.__version__ import __version__,__author__,__email__
__pyvoafront_instance__.__version__ = __version__
__pyvoafront_instance__.__author__ = __author__
__pyvoafront_instance__.__email__ = __email__

import sys
module = sys.modules[__name__]

for attr_name in dir(__pyvoafront_instance__):
    if not attr_name.startswith("_") and callable(getattr(__pyvoafront_instance__, attr_name)):
        setattr(module, attr_name, getattr(__pyvoafront_instance__, attr_name))
