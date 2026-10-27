# Unreleased
Since 0.5.0 (2026-08-06), in short:

- data sources: `measles-usa` and `ebolardc` come in, `sentinellesIRA` and
  `risklayer` go out for licence reasons (23 databases, each one's licence in
  the README); `pf.setlive(True)` reads the providers' files instead of the
  frozen Zenodo copies; five new keys in the database descriptions; Kosovo is
  left out, and France no longer includes French Guiana and French Polynesia.
- parsing: day-first dates are read right in `govcy` and `dgs`, locations
  that were lost are matched again (`rki`, `minciencia` and four more), and
  `tests/test_sources.py` checks every database against its files.
- maps and charts: matplotlib maps are drawn in Eckert IV and both backends
  use OpenStreetMap tiles; `show_values` writes the values on the map; many
  bokeh fixes, to the map proportions, the date slider, the colours and
  `savefig()`.
- behaviour changes: whole location names from `get()`, `'tot_cases smooth7'`
  with a space, the death count as default `which`, `setwhom(reload=False)`
  without parsing, and `pip install pyvoa` brings matplotlib and bokeh, making
  `pyvoa-full` unnecessary.
- packaging: Python 3.13 and 3.14, tested lower bounds for every dependency,
  `pyvoa/js/` back in the wheel, and the API documentation published online.

The details follow.

Data sources:

- new databases: `measles-usa`, the US measles cases of the JHU tracking team,
  and `ebolardc`, the 2026 Ebola outbreak in the DR Congo by health zone.
  `ebolardc` is read from its provider only, the INSP asking to be consulted
  before any republication, which a mirror would be.
- removed: `sentinellesIRA` and `risklayer`, whose data are not licensed for
  redistribution. 23 databases are shipped; the README gives each one's
  licence, set by its provider.
- live mode: `pf.setlive(True)` reads the upstream files instead of the frozen
  Zenodo copies (now record 23601685), `pf.getlive()` tells which is in use.
- new keys in the database descriptions: `names` (csv with no header line),
  `splitwhere` (composite locations), `cumulative` and `fillmissing` (sources
  reporting increments), `dateformat` (day-first dates).
- Kosovo is left out of every database, as the UN does not recognise it; `jhu`
  used to add it into Serbia. `owid` and `mpoxgh` no longer merge French
  Guiana and French Polynesia into France, which inflated France's rates.

Parsing:

- fix: dates were read month-first in the day-first `govcy` and `dgs`; `govcy`
  now takes the source's own running totals.
- fix: locations were lost on the way, and are now matched: 22 German
  Landkreise named like the city they surround (`rki`, 6 % of the cases), 140
  Chilean comunas whose codes were truncated upstream (`minciencia`), and
  naming mismatches in `covid19india`, `escovid19data`, `dgs` and `moh`.
  `tests/test_sources.py` compares every database with a direct read of its
  files.
- fix: locations a source reports but its geometry lacks (Curaçao, the US
  territories, Lakshadweep, …) keep their counts and are simply not drawn.

Maps and charts:

- matplotlib maps are drawn on an equal-area projection, Eckert IV;
  `projection='mercator'` brings Web Mercator back, `listprojection()` lists
  both. Bokeh stays in Mercator.
- maps use OpenStreetMap tiles by default, on both backends; `positron` and
  `stamen` are withdrawn, so `listtile()` gives `['openstreet', 'esri']`.
- new keywords: `pyvoalogo` (the logo is no longer stamped unasked),
  `return_pltaxis` and `maxcountrydisplayed`; `maxlettersdisplayed` defaults
  to 20. Locations missing from the parsed database are shown in pink.
- `map(typeofmap='show_values')` writes each location's value on the map,
  plainly between 0.001 and 999 (`570`, `0.0123`) and in scientific notation
  otherwise (`5.49×10⁷`), under matplotlib and bokeh alike;
  `typeofmap` takes a list to combine it, as in `['dense', 'show_values']`.
- fix: bokeh maps were squashed by their colour bar; they keep their
  proportions now, and are framed like matplotlib's, pink locations included.
- fix: `listtile()` and `listprojection()` raise a `PyvoaError` when no
  backend is set, and a backend named by `MPLBACKEND`, such as Agg, is no
  longer switched to TkAgg at the first matplotlib chart.
- fix: `savefig()` saved the previous bokeh figure instead of the last one.
- fix: a bokeh histogram or pie chart with `dateslider` opened on the wrong
  date, and mixed its bars up once the slider moved; with the slider, a pie
  chart gathers the other locations into 'SumOthers' as it does without. The
  title follows the slider, and the colour bar of a map labels its ticks
  legibly at every date.
- the date slider covers the histogram by value too, which took
  `dateslider=True` and binned every date together. A location keeps its
  colour in every histogram and pie chart, from one date to another and with
  or without the slider, and 'SumOthers' is white.
- fix: two bokeh charts with a date slider in one notebook shared a single
  Play timer, so that pausing one stopped the other.

Behaviour changes:

- `get()` returns location names whole; they are cut in chart labels only.
- a variable read with an option is named `'tot_cases smooth7'`, with a space,
  like `'tot_cases daily'`; it was `'tot_casessmooth7'`.
- the default `which` is the death count when the database has one, otherwise
  its first cumulative variable.
- `setwhom()` on the current database redoes what `reload` asks instead of
  doing nothing, and `reload=False` really reads the pickles back without
  parsing (`owid` in 0.6 s instead of 9.4 s).
- `listwhom(detailed=True)` no longer lists the variables: see `listwhich()`.
- `plot()` refuses `dateslider`, which it ignored.
- `saveoutput()` writes `pyvoa_out.*` by default, instead of `pycoa.ut.*`.
- `pf.set_verbose_mode()` and `pf.get_verbose_mode()` are front methods again.
- `pip install pyvoa` brings the matplotlib and bokeh backends with it;
  `pyvoa-full`, which only added them, is no longer needed.

Packaging and documentation:

- Python 3.13 and 3.14 are supported and tested.
- fix: on Windows, `import pyvoa.front` failed with `KeyError: 1`. The
  database descriptions, the bokeh callbacks and a scraped page were read in
  the locale's encoding, cp1252 there, instead of utf-8, and a description
  that failed to read stopped the import instead of being set aside.
- fix: a script whose output went to a file or a pipe on Windows could see a
  `UnicodeEncodeError` in place of a `PyvoaError`, when the message held a
  character cp1252 lacks (an emoji, a Greek or Japanese name). Such a
  character is now printed as `?`, and the error is the one raised.
- every dependency has a lower bound, tested by a `minimum` CI job (pandas
  2.1.1, geopandas 1.0, shapely 2.0.2, numpy 1.26); `beautifulsoup4` replaces
  `bs4`.
- fix: matplotlib maps on an OpenStreetMap basemap, the default, failed with
  "AxesImage.set() got an unexpected keyword argument 'headers'" when
  contextily was older than 1.7, as it can be in an Anaconda installation.
  contextily 1.7 is now the declared minimum.
- fix: with pycountry older than 23.12.7, the `jhu` database failed to parse,
  since those releases do not know Türkiye, the name JHU uses. pycountry
  23.12.7 is now the declared minimum.
- fix: an error page served by a busy server (a 429 or a 503 of Zenodo) was
  cached as if it were the data, and in archive mode never downloaded again.
  It is now refused, and the download fails with a `PyvoaError`.
- fix: the nine regions of England (North East, London, …) were missing from
  the United Kingdom's geography, every English district falling under
  "England": the ONS lookup of districts to regions had moved, and its error
  message was read in its place. It is read at its new address, and archived
  in the Zenodo record 23599920.
- fix: every bokeh time series (`plot()`) failed with "Cannot setitem on a
  Categorical with a new category (#FFFFFF)" since the white of 'SumOthers'
  came in, `where` being a Categorical.
- fix: a bokeh map with `typeofmap='show_values'` and the date slider failed
  with "cannot reindex on an axis with duplicate labels"; its labels give the
  last date, the one the map opens on.
- fix: `map(input=...)` of a GeoDataFrame of one's own failed with an
  `AttributeError` when no database was loaded, although its docstring
  offers it; the docstring now says the table needs a `geometry` column.
- fix: under bokeh, `savefig()` named its file for the rest of the session
  (through `output_file()`), so that in a script the next chart shown was
  written over the one saved.
- fix: `plot(typeofplot='compare')` of a table of one's own (`input=`)
  failed with "'AllVisu' object has no attribute 'granularity'": it read the
  granularity of a database, for a fallback no granularity ever triggered.
- the axes of the bokeh `compare` and `versus` plots are written in the ×10
  notation of the other time series (4×10²), no longer as 4.00e+2.
- fix: `where` was ignored for a table of one's own (`input=`): every
  location came back, and `option='sumall'` added them all up. The table is
  now cut to the locations asked for, compared regardless of case, and a
  name it lacks raises a `PyvoaError` that lists those it has.
- pandas' `mode.chained_assignment` option is set under pandas 2 only:
  pandas 3.1 warns at each use (Pandas4Warning), and pandas 4 removes it,
  which would make `import pyvoa` fail.
- fix: `option='sumall'` repaired the geometry of every row of the database
  before joining those of the last date: `minciencia` ran out of memory
  (over 8 GB) and `owid` took about two minutes. Only the last date is
  repaired now: 1.1 GB and 30 s for `minciencia`, under a second for `owid`.
- fix: `option='normalize:pop…'` left 518 of the 519 health zones of
  `ebolardc` empty: the parser upper-cases the codes, the INRB geography
  keeps them mixed-case. They are now compared regardless of case. The
  locations asked for that have no population are named in a warning,
  rather than left silently empty, and a database whose geography has no
  population at all (`dpc`, `rki`, …) says so in plain words.
- fix: `hist(typeofhist='value')` under matplotlib failed when every
  location had the same value (one location under `sumall`, or only
  zeros); it draws two bins from 0 to that value, as bokeh does. A pie
  chart of negative values, or of values all zero, raises a `PyvoaError`
  saying so on both backends: matplotlib failed, bokeh drew a wrong pie.
- the District of Columbia has a population (2020 census, 689,545) in the
  geography of the United States, so that `normalize` covers it.
- France in `owid`, `europa` and `mpoxgh` now counts its overseas
  territories (Guadeloupe, Martinique, French Guiana, Réunion, Mayotte,
  French Polynesia), and the United Kingdom Jersey and Guernsey, as `jhu`
  already did: a new `merge` key of the database description folds them in.
  Each part's running totals are carried over the days it does not report
  before they are summed, rates per inhabitant (`intensive` columns) are
  averaged weighted by population, and `normalize` divides by the population
  of the whole. Jersey and Guernsey get a population (2021 censuses).
- removed: the seaborn backend, which `listvis()` no longer offered;
  matplotlib and bokeh draw every chart.
- fix: `option='sumall'` counts a location with no value on a date with its
  last one, so that a histogram of the sum no longer drops it.
- the Zenodo archives of `mpoxgh` and `dpc` are refreshed from their live
  sources: mpox data now run to 2026-04-30 (from 2023-10-19), Italian data
  to 2025-01-08 (from 2023-10-25).
- every chart, of each backend, is drawn and written to a file by the
  offline test suite, its tiles alone stubbed out, so that a new release of
  matplotlib, bokeh, contextily or pandas that breaks one fails in CI.
- fix: live mode read the geographic references upstream as well, where
  several have moved or changed shape: on an empty cache, every world
  database failed to load (the UN M49 table of Wikipedia no longer parses),
  and so did the geographies of Chile, India and Malaysia. Live mode now
  applies to the data files of the databases alone; the geography is read
  from the archive in both modes.
- fix: the wheel of 0.5.0 left out `pyvoa/js/`, so that a bokeh chart raised
  `FileNotFoundError` on an installed copy; the callbacks are shipped again.
- the API documentation is published at <https://pyvoa.github.io/pyvoa/>,
  the bokeh callbacks of `pyvoa/js/` included.
- the bokeh callbacks of `pyvoa/js/` are run in node by the test suite, and
  checked against the Python they mirror; the `dev` extra brings node with
  `nodejs-wheel-binaries`, and bokeh, so that CI runs the bokeh tests too.
- `GeoCountry` converts region and subregion codes to names and back.
- a welcome banner is printed when `pyvoa.front` is imported.
- a new example reads the Insee death records into a DataFrame and plots them
  through `input=`: `PyvoaFront-withINSEE.ipynb` and
  `examples/pyfiles/insee_deaths.py`.

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

# Before pyvoa — CoCoA and pycoa, 2020 to 2023

pyvoa is the third name of one continuous project, and version 0.3.0 above is
the import of the code base it had already accumulated. The lineage:

| | name | dates | repository |
|---|---|---|---|
| 1 | **CoCoA** — Covid Collaborative Analysis | 2020-04-29 to 2020-11-26 | <https://github.com/tjbtjbtjb/CoCoA> (public, archived) |
| 2 | **PyCoA** — Python Covid Analysis | 2020-11-18 to 2023 | <https://github.com/coa-project/pycoa> (private), until 2025-03-24 |
| 3 | **pyvoa** — Python Virus Open Analysis | since 2023 | a branch of the pycoa repository, then <https://github.com/pyvoa/pyvoa> from 2025-03 |

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

## PyCoA, november 2020 to 2023, and pyvoa in its repository until march 2025

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

After v2.22 the work went on untagged for 311 more commits. In 2023 the project
was renamed pyvoa, and developed in a branch of the pycoa repository:

- matplotlib and seaborn backends joined bokeh in may 2024, and the front end
  was pulled apart from the visualization classes — batch output separated from
  graphical output, `bypop` moved out of `allvisu`, `front.py` rewritten.
- an Olympics medal dataset was carried for a while as an experiment. pyvoa
  dropped it in 0.4.0, on the grounds that it is not a virus database.
- in february and march 2025 pyvoa left the pycoa repository for a repository
  of its own, and the code took the name: `src` became `pyvoa`, the JSON
  descriptions became `pyvoa-data`, `Coa` became `Pyvoa` throughout, and the
  covid-specific vocabulary was taken out of the code. The last pycoa commit is
  dated 2025-03-24, and pyvoa 0.3.0 was tagged two days later.
