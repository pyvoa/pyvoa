# pyvoa

[![CI](https://github.com/pyvoa/pyvoa/actions/workflows/ci.yml/badge.svg)](https://github.com/pyvoa/pyvoa/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pyvoa)](https://pypi.org/project/pyvoa/)
[![Python](https://img.shields.io/pypi/pyversions/pyvoa)](https://pypi.org/project/pyvoa/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21829901.svg)](https://doi.org/10.5281/zenodo.21829901)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

[Pyvoa](https://pyvoa.org) (Python Virus Open Analysis) is a collection of Python™ code that provides:

 - easy access to COVID-19 databases, as well as other viral datasets;
 - tools to visualize and analyze data, such as time series and maps.

This environment is designed to be accessible to non-specialists: high-school students learning Python™, university students, science journalists, and even researchers who are not familiar with data extraction. Simple analyses can be performed directly, while more advanced analyses can be carried out by users experienced in Python™ programming.

Pyvoa provides access to multiple databases and delivers data in a standardized format. It also ensures seamless integration with geolocation databases (handling country or region names, enabling joins across datasets with differing descriptions, and generating maps). This geolocation information can furthermore be reused for applications beyond viral data analysis.

## Installation

pyvoa requires Python ≥ 3.10 and is published on PyPI:

```bash
pip install pyvoa          # the library: data access, standardisation, geolocation
pip install pyvoa-full     # the same, plus the matplotlib and bokeh plotting backends
```

Install `pyvoa-full` if you want charts and maps: `pyvoa` on its own gives you
the data as pandas or geopandas objects, and the plotting backends are optional
imports that pyvoa detects at runtime.

To work from a clone instead, see [CONTRIBUTING.md §3](CONTRIBUTING.md#3-development-setup).

## A first example

```python
import pyvoa.front as pf

pf.setwhom('owid')          # select a database — Our World in Data, worldwide, by country
pf.listwhich()              # which variables does it expose?

# the data, as a pandas DataFrame: one row per date and per place
df = pf.get(where=['France', 'Italy', 'Spain'],
            which='total_deaths',
            what='daily',
            output='pandas')

# the same selection, as a chart (needs pyvoa-full)
pf.setvis('matplotlib')     # or 'bokeh'
pf.plot(where=['France', 'Italy', 'Spain'], which='total_deaths', what='daily')
pf.map(which='total_deaths')   # every place the database covers, on a map
```

`where` takes a place name or a list of them, matched through the geolocation
layer, so case and accents do not matter (`'france'` finds `France`).
`pf.listwhere()` gives the places the selected database actually carries —
countries for `owid`, *départements* for `spf`, and so on; asking for one it
does not have raises a `PyvoaError` naming it.

`what` is the pre-treatment applied to the series — `current` (the raw
cumulative or instantaneous value), `daily` or `weekly`. `output` selects the
return type: `pandas`, `geopandas`, `list`, `dict` or `array`.

Downloads are cached under `~/.cache/pyvoa.data_<username>/`, so the second run
of a script is fast; `pf.setwhom('owid', reload=False)` goes further and reuses
the local copy saved by a previous call rather than fetching anything.

### Archived data, live data

By default pyvoa reads every payload from the project's Zenodo mirrors. A given
release therefore always returns the same numbers, whatever has become of the
provider since — which is the point, most of these series being a historical
record whose original URLs have moved or gone.

For a source still publishing, that is not always what you want:

```python
pf.setlive(True)            # read the upstream sources instead
pf.setwhom('ebolardc')      # ... and fetch today's file
pf.getlive()                # True
pf.setlive(False)           # back to the archive
```

The live URL of each dataset is the `urlparent` field of its JSON descriptor,
next to the `urldata` mirror the archive mode uses. Switching mode clears the
selected database, so call `setwhom()` again afterwards — the frame in memory
came from the other source. The two copies are cached under different names and
never overwrite each other; in live mode a cached file is re-downloaded once it
is more than a few hours old, whereas an archived one is fetched once and kept.

Live data are the most recent ones, and the least dependable: an upstream file
may have moved, changed format or disappeared since the release you are running,
and results change from one day to the next. A database whose archive does not
carry a given file — one added after the last deposit — is fetched from its
provider in either mode.

The introspection functions are the fastest way to explore the API — every one
of them returns a plain Python list:

```python
pf.listwhom()      # the databases
pf.listwhich()     # the variables of the selected database
pf.listwhat()      # ['current', 'daily', 'weekly']
pf.listwhere()     # the places the selected database covers
pf.listoption()    # e.g. 'sumall', 'nonneg', 'smooth7', 'normalize:pop100'
pf.listvis()       # ['bokeh', 'matplotlib']
pf.listoutput()    # ['geopandas', 'pandas', 'list', 'dict', 'array']
```

## Supported databases

25 databases are shipped with pyvoa; `pf.listwhom()` returns the keys below, and
`pf.setwhom(key)` selects one. Each is described by a JSON file in
[`pyvoa/data/`](pyvoa/data/) — adding a source usually means adding one such
file and no Python at all (see [CONTRIBUTING.md §6](CONTRIBUTING.md#6-adding-a-new-database)).
The payloads are read from Zenodo mirrors of the upstream files, so a series
stays reproducible after its original provider stops publishing. *Read from*
says where each one is available: **both** for the twenty databases carrying a
mirror and an upstream file that still resolves — which does not mean the
provider still updates it — **archive only** for the three whose provider has
gone (`phe` lost its API host, `minciencia` and `moh` renamed or withdrew
files), and **live only** for the two added since the last deposit, which are
always fetched from their provider. Only the archived ones are
reproducible; see [Archived data, live data](#archived-data-live-data).

| Key | Coverage | Granularity | Source | Read from |
|---|---|---|---|---|
| `covid19india` | India | region | covid19india.org | both |
| `covidtracking` | United States | subregion (states) | The COVID Tracking Project | both |
| `dgs` | Portugal | region | Direção-Geral da Saúde | both |
| `dpc` | Italy | region | Dipartimento della Protezione Civile | both |
| `ebolardc` | Democratic Republic of the Congo | subregion (health zones) | Institut National de Santé Publique, via INRB/UMIE | live only |
| `escovid19data` | Spain | subregion (provinces) | escovid19data | both |
| `europa` | worldwide | country | European Commission, Joint Research Centre | both |
| `govcy` | Cyprus | country | Government of Cyprus | both |
| `imed` | Greece | subregion | iMEDD | both |
| `jhu` | worldwide | country | Johns Hopkins University CSSE | both |
| `jhu-usa` | United States | subregion (states) | Johns Hopkins University CSSE | both |
| `jpnmhlw` | Japan | subregion (prefectures) | Ministry of Health, Labour and Welfare | both |
| `measles-usa` | United States | subregion (states) | Johns Hopkins University Measles Tracking Team | live only |
| `minciencia` | Chile | subregion | Ministerio de Ciencia, Tecnología, Conocimiento e Innovación | archive only |
| `moh` | Malaysia | subregion (states) | Ministry of Health | archive only |
| `mpoxgh` | worldwide | country | Global.health, via Our World in Data | both |
| `owid` | worldwide | country | Our World in Data | both |
| `phe` | United Kingdom | subregion | Public Health England / UKHSA | archive only |
| `risklayer` | Europe | subregion | Risklayer, for WHO Europe | both |
| `rki` | Germany | subregion (*Kreise*) | Robert Koch Institut | both |
| `sciensano` | Belgium | region | Sciensano | both |
| `sentinellesIRA` | France | region | Réseau Sentinelles — acute respiratory infections | both |
| `spf` | France | subregion (*départements*) | Santé publique France | both |
| `spfnational` | France | country | Santé publique France | both |
| `sumeau` | France | country | SUM'EAU — SARS-CoV-2 in wastewater | both |

Most of these are COVID-19 series; `mpoxgh` covers mpox, `sentinellesIRA`
acute respiratory infections, `ebolardc` the 2026 Bundibugyo ebolavirus
outbreak in the Democratic Republic of the Congo and `measles-usa` the U.S.
measles cases. Upstream providers stopped updating several of
these datasets after the pandemic, so the last available date varies from one
database to the next — `setwhom()` prints it.

## Documentation and examples

- [`examples/notebooks/`](examples/notebooks/) — Jupyter notebooks, starting
  with `PyvoaForBeginners.ipynb`; `GeoByExamples.ipynb` covers the geolocation
  layer on its own.
- [`examples/pyfiles/`](examples/pyfiles/) — `owid.py` and `using_geo.py`, the
  same workflows as plain scripts.
- <https://pyvoa.org> — project website.
- `pf.whattodo()` returns a DataFrame listing every keyword accepted by `get`,
  `plot`, `hist` and `map`, with its allowed values — the quickest reference
  from inside a session.

pyvoa is designed to run comfortably in a notebook, locally or on a hosted
service such as Google Colab or Binder, but nothing requires Jupyter: it works
just as well from a script or a console.

## Community and support

- **Questions about using pyvoa** — [GitHub Discussions](https://github.com/pyvoa/pyvoa/discussions). Beginner questions are welcome: pyvoa is meant for people who are new to data analysis.
- **Bugs and new data sources** — [open an issue](https://github.com/pyvoa/pyvoa/issues/new/choose). [SUPPORT.md](SUPPORT.md) lists the support channels and two checks worth running first, since many problems originate upstream rather than in pyvoa.
- **Contributing** — [CONTRIBUTING.md](CONTRIBUTING.md), including the checklist for [adding a new database](CONTRIBUTING.md#6-adding-a-new-database).
- **Conduct** — participation is covered by our [Code of Conduct](CODE_OF_CONDUCT.md).
- **Security or privacy concerns** — <contact@pyvoa.org>, rather than a public issue.

## Citation

If you use pyvoa in your work, please cite it. The metadata lives in
[CITATION.cff](CITATION.cff), which GitHub renders as a ready-made citation via
the *Cite this repository* button. Authorship is documented in
[AUTHORS](AUTHORS), and other contributions in [CONTRIBUTORS.md](CONTRIBUTORS.md).

## Funding

This work was supported by the IdEx « Université Paris Cité 2022 »
(ANR-18-IDEX-0001) and by the
[« Institut Covid-19 Ad Memoriam »](https://institut-ad-memoriam.u-pariscite.fr/)
of Université Paris Cité.

Both must be acknowledged in any publication, presentation or derived material
about pyvoa; see the *Funding* section of [AUTHORS](AUTHORS).

## Licence

[MIT](LICENSE).
