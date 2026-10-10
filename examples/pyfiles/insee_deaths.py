#!/usr/bin/env python3
"""
insee_deaths.py — daily deaths in France since 2000, from the Insee death records.

pyvoa ships no Insee database: this script shows how a DataFrame built outside
pyvoa is handed to it through ``input=``. It reads the *Fichier des personnes
décédées* published by Insee on data.gouv.fr, counts the deaths per day and per
département of death, and draws one curve per year with
``typeofplot='yearly'``. The excess-mortality peaks are then annotated.

    https://www.data.gouv.fr/datasets/fichier-des-personnes-decedees

It is the script twin of examples/notebooks/PyvoaFront-withINSEE.ipynb, and
produces the figure of the data.gouv.fr reuse
https://www.data.gouv.fr/reuses/deces-journaliers-en-france-depuis-2000-vus-par-pyvoa

Usage
-----
    pip install pyvoa-full
    python insee_deaths.py                  # writes insee_deaths.png
    python insee_deaths.py -o deaths.pdf    # elsewhere, or in another format

The first run downloads about 3 GB (one file per year, monthly files for the
current one) into ~/.cache/pyvoa.data_<user>/; later runs read them back.

Licence: MIT, as pyvoa itself. The data are under the Licence Ouverte v2.0.
"""

import argparse
import json

import matplotlib
import pandas as pd

import pyvoa.front as pf
import pyvoa.tools as pt

CATALOGUE = 'https://www.data.gouv.fr/api/1/datasets/fichier-des-personnes-decedees/rdf.jsonld'
FIRST_YEAR, LAST_YEAR = 2000, 2026
WHEN = '01/01/2000:15/07/2026'

# The resource titled deces-2026-m09.txt actually serves deces-2025-m09.txt
# (same url basename, same size): reading it would add September 2025 a second
# time. Left out until Insee fixes it.
EXCLUDED = {'deces-2026-m09.txt'}

TITLE = 'Nombre de décès journaliers en France de 2000 à mi-juillet 2026'
BANNER = 'Données INSEE issues de data.gouv.fr 2000-2026 / @pyvoa.org'


def insee_files():
    """Return the files to read, year by year: the annual one, else the monthly ones."""
    with open(pt.get_local_from_url(CATALOGUE, expiration_time=86400, live=True)) as f:
        graph = pd.DataFrame(json.load(f)['@graph'])
    graph = graph.dropna(subset=['title', 'accessURL'])
    graph = graph[~graph['title'].isin(EXCLUDED)]
    files = {}
    for year in range(FIRST_YEAR, LAST_YEAR + 1):
        annual = graph[graph['title'] == f'deces-{year}.txt']
        monthly = graph[graph['title'].str.fullmatch(rf'deces-{year}-m\d\d\.txt')]
        chosen = annual if len(annual) else monthly
        files[year] = list(chosen.sort_values('title')['accessURL'])
    return files


def read_insee_file(url):
    """Count the deaths of one Insee file per date of death and per département.

    The files are fixed-width text: the name, holding a '*', in the first 80
    characters, the sex at 80, the date of death (AAAAMMJJ) from 154 and the
    code of the place of death from 162, the département in its first two
    characters. They are read as latin-1, which keeps one character per byte
    and so keeps the columns where the specification puts them. Lines with no
    valid date of death, among them deaths whose day or month is unknown
    (written 00), are dropped.
    """
    with open(pt.get_local_from_url(url, live=True), 'rb') as f:
        lines = pd.Series(f.read().decode('latin1').splitlines())
    lines = lines[lines.str[:80].str.contains('*', regex=False) & lines.str[80].isin(['1', '2'])]
    date = pd.to_datetime(lines.str[154:].str.strip().str[:8], format='%Y%m%d', errors='coerce')
    deaths = pd.DataFrame({'date': date, 'where': lines.str[162:164]}).dropna()
    return deaths.groupby(['date', 'where']).size()


def insee_deaths():
    """Return the cumulative deaths per département, in the long format pyvoa reads."""
    counts = []
    for year, urls in insee_files().items():
        for url in urls:
            print(year, url)
            counts.append(read_insee_file(url))
    daily = pd.concat(counts).groupby(level=['date', 'where']).sum().reset_index(name='deaths')
    daily = daily[daily['date'] >= f'{FIRST_YEAR}-01-01'].sort_values('date')
    daily['tot_deaths'] = daily.groupby('where')['deaths'].cumsum()
    return daily[['date', 'where', 'tot_deaths']].reset_index(drop=True)


# What is annotated: the label, where it is written (day of the year, number
# of deaths), the year the arrows point at, and for each arrow the window of
# days in which it points at the highest value. The colours are the ones the
# yearly plot gives those years.
ANNOTATIONS = [
    ('Grippe (2018)', (55, 2420), 2018, [(45, 75)]),
    ('Pics COVID (2020)', (35, 2950), 2020, [(80, 110), (295, 325)]),
    ('Canicules (2026)', (150, 3250), 2026, [(145, 160), (170, 190)]),
    ('Canicule (2003)', (290, 3480), 2003, [(215, 230)]),
    ('Reprises\népidémiques\nCOVID (2022)', (285, 2950), 2022, [(95, 120), (190, 210), (340, 365)]),
]


def year_colour(year):
    """Return the colour of a year: the 20-colour cycle, starting in 2000."""
    return matplotlib.colormaps['tab20'].colors[(year - FIRST_YEAR) % 20]


def annotate(ax):
    """Recolour the yearly curves and add the arrows, the title and the banner."""
    annotated = {year for _, _, year, _ in ANNOTATIONS}
    curves = {}
    for line in ax.get_lines():
        year = int(line.get_label().split()[0])
        curves[year] = line
        line.set_color(year_colour(year))
        line.set_linewidth(2.5 if year in annotated else 1.5)
        line.set_zorder(3 if year in annotated else 2)
    ax.get_legend().remove()
    ax.set_ylabel('')
    ax.set_ylim(1000, 3700)
    ax.set_xlim(-5, 370)
    ax.set_title('')
    ax.set_title(TITLE, fontweight='bold', loc='left')

    for label, xytext, year, windows in ANNOTATIONS:
        x, y = curves[year].get_data()
        peaks = pd.Series(y, index=x)
        for i, (d0, d1) in enumerate(windows):
            peak = peaks.loc[d0:d1].idxmax()
            ax.annotate(label if i == 0 else '', xy=(peak, peaks[peak]), xytext=xytext,
                        fontsize=12, ha='center', va='bottom', zorder=4,
                        arrowprops={'arrowstyle': '->', 'color': year_colour(year), 'lw': 2,
                                    'shrinkA': 2, 'shrinkB': 2})
    ax.text(0.02, 0.03, BANNER, transform=ax.transAxes, fontsize=12, zorder=5,
            bbox={'facecolor': 'yellow', 'edgecolor': 'none', 'pad': 3})


def main():
    """Build the series, draw it and write the figure."""
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('-o', '--output', default='insee_deaths.png')
    args = parser.parse_args()

    insee_pd = insee_deaths()
    pf.setbatch()
    pf.setvis('matplotlib')
    ax = pf.plot(input=insee_pd, which='tot_deaths', option='sumall', what='daily',
                 typeofplot='yearly', when=WHEN, title=TITLE, pyvoalogo=True)
    ax.figure.set_size_inches(12.8, 7.2, forward=False)
    annotate(ax)
    pf.savefig(args.output)


if __name__ == '__main__':
    main()
