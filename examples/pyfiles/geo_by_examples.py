#!/usr/bin/env python3
"""
geo_by_examples.py — the geo module of pyvoa, by examples.

The script twin of examples/notebooks/GeoByExamples.ipynb: the same calls, in
the same order, with the same explanations as comments. What the notebook
displays is printed, and its maps are written as geo_*.png in the current
directory.

Usage
-----
    pip install pyvoa
    python geo_by_examples.py

The first run downloads the geographic files it uses into
~/.cache/pyvoa.data_<user>/. Full reference:
https://pyvoa.github.io/pyvoa/api/geo.html

Licence: MIT, as pyvoa itself.
"""

import geopandas as gpd
import matplotlib
import pandas as pd

import pyvoa.geo as pg
from pyvoa.tools import PyvoaError

matplotlib.use('Agg')     # no window: the maps go to files

# GeoCountry: inside a country
#
# `GeoCountry('FRA')` loads the geography of a country, given by its ISO 3166 alpha-3 code.
# `get_list_countries()` lists those pyvoa knows (<https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoCountry>).
print(pg.GeoCountry().get_list_countries())
fra = pg.GeoCountry('FRA')
print(fra.get_country())

# What the geography carries: its source files (`get_source` <https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoCountry.get_source>), its
# columns (`get_list_properties` <https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoCountry.get_list_properties>), its regions and subregions —
# for France, the régions and the départements.
print(fra.get_source())
print(fra.get_list_properties())
print(fra.get_region_list())
print(fra.get_subregion_list())

# From a region to its subregions, by name — the case does not matter — or by code
# (<https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoCountry.get_subregions_from_region>).
print(fra.get_subregions_from_region(name='Bretagne'))
print(fra.get_subregions_from_region(name='BretagnE'))   # same answer
print(fra.get_subregions_from_region(code='11'))         # Île-de-France
print(fra.get_subregions_from_list_of_region_names(['Normandie', 'Hauts-de-France']))

# `get_data()` <https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoCountry.get_data> returns the geography as a GeoDataFrame, by subregion;
# `get_data(True)` by region. `set_dense_geometry()` <https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoCountry.set_dense_geometry> brings the overseas
# parts next to the mainland, as `map(typeofmap='dense')` does (France and the USA).
print(fra.get_data())
fra.get_data().plot().figure.savefig('geo_france.png')
fra.set_dense_geometry()
fra.get_data().plot().figure.savefig('geo_france_dense.png')

# GeoInfo: facts about countries
#
# `get_list_field()` lists what can be added; `get_source()` says where each comes from
# (<https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoInfo>).
gi = pg.GeoInfo()
print(gi.get_list_field())
print(gi.get_source())
print(gi.get_source('geometry'))

# `add_field()` <https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoInfo.add_field> adds one field or a list of them to a table whose
# `where` column names countries, in any spelling GeoManager understands. `overload=True` replaces a
# column that exists already; `geofield` names the column of countries when it is not `where`.
frame = pd.DataFrame({'where': ['France', 'Italy', 'Germany', 'Tunisia', 'Egypt'],
                      'value': [1, 2, 3, 4, 5]})
print(frame)
print(gi.add_field(input=frame, field='population'))
print(gi.add_field(input=frame, field=['capital', 'region_name_list', 'population', 'region_code_list']))
frame2 = frame.assign(capital=['a', 'b', 'c', 'd', 'e'])
print(gi.add_field(input=frame2, field='capital', overload=True))
frame3 = frame.rename(columns={'where': 'here'})
print(gi.add_field(input=frame3, field='area', geofield='here'))

# With the `geometry` field, a list of countries becomes a map:
countries = pg.GeoRegion().get_countries_from_region('commonwealth')
world = gpd.GeoDataFrame(gi.add_field(input=pd.DataFrame({'where': countries}), field='geometry'))
world.plot().figure.savefig('geo_commonwealth.png')

# GeoManager: one name for every spelling
#
# A GeoManager converts country names to a *standard*: `'iso2'` (default), `'iso3'`, `'name'` or `'num'`
# (`get_list_standard` <https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoManager.get_list_standard>), given when it is created or with
# `set_standard` <https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoManager.set_standard>).
gm = pg.GeoManager()
print(gm.get_list_standard())
gm.set_standard('name')
print(gm.get_standard())
print(pg.GeoManager('iso3').get_standard())

# `to_standard()` <https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoManager.to_standard> takes a name or a list of them, in English or in ISO
# codes. A name that is not a country raises a `PyvoaError`, unless `interpret_region=True` lets it stand
# for the countries of a region. An ambiguous name gives its first match, with a warning.
print(gm.to_standard('england'))
print(gm.to_standard(['esp', 'it', 'Berlin']))
try:
    gm.to_standard('European Union')
except PyvoaError:
    print('not a country')
print(gm.to_standard('European Union', interpret_region=True))
print(gm.to_standard(['usa', 'South America', 'russia'], interpret_region=True))
print(gm.to_standard('french'))   # ambiguous: first match, with a warning

# Some databases spell countries their own way; `db=` reads names as that database writes them
# (`get_list_db` <https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoManager.get_list_db>). `output` chooses what comes back: `'list'` (default),
# `'dict'` or `'pandas'` (`get_list_output` <https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoManager.get_list_output>).
print(gm.get_list_db())
print(gm.to_standard('Congo (Kinshasa)', db='jhu'))
print(gm.to_standard(['fr', 'spain', 'england'], output='dict'))
print(gm.to_standard(['fr', 'spain', 'england'], output='pandas'))

# GeoRegion: groups of countries
#
# Continents and sub-continents (UN M49 and UN geoscheme), economic and political unions
# (<https://pyvoa.github.io/pyvoa/api/geo.html#pyvoa.geo.GeoRegion>). These are the names `where=` accepts for a region.
gr = pg.GeoRegion()
print(gr.get_region_list())
print(gr.get_source())
print(gr.get_countries_from_region('South America'))
print(gr.get_pandas())
