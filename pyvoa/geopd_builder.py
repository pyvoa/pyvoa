"""Assembly of a parsed database and its geography.

``GPDBuilder`` joins the DataFrame produced by ``pyvoa.jsondb_parser`` to the
matching geography, applies the statistical options a query asks for -- daily
and weekly differences, smoothing, cumulative sums, normalisation by population
-- and hands back one GeoDataFrame together with the visualisation dispatcher
built for it.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
"""

import datetime as dt
import re

import geopandas as gpd
import numpy as np
import pandas as pd

import pyvoa.geo as coge
import pyvoa.jsondb_parser as parser
from pyvoa.kwargs_options import InputOption
from pyvoa.tools import (
   PyvoaError,
   PyvoaWarning,
   dumppkl,
   extract_dates,
   flat_list,
   getnonnegfunc,
   kwargs_values_testing,
   verb,
   info
)

pd.options.mode.chained_assignment = None  # default='warn'


class GPDBuilder:
   """One database, joined to its geography and ready to be queried.

   Built from the name of a database: parses it through
   ``pyvoa.jsondb_parser``, attaches the geometry of the locations it covers,
   and keeps the result as a single GeoDataFrame. :meth:`get_stats` then applies
   to it the statistical options a query asks for -- daily and weekly
   differences, smoothing, cumulative sums, normalisation by population.

   ``front`` builds one of these per database selected with ``setwhom()``; there
   is no reason to build one directly.
   """

   def __init__(self, db_name = None):
        """Build the GeoDataFrame of one database.

        Calls the parser for the data, the geography for the locations, and
        the visualisation dispatcher for the charts, so that a GPDBuilder is
        usable as soon as it is built.

        Parameters
        ----------
        db_name : str
            The database to load. With None, nothing is loaded.
        """
        if db_name is not None:
            verb("Init of geopd_builder.GPDBuilder()")
            self.db = db_name
            self.currentmetadata = parser.MetaInfo().getcurrentmetadata(db_name)
            self.currentdata = parser.DataParser(db_name)
            self.slocation = self.currentdata.get_locations()
            #self.geo = self.currentdata.get_geo()
            self.db_world = self.currentdata.get_world_boolean()
            self.codisp  = None
            self.code = self.currentmetadata['geoinfo']['iso3']
            self.granularity = self.currentmetadata['geoinfo']['granularity']
            self.namecountry = self.currentmetadata['geoinfo']['iso3']
            self._gi = coge.GeoInfo()
            self.namepkldata = None
            self.namepklgeo = None
            self.reload  = False
            try:
                if self.granularity == 'country':
                       self.geo = coge.GeoManager('name')
                       geopan = gpd.GeoDataFrame()#crs="EPSG:4326")
                       info = coge.GeoInfo()
                       alllocationsgeo = self.geo.get_GeoRegion().get_countries_from_region('world')
                       geopan['where'] = [self.geo.to_standard(c)[0] for c in alllocationsgeo]
                       geopan = info.add_field(field=['geometry'],input=geopan ,geofield='where')
                       geopan = gpd.GeoDataFrame(geopan, geometry=geopan.geometry, crs="EPSG:4326")
                       geopan = geopan[geopan['where'] != 'Antarctica']
                       where_kindgeo = geopan.dropna().reset_index(drop=True)
                else:
                       self.geo = coge.GeoCountry(self.code)
                       if self.granularity == 'region':
                            where_kindgeo = self.geo.get_region_list()[['code_region', 'name_region', 'geometry']]
                            where_kindgeo = where_kindgeo.rename(columns={'name_region': 'where'})
                            if self.code == 'PRT':
                                 tmp = where_kindgeo.rename(columns={'name_region': 'where'})
                                 tmp = tmp.loc[tmp.code_region=='PT.99']
                                 self.boundary_metropole =tmp['geometry'].total_bounds
                            if self.code == 'FRA':
                                 tmp = where_kindgeo.rename(columns={'name_region': 'where'})
                                 tmp = tmp.loc[tmp.code_region=='999']
                                 self.boundary_metropole =tmp['geometry'].total_bounds
                       elif self.granularity == 'subregion':
                            where_kindgeo = self.geo.get_subregion_list()[['code_subregion', 'name_subregion', 'geometry']]
                            where_kindgeo = where_kindgeo.rename(columns={'name_subregion': 'where'})
                       else:
                           raise PyvoaError('What is the granularity of your  database ?')
            except Exception as e:
                raise PyvoaError('What data base are you looking for ?') from e
            self.where_geodescription = where_kindgeo
        else:
            self.db = 'in-house data'
            self.currentdata = None

   def getwheregeometrydescription(self,):
        """Return the geometry of each location, as a 'where'/'geometry' frame."""
        return self.where_geodescription

   def gettypeofgeometry(self):
        """Return the geography object backing this database.

        Returns
        -------
        A GeoManager for a world-wide database, a GeoCountry otherwise.
        front reads its type to decide how to draw a map.
        """
        return self.geo

   def get_available_keywords(self):
       """Return available from the jsondb_parser."""
       return self.currentdata.get_available_keywords()

   def factory(self,reload=True):
       """Return an instance of GPDBuilder and of the display methods.

       Recommended over building them separately, which risks a mismatch in the
       labels of the figures.
       """
       f = self.db+'.pkl'
       if reload:
          data, geo=self.split_data_geo(self.currentdata.get_maingeopandas())
          self.namepkldata = 'data'+f
          datadata = {}
          datadata['listwhich'] = self.listwhich(self.db)
          datadata['listwhere'] = self.listwhere()
          datadata['data'] = data
          dumppkl(self.namepkldata, datadata)
          self.namepklgeo  = 'geo'+f
          geodata = {}
          geodata['geo'] = geo
          geodata['geodescription'] = self.where_geodescription
          dumppkl(self.namepklgeo,geodata)

       self.setvisu(self.db,geo)
       self.reload = reload
       return data,geo,self.getvisu()

   def getpklname(self,geoordata='geo'):
        if geoordata == 'geo':
            return self.namepklgeo
        elif geoordata == 'data':
            return self.namepkldata
        else:
            PyvoaError("No geo nor data ... crashed")

   def getdatabase(self):
        """Return the whole database, as parsed, for every location and variable.

        The table :meth:`get` selects from, before any selection: this is the raw
        material, not a query. Its size is reported through info().

        Returns
        -------
        pandas.DataFrame
            Every variable of the current database, for every location and date.
        """
        col = list(self.currentdata.get_maingeopandas().columns)
        mem=f'{self.currentdata.get_maingeopandas()[col].memory_usage(deep=True).sum():,}'
        info('Memory usage of all columns: ' + mem + ' bytes')
        df = self.currentdata.get_maingeopandas()
        return df

   @staticmethod
   def split_data_geo(mypyvoageopd):
      """Split a geo DataFrame into its data and its geometry.

      The geometry repeats on every date, which is wasteful to carry around
      and to pickle. Splitting it out leaves one row per location.

      Parameters
      ----------
      mypyvoageopd : gpd.GeoDataFrame
          the full frame.

      Returns
      -------
      tuple
          (data without the geometry column, one 'where'/'geometry'
          row per location).
      """
      data = mypyvoageopd.drop(columns='geometry').reset_index(drop=True)
      geo = mypyvoageopd[['where','geometry']].drop_duplicates(subset=['where']).reset_index(drop=True)
      return data,geo

   def setvisu(self,db_name,wheregeometrydescription):
       """Set the Display."""
       import pyvoa.visualizer as output
       self.codisp = output.AllVisu(db_name, wheregeometrydescription)

   def getvisu(self):
       """Return the instance of Display initialized by factory."""
       return self.codisp

   def setgeo(self,geo):
       """Set the geography object used to resolve locations."""
       self.geo = geo

   def getgeo(self):
       """Return the geography object used to resolve locations."""
       return self.geo

   def get_parserdb(self):
       """Return the DataParser holding the parsed database."""
       return self.currentdata


   def get_available_GPDBuilder(self):
        """Return all the available Covid19 GPDBuilder."""
        return self.GPDBuilder_name

   def subregions_deployed(self,listloc,typeloc='subregion'):
        """Expand a list of locations into the individual places it covers.

        A region name is replaced by the subregions it contains, so that a
        selection such as 'Occitanie' becomes the departements below it. Names
        already at the requested level are kept as they are.

        Parameters
        ----------
        listloc : list
            the locations to expand.
        typeloc : str
            the level to expand to, 'subregion' (default) or
            'region'.

        Returns
        -------
        list
            the flattened list of locations.

        Raises
        ------
        PyvoaError
            if an entry is neither a region nor a subregion of this
            database, or if a subregion is asked for at region granularity.
        """
        exploded = []
        for i in listloc:
            if typeloc == 'subregion':
                if self.geo.is_region(i):
                    i = [self.geo.is_region(i)]
                    tmp = self.geo.get_subregions_from_list_of_region_names(i,output='name')
                elif self.geo.is_subregion(i):
                   tmp = i
                else:
                    raise PyvoaError(i + ': not subregion nor region ... what is it ?')
            elif typeloc == 'region':
                tmp = self.geo.get_region_list()

                if i.isdigit():
                    tmp = list(tmp.loc[tmp.code_region==i]['name_region'])
                elif self.geo.is_region(i):
                    tmp = self.geo.get_regions_from_macroregion(name=i,output='name')
                    if self.currentmetadata['geoinfo']['iso3'] in ['USA', 'FRA', 'ESP', 'PRT']:
                        tmp = tmp[:-1]
                else:
                    if self.geo.is_subregion(i):
                        raise PyvoaError(i+ ' is a subregion ... not compatible with a region DB granularity?')
                    else:
                        raise PyvoaError(i + ': not subregion nor region ... what is it ?')
            else:
                raise PyvoaError('Not subregion nor region requested, don\'t know what to do ?')
            if exploded:
                exploded.append(tmp)
            else:
                exploded=[tmp]
        return flat_list(exploded)

   def listwhich(self,dbname=None):
       """List the variables a database offers.

       Parameters
       ----------
       dbname : str, optional
           The database to ask about. Defaults to the one selected with
           :meth:`setwhom`.

       Returns
       -------
       list of str
           The values 'which' accepts, sorted alphabetically. Beware that the
           default of 'which' is not this first entry but the first cumulative
           variable the database declares, as :meth:`get` describes.

       Raises
       ------
       PyvoaError
           If no database was named and none has been selected.
       """
       if dbname:
           dic = parser.MetaInfo().getcurrentmetadata(dbname)

       elif self.db:
           dic = parser.MetaInfo().getcurrentmetadata(self.db)
       else:
           raise PyvoaError('listwhich for which database ? I am lost ... are you ?')
       return sorted(parser.MetaInfo().getcurrentmetadatawhich(dic))


   def listwhere(self, cluster_and_not = True):
        """List the locations the current database can be asked for.

        What a location is depends on the granularity of the database: the
        countries of a world-wide or European one, the regions or the subregions
        of a national one. Clusters -- the names standing for a group of
        locations, such as a continent, 'European Union' or 'World' -- are
        listed alongside them.

        Parameters
        ----------
        cluster_and_not : bool
            If True, the default, return the individual locations *and* the
            clusters. If False, return the clusters only.

        Returns
        -------
        list of str or str
            The locations, sorted. A database covering a single country is the
            exception: it returns that country's ISO3 code alone, whatever this
            flag says, since there is nothing to choose from.

        Raises
        ------
        PyvoaError
            If no database has been selected, if the selection is a table of your
            own ('in-house data', whose locations are yours to know), or if the
            granularity of the database is not one pyvoa knows.
        """
        if self.db is None or self.db=='in-house data':
            raise PyvoaError("listwhere not available use your on where ... ")
        granularity = parser.MetaInfo().getcurrentmetadata(self.db)['geoinfo']['granularity']
        code = parser.MetaInfo().getcurrentmetadata(self.db)['geoinfo']['iso3']
        coge.GeoManager('name')
        #self.gpdbuilder.geo.GeoManager('iso3')
        def clust():
            """List the clusters of locations this database offers.

            For a single country, the country itself; for a world-wide or European
            database, its regions, plus 'European Union' for the European one.
            """
            if granularity == 'country' and code not in ['WLD','EUR']:
                return  self.gettypeofgeometry().to_standard(code)
            else:
                r = self.gettypeofgeometry().get_region_list()
                if not isinstance(r, list):
                    r=sorted(r['name_region'].to_list())
                r.append(code)
                if code  == 'EUR':
                    r.append('European Union')
                if code  == 'WLD':
                    r.remove('WLD')
                    r.append('World')
                return r

        if granularity == 'country' and code not in ['WLD','EUR']:
            return code

        if cluster_and_not:
            if self.db_world:
                if granularity == 'country' and code not in ['WLD','EUR'] :
                    r =  self.gettypeofgeometry().to_standard(code)
                else:
                    if code == 'WLD':
                        r = self.gettypeofgeometry().get_GeoRegion().get_countries_from_region('World')
                    elif code == 'EUR':
                        r = self.gettypeofgeometry().get_GeoRegion().get_countries_from_region('Europe')
                    else:
                        r = []
                    r += [self.gettypeofgeometry().to_standard(c)[0] for c in r]
                r+=clust()
            else:
                r = clust()
                if granularity == 'subregion':
                    pan = self.gettypeofgeometry().get_subregion_list()
                    r += list(pan.name_subregion.unique())
                elif granularity == 'region':
                    pan = self.gettypeofgeometry().get_region_list()
                    r += list(pan.name_region.unique())
                elif granularity == 'country':
                    r.append(code)
                else:
                    raise PyvoaError('What is the granularity of your DB ?')
            return sorted(r)
        else:
            return sorted(clust())

   def whereclustered(self,**kwargs):
        """Handle the name and the geometry of a cluster of locations.

        Returns a pandas in which the locations of a cluster have been collapsed:
        their names summed, their values summed or averaged depending on the
        variable, and their geometries merged. Names are compared upper-cased, so
        the comparison is case insensitive.
        """
        input = kwargs.get('input')
        #if 'geometry' not in list(input.columns):
        #    return input

        which = kwargs['which']
        where = kwargs['where']
        option=kwargs.get('option')
        dpop = InputOption().dictpop

        has_normalize = any(o.startswith("normalize:") for o in option)
        has_sumall = "sumall" in option

        if has_sumall and kwargs['typeofmap']=='dense':
            raise PyvoaError("dense + sumall not compatible ...")

        which = kwargs.get('which')
        newpd = pd.DataFrame()
        if not isinstance(where[0],list):
            where = [where]

        if has_sumall:
            for w in where:
                temp = pd.DataFrame()
                if not isinstance(w,list):
                    w=[w]

                if self.db_world:
                    self.geo.set_standard('name')
                    w_s = self.geo.to_standard(w,output='list',interpret_region=True)
                else:
                    w_s = self.subregions_deployed(w,self.granularity)

                temp = input.loc[input['where'].str.upper().isin([x.upper() for x in w_s])].reset_index(drop=True)
                if has_normalize:
                    for idx,i in enumerate(dpop.keys()):
                        if isinstance(which,list):
                            which=which[0]
                        if idx==0:
                            temptemp = self.normbypop(temp,which,i)
                        else:
                            temptemp = pd.merge(temptemp,self.normbypop(temp,which,i),how="outer")
                    temp = temptemp

                temp = gpd.GeoDataFrame(temp, geometry=temp.geometry, crs="EPSG:4326").reset_index(drop=True)
                wherejoined  = ',' .join(flat_list(w))
                code = temp.loc[temp.date==temp.date.max()]['code']
                codejoined  = ',' .join(code)
                if has_normalize:
                    if 'population_subregion' in list(temp.columns):
                        temp=temp.rename(columns={"population_subregion": "population"})
                    population = temp.loc[temp.date==temp.date.max()]['population']
                    populationsum = np.nansum(population)

                # Canada, Chile, Greece, Norway seem to have geometry problems
                # They can be drawn individually but not when 'sumall' is present
                # buffer(0) fixe the problem.
                temp["geometry"] = temp["geometry"].buffer(0)
                geometryjoined = temp.loc[temp.date == temp.date.max()]["geometry"].unary_union
                temp = temp.groupby(['date'])[which].sum(min_count=1).reset_index()
                temp['where'] = len(temp)*[wherejoined]
                temp['code'] = len(temp)*[codejoined]
                temp['geometry'] = len(temp)*[geometryjoined]
                if has_normalize:
                    temp['population'] = len(temp)*[populationsum]
                if newpd.empty:
                    newpd = temp
                else:
                    newpd = pd.concat([newpd,temp])
        else:
            where = flat_list(where)
            if self.db_world:
                where = self.geo.to_standard(where,output='list',interpret_region=True)
            else:
                where = self.subregions_deployed(where,self.granularity)
            newpd = input.loc[input['where'].str.upper().isin([x.upper() for x in where])]
            newpd = gpd.GeoDataFrame(newpd, geometry=newpd.geometry, crs='EPSG:4326').reset_index(drop=True)

        where_geometry_none = newpd[newpd['geometry'].isna()]['where'].unique()
        if where_geometry_none.size>0:
            PyvoaWarning('Those localisation have None geometry, remove them ...:'+str(where_geometry_none))
        newpd = newpd.dropna(subset=['geometry'])
        return newpd

   def get_stats(self,**kwargs):
       """Return the keyword arguments filled in from the input arguments.

       Tests every argument and its values, and applies the options asked for, in
       particular 'nonneg', which redistributes values so as to remove the
       negative ones.
       """
       defaultargs = InputOption().d_batchinput_args
       option = kwargs.get('option',defaultargs['option'][0])
       kwargs_values_testing(option,defaultargs['option'],'option error ... ')
       output = kwargs['output']
       kwargs_values_testing(output,defaultargs['output'],'output error ...')

       which = kwargs.get('which')
       if not isinstance(which,list):
           which=[which]
       input = kwargs.get('input')
       # what  = kwargs.get('what')
       when  = kwargs.get('when')
       where = kwargs.get('where')
       if kwargs['kwargsuser']['input'].empty:
           remove_all_execept_which = [x for x in self.listwhich(self.db) if x not in which]
           input = input.drop(columns=remove_all_execept_which)

       if input.empty:
            available_keywords = self.get_available_keywords()
            kwargs_values_testing(which,available_keywords,'which error ...')
            input = self.currentdata.get_maingeopandas()

            #anticolumns = [x for x in available_keywords if x not in which]
            #input = input[which].loc[:,input.columns.isin(anticolumns)]
       date_max_by_where = input.groupby('where')['date'].max()
       if date_max_by_where.nunique() > 1:
            PyvoaWarning(
                "Some 'where' values have different end dates; "
                "the data will be reindexed."
            )

            all_dates = np.sort(input['date'].unique())

            input = (
                input.set_index(['where', 'date'])
                  .groupby(level=0)
                  .apply(lambda g: g.droplevel(0)
                                    .reindex(all_dates)
                                    .ffill()
                                    .bfill())
                  .reset_index()
                  .rename(columns={'index': 'date'})
            )

       if not pd.api.types.is_datetime64_any_dtype(input['date']):
          input['date'] = pd.to_datetime(input['date'], errors='coerce')

       when_beg_data, when_end_data = input.date.min(), input.date.max()
       when_beg, when_end = dt.date(1, 1, 1), dt.date.today()

       if when:
           when_beg, when_end = extract_dates(when)
           if when_beg < when_beg_data.date():
                when_beg = when_beg_data
                PyvoaWarning("No available data before "+str(when_beg_data) + ' - ' + str(when_beg) + ' is considered')
           if when_end > when_beg_data.date():
                when_end = when_end_data
                PyvoaWarning("No available data after "+str(when_end_data) + ' - ' + str(when_end) + ' is considered')
       else:
            when_beg, when_end = input.date.min(), input.date.max()
       if when_beg != when_end:
           input = input[(input.date >= pd.to_datetime(when_beg)) & (input.date <= pd.to_datetime(when_end))]
           kwargs['input'] = input
           when_beg_data,when_end_data = when_beg, when_end

       #kwargs['when'] = [str(when_beg_data)+':'+str(when_end_data)]
       kwargs['when']=[when_beg_data.strftime("%d/%m/%Y")+':'+when_end_data.strftime("%d/%m/%Y")]

       bypopvalue = None
       #datesunique = list(input.date.unique())
       kwargs['input'] = input

       if kwargs['kwargsuser']['input'].empty:
          input = self.whereclustered(**kwargs)

       prefix = ['date', 'where']
       suffix = ['code','geometry']
       for w in which:
           option = kwargs.get('option',defaultargs['option'][0])
           input[w] = (
           input.groupby('where')[w]
                 .apply(lambda s: s.bfill().ffill())
                 .reset_index(level=0, drop=True)
                 .fillna(0)
                 )

           #kwargs['input'] = input
           #if kwargs['kwargsuser']['input'].empty:
           #       input = self.whereclustered(**kwargs)

           has_normalize = any(o.startswith("normalize:") for o in option)
           has_sumall = "sumall" in option

           if has_sumall and has_normalize:
                normalize = [x for x in option if x.startswith('normalize:')]
                option = [x for x in option if not x.startswith('normalize:')]
                normalize = re.sub(r'normalize:', '', normalize[0])
                option.append('sumallandnormalize:'+normalize)

           concatpd = pd.DataFrame()
           basecolumns=list(input.columns)

           for o in option:
               temppd = input
               if o == 'nonneg':
                   if w.startswith(('cur_idx_', 'cur_tx_')):
                        print('The default option nonneg cannot be used with instantaneous data, such as : ' + w)
                   temppd = getnonnegfunc(temppd, w)
               elif o == 'smooth7':
                    temppd[w] = temppd[w].astype(float)
                    temppd.loc[:,w] = temppd.groupby(['where'])[w].rolling(7,min_periods=7).mean().reset_index(level=0,drop=True)
                    inx7 = temppd.groupby('where').head(7).index
                    temppd = temppd.reset_index(drop=True)
                    temppd.loc[inx7, w] = temppd[w].bfill()
               elif o == 'sumall':
                    if 'geometry' in list(temppd.columns):
                        if w.startswith(('cur_idx_', 'cur_tx_')):
                            temppd = temppd.groupby(prefix+suffix).mean().reset_index()
                    else:
                        temppd = temppd.groupby('date').agg(
                            where=('where', lambda x: ','.join(x)), **{w: (w, 'sum')}).reset_index()
               elif o.startswith('normalize:'):
                     temppd = self.normbypop(temppd , w ,o)
                     kwargs['input'] = temppd
                     temppd = self.whereclustered(**kwargs)
                     bypopvalue=o
               elif o.startswith('sumallandnormalize:'):
                    bypop = re.sub(r'sumalland', '', o)
                    dpop = InputOption().dictpop
                    temppd.loc[:,w+' '+bypop]=temppd[w]/temppd['population']*dpop[re.sub(r'normalize:', '', bypop)]
               if concatpd.empty:
                    concatpd = temppd
               else:
                    concatpd = pd.merge(concatpd, temppd,  how="right", on=basecolumns)

           if not concatpd.empty:
               input = concatpd

           windows = InputOption().windows
           for k,v in windows.items():
               input.loc[:,w+k]  = input.groupby('where')[w].diff(v)
               input.loc[:,w+k]  = input[w + k].bfill()
               if bypopvalue is not None:
                  input = self.normbypop(input, w+k ,bypopvalue)

       if when_beg == when_end:
          input = input[(input.date >= pd.to_datetime(when_beg)) & (input.date <= pd.to_datetime(when_end))]

       if 'geometry' in input.columns:
         input = gpd.GeoDataFrame(input, geometry=input.geometry, crs='EPSG:4326').reset_index(drop=True)
       if not isinstance(kwargs['which'],list):
           kwargs['which'] = [kwargs['which']]

       if input.empty:
           raise PyvoaError('Data seems to be empty for :'+str(where))

       # uniqwhere=list(input['where'].unique())
       others = sorted([c for c in input.columns if c not in prefix + suffix])
       new_order = prefix + others + suffix
       if 'geometry' not in input.columns:
           new_order.remove('geometry')
       if 'code' not in input.columns:
          new_order.remove('code')
       kwargs['input'] = input[new_order].reset_index(drop=True)
       return kwargs

   def normbypop(self, pandy , val2norm ,bypop):
    """Return a pandas with a normalisation column added by population.

    Can normalise by '100', '1k', '10k', '100k' or '1M', naming the new
    variable accordingly.
    """
    dpop = InputOption().dictpop
    if pandy.empty:
        raise PyvoaError('normbypop problem, your pandas seems to be empty ....')
    value = re.sub(r'normalize:', '', bypop)
    # clust = list(pandy['where'].unique())  # unused since its only reader was dead code

    pop_field='population'

    uniquepandy = pandy.groupby('where').first().reset_index()
    if self.db_world:
        try:
            uniquepandy = self._gi.add_field(input = uniquepandy,field = 'population',overload=True)
        except Exception as e:
            raise PyvoaError(self.db + ' has no information for what concern: '+pop_field) from e
    else:
        if not isinstance(self._gi,coge.GeoCountry) or self._gi.get_country() != self.geo.get_country():
            self._gi = None

        if self._gi is None :
            self._gi = self.geo
        pop_field='population_subregion'
            # regsubreg={i:self.geo.get_subregions_from_region(name=i) for i in clust}
        if self.granularity in ('region', 'subregion'):
            try:
                uniquepandy = self._gi.add_field(input=uniquepandy, field=pop_field, input_key='code',overload=True)
            except Exception as e:
                raise PyvoaError(self.db + ' has no information for what concern: '+pop_field) from e
        else:
            raise PyvoaError('This is not region nor subregion what is it ?!')
    uniquepandy = uniquepandy[['where',pop_field]]
    if pop_field not in pandy.columns:
        pandy = pd.merge(pandy,uniquepandy,on='where',how='outer')
    if not isinstance(val2norm, list):
        val2norm=[val2norm]

    for i in val2norm:
        i+' '+bypop
        pandy.loc[:,i+' '+bypop]=pandy[i]/pandy[pop_field]*dpop[value]
    return pandy

   def saveoutput(self,**kwargs):
       """Save a pyvoa pandas as an output file.

       Parameters
       ----------
       pandas : pd.DataFrame
           The pyvoa pandas to save. Mandatory.
       saveformat : str
           'excel' or 'csv'. Default is 'excel'.
       savename : str
           The file name, without its extension. Default is 'pyvoa_out', hence
           pyvoa_out.xlsx or pyvoa_out.csv.

       Notes
       -----
       The 'date' column is rewritten as dd/mm/yyyy strings in place, on the
       frame given rather than on a copy of it.
       """
       possibleformat=['excel','csv']
       saveformat = 'excel'
       savename = 'pyvoa_out'
       pandyori = ''
       if 'saveformat' in kwargs:
            saveformat = kwargs['saveformat']
       if saveformat not in possibleformat:
           raise PyvoaError('Output option '+saveformat+' is not recognized.')
       if 'savename' in kwargs and kwargs['savename'] != '':
          savename = kwargs['savename']

       if 'pandas' not in kwargs:
          raise PyvoaError('Absolute needed variable : the pandas desired ')
       else:
          pandyori = kwargs['pandas']
       pandy = pandyori
       pandy['date']=pandy['date'].apply(lambda x: x.strftime('%d/%m/%Y'))
       if saveformat == 'excel':
           pandy.to_excel(savename+'.xlsx',index=False, na_rep='NAN')
       elif saveformat == 'csv':
           pandy.to_csv(savename+'.csv', encoding='utf-8', index=False, float_format='%.4f',na_rep='NAN')

   ## https://www.kaggle.com/freealf/estimation-of-rt-from-cases
   def smooth_cases(self,cases):
        """Smooth a daily series with a centred gaussian window.

        Uses a seven-day gaussian window and drops everything up to the last
        zero, so that the series starts where the epidemic is actually under
        way. Used by the Rt estimation below.

        Parameters
        ----------
        cases : pd.Series
            the daily counts.

        Returns
        -------
        pd.Series
            the smoothed counts.
        """
        new_cases = cases

        smoothed = new_cases.rolling(7,
            win_type='gaussian',
            min_periods=1,
            center=True).mean(std=2).round()
            #center=False).mean(std=2).round()

        zeros = smoothed.index[smoothed.eq(0)]
        if len(zeros) == 0:
            idx_start = 0
        else:
            last_zero = zeros.max()
            idx_start = smoothed.index.get_loc(last_zero) + 1
        smoothed = smoothed.iloc[idx_start:]
        new_cases.loc[smoothed.index]

        return smoothed

   def get_posteriors(self,sr, window=7, min_periods=1):
        """Estimate the posterior distribution of the reproduction number Rt.

        Bayesian day-by-day update over a grid of possible Rt values, with a
        gamma prior and a Poisson likelihood whose rate follows from the
        previous day's count and a serial interval of seven days. Adapted from
        the kaggle notebook credited above the method.

        Parameters
        ----------
        sr : pd.Series
            the smoothed daily counts.
        window : int
            the smoothing window, kept for signature
            compatibility.
        min_periods : int
            likewise.

        Returns
        -------
        tuple
            (posteriors over the Rt grid for each day, the log
            likelihood of the series).
        """
        from scipy import stats as sps
        # We create an array for every possible value of Rt
        R_T_MAX = 12
        r_t_range = np.linspace(0, R_T_MAX, R_T_MAX*100+1)

        # Gamma is 1/serial interval
        # https://wwwnc.cdc.gov/eid/article/26/6/20-0357_article
        GAMMA = 1/7

        lam = sr[:-1].values * np.exp(GAMMA * (r_t_range[:, None] - 1))

        # Note: if you want to have a Uniform prior you can use the following line instead.
        # I chose the gamma distribution because of our prior knowledge of the likely value
        # of R_t.

        # prior0 = np.full(len(r_t_range), np.log(1/len(r_t_range)))
        prior0 = np.log(sps.gamma(a=3).pdf(r_t_range) + 1e-14)

        likelihoods = pd.DataFrame(
            # Short-hand way of concatenating the prior and likelihoods
            data = np.c_[prior0, sps.poisson.logpmf(sr[1:].values, lam)],
            index = r_t_range,
            columns = sr.index)

        # Perform a rolling sum of log likelihoods. This is the equivalent
        # of multiplying the original distributions. Exponentiate to move
        # out of log.
        posteriors = likelihoods.rolling(window,
                                     axis=1,
                                     min_periods=min_periods).sum()
        posteriors = np.exp(posteriors)

        # Normalize to 1.0
        posteriors = posteriors.div(posteriors.sum(axis=0), axis=1)

        return posteriors
