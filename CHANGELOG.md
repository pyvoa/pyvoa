# Unreleased
- `get()` returns location names whole. They used to be cut to
  `maxlettersdisplayed` (20 characters, then '...') in the selection step that
  `get()` shares with the charts, so `get()` handed out `'Heilbronn
  (Landkreis...'` and a join of its output on the names failed. The cut is now
  made by `AllVisu`, for the charts only — the labels, legends and tooltips of
  `plot()`, `hist()` and `map()`, matplotlib and bokeh alike, bokeh's hover
  included — by `tools.shorten_locations()`, which keeps whole two names it
  would otherwise make identical. The docstrings said the cut was at ten
  characters and that `maxlettersdisplayed` was not read; neither was true.
- fix: the dense map joined its geometry on the cut names, so a location named
  in more than 20 characters lost it: three French départements
  (Alpes-de-Haute-Provence, Territoire de Belfort, Collectivités d'Outre-Mer)
  were left undrawn by `spf`.
- fix: the matplotlib time-series legend cut every label to ten characters on
  its own, whatever `maxlettersdisplayed` said.
- fix: `plot()`, `hist()` and `map()` neither returned the bokeh figure nor kept
  it for `savefig()`, which saved the previous figure instead.
- fix: a pie chart, or a histogram by value, of fewer locations than the twelve
  colours of the palette raised a `ValueError`.
- fix: the parser called `GroupBy.sum(skipna=False)`, which pandas only
  accepts from version 3, while the declared floor is 2.1.1: on the floor every
  database failed to parse, and the `minimum` CI job was red. The same result —
  a group holding a missing value stays missing — is now computed with
  `min_count=1` and a mask, on every supported pandas.
- fix: `typeofhist='pie'` on matplotlib, when no colours were given, and the
  bokeh histogram by value both raised a `NameError` (`cmap`, `lcolors`).
- fix: `GPDBuilder.getpklname()` built its `PyvoaError` without raising it, and
  returned `None` on a wrong argument.
- the manuscript and the README count 24 databases, since `sentinellesIRA` was
  removed for copyright reasons; the manuscript no longer cites the Réseau
  Sentinelles among the supported sources, and the README explains the
  *both (prefer live)* marking of `ebolardc` and `measles-usa`, both now
  mirrored on Zenodo.
- `ruff check .` is clean again: imports sorted, dead assignments commented
  out, and docstrings restored on `listwhere()`, `listwhich()` and
  `getdatabase()` of the front, which had lost them.
- locations reported by a source but missing from its geometry file are no
  longer dropped with their counts: they get an empty geometry, which goes
  through every join and is simply not drawn. That covers Curaçao, Sint
  Maarten and the Caribbean Netherlands in the world geometry, which predates
  the 2010 dissolution of the Netherlands Antilles (owid, europa, mpoxgh);
  Puerto Rico, Guam, the US Virgin Islands, the Northern Mariana Islands and
  American Samoa in the USA geography, as a `Territories` census region
  (jhu-usa, covidtracking); Lakshadweep (covid19india); and the Antártica
  comuna, 12202 (minciencia). `map()` raises a `PyvoaError` naming them when
  every location it is asked for is one of those.
- fix: `convertmercator()`, which `get()` runs on every geometry, skipped a
  location whose geometry was empty (falsy), so the join that followed left
  it with none, and `get()` dropped it.
- the Indian geography merges Dadra and Nagar Haveli with Daman and Diu into
  the union territory they formed in 2020 (`IN.DH`), under the name
  covid19india reports them by.
- covid19india: `Uttarakhand` mapped to the `Uttaranchal` of the Indian
  geography (6452 deaths were dropped), and `Andaman and Nicobar Islands` to
  `Andaman and Nicobar` — the existing rule mapped it to itself.
- escovid19data: `Balears, Illes` and `Palmas, Las` mapped to `Illes Balears`
  and `Las Palmas` (2146 deaths were dropped).
- ebolardc: `Rumba` mapped to `Rimba`. It is a typo of the 2026-07-11 sitrep,
  the only day it appears, in the middle of Rimba's series.
- fix: `fill_missing_dates()` no longer forward- and back-fills the days it
  inserts (introduced in `cf7bb53`). On a column of increments declared
  `cumulative`, the previous day's increment was repeated before the
  `cumsum`, so govcy reported 2082 deaths instead of 672, and every database
  using `cumulative` (dgs, measles-usa, moh, risklayer, sciensano, spf) was
  affected, `fillmissing` included. An inserted day stays NaN again; the
  cumulative series are forward-filled by `GPDBuilder.get`, as before.
- fix: `fill_missing_dates()` drops the timezone of a tz-aware date column
  before reindexing on its naive daily range. Since `cf7bb53`, rki (stamped
  in UTC) came out with every `tot_cases` / `tot_deaths` value NaN.
- new optional dataset key `dateformat` (a `strftime` pattern) fixes how the
  `date` column is read. Without it the parser keeps `format="mixed"`, which
  reads an ambiguous `9/3/2020` month-first: govcy and dgs, both day-first,
  had every date with a day ≤ 12 swapped with its month.
- govcy: `dateformat` `%d/%m/%Y`, and `tot_deaths` / `tot_cases` now read the
  source's own running totals (`total deaths`, `total cases`) instead of
  cumulating its daily columns, whose sum does not match them (673 vs 672
  deaths, 216652 vs 218374 cases).
- dgs: `dateformat` `%d-%m-%Y`, and `AÇORES` mapped to the `Azores` of the
  PRT geography, which dropped 7355 cases.
- moh: `W.P. Kuala Lumpur`, `W.P. Putrajaya` and `W.P. Labuan` mapped to the
  `Wilayah Persekutuan` / `Wilayah Persekutuan Labuan` of the MYS geography.
  The three federal territories were dropped, 10.7 % of the cases.
- risklayer: `cumulative` removed from `CumulativePositive` and
  `IncidenceCumulative`, which are already running totals and would have been
  cumulated twice by a source with more than one date per location.
- fix: the German geography (`GeoCountry('DEU')`) merged the rows of the
  DE-counties geojson on the county *name*, and kept one code per name. The
  22 Landkreise named like the kreisfreie Stadt they surround (München,
  Leipzig, Rostock, Kassel, Karlsruhe, …) were dropped, and rki lost 6.0 % of
  its cases and 5.4 % of its deaths, while each of those cities was drawn
  with its Landkreis's surface. The rows are now merged on the AGS code, and
  such a Landkreis is named after its type, `München (Landkreis)`; the city
  keeps its bare name. rki now matches its source exactly over its 401
  counties. The twelve Berlin districts rki also ships (11001–11012) are
  still left out, rightly: they add up exactly to Berlin (11000).
- Docstring updates
- Adding an ASCII banner when loading the front
- Enhancement and compatibility fixes for notebooks and py file examples
- Highlight locations absent from the original database in pink on the map.
- Add log scale in Bokeh
- Remove duplicate columns in the main pandas
- Fill missing values in maps for JHU and mpox datasets
- bug fix for 3 regions : Bug fix for regions. SACD, CENSAD and CELAC
- `set_verbose_mode()` and `get_verbose_mode()` are methods of the front class,
  so `pf.set_verbose_mode(2)` works alongside the rest of the front-level API
  and both appear in the published reference. They were previously reachable
  only as a side effect of being imported into `pyvoa/front.py`, which is why
  the lint pass removed them without anyone noticing. `pyvoa.tools` keeps the
  functions themselves; the front methods delegate. Front-level values are
  checked: anything other than 0, 1 or 2 raises a `PyvoaError` naming the three
  levels, where `pyvoa.tools.set_verbose_mode()` takes whatever it is given.
- `saveoutput()` writes `pyvoa_out.xlsx` / `pyvoa_out.csv` when no `savename`
  is given. The default used to be `pycoa.ut`, the wreckage of a `pycoa`
  rename that had run through the string itself, so the files came out as
  `pycoa.ut.xlsx`. An explicit `savename` is unaffected.
- fix: `saveoutput()` called before any `setwhom()` raised a bare
  `AttributeError` on `None`, since the writer lives on the `GPDBuilder` that
  only exists once a database is selected. It raises a `PyvoaError` naming
  `setwhom()`, like the rest of the library.
- the distribution now names its authors: `[project] authors` in
  `pyproject.toml` carries the three people, spelled as in `AUTHORS` and
  `CITATION.cff`, instead of the project address, so
  `importlib.metadata.metadata("pyvoa")["Author"]` and `pyvoa.__author__` no
  longer disagree. `maintainers` stays `contact@pyvoa.org`, the stable contact
  point. The build requirements dropped `wheel`, which setuptools declares by
  itself, and gained the `setuptools>=64` floor that reading the version out of
  `pyvoa/__version__.py` needs.
- `pyvoa/__version__.py` documents what it is instead of referring to the
  `setup.py` that no longer exists: that setuptools and `tests/test_paper.py`
  both read it *statically*, and that it must therefore stay a plain literal
  with no imports. `__author__` and `__email__` are marked as a mirror of
  `AUTHORS`, which is the canonical record.
- author metadata is aligned across the repository. `AUTHORS` and
  `paper/main.tex` carry the affiliations in the form the journal expects, and
  `CITATION.cff`, `.zenodo.json`, `codemeta.json` and `schemaorg.jsonld` now
  repeat them verbatim, together with Olivier Dadoun's `dadoun@in2p3.fr`
  address and the paper's keywords (`epidemiological data`, `geospatial data`).
  The same pass brought the two schema files back in step with
  `pyproject.toml`: `beautifulsoup4` instead of `bs4`, and Python 3.13 among
  the supported runtimes.
- every dependency now declares a lower bound, and the bounds are tested: a
  `minimum` CI job installs the floors on python 3.10 and runs the suite, so
  they cannot quietly become false. There are no upper bounds, on purpose — a
  cap in a library propagates into every environment that installs it. The
  declared minimum is pandas 2.1.1, geopandas 1.0, shapely 2.0.2, numpy 1.26.
- `bs4` is replaced by `beautifulsoup4` in the dependency list. It is the same
  code — `bs4` is a forwarding package — but its versions are `0.0.x`, so it
  could not carry a meaningful bound.
- `GeoCountry` gained four converters between codes and names:
  `from_subregion_codes_to_names`, `from_subregion_names_to_codes`,
  `from_region_names_to_codes` and `from_region_codes_to_names`. Each takes a
  list and answers in the same order, so the two lists can be zipped, and
  translates a repeated entry as many times as it appears. A non-list
  argument, or an entry absent from the country data, raises a `PyvoaError`
  that names the offending entries.
- Python 3.13 is declared as supported and added to the CI test matrix, which
  now covers 3.10, 3.11, 3.12 and 3.13.
- Python 3.14 joins them: the classifier is declared in `pyproject.toml`, the
  runtime is listed in `codemeta.json` and `schemaorg.jsonld`, and the `test`
  job of the CI matrix now runs the offline suite on 3.10 through 3.14. The
  manuscript's code-metadata table follows. Nothing in the package needed a
  change — no module removed in 3.14 is imported — so this is a claim the
  matrix now verifies rather than a port.
- fix: the four `GeoInfo` tests built a real `GeoInfo(0)`, which builds a
  `GeoManager` and downloads about ten pages, so they failed on CI and passed
  locally only on a warm cache. They now use `GeoInfo.__new__`, like the
  `GeoManager` tests next to them.
- `README.md` now documents installation (`pip install pyvoa`, `pyvoa-full`), a
  first example, and a table of the 23 supported databases with their coverage,
  granularity and source.
- fix: `GeoCountry('CHL')` gives every comuna its own `code_subregion`.
  The `COD_COMUNA` field of the meteochile shapefile is four characters wide,
  so the five-digit CUT codes of the regions numbered 10 and above lost their
  last digit upstream: the nine comunas of the Llanquihue province all read
  `1010` instead of `10101` to `10109`, and 346 comunas collapsed onto 254
  distinct values. Only 206 of them matched the `minciencia` join key, the
  other 140 dropping out of every map and series without a word. The code is
  now resolved from the comuna name through a CUT table archived on Zenodo
  (record 23047588, `chl_comuna_codes.csv`), so all 346 codes are distinct and 345 of
  them match the database — the one gap being Antártica (`12202`), which the
  shapefile has no geometry for. `Zona sin demarcar`, the undelimited Campo de
  Hielo Sur, is no comuna and keeps the `00000` the truncated field gave it.
  Ñuble comes with it: the CUT codes postdate its 2018 split out of Bío-Bío
  while the shapefile predates it, so `get_data(True)` would otherwise have
  returned two regions both named `Región del Bío-Bío`. It is named `Región de
  Ñuble` wherever `code_region` is `16`, and the region list is the sixteen
  official regions plus the undelimited zone.

# version 0.5.0
Eight months and 236 commits since 0.4.2 (2025-12-12 to 2026-08-06), in two
strands: the data and visualization work that occupied most of the period, and
the publication-readiness push of the last few days. A handful of names
changed, so this is not a drop-in upgrade from 0.4.2 — see the renames below.

Data sources and caching:

- eleven database descriptions were added, taking the catalogue from 12 to 23:
  `covid19india`, `covidtracking`, `dgs`, `dpc`, `escovid19data`, `jpnmhlw`,
  `minciencia`, `moh`, `phe`, `risklayer` and `rki`. `listwhom()` now answers
  in alphabetical order.
- the databases read from the project's own Zenodo deposits rather than from
  the original upstream sites, which had grown unreliable. The downloader
  identifies itself as wget, and a file under 1000 characters is treated as a
  failed download and fetched again.
- the download cache moved out of the system temporary directory to
  `~/.cache/pyvoa.data_<user>`, so it survives a reboot.
- `html5lib` became a mandatory dependency.

Geography:

- `where` is forced to a string internally, so numeric département or state
  codes no longer have to be cast at the call site.
- fix: USA subregions gained a three-character `code_region`; the ESP subregion
  naming was homogenised on `Coruña, A`; DEU data is cast to geopandas;
  Belgium's mixture of NaN and None in the geo data no longer breaks a lookup.
- fix: Canada, Chile, Greece and Norway could be drawn individually but not
  under `sumall`, an invalid-geometry problem worked around with `buffer(0)`.
  Portugal needed a different CRS.
- fix: the `europa` database declared its geography as `EUR` while its data is
  world-wide; it is described as `WLD` now.

Visualization:

- `setvisu()` is now `setvis()`, and `get_echoinfo()` moved to the front module.
- the axis-type option is now `scale` (`linear` or `log`), and it applies to
  both the matplotlib and the bokeh backends.
- the bokeh callbacks left the Python sources for `pyvoa/js/`: slider, rollover
  and animation are now three JavaScript files.
- location labels are truncated to a common length, decided in one place, with
  a `dicodisplayloc` keyword to override the displayed name.
- fix: a long list of plotting defects — log scales on histograms and on the
  yearly plot, missing histogram axis labels, the date slider, autozoom for
  maps with few points, country borders, 10⁸ tick notation on bokeh maps,
  colour maps that disagreed between the two backends, `savefig`, and the size
  and placement of the logo.

Data handling:

- fix: cumulative series were reworked throughout — the cumulative sum is taken
  after the missing values are filled, the first `tot_*` variable is selected
  by default, and several databases carried a cumulation they should not have.
- fix: the non-negative filter broke against newer pandas and numpy.
- a pandas or geopandas frame can be plotted through `input=` without calling
  `setwhom()` first, and a session can move between the two in either
  direction.

Errors, warnings and verbosity:

- `PyvoaError` is a real `Exception` subclass and is raised everywhere, instead
  of being called as a bare statement. It is the single exception type of the
  library; the former `PyvoaTypeError`, `PyvoaKeyError`, `PyvoaDbError`,
  `PyvoaWhereError`, `PyvoaLookupError`, `PyvoaConnectionError` and
  `PyvoaNotManagedError` names are gone.
- fix: a missing `import shutil` made every error raise `UnboundLocalError`
  instead of `PyvoaError` when running outside a terminal (script, cron, CI).
- fix: an unknown database name passed to `setwhom()` is reported as a
  `PyvoaError` rather than a `KeyError` from the JSON parser.
- fix: `return_nonan_dates_pandas` trims the leading all-NaN dates.
- `pyvoa/error.py` is gone: the error and warning helpers live in `tools.py`,
  which is also where the geometry helper `wgs84_to_web_mercator` moved, so
  both backends share one copy.
- Warnings are quiet at verbosity 1, and the noise that external modules print
  when a French map archive or a datetime column is read is swallowed below
  verbosity 2. This entry used to say that `set_verbose_mode()` was exposed on
  the front module as well. It was, on `main`, from `36e0768` (february 2026)
  until `5b127de` cleared the lint findings hours before the tag: the name was
  only ever imported into `front.py`, never used there, so ruff reported it as
  an unused import and removed it. No released version shipped it, and the
  claim was written four days after the removal. It is true again from the next
  release; see the Unreleased entry.

Packaging, tests and process:

- packaging moved to PEP 621: `setup.py` is deleted, `pyproject.toml` reads the
  version from `pyvoa/__version__.py`, and `import pyvoa` exposes
  `pyvoa.__version__` without pulling in the heavy dependencies.
- minimum Python is now 3.10; 3.10, 3.11 and 3.12 are tested.
- a pytest suite that never touches the network by default: any test needing an
  upstream server is marked `@pytest.mark.network` and deselected.
- continuous integration on GitHub Actions: lint, the test matrix, and a weekly
  job for the network tests.
- `ruff check .` is clean and enforced by CI.
- community files for citation and contribution: `AUTHORS`, `CITATION.cff`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md` and the issue forms.
- `__pycache__` is no longer tracked.

# version 0.4.2
- a re-release for pip: the version string and the help text, nothing else.

# version 0.4.1
- cosmetic: the project logo is the PNG one, and the JPEG `pyvoa_logo2.jpg` is
  dropped from the package data.

# version 0.4.0
Five months and 359 commits (2025-07-08 to 2025-12-12). The release settles the
vocabulary of the front-end API and finishes the visualization layer inherited
from pycoa, so nearly every rename a 0.3.x user has to know about is here.

- Most of the work consisted in adding decorators to the classes.
- Jupyter is not mandatory to use pyvoa; it can be used from a console.
- add json description of the database
- we use one class per visualization
- renamed on the front, with no compatibility aliases: `setvisu()` is
  `setvis()` (by way of a short-lived `setgraphics()`), `listvisu()` is
  `listvis()`, `getrawdb()` is `getdatabase()`, `listbypop()` is `listpop()`,
  `listtiles()` is `listtile()`, `listmapoption()` is `listmap()`,
  `listchartkargskeys()` is `listargument()`, and `getvisukwargs()` is
  `getkwargsvisu()`. `setdisplay()`, `getdisplay()` and `setoptvis()` are gone.
  `getvis()`, `listchart()`, `listargumentvalue()` and `getdbmetadata()` are
  new.
- renamed among the chart options: `bylocation` is `location`, `byvalue` is
  `value`, `menulocation` is `compare`, `bypop` is `pop`. `typeofmap` is new.
- `setbatch()` renders without opening a window, on every backend.
- a date slider for the bokeh maps, histograms and pie charts, with a play
  button.
- an external pandas or geopandas frame can be passed as `input=` and charted
  without loading a database at all, and the figure or map object can be
  retrieved rather than only displayed.
- a `help()` function in English, using ANSI codes instead of colorama, and a
  welcome message on import.
- matplotlib, seaborn and bokeh are detected at import, so a missing backend is
  reported instead of raising. The seaborn backend caught up with the others
  (yearly plot, legends, `savefig`, watermark, use from a terminal), and a
  folium map was added and then withdrawn from the advertised list before the
  tag.
- titles, legends, axis labels, logo and watermark were harmonised across the
  backends, and the plot title carries the database name and the date.
- fix: `bypop` was broken outright; `nonneg` is no longer applied by default;
  `sumall`, the cumulative sums, the empty-data cases and the map bounds under
  the date slider were each fixed several times over.
- fix: geography — the FRA description left an obsolete URL for the cached
  copy, France's overseas collectivities joined the dense geometry, GRC got a
  working URL, `europa` and `govcy` entered `geo.py`, and the mpox database
  lost an invalid `XKX` iso3.
- the JHU database is back, the `empty` placeholder is gone, and the Olympics
  database was removed for not being a virus database.
- the surviving `pycoa` references became `pyvoa`, and `pyvoa.fr` became
  `pyvoa.org`.

# version 0.3.1
First full release on PyPI. No git tag was ever pushed for it; the release was
prepared in `05b3f0c`.

- cosmetic and docstrings
- version for pip, first full version
- the docstrings were written across the whole code base with LLM assistance.
- Google Colab is detected and handled.
- the front-end input handling was refactored, and the error messages with it.
  `PyvoaError` no longer calls `sys.exit()`, so a caller can catch it and carry
  on.
- the error banner adapts to the terminal size, and to there being no terminal.

# version 0.3.0
- import of the whole former pycoa software into pyvoa
- using matplotlib as graphical output
- the import landed in a single commit — 24 files, about 5100 lines — bringing
  the bokeh, matplotlib and seaborn visualizers, the geo module and the JSON
  database descriptions.
- bokeh is detected rather than assumed, and the data path the import brought
  with it was corrected.

# version 0.2.2
- nothing (pip troubles with previous version)

# version 0.2.1
- Structure of the package to deal with pip
- data file can be access now. See test1.py
- no git tag was pushed for this one either.

# version 0.2.0
Adding geo and a python example. This changelog starts here.

# version 0.1.0
First import, skeleton only: the project structure and a first upload to PyPI.

---

# Before pyvoa — CoCoA and pycoa, 2020 to 2025

pyvoa is the third name of one continuous project, and version 0.3.0 above is
the import of the code base it had already accumulated. The lineage:

| | name | dates | repository |
|---|---|---|---|
| 1 | **CoCoA** — Covid Collaborative Analysis | 2020-04-29 to 2020-11-26 | <https://github.com/tjbtjbtjb/CoCoA> (public, archived) |
| 2 | **PyCoA** — Python Covid Analysis | 2020-11-18 to 2025-03-24 | <https://github.com/coa-project/pycoa> (private) |
| 3 | **pyvoa** — Python Virus Open Analysis | since 2025-03 | <https://github.com/pyvoa/pyvoa> |

## CoCoA, april to november 2020

Started during the Covid Hackathon of April 2020 by Tristan Beau, Julien
Browaeys and Olivier Dadoun. 266 commits, tags `v0.1` (may 2020), `v0.2` and
`v0.3` (june 2020), and a `1.0` announced in the README while the code still
called itself `pre1.0`.

- the aim was already the one pyvoa states today: simplified, unified access to
  Covid databases for people who are not data specialists — pupils, students,
  science journalists, and scientists outside the field — with raw data, time
  series and maps a few lines of code away.
- bokeh output from `v0.2`, in may 2020; worldometers support in july.
- three modules of that first design are still in pyvoa under the same names:
  `geo.py`, which arrived in july 2020 already carrying `GeoManager` and the
  standardisation of location names, and `tools.py`, renamed from `verb.py` in
  november 2020. A third, `error.py`, survived until 0.5.0 folded it into
  `tools.py`.
- in november 2020 the project was renamed and moved; the CoCoA README has
  pointed at the new home ever since.

## PyCoA, november 2020 to march 2025

The repository is private, so the history below is summarised from pycoa's own
`Release_notes.md` and from its log — the authoritative record, and not public.

1924 commits on the main line — Olivier Dadoun (about 1350), Tristan Beau
(about 470), Noam Boulze (77), Alexander Martínez Méndez and Julien Browaeys.
2021 was the busiest year, at 822 commits.

- **v1.0, november 2020** — first official release: the worldwide JHU database.
- **v2.0, february 2021** — major release. More than one database at last:
  OWID worldwide, JHU-USA, and SPF and OpenCovid19 for France. A `GeoCountry`
  class for local geography, an automatic cache, and a wide rework of the
  graphical output, the data processing and the front end.
- **v2.01 and v2.02, march 2021** — local databases for the USA
  (Covidtracking), Italy (dpc) and India (covid19india). A pandas dataframe
  became the standard output; pie charts and the date slider arrived; Windows
  and SPF fixes.
- **v2.10, october 2021** — national databases for ESP, DEU, BEL, GBR and PRT,
  the Obépine and opencovid19national French sets, map labels for the bokeh
  maps, a `rapport` class, `export` and `merger`, and `sumall` over lists of
  lists.
- **v2.11** — decorators and kwargs uniformised across the front, date plots
  over several variables and locations, `vline` and `hline` modes, the GRC and
  CYP databases, geopandas output.
- **v2.20, march 2022** — population figures for the USA and France and
  normalisation by population, yearly and spiral plots, a choice between dense
  and standard geometry for ESP, FRA and USA, the Insee, Risklayer, Europa,
  Greece and Cyprus databases, and the bokeh figure handed back to the caller.
- **v2.21, september 2022** — the `condensed` map label for USA and FRA, and
  repairs to databases that had changed shape upstream. Tagged for FdS 2022.
- **v2.22, november 2023** — the database parsing split into a `dbparser`
  class, so that one file describes a database; `setwhom(reload=True)` reading
  a pickled cache; OWID replacing JHU as the default database.

After v2.22 the work went on untagged for 311 more commits, and that stretch is
what became pyvoa:

- matplotlib and seaborn backends joined bokeh in may 2024, and the front end
  was pulled apart from the visualization classes — batch output separated from
  graphical output, `bypop` moved out of `allvisu`, `front.py` rewritten.
- an Olympics medal dataset was carried for a while as an experiment. pyvoa
  dropped it in 0.4.0, on the grounds that it is not a virus database.
- in february and march 2025 the rename happened: `src` became `pyvoa`, the
  JSON descriptions became `pyvoa-data`, `Coa` became `Pyvoa` throughout, and
  the covid-specific vocabulary was taken out of the code — the point at which
  the project stopped being about one virus. The last pycoa commit is dated
  2025-03-24, and pyvoa 0.3.0 was tagged two days later.
