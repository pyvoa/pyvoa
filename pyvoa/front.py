
"""The user-facing front end of pyvoa.

Defines the ``front`` class and instantiates it once, then exposes every one of
its methods at module level, so that ``import pyvoa.front as pf`` gives direct
access to ``pf.setwhom()``, ``pf.get()``, ``pf.plot()``, ``pf.hist()`` and
``pf.map()``.

The four chart methods share one pipeline, built from stacked decorators:
``input_wrapper`` validates and fills in the keyword arguments,
``input_visuwrapper`` refuses what the chosen backend cannot draw, ``decoget``
casts the result to the requested output type, and ``decoplot`` / ``decohist``
/ ``decomap`` build the figure. Because ``functools.wraps`` carries the
innermost docstring outward, the public contract of each method is documented
on its innermost definition.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
"""

# --- Imports ----------------------------------------------------------
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
#warnings.filterwarnings("ignore", category=DeprecationWarning, module='jupyter_client')
#warnings.simplefilter(action="ignore", category=DeprecationWarning, module='jupyter_client')

import ast
import random
from functools import wraps
from importlib import import_module

import geopandas as gpd
import numpy as np
import pandas as pd

import pyvoa.geo as coge
import pyvoa.geopd_builder as coco
import pyvoa.help as h
from pyvoa.jsondb_parser import MetaInfo
from pyvoa.kwargs_options import InputOption
from pyvoa.tools import (
    PyvoaError,
    PyvoaInfo,
    PyvoaWarning,
    all_or_none_lists,
    convertmercator,
    fill_missing_dates,
    get_live_mode,
    info,
    kwargs_keystesting,
    kwargs_values_testing,
    readpkl,
    set_live_mode,
)

# Aliased, and deliberately so. The loop at the foot of this module copies every
# public method of the singleton onto the module, which overwrites a module
# global of the same name: were these imported under their own names, the
# methods below would call themselves and recurse. setlive() escapes the same
# trap only because set_live_mode() happens to be spelled differently.
from pyvoa.tools import get_verbose_mode as _get_verbose_mode
from pyvoa.tools import set_verbose_mode as _set_verbose_mode
from pyvoa.visualizer import AllVisu


def getversion():
    """Return the installed pyvoa version, for the welcome message.

    Imports pyvoa.__version__ lazily and falls back to 'unknown' rather than
    raising, so that a broken or partial installation still prints a banner
    instead of failing at import time.

    Returns
    -------
    str
        the version, or 'unknown'.
    """
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

    Attributes
    ----------
    meta : MetaInfo
        Metadata information for the graphical data.
    av : InputOption
        Input options for graphical input arguments.
    lvisu : list
        List of available visualizations.
    available_libs : dict
        Dictionary of available graphical libraries.
    lwhat : list
        List of available 'what' options for data processing.
    lhist : list
        List of available histogram types.
    loption : list
        List of available options for data processing.
    ltiles : list
        List of available tile options for maps.
    largument : list
        List of available keyword argument keys for chart functions.
    listchartkargsvalues : list
        List of available keyword argument values for chart functions.
    listviskargskeys : list
        List of available visualization keyword argument keys.
    db : str
        Current database name.
    gpdbuilder
        Current GPDBuilder instance.
    vis
        Current visualization setting.
    allvisu
        All available visualizations.
    charts
        Current chart settings.
    namefunction : str
        Name of the currently set function.
    _setkwargsvisu : dict
        Dictionary for visualization options.
    """

    def __init__(self):
        """Build the pyvoa front end.

        Instantiates the database catalogue and the keyword-argument catalogue,
        detects which of the three visualisation backends are actually
        installed, and caches the lists the list*() methods answer with. No
        database is selected and no backend is chosen at this point: setwhom()
        and setvis() do that.
        """
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
        self.gpdbuilder = None
        self.gpdbuilderdata = None
        self.gpdbuildergeo = None
        self.vis = None
        self.allvisu = None
        self.charts = None
        self.namefunction = None
        self._setkwargsvisu = None
        self.batch = False
        self.outcome = None

    def whattodo(self,):
        """Generate a DataFrame summarizing available methods and their options.

        This method constructs a DataFrame that combines information from two dictionaries:
        one containing graphics input arguments and another with visualization options.
        The resulting DataFrame is organized by method names and their corresponding
        available options.

        Returns
        -------
        pd.DataFrame
            A DataFrame with methods as the index and their available
            options listed in the columns. The DataFrame is sorted by the 'Arguments'
            column in descending order.

        Raises
        ------
        None
            This method does not raise any exceptions.
        """
        dico1 = {k:str(v) for k,v in self.av.d_batchinput_args.items()}
        dico2 = {k:str(v) for k,v in self.av.d_graphicsinput_args.items()}
        dico2['vis'] = self.lvisu
        def df(d,k):
            """Turn one argument dictionary into a two-column frame.

            Parameters
            ----------
            d : dict
                argument name -> accepted values.
            k : str
                the methods these arguments belong to, used as the index.

            Returns
            -------
            pd.DataFrame
                columns 'Arguments' and 'Available options'.
            """
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

    def setlive(self,live=True):
        """Chooses where the data are downloaded from.

        By default, pyvoa reads every file from a frozen Zenodo archive, so that
        a given release always returns the same data. Calling setlive(True)
        switches to the live upstream sources, i.e. the 'urlparent' field of the
        json database description files for the epidemiological data.

        The live sources are the most recent ones, but they may have moved,
        changed format or disappeared. Some datasets have no live source
        declared; those keep using the archive and a warning is issued.

        Parameters
        ----------
        live : bool
            True to use the live sources, False for the archive.

        Returns
        -------
        bool
            The data source mode which has been set.
        """
        if live not in [0,1]:
            raise PyvoaError('live must be a boolean ... ')
        previous = get_live_mode()
        set_live_mode(live)
        if get_live_mode() != previous:
            # the currently loaded database comes from the other source, so it
            # must be parsed again by the next setwhom call
            self.db = ''
            self.gpdbuilder = None
            self.gpdbuilderdata = None
            self.gpdbuildergeo = None
            self.allvisu = None
        if get_live_mode():
            PyvoaWarning('Using live upstream data sources. '
                         'Results may change from one day to the next, and some '
                         'sources may be unreachable.')
        else:
            info('Using the archived (Zenodo) data sources.')
        return get_live_mode()

    def getlive(self,):
        """Say whether the live upstream sources are in use.

        Returns
        -------
        bool
            True when the live upstream sources are used, False when the frozen
            Zenodo archive is.
        """
        return get_live_mode()

    def set_verbose_mode(self, v):
        """Set how much pyvoa prints.

        The verbosity is global to the library: it governs info(), verb(),
        PyvoaInfo() and PyvoaWarning() wherever they are called, not only the
        front end.

        Parameters
        ----------
        v : int
            0 to silence everything, 1 for information and warnings, which is
            the default, 2 to add the debug output. At verbosity 2 pandas and
            the standard warnings filter are set back to their default noise;
            below it, both are quietened.

        Returns
        -------
        int
            The verbosity which has been set.

        Raises
        ------
        PyvoaError
            If v is not 0, 1 or 2.
        """
        if v not in (0, 1, 2):
            raise PyvoaError('verbose mode must be 0 (silent), 1 (info) or 2 (debug) ...')
        return _set_verbose_mode(v)

    def get_verbose_mode(self):
        """Return how much pyvoa prints.

        Returns
        -------
        int
            0 if silent, 1 for information and warnings, 2 for debug.
        """
        return _get_verbose_mode()

    def setwhom(self,base,**kwargs):
        """Set the current GPDBuilder database and optionally reloads it.

        This method updates the current database to the specified base if it is supported.
        If the `reload` parameter is set to True, it will reload the database; otherwise, it will read from a cached file.

        Parameters
        ----------
        base : str
            The name of the GPDBuilder database to set as the current database.
        **kwargs
            Additional keyword arguments that may be used for further customization.

        Raises
        ------
        PyvoaError
            If the `reload` parameter is not a boolean (0 or 1).
        PyvoaError
            If the specified `base` is not in the list of supported GPDBuilders.

        Returns
        -------
        None
            This method does not return a value.
        """
        reload = kwargs.get('reload', True)
        if reload not in [0,1]:
            raise PyvoaError('reload must be a boolean ... ')
        if base not in self.listwhom():
            raise PyvoaError(base + ' is not a supported GPDBuilder. '
                                    'See pyvoa.fron.listwhom() for the full list.')
        # Check if the current base is already set to the requested base
        # visu = self.getvis()

        if self.db == base:
            info(f"The GPDBuilder '{base}' is already set as the current database")
            print('Available key-words, which ∈', self.listwhich())
            return
        else:
            self.gpdbuilder  = coco.GPDBuilder(db_name=base)
            self.gpdbuilderdata, self.gpdbuildergeo, self.allvisu = self.gpdbuilder.factory(reload)
            if not reload:
                self.gpdbuilderdata = readpkl('data'+base + '.pkl')
                self.gpdbuildergeo = readpkl('geo'+base + '.pkl')
                pandy = self.gpdbuilder.getwheregeometrydescription()
                self.allvisu = AllVisu(base, pandy)
        self.db = base
        self.get_echoinfo()

    def get_echoinfo(self):
      """Print a summary of the selected database.

      Reports the variables it offers, a handful of example locations, and
      the first and last dates it covers. Output goes through info(), so it
      is silent unless the verbosity allows it.
      """
      info('Few information concernant the selected database : ', self.db)
      info('Available key-words, which ∈', sorted(self.listwhich()))
      info('Example of where : ', random.choices(self.listwhere(), k=min(5,len(self.listwhere()))),' ...')
      info('Last date data ', self.gpdbuilderdata['date'].max())
      info('First date data ', self.gpdbuilderdata['date'].min())

    def help(self,):
        """Print the full pyvoa command reference to the terminal.

        Delegates to pyvoa.help.display_full_help().
        """
        return h.display_full_help()

    def input_wrapper(func):
        """Validate and format the input arguments of a chart method.

        Ensures the arguments are properly formatted and validated before they
        reach the decorated function. Transforms 'where', 'which' and 'option'
        into lists when they are not already, and checks the compatibility of the
        visualisation options with the function asked for ('get', 'plot', 'hist'
        or 'map').

        Parameters
        ----------
        func : function
            The function to be decorated.

        Returns
        -------
        function
            The decorated function, with input handling and validation.

        Raises
        ------
        PyvoaError
            If the input arguments are not properly formatted, or if there are
            compatibility issues between the visualisation options and the
            requested function.
        """
        @wraps(func)
        def wrapper(self,**kwargs):
            """Wrap and format the user input arguments for the geopd_builder class.

            Fills a missing argument with its default value, transforms 'where',
            'which' and 'option' into lists when they are not already, and orders the
            items of 'option'.
            """
            input = kwargs.get('input',pd.DataFrame())
            if not isinstance(input,pd.DataFrame):
                PyvoaError('input field must be a pd.DataFrame()!')
            if self.gpdbuilderdata is None and input.empty:
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

            kwargs_keystesting(kwargs,self.largument + self.listviskargskeys,' kwargs keys not recognized ...')
            default = { k:[v[0]] if isinstance(v,list) else v for k,v in self.av.d_batchinput_args.items()}
            default['output'] = default['output'][0]
            default['input'] = kwargs.get('input',pd.DataFrame())
            dicovisu = {k:kwargs.get(k,v[0]) if isinstance(v,list) else kwargs.get(k,v) for k,v in self.av.d_graphicsinput_args.items()}

            for i in self.av.d_graphicsinput_args:
                kwargs_values_testing(
                    dicovisu[i],
                    self.av.d_graphicsinput_args[i],
                    f"value of {i} not correct"
                )

            for k in default:
                if k in kwargs and k not in ['when','input']:
                    if isinstance(kwargs[k],list):
                        default[k] = kwargs[k]
                    else:
                        default[k] = [kwargs[k]]
                default['when'] = kwargs.get('when')

            kwargs = {**default, **dicovisu}

            kwargs['what'] = kwargs.get('what',kwargs['what'][0])
            if isinstance(kwargs['what'],list):
                kwargs['what'] = kwargs['what'][0]
            kwargs['kwargsuser'] = kwargs.copy()

            if kwargs['where'][0] == '':
                if input.empty:
                    if self.gpdbuilderdata is not None:
                        kwargs['where'] = list(self.gpdbuilderdata['where'].unique())
                else:
                    kwargs['where'] = list(input['where'].unique())
            else:
                if self.db != 'in-house data':
                    self.test_where(kwargs['where'])

            if not all_or_none_lists(kwargs['where']):
                raise PyvoaError('For coherence all the element in where must have the same type list or not list ...')
            if 'sumall' in kwargs['option']:
                kwargs['option'].remove('sumall')
                kwargs['option'].append('sumall')
                if len(kwargs['which'])>1:
                    raise PyvoaError('sumall option incompatible with multiple variables... please keep only one variable!')

                #if not when:
                #    kwargs['when'] = input.date.min().strftime("%d/%m/%Y")+':'+input.date.max().strftime("%d/%m/%Y")
            kwargs['which'] = kwargs.get('which')
            if kwargs['which']=='':
                kwargs['which'] = self.gpdbuilder.get_available_keywords()[0]

            if kwargs['input'].empty:
                kwargs['input'] = self.gpdbuilderdata
                print(self.gpdbuildergeo)
                transfo = convertmercator(self.gpdbuildergeo)
                kwargs['input'] = pd.merge(kwargs['input'],transfo,how='left')
                kwargs = self.gpdbuilder.get_stats(**kwargs)
                kwargs['input'] = gpd.GeoDataFrame(kwargs['input'],geometry=kwargs['input'].geometry, crs="EPSG:4326")
            else:
                PyvoaInfo("In your DataFrame : the date must be in pd.to_datetime format !")
                if not all(col in input.columns for col in ['date', 'where']):
                    raise PyvoaError("['date', 'where'] must be in your pandas")
                if not all(i in input.columns for i in ['where', 'date']):
                    raise PyvoaError("Minimal requierement for your input pandas : 'where' AND 'date'  must be in the columns name")
                #when = kwargs.get('when')
                kwargs = coco.GPDBuilder().get_stats(**kwargs)
                self.db = 'in-house data'
                input = input.loc[input['where'].isin(kwargs['where'])]
                kwargs['input'] = input
                self.allvisu = AllVisu(self.db, kwargs['input'])

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
                kwargs['what'] = kwargs['which'][:1]
            print(kwargs['input'])
            return func(self,**kwargs)
        return wrapper

    def test_where(self, where):
        """Check that every location asked for exists in the database.

        Flattens clusters of locations, then compares case-insensitively
        against listwhere().

        Parameters
        ----------
        where : list
            the locations to check, possibly nested.

        Returns
        -------
        bool
            True if all of them are known.

        Raises
        ------
        PyvoaError
            naming the locations that are not.
        """
        flat_where = []
        upwhere = [i.upper() for i in self.listwhere()]
        for w in where:
            if isinstance(w, list):
                flat_where.extend(w)
            else:
                flat_where.append(w)

        missing = [w for w in flat_where if w.upper() not in upwhere]
        if missing:
            raise PyvoaError('This location do not exit in the DB :' + str(missing))
        else:
            return True

    def input_visuwrapper(func):
        """Refuse a chart the requested backend cannot draw.

        Checks that the input arguments of the decorated function are compatible
        with the function asked for, in particular that 'hist' and 'map' are given
        a single variable and that a date slider is asked for only under bokeh.

        Parameters
        ----------
        func : function
            The function to be decorated.

        Returns
        -------
        function
            The decorated function, with input handling and validation.

        Raises
        ------
        PyvoaError
            If the input arguments are not properly formatted, or if there are
            compatibility issues between the visualisation options and the
            requested function.
        """
        @wraps(func)
        def inner(self,**kwargs):
            """Refuse a chart the current backend cannot draw.

            Checks that a backend is set, that a date slider is asked for only in
            bokeh, and that hist() and map() are given a single variable.
            """
            if self._setkwargsvisu is None:
                raise PyvoaError("vis is not set can you can not use charts functions  ...")
            kwargs['vis'] = self.vis
            if 'get' not in func.__name__:
                z = { **self.getkwargsvisu(), **kwargs }
            if self.getvis() is not None:
                if func.__name__ in ['hist','map']:
                    if z['dateslider'] and self.vis != 'bokeh':
                        raise PyvoaError('dateslider available only visu Bokeh')

                    if isinstance(z['which'],list) and len(z['which'])>1:
                        raise PyvoaError("Histo and map available only for ONE variable ...")

                    #z['input'] = z['input'].sort_values(by=kwargs['which'], ascending=False).reset_index(drop=True)
                    if func.__name__ == 'map':
                            z.pop('typeofhist')
                            z.pop('typeofplot')
                            z.pop('bins')
                    #shortenwhere = {i:i[:self.maxlettersdisplay] + '...' if len(i)>self.maxlettersdisplay else i for i in z['where']}
                    #z['input']['where'] = kwargs['input']['where'].replace(shortenwhere)
                return func(self,**z)
            else:
                PyvoaWarning("Graphics asked can't be displayed, no visualization has been setted")
        return inner

    def decoget(func):
        """Decorate casting the assembled table to the requested output type.

        Reads the 'output' keyword and converts the DataFrame the wrapper built
        into a pandas or geopandas frame, a dict, a list or a numpy array. It
        is the last step shared by get(), plot(), hist() and map().
        """
        @wraps(func)
        def inner(self,**kwargs):
            """Retrieve and process data based on the specified output format.

            This method accepts a pandas DataFrame as input and converts it into various formats
            such as pandas DataFrame, GeoPandas DataFrame, dictionary, list, or numpy array
            based on the 'output' keyword argument. It also logs memory usage for the DataFrame
            if the output is set to 'pandas'.

            Parameters
            ----------
            **kwargs
                Arbitrary keyword arguments. Expected keys include:
                - 'input': A pandas DataFrame to be processed.
                - 'output': A string indicating the desired output format.
                Options include 'pandas', 'geopandas', 'dict', 'list', or 'array'.

            Returns
            -------
            The processed data in the specified output format.

            Raises
            ------
            PyvoaError
                If the specified output format is unknown.

            Notes
            -----
            - If the output is 'pandas', the method will log the memory usage of the DataFrame.
            - If the output is 'geopandas', it merges the input DataFrame with geometry data.
            - If the output is 'dict', it converts the DataFrame to a dictionary.
            - If the output is 'list' or 'array', it converts the DataFrame to a list or numpy array respectively.
            """
            output = kwargs.get('output')
            pandy = kwargs.get('input')

            if 'geometry' not in list(pandy.columns):
                output = 'pandas'
            if isinstance(output,list):
                output=output[0]
            self.setnamefunction(self.get)
            if output == 'pandas':
                def color_df(val):
                    """Return the display colour of one column: date blue, where red."""
                    if val.columns=='date':
                        return 'blue'
                    elif val.columns=='where':
                        return 'red'
                    else:
                        return 'black'
                if 'geometry' in list(pandy.columns):
                    pandy = pandy.drop(columns='geometry')
                casted_data = pandy.copy()
                col=list(pandy.columns)
                mem=f'{pandy[col].memory_usage(deep=True).sum():,}'
                info('Memory usage of all columns: ' + mem + ' bytes')
            elif output == 'geopandas':
                if 'geometry' in list(pandy.columns):
                    casted_data = pandy.copy()
                else:
                    casted_data = pd.merge(pandy, self.gpdbuilder.getwheregeometrydescription(), on='where')
                    casted_data = gpd.GeoDataFrame(casted_data)
            elif output == 'dict':
                return pandy.to_dict('split')
            elif output == 'array':
                return pandy.to_numpy()
            elif output == 'list':
                return pandy.values.tolist()
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

            kwargs['input'] = casted_data.copy()
            return func(self,**kwargs)
        return inner

    @input_wrapper
    @decoget
    def get(self,**kwargs):
        """Query the current database and return the data as a table.

        This is the data-access entry point of pyvoa. It applies the selection
        described by the keyword arguments to the database chosen with
        :meth:`setwhom`, and returns the result in the format asked for by
        ``output``. :meth:`plot`, :meth:`hist` and :meth:`map` take the same
        selection arguments and draw the result instead of returning it.

        A database must have been selected with :meth:`setwhom` beforehand,
        unless a table of your own is passed as ``input``.

        Parameters
        ----------
        where : str or list of str, optional
            The location(s) to select. Defaults to every location the database
            holds; :meth:`listwhere` lists them.
        which : str or list of str, optional
            The variable(s) to read. Defaults to the first keyword the database
            declares; :meth:`listwhich` lists them.
        what : {'current', 'daily', 'weekly'}, optional
            How the values are reported. Defaults to 'current'; see
            :meth:`listwhat`.
        when : str, optional
            A date as ``dd/mm/yyyy``, or a range as ``dd/mm/yyyy:dd/mm/yyyy``.
            Either side of the range may be left empty.
        option : str or list of str, optional
            One or more of '', 'nonneg', 'smooth7', 'sumall' or
            'normalize:pop...'; see :meth:`listoption`.
        input : pandas.DataFrame, optional
            Read this table instead of the database. It must carry at least a
            'date' and a 'where' column.
        output : {'pandas', 'geopandas', 'list', 'dict', 'array'}, optional
            The type to return. Defaults to 'pandas'; see :meth:`listoutput`.

        Returns
        -------
        pandas.DataFrame or geopandas.GeoDataFrame or list or dict or numpy.ndarray
            The selected data, in the type named by ``output``.

        Raises
        ------
        PyvoaError
            If no database has been selected and no ``input`` was given, if a
            keyword or one of its values is not recognised, if a location asked
            for in ``where`` is absent from the database, or if ``typeofplot`` or
            ``typeofhist`` is passed, both belonging to :meth:`plot` and
            :meth:`hist`.

        Notes
        -----
        The signature above is the one this method answers to, not the one written
        in the source below it: the decorators consume these keyword arguments and
        hand the undecorated body the assembled table. :meth:`whattodo` lists every
        argument together with the values it accepts.
        """
        columns=list(kwargs['input'].columns)
        tokeep = ['date', 'where', 'code'] + kwargs['which'] + (['geometry'] if 'geometry' in columns else [])
        return kwargs['input'][tokeep]

    def decomap(func):
        """Decorate preparing the geometry a map is drawn from.

        Settles 'typeofmap' against the database: a national one ('not dense'
        by default) may be drawn dense or not, while a world-wide one has no
        such choice and is forced back to None. Then hands the geometry to the
        backend and shows the map it returns.
        """
        @wraps(func)
        def inner(self,**kwargs):
            """Inner function to process input parameters and modify geometry settings.

            Parameters
            ----------
            self
                The instance of the class.
            **kwargs
                Additional keyword arguments that may include:
                - where (str): A condition to filter data.
                - output: Optional output parameter (ignored in processing).
                - bypop: Optional population parameter (ignored in processing).
                - dateslider: Optional date slider parameter (default is None).
                - input (DataFrame): Input data that may be modified based on geometry settings.

            Returns
            -------
            The result of the function `func` after processing the input parameters.

            Raises
            ------
            Any exceptions raised by the `func` or during the processing of geometry settings.
            """
            input = kwargs.get('input')
            # originalinput = input.copy()
            if 'geometry' not in list(input.columns):
                raise PyvoaError('No geometry inside your pandas, map can not be asked')
            # where = kwargs.get('where')

            mapoption = kwargs.get('typeofmap',None)
            if isinstance(self.gpdbuilder.gettypeofgeometry(), coge.GeoCountry):
                mapoption = kwargs.get('typeofmap','not dense')
            else:
                #PyvoaWarning('typeofmap not compatible with this db, dummy argument')
                mapoption = None

            if 'output' in kwargs:
                kwargs.pop('output')
            if 'pop' in kwargs:
                kwargs.pop('pop')
            # dateslider = kwargs.get('dateslider', None)

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
        """Decorate building a histogram and handing it on to be shown.

        Merges the stored drawing options into the call, drops the geometry
        column that bokeh has no use for, and asks the backend for the figure.
        The single-variable rule is enforced earlier, in input_visuwrapper.
        """
        @wraps(func)
        def inner(self,**kwargs):
            """Inner method to generate a histogram visualization based on provided keyword arguments.

            Parameters
            ----------
            **kwargs
                Arbitrary keyword arguments that may include:
                - typeofhist: The type of histogram to generate.
                - output: This argument is removed from kwargs and not used.
                - pop: If present, this argument is removed from kwargs and not used.

            Raises
            ------
            PyvoaError
                If no visualization has been set up.

            Returns
            -------
            The result of the visualization function applied to the generated histogram outcome.
            """
            # dateslider = kwargs.get('dateslider')
            typeofhist = kwargs.get('typeofhist')
            if self.getvis() == 'bokeh' and 'geometry' in kwargs['input'].columns:
                kwargs['input'] = kwargs['input'].drop(columns='geometry')
            if kwargs.get('pop'):
              kwargs.pop('pop')
            if self.getvis():
                z = { **self.getkwargsvisu(), **kwargs  }
                if self.getvis() not in ['bokeh','seaborn'] and typeofhist == 'location' :
                    return func(self,self.allvisu.hist(**z)[0])
                else:
                    return func(self,self.allvisu.hist(**z))
            else:
                raise PyvoaError(" No visualization has been set up !")
        return inner

    @input_wrapper
    @input_visuwrapper
    @decoget
    @decomap
    def map(self,**kwargs):
        """Draw the selected data on a choropleth map.

        Selects data exactly as :meth:`get` does, then renders it geographically
        with the current visualisation backend. Like :meth:`hist`, it takes a
        single variable. :meth:`setvis` must have chosen a backend first, and
        :meth:`setwhom` a database whose geography is known.

        Parameters
        ----------
        where : str or list of str, optional
            The location(s) to select. Defaults to every location the database
            holds; :meth:`listwhere` lists them.
        which : str or list of str, optional
            The variable(s) to read. Defaults to the first keyword the database
            declares; :meth:`listwhich` lists them.
        what : {'current', 'daily', 'weekly'}, optional
            How the values are reported. Defaults to 'current'; see
            :meth:`listwhat`.
        when : str, optional
            A date as ``dd/mm/yyyy``, or a range as ``dd/mm/yyyy:dd/mm/yyyy``.
            Either side of the range may be left empty.
        option : str or list of str, optional
            One or more of '', 'nonneg', 'smooth7', 'sumall' or
            'normalize:pop...'; see :meth:`listoption`.
        input : pandas.DataFrame, optional
            Read this table instead of the database. It must carry at least a
            'date' and a 'where' column.
        typeofmap : {None, 'not dense', 'dense', 'folium'}, optional
            How the geography is drawn; :meth:`listmap` lists them.
        tile : {'esri', 'positron', 'stamen', 'openstreet', None}, optional
            The background tiles; :meth:`listtile` lists them.
        vis : {'matplotlib', 'bokeh', 'seaborn'}, optional
            The backend to draw with; :meth:`listvis` gives the ones actually
            installed.
        title, copyright : str, optional
            The text drawn on the figure.
        mode : {'mouse', 'vline', 'hline'}, optional
            The hover mode.
        guideline : bool, optional
            Whether to draw the guide lines.
        scale : {'linear', 'log'}, optional
            The scale of the value axis. Defaults to 'linear'.
        maxlettersdisplayed : int, optional
            Location names are cut past this length.
        dateslider : bool, optional
            Add a slider over the dates. Bokeh only.

        Returns
        -------
        object
            The map built by the backend. Under bokeh it is also shown, unless
            :meth:`setbatch` was called.

        Raises
        ------
        PyvoaError
            If no backend has been set up, if ``which`` names more than one
            variable, if ``dateslider`` is asked for outside bokeh, if a keyword
            or one of its values is not recognised, or if ``typeofplot`` or
            ``typeofhist`` is passed, both belonging to :meth:`plot` and
            :meth:`hist`.

        Notes
        -----
        The signature above is the one this method answers to, not the one written
        in the source below it: the decorators consume these keyword arguments and
        hand the undecorated body the map it has built. :meth:`whattodo` lists every
        argument together with the values it accepts.
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
        """Draw the selected data as a histogram or a pie chart.

        Selects data exactly as :meth:`get` does, then renders it with the current
        visualisation backend instead of returning it. Unlike :meth:`plot`, it
        takes a single variable. :meth:`setvis` must have chosen a backend first,
        and :meth:`setwhom` a database.

        Parameters
        ----------
        where : str or list of str, optional
            The location(s) to select. Defaults to every location the database
            holds; :meth:`listwhere` lists them.
        which : str or list of str, optional
            The variable(s) to read. Defaults to the first keyword the database
            declares; :meth:`listwhich` lists them.
        what : {'current', 'daily', 'weekly'}, optional
            How the values are reported. Defaults to 'current'; see
            :meth:`listwhat`.
        when : str, optional
            A date as ``dd/mm/yyyy``, or a range as ``dd/mm/yyyy:dd/mm/yyyy``.
            Either side of the range may be left empty.
        option : str or list of str, optional
            One or more of '', 'nonneg', 'smooth7', 'sumall' or
            'normalize:pop...'; see :meth:`listoption`.
        input : pandas.DataFrame, optional
            Read this table instead of the database. It must carry at least a
            'date' and a 'where' column.
        typeofhist : {'location', 'value', 'pie'}, optional
            The kind of histogram. Defaults to 'location'; :meth:`listhist` lists
            them.
        bins : int, optional
            The number of bins. Defaults to 10.
        orientation : {'horizontal', 'vertical'}, optional
            The direction the bars run in.
        vis : {'matplotlib', 'bokeh', 'seaborn'}, optional
            The backend to draw with; :meth:`listvis` gives the ones actually
            installed.
        title, copyright : str, optional
            The text drawn on the figure.
        mode : {'mouse', 'vline', 'hline'}, optional
            The hover mode.
        guideline : bool, optional
            Whether to draw the guide lines.
        scale : {'linear', 'log'}, optional
            The scale of the value axis. Defaults to 'linear'.
        maxlettersdisplayed : int, optional
            Location names are cut past this length.
        dateslider : bool, optional
            Add a slider over the dates. Bokeh only.

        Returns
        -------
        object
            The figure built by the backend. Under bokeh it is also shown, unless
            :meth:`setbatch` was called.

        Raises
        ------
        PyvoaError
            If no backend has been set up, if ``which`` names more than one
            variable, if a keyword or one of its values is not recognised, or if
            ``typeofplot`` is passed, which belongs to :meth:`plot`.

        Notes
        -----
        The signature above is the one this method answers to, not the one written
        in the source below it: the decorators consume these keyword arguments and
        hand the undecorated body the figure it has built. :meth:`whattodo` lists every
        argument together with the values it accepts.
        """
        self.setnamefunction(self.hist)
        if self.getvis() == 'bokeh':
            from bokeh.io import (
            show,
            )
            if not self.batch and fig:
                show(fig)
        else:
            import matplotlib.pyplot as plt
            if not self.batch:
                plt.show()
            self.outcome = fig
            return fig

    def decoplot(func):
        """Decorate preparing the data of a time-series plot.

        Reads 'typeofplot', refuses 'versus' with more than two variables, and
        merges the stored drawing options into the call.
        """
        @wraps(func)
        def inner(self,**kwargs):
            """Inner method to plot visualization based on provided keyword arguments.

            This method checks if a display is set up and, if so, merges the visualization keyword arguments with any additional keyword arguments provided. It then calls the plotting function and returns the outcome. If no display is set up, it raises a PyvoaError.

            Parameters
            ----------
            **kwargs
                Additional keyword arguments to be passed to the plotting function.

            Returns
            -------
            The outcome of the plotting function.

            Raises
            ------
            PyvoaError
                If no visualization has been set up.
            """
            # input=kwargs['input']

            which = kwargs.get('which')
            typeofplot = kwargs.get('typeofplot',self.listplot()[0])
            if kwargs.get('output'):
                kwargs.pop('output')

            if typeofplot == 'versus' and len(which)>2:
                raise PyvoaError(" versu can be used with 2 variables and only 2 !")
            if kwargs.get('pop'):
                kwargs.pop('pop')
            if self.getvis():
                z = {**self.getkwargsvisu(),**kwargs}
                return func(self,self.allvisu.plot(**z))
            else:
                raise PyvoaError(" No visualization has been set up !")
        return inner

    @input_wrapper
    @input_visuwrapper
    @decoget
    @decoplot
    def plot(self,fig):
        """Draw the selected data as a time series.

        Selects data exactly as :meth:`get` does, then renders it with the current
        visualisation backend instead of returning it. :meth:`setvis` must have
        chosen a backend first, and :meth:`setwhom` a database.

        Parameters
        ----------
        where : str or list of str, optional
            The location(s) to select. Defaults to every location the database
            holds; :meth:`listwhere` lists them.
        which : str or list of str, optional
            The variable(s) to read. Defaults to the first keyword the database
            declares; :meth:`listwhich` lists them.
        what : {'current', 'daily', 'weekly'}, optional
            How the values are reported. Defaults to 'current'; see
            :meth:`listwhat`.
        when : str, optional
            A date as ``dd/mm/yyyy``, or a range as ``dd/mm/yyyy:dd/mm/yyyy``.
            Either side of the range may be left empty.
        option : str or list of str, optional
            One or more of '', 'nonneg', 'smooth7', 'sumall' or
            'normalize:pop...'; see :meth:`listoption`.
        input : pandas.DataFrame, optional
            Read this table instead of the database. It must carry at least a
            'date' and a 'where' column.
        typeofplot : {'date', 'compare', 'versus', 'spiral', 'yearly'}, optional
            The kind of plot. Defaults to 'date'; :meth:`listplot` lists them.
            'compare' and 'spiral' are bokeh only, and 'versus' takes exactly two
            variables.
        vis : {'matplotlib', 'bokeh', 'seaborn'}, optional
            The backend to draw with; :meth:`listvis` gives the ones actually
            installed.
        title, copyright : str, optional
            The text drawn on the figure.
        mode : {'mouse', 'vline', 'hline'}, optional
            The hover mode.
        guideline : bool, optional
            Whether to draw the guide lines.
        scale : {'linear', 'log'}, optional
            The scale of the value axis. Defaults to 'linear'.
        maxlettersdisplayed : int, optional
            Location names are cut past this length.
        dateslider : bool, optional
            Add a slider over the dates. Bokeh only.

        Returns
        -------
        object
            The figure built by the backend. Under bokeh it is also shown, unless
            :meth:`setbatch` was called.

        Raises
        ------
        PyvoaError
            If no backend has been set up, if 'versus' is asked for with other
            than two variables, if a keyword or one of its values is not
            recognised, or if ``typeofhist`` is passed, which belongs to
            :meth:`hist`.

        Notes
        -----
        The signature above is the one this method answers to, not the one written
        in the source below it: the decorators consume these keyword arguments and
        hand the undecorated body the figure it has built. :meth:`whattodo` lists every
        argument together with the values it accepts.
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
            # outside the batch test, as in map() and hist(): savefig() reads
            # self.outcome, and setbatch() must not leave it unset.
            self.outcome = fig
            return fig

    def setnamefunction(self,name):
        """Set the name of the function.

        This method assigns the name of the provided function to the instance variable `namefunction`.

        Parameters
        ----------
        name : function
            The function whose name will be assigned to `namefunction`.

        Returns
        -------
        None
        """
        # self.namefunction = name : it updates the visu + redraws the last chart
        self.namefunction = name.__name__

    def getnamefunction(self,):
        """Retrieve the name of the function.

        Returns
        -------
        str
            The name of the function associated with the instance.
        """
        return self.namefunction

    def listoutput(self,):
        """Return a list of output values from the batch input arguments.

        This method retrieves the 'output' key from the `d_batchinput_args` dictionary
        of the `av` attribute and converts it into a list.

        Returns
        -------
        list
            A list containing the output values.
        """
        return list(self.av.d_batchinput_args['output'])

    def listvis(self,):
        """Return the visualization list.

        This method retrieves the visualization list associated with the instance.

        Returns
        -------
        list
            The visualization list.
        """
        if 'seaborn' in self.lvisu:
            self.lvisu.remove('seaborn')
        return self.lvisu

    def listmap(self,):
        """List the map types available.

        Returns
        -------
        list
            the values 'typeofmap' accepts. 'folium' is left out: it is
            selected through map(typeofmap='folium') but is not a rendering
            mode of the other backends.
        """
        optmap = [ i for i in list(self.av.d_graphicsinput_args['typeofmap']) if i ]
        if 'folium' in optmap:
            optmap.remove('folium')
        return optmap

    def listwhom(self, detailed = False):
        """List the names of databases and their associated metadata.

        Parameters
        ----------
        detailed : bool, optional
            If True, returns a detailed DataFrame containing database names, ISO3 codes, granularity, and variables. Defaults to False.

        Returns
        -------
        list or pd.DataFrame:
        - If detailed is False, returns a list of database names.
        - If detailed is True, returns a DataFrame with columns for database names, ISO3 codes, granularity, and variables.

        Raises
        ------
        PyvoaError
            If the detailed argument is not a boolean.
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
                    # for datasets in mypd.parsingjson.values[0]['datasets']:
                    #     pdata = pd.DataFrame(datasets['columns'])
                    varls.append(self.listwhich(i))

            dico.update({'dbname': namels})
            dico.update({'iso3': iso3ls})
            dico.update({'granularity': grls})
            dico.update({'variables': varls})
            return pd.DataFrame.from_dict(dico, orient='index').T.reset_index(drop=True).set_index('dbname')
        else:
            return namedb

    def listwhat(self,):
        """Return the value of the lwhat attribute.

        This method retrieves the current value of the lwhat attribute from the instance.

        Returns
        -------
        The value of the lwhat attribute.
        """
        return self.lwhat

    def listchart(self,):
        """List the charts the current backend can draw.

        Returns
        -------
        pd.Series
            the plot, histogram and map types supported by the
            backend chosen with setvis(), indexed by method name.

        Raises
        ------
        PyvoaError
            if no backend has been set.
        """
        if self.vis is None:
            raise PyvoaError('Vis has not be set !')
        return self.av.pdcharts[self.vis]

    def listhist(self,):
        """Return the list histogram.

        This method retrieves the histogram of the list stored in the instance.

        Returns
        -------
        list
            The list histogram.
        """
        if self.vis is None:
            raise PyvoaError('Vis has not be set !')
        self.lhist = self.av.pdcharts[self.vis]['hist']
        self.lhist = ast.literal_eval(self.lhist.split("=", 1)[1])
        return self.lhist

    def listplot(self,):
        """Return a list of the types of plots from the graphics input arguments.

        This method retrieves the 'typeofplot' key from the
        'd_graphicsinput_args' attribute of the 'av' object and
        returns it as a list.

        Returns
        -------
        list
            A list containing the types of plots.
        """
        if self.vis is None:
            raise PyvoaError('Vis has not be set !')
        self.lplot = self.av.pdcharts[self.vis]['plot']
        self.lplot = ast.literal_eval(self.lplot.split("=", 1)[1])
        return self.lplot

    def listoption(self,):
        """Return the value of the loption attribute.

        This method retrieves the current value of the loption attribute from the instance.

        Returns
        -------
        The value of the loption attribute.
        """
        return [x for x in self.loption if x != '']

    def listargument(self,):
        """Return the keys of the largument attribute.

        This method retrieves the keys stored in the largument attribute of the instance.

        Returns
        -------
        list
            A list of keys from the largument attribute.
        """
        return self.largument

    def listargumentvalue(self,):
        """Return the values of the lchartkargs attribute.

        This method retrieves the values stored in the lchartkargsvalues attribute of the instance.

        Returns
        -------
        list
            The values of the lchartkargsvalues attribute.
        """
        return self.largumentvalue

    def listtile(self,):
        """Return the list of tiles.

        This method retrieves the current list of tiles stored in the instance.

        Returns
        -------
        list
            A list containing the tiles.
        """
        if self.av.pdcharts[self.vis]['map']:
            return self.ltiles
        else:
            raise PyvoaError(self.vis+ ' : has not map function !')

    def listwhich(self,dbname=None):
        """List the current metadata for a specified database.

        This method retrieves the current metadata for the given database name. If no database name is provided, it uses the default database associated with the instance. If neither is available, it raises an error.

        Parameters
        ----------
        dbname : str, optional
            The name of the database for which to list the metadata. If not provided, the default database will be used.

        Returns
        -------
        list
            A sorted list of metadata associated with the specified database.

        Raises
        ------
        PyvoaError
            If no database name is provided and no default database is set.
        """
        if dbname:
            dic = self.meta.getcurrentmetadata(dbname)

        elif self.db:
            dic = self.meta.getcurrentmetadata(self.db)
        else:
            raise PyvoaError('listwhich for which database ? I am lost ... are you ?')
        return sorted(self.meta.getcurrentmetadatawhich(dic))

    def listwhere(self, cluster_and_not = True):
        """List regions or countries based on the current metadata and specified granularity.

        Parameters
        ----------
        clustered : bool
            If True, returns a clustered list of regions. Defaults to False.

        Returns
        -------
        list or str: A list of region names or a single country code, depending on the granularity and the clustered flag.

        Raises
        ------
        PyvoaError
            If the granularity of the database is not recognized.

        Notes
        -----
        The function retrieves the current metadata to determine the granularity and ISO3 code.
        If the granularity is 'country' and the code is not 'WLD' or 'EUR', it returns the country code.
        If clustered is True, it returns a list of regions based on the ISO3 code.
        If clustered is False, it returns a list of countries based on the granularity and the current database settings.
        """
        if self.db is None or self.db=='in-house data':
            raise PyvoaError("listwhere not available use your on where ... ")
        granularity = self.meta.getcurrentmetadata(self.db)['geoinfo']['granularity']
        code = self.meta.getcurrentmetadata(self.db)['geoinfo']['iso3']
        coge.GeoManager('name')
        #self.gpdbuilder.geo.GeoManager('iso3')
        def clust():
            """List the clusters of locations this database offers.

            For a single country, the country itself; for a world-wide or European
            database, its regions, plus 'European Union' for the European one.
            """
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

        if cluster_and_not:
            if self.gpdbuilder.db_world:
                if granularity == 'country' and code not in ['WLD','EUR'] :
                    r =  self.gpdbuilder.to_standard(code)
                else:
                    if code == 'WLD':
                        r = self.gpdbuilder.geo.get_GeoRegion().get_countries_from_region('World')
                    else:
                        r = self.gpdbuilder.geo.get_GeoRegion().get_countries_from_region('Europe')
                    r += [self.gpdbuilder.geo.to_standard(c)[0] for c in r]
                r+=clust()
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
            return sorted(r)
        else:
            return sorted(clust())


    def listpop(self):
        """Return a list of keys from the dictionary `lpop`."""
        return self.lpop

    def getwhom(self, db = None, detailed=False,return_error=True):
        """Retrieve the database instance associated with the current object.

        Parameters
        ----------
        return_error : bool
            A flag indicating whether to return an error if the database instance is not available. Defaults to True.
        detailed : bool
            If True, displays detailed information about the database instance. Defaults to False.

        Returns
        -------
        The database instance associated with the current object.
        """
        if db:
            if detailed:
                whomlist=self.listwhom(True)
                print(whomlist[whomlist.index == db])
                return None
        else:
            if self.db=='':
                if return_error:
                    raise PyvoaError('Something went wrong ... does a db has been loaded ? (setwhom)')
                else:
                    return None
            if detailed:
                whomlist=self.listwhom(True)
                print(whomlist[whomlist.index==self.db])
            return self.db

    def getdbmetadata(self,db=None):
        """Return the JSON description of a database.

        Parameters
        ----------
        db : str
            the database to describe. Defaults to the one selected
            with setwhom().

        Returns
        -------
        dict
            its metadata -- geography, datasets, urls and columns.

        Raises
        ------
        PyvoaError
            if db is not a known database, or if none was given and
            none has been selected.
        """
        if db:
            if db in self.listwhom():
               return self.meta.getcurrentmetadata(db)
            else:
               raise PyvoaError('Database'+ db +' is not in the pyvoa listing, please have a look')
        elif self.db:
            return self.meta.getcurrentmetadata(self.db)
        else:
            raise PyvoaError('Database has not been defined')

    def getwhichinfo(self, which=None):
        """Retrieve information based on the specified keyword.

        Parameters
        ----------
        which : str, optional
            The keyword for which information is to be retrieved.
            If provided, the function will print the keyword's definition and its associated URL.
            If not provided, the function will return the database description.

        Raises
        ------
        PyvoaError
            If the provided keyword does not exist in the database.

        Returns
        -------
        DataFrame
            The database description if no keyword is specified.
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
        """Retrieve the full database and logs its memory usage.

        This method fetches the complete database from the `gpdbuilder` object, calculates the total memory usage of all columns, and logs this information. It then returns the full database as a DataFrame.

        Returns
        -------
        pandas.DataFrame
            The full database retrieved from the `gpdbuilder`.
        """
        col = list(self.gpdbuilder.get_fulldb().columns)
        mem=f'{self.gpdbuilder.get_fulldb()[col].memory_usage(deep=True).sum():,}'
        info('Memory usage of all columns: ' + mem + ' bytes')
        df = self.gpdbuilder.get_fulldb()
        return df

    def setkwargsvisu(self,**kwargs):
        """Set visualization parameters using keyword arguments.

        This method updates the internal dictionary of visualization parameters.
        If the internal dictionary `_setkwargsvisu` already exists, it updates
        the existing keys with the provided values only if the values are truthy.
        If `_setkwargsvisu` does not exist, it initializes it with the provided
        keyword arguments.

        Parameters
        ----------
        **kwargs
            Arbitrary keyword arguments representing visualization parameters.
            Only keys with truthy values will be set in the internal dictionary.

        Returns
        -------
        None
        """
        if self._setkwargsvisu:
            for k,v in kwargs.items():
                if v:
                    self._setkwargsvisu[k] = v
        else:
            self._setkwargsvisu = kwargs

    def getkwargsvisu(self,):
        """Return the drawing options set by setkwargsvisu().

        Returns
        -------
        dict
            the stored options, or None if none have been set.
        """
        return self._setkwargsvisu

    def setvis(self,vis=' '):
        """Set the visualization and updates the keyword arguments for the visualization settings.

        Parameters
        ----------
        **kwargs
            Arbitrary keyword arguments that may include visualization settings.

        Raises
        ------
        PyvoaError
            If the specified visualization is not implemented.

        Notes
        -----
        This method retrieves default visualization settings from the object's graphics input arguments,
        updates them with any provided keyword arguments, and checks if the specified visualization is
        available. If it is, the visualization is set, and a confirmation message is logged. Otherwise,
        an error is raised.

        Examples
        --------
        setvis('example_visualization')
        """
        if vis not in self.lvisu:
            raise PyvoaError("Sorry but " + vis + " visualisation isn't installed ")
        else:
            self.vis = vis
            PyvoaInfo(f"The visualization has been set correctly to: {vis}")
        self.setkwargsvisu(vis=vis)

    def setbatch(self,):
        """Stop the charts from being shown as they are built.

        In batch mode the chart methods return their figure without displaying
        it, which is what a script writing files rather than driving a notebook
        wants.
        """
        self.batch = True

    def getvis(self,):
        """Return the display attribute of the instance.

        This method retrieves the value of the `vis` attribute from the instance.

        Returns
        -------
        The value of the `vis` attribute.
        """
        return self.vis

    def saveoutput(self,**kwargs):
        """Save output to a specified format.

        This method saves a pandas DataFrame to a file in the specified format. It requires a pandas DataFrame to be provided and allows for customization of the save format and file name.

        Parameters
        ----------
        **kwargs
            Keyword arguments that can include:
            - pandas (pd.DataFrame): The DataFrame to save. This is mandatory.
            - saveformat (str): The format to save the DataFrame in. Default is 'excel'.
            - savename (str): The file name, without its extension. Left
            empty, it defaults to 'pyvoa_out', so the file is written as
            pyvoa_out.xlsx or pyvoa_out.csv.

        Raises
        ------
        PyvoaError
            If the provided DataFrame is empty, if mandatory arguments are not provided,
            or if no database has been selected yet with setwhom().

        Returns
        -------
        None
        """
        kwargs_keystesting(kwargs, ['pandas','saveformat','savename'], 'Bad args used in the pyvoa.saveoutput function.')
        pandy = kwargs.get('pandas', pd.DataFrame())
        saveformat = kwargs.get('saveformat', 'excel')
        savename = kwargs.get('savename', '')
        if pandy.empty:
            raise PyvoaError('Pandas to save is mandatory there is not default !')
        else:
            # The writer lives on GPDBuilder, which only exists once a database
            # has been selected. Without this, the call below fails on None with
            # an AttributeError, which is not the library's exception type.
            if self.gpdbuilder is None:
                raise PyvoaError('Something went wrong ... does a db has been loaded ? (setwhom)')
            self.gpdbuilder.saveoutput(pandas=pandy,saveformat=saveformat,savename=savename)

    def savefig(self,name):
        """Save the current figure to a file.

        This method checks the display type and saves the figure accordingly. If the display type is 'bokeh', it uses the Bokeh library to export the figure as a PNG file. Otherwise, it uses the standard savefig method. If the name function is 'get', it raises a PyvoaError indicating that saving is not allowed for a pandas DataFrame.

        Parameters
        ----------
        name : str
            The name of the file to save the figure as.

        Raises
        ------
        PyvoaError
            If the name function is 'get', indicating that saving a pandas DataFrame is not permitted.
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
                from bokeh.plotting import output_file, save
                output_file(name+'.html')
                save(self.outcome)
            else:
                    # bbox_inches='tight': the location histogram puts its
                    # labels outside the axes and the legend to the right of
                    # them, and the default bounding box cuts both off.
                    self.outcome.figure.savefig(name, bbox_inches='tight')
            print('Figure :', name, ' has been saved ')
        else:
            raise PyvoaError('savefig can\'t be used to store a panda DataFrame')

# this trick allow you to do
# import pyvoa.front as pv
# pv.setwhom(...)
# pv.map(...)

__pyvoafront_instance__ = front()

from pyvoa.__version__ import __author__, __email__, __version__

__pyvoafront_instance__.__version__ = __version__
__pyvoafront_instance__.__author__ = __author__
__pyvoafront_instance__.__email__ = __email__

import sys

module = sys.modules[__name__]

for attr_name in dir(__pyvoafront_instance__):
    if not attr_name.startswith("_") and callable(getattr(__pyvoafront_instance__, attr_name)):
        setattr(module, attr_name, getattr(__pyvoafront_instance__, attr_name))
