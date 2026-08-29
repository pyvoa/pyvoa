"""Parsing of the JSON database descriptions.

``MetaInfo`` reads the description files shipped under ``pyvoa/data/``, one per
database, and answers what is available and what each one declares.
``DataParser`` downloads the datasets a description names, normalises their
columns to pyvoa's own, resolves their locations against the matching geography
and concatenates the result into a single long DataFrame.

Adding a database means adding a JSON file here, not writing python.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
"""
import importlib.resources as pkg_resources
import json
import os.path
from os import listdir
from os.path import isfile, join

import numpy as np
import pandas as pd

import pyvoa
import pyvoa.geo as coge
from pyvoa.tools import (
    PyvoaError,
    PyvoaWarning,
    fill_missing_dates,
    get_live_mode,
    get_local_from_url,
    week_to_date,
)


class MetaInfo:
  """The catalogue of the databases pyvoa ships.

  Reads the JSON description files under pyvoa/data/, one per database,
  and answers what is available and what a given database declares: its
  geography, its datasets and their urls, and the columns each of them
  carries. Adding a database means adding a file here, not writing code.
  """

  def __init__(self):
        """Describe the epidemiological variables of a database.

        For the database called namedb, returns a dictionary keyed on the
        epidemiological variable, whose values are the new variable name for
        pyvoa's purposes (an empty string by default), a description of the
        variable (an empty string by default, though describing it is strongly
        recommended), the url of the csv the variable is read from, and the url of
        the master page where a general description may be found (an empty string
        by default).
        """
        self.dropdb = []
        self.pdjson = MetaInfo.getallmetadata()

  @staticmethod
  def parsejson(file):
    """Parse the description of the selected database, in json format.

    The json description reads like this::

        "header": "Some Header",
        "geoinfo": {
                    "granularity": "country / region / subregion ",
                    "iso3": "World / Europe /country name / ..."
                    },
        "columns / rows ": [
                {
                        "name":"XXX",
                        "alias":"XXX",
                        "description":"Some description of the variable",
                        "url": "https://XXX",
                        "urlmaster":"https://XXX"
                },
                ...
                ]
        }

    where columns / rows are the ones to keep from the database, 'name' is the
    name of the variable in pyvoa, 'alias' its original name in the database,
    'url' the location of the database and 'urlmaster' an optional master url.
    """
    filename = os.path.basename(file)
    check_file = os.path.isfile(file)

    if check_file:
        sig, msg = 1, ''
        try:
            with open(file, 'r') as fp:
                data = json.load(fp)
                sig, msg = MetaInfo.checkmetadatastructure(data)
                if sig == 0:
                    data = 'Database json description incompatible: '+ msg
        except ValueError as e:
            sig = 0
            data = 'Invalid json file ' + filename + f': {e}'
    else:
        sig = 0
        data = 'This file :' + filename +  ' do not exist'
    return {sig:data}

  @staticmethod
  def getallmetadata():
      """List every valid json file of the json folder.

      Returns
      -------
      dict
          The database name as the key, and the parsed json file as the value,
          or the error if the file does not exist or is not valid. Only valid
          json files are returned.
      """
      #pkg_resources.files(pyvoa).joinpath("data", filename)
      #currentpath=os.getcwd()
      #if os.path.isdir(currentpath+'/json'):
      #  jsp = currentpath+'/json/'
      #elif os.path.isdir(currentpath+'/../json'):
      #      jsp = currentpath+'/../json/'
      #else:
      #      raise PyvoaError('Where the json database description folder is supposed to be ?')
      pathmetadb = str(pkg_resources.files(pyvoa).joinpath("data"))
      onlyfiles = [f for f in listdir(pathmetadb) if isfile(join(pathmetadb, f)) and f.endswith('.json')]
      col = ['name','validejson','parsingjson']
      df = pd.DataFrame(columns = col)
      valide = ''
      for i in onlyfiles:
         name = i.replace('.json','')
         metadata = MetaInfo.parsejson(pathmetadb+"/"+i)
         try:
             meta = metadata[1]
             valide = 'GOOD'
         except IndexError:
             meta = metadata[0]
             valide = 'BAD'
         tmp=pd.DataFrame([[name,valide,meta]],columns=col)
         df = pd.concat([df,tmp],ignore_index=True)
      return df

  def getcurrentmetadata(self,namedb):
      """Return current meta information from the json file i.e from "namedb".json."""
      if namedb:
          line = self.pdjson.loc[self.pdjson.name == namedb]
          if line.empty:
              raise PyvoaError('Unknown database "' + str(namedb) + '". Available '
                  'databases are : ' + ', '.join(sorted(self.pdjson.name)) + '.')
          if line.validejson.values[0] == 'GOOD':
              try:
                  return line.parsingjson.values[0]
              except Exception as e:
                  raise PyvoaError('Database json description incompatible, please check') from e
          else:
            error =  " Database json parsing error:\n" + line.parsingjson.values[0]
            raise PyvoaError(error)
      else:
          raise PyvoaError("Does a Database has been selected ? 🤔")

  def getcurrentmetadatawhich(self,dico):
      """Retrieve the "which" values from the parsed json.

      They are the ones defined by the 'name' keyword in the json file.
      """
      which=[]
      for i in dico['datasets']:
        for j in i['columns']:
            if j['name']:
                which.append(j['name'])
        if 'namedata' in i:
                which.append(i['namedata'])
      if 'date' in which:
            which = list(filter(('date').__ne__, which))
      if 'where' in which:
            which = list(filter(('where').__ne__, which))
      return which

  @staticmethod
  def checkmetadatastructure(metastructure):
      """Check that the mandatory json metadata keys are present.

      Some metadata are mandatory in the json file; this checks that all of them
      are there.

      Returns
      -------
      list
          A 2D list: sig (1 ok, 0 not good) and the message.
      """

      def test(dico,lm):
          """Report whether every key of lm is present in dico.

          Returns
          -------
          list
              [1, 'validated'] if all are there, else [0, a message
              naming the first one missing].
          """
          sig = 1
          msg = 'pyvoa.json meta structure is validated'
          for i in lm:
              if i not in dico:
                 sig = 0
                 msg = 'Missing in your json file : '+i
          return [sig,msg]

      jsonkeys0 = ['geoinfo','datasets']
      sig, msg = test(metastructure,jsonkeys0)
      if sig == 1:
          geoinfokeys = ['granularity','iso3','locationmode']
          sig, msg = test(metastructure['geoinfo'],geoinfokeys)
          if sig == 1:
              datasetskeys = ['urldata','columns']
              for i in metastructure['datasets']:
                  sig, msg = test(i,datasetskeys)
                  if sig == 1:
                      columnskeys = ['name']
                      for i in metastructure['datasets']:
                          for j in i['columns']:
                              sig,msg = test(j,columnskeys)
      return [sig,msg]

class DataParser:
  """One database, parsed from its JSON description into a DataFrame.

  Downloads the datasets the description declares, normalises their
  columns to pyvoa's names, resolves their locations against the matching
  geography, and concatenates the result into a single long DataFrame
  indexed by date and location. The keyword definitions and source urls
  are kept alongside, so that a variable can be traced back to the file
  and the provider it came from.
  """

  def __init__(self, namedb):
        """Load one database and parse it.

        Reads the JSON description of namedb, picks the geography that matches
        its declared granularity -- a GeoManager for a world-wide database, a
        GeoCountry for a national one -- and parses the data straight away, so
        a DataParser is usable as soon as it is built.

        Parameters
        ----------
        namedb : str
            the database name, as listed by MetaInfo.

        Raises
        ------
        PyvoaError
            if the granularity is not one of country, region or
            subregion, or if parsing fails, which usually means the
            upstream file changed shape.
        """
        self.db = namedb
        self.granu_country = False
        self.metadata = MetaInfo().getcurrentmetadata(namedb)
        granularity = self.metadata['geoinfo']['granularity']
        code = self.metadata['geoinfo']['iso3']
        if granularity == 'country': # world wide dba
            self.granu_country = True
            self.geo = coge.GeoManager('name')
            self.geo_all = 'world'
        else: # local db
            self.geo = coge.GeoCountry(code)
            if granularity == 'region':
                self.geo_all = self.geo.get_region_list()
            elif granularity == 'subregion':
                self.geo_all = self.geo.get_subregion_list()
            else:
                raise PyvoaError('Granularity problem: neither country, region or subregion')
        try:
            # specific reading of data according to the db
            self.mainpandas = self.get_parsing()
        except Exception as e:
            raise PyvoaError("An error occured while parsing data of "+self.db+". This may be due to a data format modification. "
                "You may contact contact@pyvoa.org . Thanks.") from e

  def get_parsing(self,):
      """Parse the json file loaded by the init function (self.metadata).

      Returns a pandas with the structure ``|date|where|code|var-1 ... var-n|
      geometry``, where the var-i are the variables selected in the json file.
      "where" and "code" go through the geo methods, to assure a good
      standardization.
      """
      if 'header' in list(self.metadata.keys()):
          self.dbdescription = self.metadata['header']
      else:
          self.dbdescription = 'No description for DB = ' + self.db
      pandas_db = pd.DataFrame()
      locationmode = self.metadata['geoinfo']['locationmode']
      granularity = self.metadata['geoinfo']['granularity']
      place = self.metadata['geoinfo']['iso3']
      debug = None
      if 'debug' in list(self.metadata.keys()):
          debug = self.metadata['debug']
      replace_field = False
      if 'replace' in list(self.metadata.keys()):
          replace_field = self.metadata['replace']

      self.url = []
      self.keyword_definition = {}
      self.keyword_url = {}
      pdata = pd.DataFrame()
      for datasets in self.metadata['datasets']:
          url = datasets['urldata']
          if get_live_mode():
              if datasets.get('urlparent'):
                  url = datasets['urlparent']
              else:
                  PyvoaWarning('No live source (urlparent) for one dataset of '
                               +self.db+'. Using the archived data instead.')
          pdatatemp = pd.DataFrame(datasets['columns'])

          if 'alias' in list(pdatatemp.columns):
             # pdata.alias.fillna(pdata.name, inplace=True)
              pdatatemp["alias"] = pdatatemp["alias"].fillna(pdatatemp["name"])
          else:
              pdatatemp['alias'] = pdatatemp['name']
          if 'description' in list(pdatatemp.columns):
               pdatatemp['description'] = pdatatemp['description'].fillna(value='No description')
          else:
              pdatatemp['description'] = 'No description'

          if 'cumulative' in list(pdatatemp.columns):
             pdatatemp['cumulative'] = pdatatemp['cumulative'].fillna(value=False)
          else:
            pdatatemp['cumulative'] = False

          if 'fillmissing' in list(pdatatemp.columns):
             pdatatemp['fillmissing'] = pdatatemp['fillmissing'].fillna(value=False)
          else:
            pdatatemp['fillmissing'] = False

          usecols = pdatatemp.alias.to_list()
          selections = None
          if 'selections' in list(datasets.keys()):
              selections = datasets['selections']
              usecols += list(selections.keys())
          dropcolumns = None
          if 'dropcolumns' in list(datasets.keys()):
              dropcolumns = datasets['dropcolumns']
              usecols = None
          separator = ';'
          if 'separator' in list(datasets.keys()):
              separator = datasets['separator']
          na_values = ''
          if 'na_values' in list(datasets.keys()):
              na_values = datasets['na_values']
          names = None
          if 'names' in list(datasets.keys()):
              # csv shipped without any header line, the json gives the columns
              names = datasets['names']
          splitwhere = None
          if 'splitwhere' in list(datasets.keys()):
              # location given as "sub unit, parent unit", only a part of which
              # is the location the database is indexed by
              splitwhere = datasets['splitwhere']
          drop = {}
          if 'drop' in list(datasets.keys()):
              drop=datasets['drop']
          cast = None
          if 'cast' in list(datasets.keys()):
               cast = datasets['cast']
          decimal='.'
          if 'decimal' in list(datasets.keys()):
             decimal=datasets['decimal']
          rename_columns = None
          if 'alias' in list(pdatatemp.columns) and 'name' in list(pdatatemp.columns):
            rename_columns = pdatatemp.set_index('alias')['name'].to_dict()

          kd = pdatatemp.loc[~pdatatemp.name.isin(['where','date'])].set_index('name')['description'].to_dict()

          for k,v in kd.items():
              self.keyword_definition[k]=v
              self.keyword_url[k]=url
          try:
              thewhere=[k for k, v in rename_columns.items() if v == 'where']
              if thewhere:
                  if len(thewhere)>1:
                      raise PyvoaError('Something seral where in your json !')
                  else:
                      if cast:
                          cast.update({thewhere[0]:'str'})
                      else:
                          cast={thewhere[0]:'str'}
              pandas_temp = pd.read_csv(get_local_from_url(url,10000), sep = separator, usecols = usecols,
              #pandas_temp = pd.read_csv(url, sep = separator, usecols = usecols,
                            keep_default_na = False, na_values = na_values ,
                            header = 0 if names is None else None, names = names,
                            dtype = cast, decimal = decimal,
                            low_memory = False, nrows = debug, comment='#')
              if pdata.empty:
                 pdata = pdatatemp.copy()
              else:
                 pdata=pd.concat([pdata,pdatatemp])
          except Exception as e:
              raise PyvoaError('Something went wrong during the parsing') from e

          if drop and not debug:
              for key,val in drop.items():
                  if key in pandas_temp.columns:
                      if not isinstance(val,list):
                          val=[val]
                      for i in val:
                            pandas_temp = pandas_temp.dropna(subset=[key])
                            pandas_temp = pandas_temp[~(pandas_temp[key].str.startswith(i))]

          if selections:
              for key,val in selections.items():
                  if key in pandas_temp.columns:
                      pandas_temp = pandas_temp.loc[pandas_temp[key] == val]
                      pandas_temp = pandas_temp.drop(columns=key)
                  else:
                      raise PyvoaError("This is weird " + key + " selection went wrong ! ")
          if replace_field:
             for k,v in replace_field.items():
                 if v =='np.nan':
                    replace_field[k]=np.nan
             pandas_temp = pandas_temp.replace(replace_field)
          pandas_temp = pandas_temp.rename(columns = rename_columns)

          if splitwhere and 'where' in list(pandas_temp.columns):
              pandas_temp['where'] = pandas_temp['where'].astype(str).\
                  str.split(splitwhere.get('separator',',')).\
                  str[splitwhere.get('keep',-1)].str.strip()

          if dropcolumns:
              pandas_temp = pandas_temp.drop(columns=dropcolumns)
          value_name = None
          if "namedata" in list(datasets.keys()):
              value_name = datasets['namedata']
              if "var_name" in list(datasets.keys()):
                   pandas_temp = pandas_temp.melt(id_vars='date',var_name='where',value_name=value_name)
              else:
                  pandas_temp = pandas_temp.melt(id_vars='where',var_name='date',value_name=value_name)

          if usecols and ('semaine' in usecols or 'week' in usecols):
                 pandas_temp['date'] = [ week_to_date(i) for i in pandas_temp['date']]
                 #cols=[i for i in pandas_temp.columns if i not in ['date','where']]
                 #pandas_temp[cols] = pandas_temp[cols].apply(lambda x: x/7.)

          pandas_temp['date'] = pd.to_datetime(pandas_temp['date'], errors='coerce',format="mixed").dt.date

          if granularity == 'country' and 'where' not in list(pdata.name):
              pandas_temp['where'] = place
          pandas_temp['where'] = pandas_temp['where'].astype('string')

          whereanddate =  ['date','where']
          notwhereanddate =  [ i  for i in list(pandas_temp.columns) if i not in whereanddate ]
          self.available_keywords = notwhereanddate
          pandas_temp[notwhereanddate] = pandas_temp[notwhereanddate].apply(lambda col: pd.to_numeric(col.astype(str).str.replace(",", ".", regex=False), errors="coerce"))
          pandas_temp = pandas_temp[whereanddate+notwhereanddate]
          pandas_temp = pandas_temp.groupby(whereanddate).sum(min_count=1).reset_index()
          if pandas_db.empty:
              pandas_db = pandas_temp
          else:
              pandas_db = pandas_db.merge(pandas_temp, how = 'outer', on=['where','date'])
          self.url += [url]

      pandas_db = fill_missing_dates(pandas_db)

      # a source reporting increments says nothing on a day with no new count :
      # such a day is a zero, and filling it here keeps the cumulative sum below
      # from stopping at the first gap
      coltofill = pdata.loc[pdata['fillmissing'], 'name'].to_list()
      if coltofill:
          pandas_db[coltofill] = pandas_db[coltofill].fillna(0)

      coltocumul = pdata.loc[pdata['cumulative'], 'name'].to_list()

      if coltocumul:
          where_conditions = pdata.loc[pdata['name'] == 'where', 'name']
          if not where_conditions.empty:
              wh = where_conditions.values[0]
              pandas_db[coltocumul] = pandas_db.groupby(wh)[coltocumul].cumsum()
          else:
              pandas_db[coltocumul] = pandas_db[coltocumul].apply(pd.to_numeric, errors='coerce')

              pandas_db[coltocumul] = pandas_db[coltocumul].cumsum()

      pandas_db = pandas_db.sort_values(['where','date'])
      self.available_keywords = list(pandas_db.columns)
      if 'date' in self.available_keywords:
          self.available_keywords.remove('date')
      if 'where' in self.available_keywords:
         self.available_keywords.remove('where')
      locationdb = list(pandas_db['where'].unique())
      granularity = self.metadata['geoinfo']['granularity']
      codenamedico = {}
      geopd = pd.DataFrame()
      geopdbar = pd.DataFrame()
      if granularity == 'country':
          info = coge.GeoInfo()
          if locationmode == "name":
              g = coge.GeoManager('name')
              locationdb  = g.to_standard(locationdb,output='list',db = self.db)
              g = coge.GeoManager('iso3')
              namecode  = g.to_standard(locationdb,output='dict',db = self.db)
              codenamedico = {v.upper():k.upper() for k,v in namecode.items()}
          elif locationmode == "code":
              g = coge.GeoManager('name')
              codenamedico  = g.to_standard(locationdb,output='dict',db = self.db)
              print()
              #print(namecode)
              #codenamedico = {k.upper():v.upper() for k,v in namecode.items()}
          else:
              raise PyvoaError("Geo interpretation wrong ! not code nor name ...")

          geopd=pd.DataFrame({'where':codenamedico.values(),'code':codenamedico.keys()})
          geopd=info.add_field(input=geopd,field='geometry')
      elif granularity == 'subregion':
          geopd = self.geo.get_subregion_list()
          geopdbar = geopd.copy()
          if locationmode == "code":
              geopd = geopd.loc[geopd.code_subregion.isin(locationdb)]
              geopdbar = geopdbar.loc[~geopdbar.code_subregion.isin(locationdb)]
          else:
              geopd = geopd.loc[geopd.name_subregion.isin(locationdb)]
              geopdbar = geopdbar.loc[~geopdbar.name_subregion.isin(locationdb)]
          geopd['name_subregion'] = geopd['name_subregion'].str.upper()
          geopd['code_subregion'] = geopd['code_subregion'].str.upper()
          codenamedico = geopd.set_index('code_subregion')['name_subregion'].to_dict()
          geopd = geopd.rename(columns=({"code_subregion": "code","name_subregion":"where"}))
          geopdbar = geopdbar.rename(columns=({"code_subregion":"code","name_subregion":"where"}))
          geopdbar['date'] = pandas_db['date']
      elif granularity == 'region':
          geopd = self.geo.get_region_list()
          codenamedico = self.geo.get_data().set_index('code_region')['name_region'].to_dict()
          codenamedico = geopd.set_index('code_region')['name_region'].to_dict()
          geopd = geopd.rename(columns=({"code_region": "code","name_region":"where"}))
      else:
          raise PyvoaError('Not a region nors ubregion ... sorry but what is it ?')

      if locationmode == "code":
          pandas_db = pandas_db.rename(columns={"where": "code"})
          pandas_db['code'] = pandas_db['code'].str.upper()
          pandas_db['where'] = pandas_db['code'].map(codenamedico)
      elif locationmode == "name":
          pandas_db['where'] = pandas_db['where'].str.upper()
          namecodedico={v.upper():k.upper() for k,v in codenamedico.items()}
          pandas_db['code'] = pandas_db['where'].map(namecodedico)

      else:
          raise PyvoaError("what locationmode in your json file is supposed to be ?")
      if 'where' in pandas_db.columns:
          pandas_db=pandas_db.drop(columns='where')
      pandas_db = pd.merge(pandas_db,geopd, how = 'inner', on='code')
      #add region/subregion according to geo even if not present in the original DB parsed
      if not geopdbar.empty:
          pandas_db =  pd.concat([pandas_db, geopdbar],ignore_index=True)
      pandas_db['where']=pandas_db['where'].str.title()
      self.slocation = list(pandas_db['where'].unique())
      self.dates = list(pandas_db['date'].unique())
      pandas_db=pandas_db.dropna(subset=['geometry'])
      return pandas_db

  def get_db(self,):
     """Return the current covid19 database selected. See get_available_database() for full list."""
     return self.db

  def get_geo(self,):
      """Return the geography object this database is resolved against.

      Returns
      -------
      A GeoManager for a world-wide database, a GeoCountry otherwise.
      """
      return self.geo

  def get_world_boolean(self,):
    """Tell whether this database is world-wide rather than national.

    Returns
    -------
    bool
        True when its granularity is 'country'.
    """
    return self.granu_country

  def get_locations(self,):
      """Return the locations available in the current database.

      Countries, regions or subregions, standardized through the geo methods.
      """
      return self.slocation

  def get_dates(self,):
      """Return all dates available in the current database as datetime format."""
      return self.dates

  def get_available_keywords(self):
      """Return all the available keyswords for the database selected."""
      firstvalue = next((x for x in self.available_keywords if x.startswith(("tot_", "total_"))),self.available_keywords[0])
      self.available_keywords.insert(0, self.available_keywords.pop(self.available_keywords.index(firstvalue)))
      return self.available_keywords

  def get_url(self):
      """Return all the url which have been parsed for the database selected."""
      return self.url

  def get_keyword_definition(self,which):
      """Return available keywords (originally named original keywords) definition."""
      if which and which in self.get_available_keywords():
          return self.keyword_definition[which]
      else:
          raise PyvoaError("Missing which or which not in ",self.get_available_keywords())

  def get_keyword_url(self,which):
      """Return the url the given variable was parsed from.

      Parameters
      ----------
      which : str
          the variable name.

      Returns
      -------
      The url of the file this variable comes from.

      Raises
      ------
      PyvoaError
          if which is missing or is not a variable of this
          database.
      """
      if which and which in self.get_available_keywords():
          return self.keyword_url[which]
      else:
          raise PyvoaError("Missing which or which not in ",self.get_available_keywords())

  def get_dbdescription(self):
      """Return available information concerning the db selected."""
      return self.dbdescription

  def get_maingeopandas(self,):
      """Return the parsing of the data + the geometry description as a geopandas."""
      col = list(self.mainpandas.columns)
      reorder = ['date','where','code']
      reorder += [ i for i in col if i not in reorder ]
      self.mainpandas = self.mainpandas[reorder]
      return self.mainpandas
