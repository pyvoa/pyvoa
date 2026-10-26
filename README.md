# pyvoa

[![CI](https://github.com/pyvoa/pyvoa/actions/workflows/ci.yml/badge.svg?event=push)](https://github.com/pyvoa/pyvoa/actions/workflows/ci.yml)
[![Docs](https://github.com/pyvoa/pyvoa/actions/workflows/docs.yml/badge.svg)](https://pyvoa.github.io/pyvoa/)
[![PyPI](https://img.shields.io/pypi/v/pyvoa)](https://pypi.org/project/pyvoa/)
[![Python](https://img.shields.io/pypi/pyversions/pyvoa)](https://pypi.org/project/pyvoa/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)](https://github.com/pyvoa/pyvoa/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21829901.svg)](https://doi.org/10.5281/zenodo.21829901)
[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/pyvoa/pyvoa/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/pyvoa/pyvoa)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)


[pyvoa](https://pyvoa.org) (Python Virus Open Analysis) is a Python™ package that provides:

- easy access to COVID-19 and other viral disease datasets;
- tools for analysing and visualising these data through time series, charts and maps.

It is designed to be accessible to non-specialists, including high-school students learning Python, university students, science journalists and researchers unfamiliar with data extraction. Users can perform simple analyses with a few commands or build more advanced workflows in Python.

pyvoa retrieves data from multiple providers and returns them in a standardised format. Its geolocation layer reconciles country and region names, supports joins between datasets using different geographical labels, and provides geographical information for mapping. This layer can also be used independently for applications beyond viral data analysis.

## Installation

pyvoa requires Python ≥ 3.10 and is published on PyPI:

```bash
pip install pyvoa
```

A single package provides both data as pandas or GeoPandas objects and visualisations as charts and maps,
with Matplotlib and Bokeh backends installed as dependencies.

To work from a clone instead, see [CONTRIBUTING.md §3](CONTRIBUTING.md#3-development-setup).

## A first example

```python
import pyvoa.front as pf

pf.setwhom('owid')          # select a database — Our World in Data, worldwide, country-level data
pf.listwhich()              # list the available variables

# retrieve the data as a pandas DataFrame: one row per date and place
df = pf.get(where=['France', 'Italy', 'Spain'],
            which='total_deaths',
            what='daily',
            output='pandas')

# plot the same selection
pf.setvis('matplotlib')     # or 'bokeh'
pf.plot(where=['France', 'Italy', 'Spain'], which='total_deaths', what='daily')

# map total deaths across all places covered by the database
pf.map(which='total_deaths')  
```

- `where` accepts a place name or a list of place names. Names are matched
  through the geolocation layer, regardless of case or accents
  (`'france'` matches `France`).

- `pf.listwhere()` lists the places covered by the selected database:
  countries for `owid`, French *départements* for `spf`, and so on.
  Requesting a place that is not covered raises a `PyvoaError` identifying
  that place.

- `what` specifies how the series is processed: `current` returns the
  original cumulative or instantaneous values, while `daily` and `weekly`
  return daily and weekly changes, respectively.

- `output` selects the return type: `pandas`, `geopandas`, `list`, `dict`
  or `array`.

Downloads are cached in `~/.cache/pyvoa.data_<username>/`, making subsequent
runs faster. Calling `pf.setwhom('owid', reload=False)` reuses the local copy
saved by a previous call without downloading the data again.


### Archived data, live data


By default, pyvoa uses archive mode, retrieving data from the project’s Zenodo mirrors wherever available. These archived snapshots preserve reproducibility even when the original providers change or their files become unavailable. Databases available only from live online sources are an exception: archive mode automatically falls back to the provider.

To retrieve data from live online sources instead of the Zenodo mirrors:

```python
pf.setlive(True)            # use live online sources
pf.setwhom('owid')          # load the database in live mode
pf.getlive()                # True
pf.setlive(False)           # return to archive mode
```

The live online URL for each dataset is stored in the `urlparent` field of its JSON descriptor, alongside the `urldata` field used in archive mode. Switching modes clears the selected database, so call `setwhom()` again afterwards to load data from the newly selected source. Live and archived copies are cached separately and never overwrite each other. In live mode, cached files are downloaded again once they are more than a few hours old; archived files are downloaded once and retained.

Live online sources provide the latest available data, but their availability and format are less predictable: a provider’s file may have moved, changed format or disappeared since your pyvoa release, and results may vary from day to day.

Some databases, such as `ebolardc`, are available only from live online sources. Others are available only through the Zenodo archive because their original URLs are no longer accessible.

### Exploring the API

The following introspection functions provide a quick way to explore the API. Each returns a standard Python list.

```python
pf.listwhom()      # available databases
pf.listwhich()     # variables available in the selected database
pf.listwhat()      # ['current', 'daily', 'weekly']
pf.listwhere()     # places covered by the selected database
pf.listoption()    # processing options, e.g. 'sumall', 'nonneg', 'smooth7', 'normalize:pop100'
pf.listvis()       # ['bokeh', 'matplotlib']
pf.listoutput()    # ['geopandas', 'pandas', 'list', 'dict', 'array']
```


## Supported databases

pyvoa includes 23 databases. `pf.listwhom()` returns the keys listed below, and `pf.setwhom(key)` selects a database. Each is described by a JSON file in [`pyvoa/data/`](pyvoa/data/). Adding a source usually requires only a new JSON descriptor, with no Python code to write (see [CONTRIBUTING.md §6](CONTRIBUTING.md#6-adding-a-new-database)).

By default, data are retrieved from Zenodo mirrors where available, preserving reproducibility even after the original files become unavailable. The *Availability* column indicates where each database can be accessed:

- **both**: available from a Zenodo mirror and a live online source. Nineteen databases fall into this category, although an accessible source is not necessarily still updated.
- **both (live recommended)**: `measles-usa`, included among those nineteen, tracks an ongoing epidemic. Its mirror preserves a snapshot, while the live online source provides more recent data.
- **archive only**: the original sources are no longer accessible for three databases. `phe` lost its API host, while files used by `minciencia` and `moh` were renamed or withdrawn.
- **live only**: `ebolardc` has no Zenodo mirror, so archive mode automatically falls back to the live online source. The database transcribes situation reports from the Institut National de Santé Publique, whose permission is required before republication.

Only the archived data provide reproducible results across retrieval dates; see [Archived data, live data](#archived-data-live-data).

The *Licence* column refers to the data licence specified by the provider and retained with the Zenodo mirror, where one exists. These terms govern reuse of the data and are separate from pyvoa’s MIT licence. For example, the licence for `imed` prohibits commercial use.


| Key | Coverage | Granularity | Source | Licence | Availability |
|---|---|---|---|---|---|
| `covid19india` | India | region | covid19india.org | CC BY 4.0 | both |
| `covidtracking` | United States | subregion (states) | The COVID Tracking Project | CC BY 4.0 | both |
| `dgs` | Portugal | region | Direção-Geral da Saúde | GPL-3.0 (DSSG compilation; DGS data without a published licence) | both |
| `dpc` | Italy | region | Dipartimento della Protezione Civile | CC BY 4.0 | both |
| `ebolardc` | Democratic Republic of the Congo | subregion (health zones) | Institut National de Santé Publique, via INRB/UMIE | INSP terms: attribution and permission required before republication | live only |
| `escovid19data` | Spain | subregion (provinces) | escovid19data | CC BY 4.0 | both |
| `europa` | worldwide | country | European Commission, Joint Research Centre | CC BY 4.0 | both |
| `govcy` | Cyprus | country | Government of Cyprus | CC BY 4.0 | both |
| `imed` | Greece | subregion | iMEDD | CC BY-NC 4.0 | both |
| `jhu` | worldwide | country | Johns Hopkins University CSSE | CC BY 4.0 | both |
| `jhu-usa` | United States | subregion (states) | Johns Hopkins University CSSE | CC BY 4.0 | both |
| `jpnmhlw` | Japan | subregion (prefectures) | Ministry of Health, Labour and Welfare | CC BY 4.0 (via Public Data License 1.0) | both |
| `measles-usa` | United States | subregion (states) | Johns Hopkins University Measles Tracking Team | CC BY 4.0 | both (live recommended) |
| `minciencia` | Chile | subregion | Ministerio de Ciencia, Tecnología, Conocimiento e Innovación | CC0 1.0 | archive only |
| `moh` | Malaysia | subregion (states) | Ministry of Health | Open Data 1.0 Government of Malaysia | archive only |
| `mpoxgh` | worldwide | country | Global.health, via Our World in Data | CC BY 4.0 | both |
| `owid` | worldwide | country | Our World in Data | CC BY 4.0 | both |
| `phe` | United Kingdom | subregion | Public Health England / UKHSA | OGL v3.0 | archive only |
| `rki` | Germany | subregion (*Kreise*) | Robert Koch Institut | dl-de/by-2-0 | both |
| `sciensano` | Belgium | region | Sciensano | CC0 1.0 | both |
| `spf` | France | subregion (*départements*) | Santé publique France | Licence Ouverte / Etalab 2.0 | both |
| `spfnational` | France | country | Santé publique France | Licence Ouverte / Etalab 2.0 | both |
| `sumeau` | France | country | SUM'EAU — SARS-CoV-2 in wastewater | Licence Ouverte / Etalab 2.0 | both |

Most of these databases contain COVID-19 series. The exceptions are `mpoxgh`, which covers mpox; `ebolardc`, which covers the 2026 Bundibugyo ebolavirus outbreak in the Democratic Republic of the Congo; and `measles-usa`, which tracks measles cases in the United States. Several providers have stopped updating their COVID-19 datasets, so the latest available date varies by database. `pf.setwhom()` displays this date when a database is selected.


## Documentation and examples

- [`examples/notebooks/`](examples/notebooks/) — Jupyter notebooks:
  `PyvoaForBeginners.ipynb` introduces the main features;
  `GeoByExamples.ipynb` explores the geolocation layer independently;
  and `PyvoaFront-withINSEE.ipynb` shows how to use pyvoa’s visualisation
  tools with an external dataset.
- [`examples/pyfiles/`](examples/pyfiles/) — Python scripts:
  `insee_deaths.py`, the script equivalent of `PyvoaFront-withINSEE.ipynb`,
  passes pyvoa a DataFrame built from INSEE death records;
  `paper_example` reproduces the examples presented in a forthcoming
  software paper.
- [pyvoa.org](https://pyvoa.org) — the project website.
- `pf.whattodo()` — a quick reference within a Python session. It returns
  a DataFrame listing all keywords accepted by `get`, `plot`, `hist`
  and `map`, along with their allowed values.

pyvoa works in Jupyter notebooks, whether run locally or on hosted services
such as Google Colab or Binder. It can also be used directly from a Python
script or an interactive console.

## API reference

The API reference is generated from the docstrings and is available at
[pyvoa.github.io/pyvoa](https://pyvoa.github.io/pyvoa/).

To build it locally, run:

```bash
pip install -r docs/requirements.txt
make -C docs html
```

Then open `docs/_build/html/index.html` in your browser.


## Community and support

- **Questions about using pyvoa** — ask in [GitHub Discussions](https://github.com/pyvoa/pyvoa/discussions). Beginner questions are welcome: pyvoa is designed to be accessible to people new to data analysis.
- **Bug reports and requests for new data sources** — [open an issue](https://github.com/pyvoa/pyvoa/issues/new/choose). Before reporting a problem, see [SUPPORT.md](SUPPORT.md) for support channels and two preliminary checks. Many problems arise from changes to the original data sources.
- **Contributing** — see [CONTRIBUTING.md](CONTRIBUTING.md), including the checklist for [adding a new database](CONTRIBUTING.md#6-adding-a-new-database).
- **Community guidelines** — all participants are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).
- **Security or privacy concerns** — contact [contact@pyvoa.org](mailto:contact@pyvoa.org) privately rather than opening a public issue.




## Citation

If you use pyvoa in your work, please cite it. Citation metadata is provided in
[CITATION.cff](CITATION.cff). On GitHub, select *Cite this repository* to
generate a formatted citation.

See [AUTHORS](AUTHORS) for authorship details and
[CONTRIBUTORS.md](CONTRIBUTORS.md) for acknowledgements of other contributions.


## Funding

This work was supported by the IdEx “Université Paris Cité 2022”, funded by
the French State through the “Investissements d’avenir” programme
(grant ANR-18-IDEX-0001), and by the
[Institut Covid-19 Ad Memoriam](https://institut-ad-memoriam.u-pariscite.fr/)
at Université Paris Cité.

The pyvoa team is required to acknowledge both funding sources in its publications, presentations and other project materials; see the *Funding* section of [AUTHORS](AUTHORS). Users of pyvoa are not required to acknowledge these funding sources in their own work.


## Licence

pyvoa’s code is released under the [MIT licence](LICENSE). The data remain
subject to their providers’ respective licences, listed in the
[supported databases](#supported-databases) table.
