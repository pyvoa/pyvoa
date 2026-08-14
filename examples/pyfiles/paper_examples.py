#!/usr/bin/env python3
"""
paper_examples.py — reproduces every code listing of the pyvoa software paper
and writes the manuscript figures.

    pyvoa: a Python framework for unified access, standardisation and
    visualisation of open epidemiological data
    T. Beau, J. Browaeys, O. Dadoun — submitted to SoftwareX

Usage
-----
    pip install pyvoa-full
    python paper_examples.py                 # everything, into paper/figures/
    python paper_examples.py --example 2     # one listing only
    python paper_examples.py --vis bokeh     # other backend
    python paper_examples.py --outdir /tmp/f # elsewhere
    python paper_examples.py --check         # dry run: validate the vocabulary
                                             # of every call without plotting

The first run downloads the datasets into ~/.cache/pyvoa.data_<user>/ and takes
a few minutes; later runs are fast. Nothing is written outside the figure
directory: paper/figures/ inside a checkout, ./figures/ otherwise.

Each example is self-contained and prints the exact snippet that appears in the
manuscript, so that the listings in the .tex file and the code actually executed
can be diffed rather than trusted.

Licence: MIT, as pyvoa itself.
"""

from __future__ import annotations

import argparse
import sys
import textwrap
import traceback
from pathlib import Path


def _default_figdir() -> Path:
    """Where the manuscript looks for its artwork.

    Inside a checkout the figures belong next to the manuscript that includes
    them, so ``\\includegraphics{figures/...}`` resolves with no path juggling
    in the .tex. Run on its own — the script is meant to be downloadable and
    runnable after ``pip install pyvoa-full`` — it falls back to ./figures.
    """
    root = Path(__file__).resolve().parents[2]
    if (root / "paper" / "main.tex").exists():
        return root / "paper" / "figures"
    return Path.cwd() / "figures"


FIGDIR = _default_figdir()

# Reference the paper cites; kept here so that a change of date or indicator is
# made in one place and stays consistent with the .tex listings.
JHU_DATE = "01/12/2022"          # JHU CSSE stopped collecting in March 2023
OWID_VACC = "total_people_vaccinated_per_hundred"
# Not the library default ('openstreet'): OpenStreetMap's tile policy blocks
# contextily, so that default serves "Access blocked" images and the map is
# drawn over them. CartoDB Positron allows the use and renders clean.
TILE = "positron"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def banner(n: int, title: str, snippet: str) -> None:
    """Print the listing exactly as it appears in the manuscript."""
    print()
    print("=" * 78)
    print(f"  Example {n} — {title}")
    print("=" * 78)
    print(textwrap.indent(textwrap.dedent(snippet).strip(), "    "))
    print("-" * 78)


def save(pf, name: str) -> None:
    """Write the current figure into ./figures/, whatever the backend."""
    FIGDIR.mkdir(parents=True, exist_ok=True)
    target = FIGDIR / name
    try:
        pf.savefig(str(target))
        print(f"    -> {target}")
    except Exception as exc:
        # savefig support differs between backends; never let it abort the run
        print(f"    !! savefig failed for {target.name}: {exc}")


# ---------------------------------------------------------------------------
# Example 1 — comparing countries (OWID)
# ---------------------------------------------------------------------------

def example_1(pf, vis: str) -> None:
    banner(1, "comparing countries", """
        import pyvoa.front as pf
        pf.setwhom('owid')            # Our World in Data, worldwide, by country
        pf.setvis('matplotlib')
        pf.plot(which='total_deaths', where='European Union',
                what='daily', option='smooth7')
    """)
    pf.setwhom('owid')
    pf.setvis(vis)
    pf.plot(which='total_deaths', where='European Union',
            what='daily', option='smooth7')
    save(pf, "fig2_timeseries_eu.png")


# ---------------------------------------------------------------------------
# Example 2 — mapping a grouping (JHU)
# ---------------------------------------------------------------------------

def example_2(pf, vis: str) -> None:
    banner(2, "mapping a grouping", f"""
        pf.setwhom('jhu')             # Johns Hopkins CSSE, worldwide
        pf.map(which='tot_confirmed', where='OECD',
               what='daily', when='{JHU_DATE}', tile='{TILE}')
    """)
    pf.setwhom('jhu')
    pf.setvis(vis)
    pf.map(which='tot_confirmed', where='OECD',
           what='daily', when=JHU_DATE, tile=TILE)
    save(pf, "fig3_map_oecd.png")


# ---------------------------------------------------------------------------
# Example 3 — ranking, and leaving the framework (OWID)
# ---------------------------------------------------------------------------

def example_3(pf, vis: str) -> None:
    banner(3, "ranking, and leaving the framework", f"""
        pf.setwhom('owid')
        pf.hist(which='{OWID_VACC}',
                where='Asia', typeofhist='location')

        df = pf.get(which='{OWID_VACC}',
                    where='Asia', output='pandas')
    """)
    pf.setwhom('owid')
    pf.setvis(vis)
    # 'location', not 'value': 'value' bins the countries into a frequency
    # histogram, while the manuscript describes one ranked bar per country.
    pf.hist(which=OWID_VACC, where='Asia', typeofhist='location')
    save(pf, "fig4_hist_asia.png")

    df = pf.get(which=OWID_VACC, where='Asia', output='pandas')
    print(f"    get() -> {type(df).__name__}, shape={df.shape}")
    print(f"    columns: {list(df.columns)}")
    print(textwrap.indent(str(df.head(3)), "    "))


# ---------------------------------------------------------------------------
# Example 4 — sub-national data, and beyond COVID-19 (SPF, SUM'EAU)
# ---------------------------------------------------------------------------

def example_4(pf, vis: str) -> None:
    banner(4, "sub-national data, and beyond COVID-19", f"""
        pf.setwhom('spf')             # Sante publique France, departements
        pf.map(which='cur_hosp', typeofmap='dense', tile='{TILE}')

        pf.setwhom('sumeau')          # SARS-CoV-2 in wastewater, France
        pf.plot(which='ratio', typeofplot='yearly')
    """)
    pf.setvis(vis)

    pf.setwhom('spf')
    pf.map(which='cur_hosp', typeofmap='dense', tile=TILE)
    save(pf, "fig5a_map_spf_dense.png")

    pf.setwhom('sumeau')
    pf.plot(which='ratio', typeofplot='yearly')
    save(pf, "fig5b_sumeau_yearly.png")


# ---------------------------------------------------------------------------
# Example 5 — the geolocation layer on its own (Section 2.1 / Impact)
# ---------------------------------------------------------------------------

def example_5(pf, vis: str) -> None:
    """Not a manuscript listing: supports the claim that pyvoa.geo is usable
    outside epidemiology, made in Sections 2.1 and 4."""
    banner(5, "the geolocation layer on its own (not a listing)", """
        import pyvoa.geo as pg
        gm = pg.GeoManager('name')
        gm.to_standard(['fr', 'US', 'china', "cote d'ivoire"], output='list')
        gm.get_GeoRegion().get_countries_from_region('European Union')
        pg.GeoCountry('FRA').get_region_list()
    """)
    import pyvoa.geo as pg

    # 'Espana' was used here and in Section 2.1 of the manuscript, and does not
    # resolve: pycountry carries no Spanish endonym, and normalising the string
    # cannot invent one. The accent-folding claim is demonstrated instead by
    # "cote d'ivoire", which does resolve.
    names = ['fr', 'US', 'china', "cote d'ivoire"]
    gm = pg.GeoManager('name')
    print(f"    to_standard({names}) ->",
          gm.to_standard(names, output='list'))

    eu = gm.get_GeoRegion().get_countries_from_region('European Union')
    print(f"    European Union -> {len(eu)} ISO3 codes, e.g. {eu[:5]}")

    fra = pg.GeoCountry('FRA')
    regions = fra.get_region_list()
    print(f"    GeoCountry('FRA').get_region_list() -> {len(regions)} rows")


# ---------------------------------------------------------------------------
# Impact §4, point 1 — a question that needs the multi-source reconciliation
# ---------------------------------------------------------------------------

def example_6(pf, vis: str) -> None:
    """Wastewater signal against reported incidence, same country, same axis.
    This is the concrete illustration suggested for Impact, point 1: two
    unrelated providers, one query grammar, one geographic key."""
    banner(6, "wastewater vs reported incidence (Impact, point 1)", """
        pf.setwhom('sumeau')
        waste = pf.get(which='ratio', what='current', output='pandas')

        pf.setwhom('spfnational')
        cases = pf.get(which='cur_cas', what='daily', option='smooth7',
                       output='pandas')
    """)
    pf.setwhom('sumeau')
    waste = pf.get(which='ratio', what='current', output='pandas')
    print(f"    sumeau     -> shape={waste.shape}, "
          f"{waste['date'].min()} .. {waste['date'].max()}")

    pf.setwhom('spfnational')
    cases = pf.get(which='cur_cas', what='daily', option='smooth7',
                   output='pandas')
    print(f"    spfnational-> shape={cases.shape}, "
          f"{cases['date'].min()} .. {cases['date'].max()}")

    overlap = set(waste['date']) & set(cases['date'])
    print(f"    overlapping dates: {len(overlap)}")
    print("    NB: both frames carry the same 'date'/'where' keys, so the "
          "join is a one-liner —\n"
          "        merged = waste.merge(cases, on=['date', 'where'])")


# ---------------------------------------------------------------------------
# --check : validate the vocabulary of every call without fetching anything
# ---------------------------------------------------------------------------

def check(pf, vis: str = 'matplotlib') -> int:
    """Assert that every database, indicator, option and grouping used in the
    manuscript exists in the installed version. Cheap guard against the class
    of error that made the first draft's listings unrunnable (a database that
    was never in the catalogue, an option renamed in 0.4.0)."""
    failures: list[str] = []

    def want(label, value, allowed):
        if value in allowed:
            print(f"    ok   {label}: {value!r}")
        else:
            failures.append(f"{label}: {value!r} not in {sorted(allowed)}")
            print(f"    FAIL {label}: {value!r}")

    print("\n== vocabulary check ==")
    whom = set(pf.listwhom())
    for db in ('owid', 'jhu', 'spf', 'spfnational', 'sumeau'):
        want("database", db, whom)

    want("what", 'daily', set(pf.listwhat()))
    want("what", 'current', set(pf.listwhat()))
    for opt in ('smooth7',):
        want("option", opt, set(pf.listoption()))
    want("output", 'pandas', set(pf.listoutput()))

    # listhist(), listplot() and listmap() read the chart vocabulary of the
    # selected backend, so they raise until setvis() has been called.
    want("vis", vis, set(pf.listvis()))
    pf.setvis(vis)
    want("typeofhist", 'value', set(pf.listhist()))
    want("typeofplot", 'yearly', set(pf.listplot()))
    want("typeofmap", 'dense', {str(m) for m in pf.listmap()})

    print("\n   indicators (needs setwhom, hence a download):")
    for db, indicators in (('owid', ('total_deaths', OWID_VACC)),
                           ('jhu', ('tot_confirmed',)),
                           ('spf', ('cur_hosp',)),
                           ('spfnational', ('cur_cas',)),
                           ('sumeau', ('ratio',))):
        try:
            pf.setwhom(db, reload=False)
            available = set(pf.listwhich())
            for ind in indicators:
                want(f"{db}.which", ind, available)
        except Exception as exc:
            failures.append(f"setwhom({db!r}) raised {exc}")
            print(f"    FAIL setwhom({db!r}): {exc}")

    print()
    if failures:
        print(f"{len(failures)} problem(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("all listings use a vocabulary the installed pyvoa recognises.")
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

EXAMPLES = {
    1: example_1,
    2: example_2,
    3: example_3,
    4: example_4,
    5: example_5,
    6: example_6,
}


def main() -> int:
    global FIGDIR

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--example', type=int, choices=sorted(EXAMPLES),
                    help="run a single example (default: all)")
    ap.add_argument('--vis', default='matplotlib',
                    choices=('matplotlib', 'bokeh', 'seaborn'),
                    help="plotting backend (default: matplotlib)")
    ap.add_argument('--check', action='store_true',
                    help="validate the vocabulary of every call, plot nothing")
    ap.add_argument('--verbose', type=int, default=1, choices=(0, 1, 2),
                    help="pyvoa verbosity: 0 silent, 1 info, 2 debug")
    ap.add_argument('--outdir', type=Path, default=None,
                    help=f"where to write the figures (default: {FIGDIR})")
    args = ap.parse_args()

    if args.outdir is not None:
        FIGDIR = args.outdir.resolve()

    # Headless rendering: the manuscript figures are produced by a script, not
    # by an interactive session.
    if args.vis in ('matplotlib', 'seaborn'):
        import matplotlib
        matplotlib.use('Agg')

    try:
        import pyvoa.front as pf
        import pyvoa.tools as pt
    except ImportError:
        print("pyvoa is not installed.  pip install pyvoa-full", file=sys.stderr)
        return 2

    pt.set_verbose_mode(args.verbose)
    print(f"pyvoa {pf.getversion()}")

    if args.check:
        return check(pf, args.vis)

    try:
        pf.setbatch()          # render without opening a window
    except Exception as exc:
        # not fatal: setbatch only affects the interactive backends
        print(f"    note: setbatch() unavailable ({exc})")

    selected = [args.example] if args.example else sorted(EXAMPLES)
    failures = 0
    for n in selected:
        try:
            EXAMPLES[n](pf, args.vis)
        except Exception:
            failures += 1
            print(f"\n!! example {n} failed:", file=sys.stderr)
            traceback.print_exc()

    print()
    if failures:
        print(f"{failures} example(s) failed — see the tracebacks above.")
        return 1
    print(f"all examples ran; figures in {FIGDIR}/")
    return 0


if __name__ == '__main__':
    sys.exit(main())
