#!/usr/bin/env python3
"""
pyvoa_for_beginners.py — the first steps with pyvoa.

The script twin of examples/notebooks/PyvoaForBeginners.ipynb: the same calls,
in the same order, with the same explanations as comments. What the notebook
displays is printed, and every chart is written to pyvoa_for_beginners/, numbered
in order: an image under matplotlib, an html page under bokeh.

Usage
-----
    pip install pyvoa
    python pyvoa_for_beginners.py

The first run downloads the databases it uses (owid and spf) into
~/.cache/pyvoa.data_<user>/. Every keyword is documented in
https://pyvoa.github.io/pyvoa/api/front.html

Licence: MIT, as pyvoa itself.
"""

from pathlib import Path

import matplotlib.pyplot as plt

import pyvoa.front as pf

OUT = Path('pyvoa_for_beginners')
OUT.mkdir(exist_ok=True)
pf.setbatch()      # draw without showing: the charts go to files
_count = 0


def save():
    """Write the chart just drawn, numbered in order."""
    global _count
    _count += 1
    name = OUT / f'{_count:02d}_{pf.getnamefunction()}_{pf.getvis()}'
    if pf.getvis() == 'bokeh':
        pf.savefig(str(name))             # bokeh appends .html
    else:
        pf.savefig(str(name) + '.png')
        plt.close('all')


# Basic usage
#
# - `setvis()` chooses the drawing library: `'bokeh'` (interactive) or `'matplotlib'` (<https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.setvis>).
# - `setwhom()` chooses the database (<https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.setwhom>). The first time, it downloads and parses it;
#   `reload=False` then reads back the copy kept on this machine, which is much faster.
pf.setvis('bokeh')
pf.setwhom('owid')       # Our World in Data, world-wide, by country

# Three charts: a time series (`plot` <https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.plot>), a histogram of the last date
# (`hist` <https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.hist>) and a map (`map` <https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.map>). Without keywords, each draws the default variable
# for every location of the database.
pf.plot(where='European Union')
save()
pf.hist(where='Asia')
save()
pf.map()
save()

# The drawing library
#
# `listvis()` lists the libraries installed. The same calls draw with either; bokeh charts can be zoomed and
# hovered, matplotlib ones are images (<https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.listvis>).
print(pf.listvis())
pf.setvis('matplotlib')
pf.plot(where='European Union')
save()
pf.map()
save()
pf.setvis('bokeh')
pf.plot(where='European Union')
save()
pf.map()
save()

# Choosing the data
#
# The database: `whom`
#
# `listwhom()` lists the databases, `listwhom(True)` describes them (<https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.listwhom>).
print(pf.listwhom())
pf.setwhom('owid', reload=False)   # read back the local copy: faster

# The variable: `which`
#
# `listwhich()` lists the variables of the current database (<https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.listwhich>).
# `tot_…` or `total_…` are running totals, `cur_…` values on the day (patients in hospital, for instance).
print(pf.listwhich())
pf.plot(which='cur_icu_patients')
save()

# How the values are reported: `what`
#
# `'current'` (default) as published, `'daily'` the change from one day to the next, `'weekly'` over seven days
# (<https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.listwhat>).
print(pf.listwhat())
pf.plot(what='daily')
save()
pf.plot(what='weekly')
save()

# Treatments: `option`
#
# - `'nonneg'`: spreads the negative corrections of a running total over the previous days;
# - `'smooth7'`: seven-day moving average;
# - `'sumall'`: one curve, the sum of all the locations asked for (slow on a world-wide database);
# - `'normalize:pop'`, `'normalize:pop100'` … `'normalize:pop1M'`: per inhabitant, per 100, … per million.
#
# Several options are given as a list (<https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.listoption>).
print(pf.listoption())
pf.plot(what='daily', option='smooth7')
save()
pf.plot(where='European Union', option=['sumall', 'normalize:pop100k'])
save()

# Where and when: `where`, `when`
#
# `where` takes a location, a list of them, or a region of the world: names, ISO codes and some aliases are
# understood (`listwhere` <https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.listwhere>). `when` takes a date `dd/mm/yyyy` or a range
# `dd/mm/yyyy:dd/mm/yyyy`, either side of which may be left empty.
pf.plot(where=['France', 'Italy', 'Esp'])   # names or codes
save()
pf.plot(where='European Union')             # a region
save()
pf.plot(where='France', when='01/01/2021:31/12/2021')
save()

# The kinds of chart
#
# Time series: `typeofplot`
#
# - `'date'` (default): one curve per location;
# - `'versus'`: one variable against another (two `which`);
# - `'yearly'`: one curve per year, for one location;
# - `'spiral'`: one turn per year, for one location (bokeh);
# - `'compare'`: a menu to choose the locations shown (bokeh, two locations or more).
#
# <https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.plot>
print(pf.listplot())
pf.plot(which=['total_deaths', 'total_cases'], where='France', typeofplot='versus')
save()
pf.plot(which='total_deaths', where='France', what='weekly', typeofplot='yearly')
save()
pf.plot(which='total_deaths', where='France', what='weekly', typeofplot='spiral')
save()
pf.plot(where=['Italy', 'France', 'Germany'], typeofplot='compare')
save()

# Histograms: `typeofhist`
#
# - `'location'` (default): one bar per location, at the last date;
# - `'value'`: how many locations fall in each range of values;
# - `'pie'`: the share of each location.
#
# Under bokeh, `dateslider=True` adds a slider over the dates (<https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.hist>).
print(pf.listhist())
pf.hist(where='South America')
save()
pf.hist(which='total_people_vaccinated', where='Europe', typeofhist='value')
save()
pf.hist(which='total_people_vaccinated', where='Europe', typeofhist='pie')
save()
pf.hist(where='South America', dateslider=True)
save()

# Maps: `typeofmap`, `tile`, `projection`
#
# - `'not dense'` (default): the locations where they are, over map tiles (`tile='openstreet'` or `'esri'`);
# - `'dense'`: overseas parts brought next to the mainland, without tiles (France and the USA);
# - `'show_values'`: the value written on each location.
#
# Under matplotlib, `projection` is `'eckert4'` (equal-area, default) or `'mercator'`. Under bokeh,
# `dateslider=True` adds a slider over the dates (<https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.map>).
print(pf.listmap())
pf.setwhom('spf', reload=False)   # Santé publique France, by département
pf.map(typeofmap='not dense')
save()
pf.map(typeofmap='dense')
save()
pf.map(typeofmap=['dense', 'show_values'])
save()
pf.setvis('matplotlib')
pf.map(tile='esri', projection='mercator')
save()

# The data themselves, and saving a chart
#
# `get()` <https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.get> takes the same keywords and returns the table drawn — a GeoDataFrame by default, or
# `output='pandas'`, `'list'`, `'dict'`, `'array'`. `savefig()` <https://pyvoa.github.io/pyvoa/api/front.html#pyvoa.front.front.savefig> writes the last chart to a
# file: an image under matplotlib, an html page under bokeh.
pf.get(which='cur_hosp', where='Paris', what='daily', output='pandas')
pf.plot(which='cur_hosp', where=['Paris', 'Rhône'])
save()
pf.savefig('hospitalisations.png')

print(f'Charts written to {OUT}/')
