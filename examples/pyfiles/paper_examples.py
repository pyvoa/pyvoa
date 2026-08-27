#!/usr/bin/env python3
r"""
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

Figures are written as PDF, which is the vector artwork Elsevier asks for and
what \includegraphics pulls in from the .tex. Examples 1-4 are the manuscript
listings and produce Figs. 2-5; example 3 carries a second listing whose output
is printed rather than drawn, and is reproduced here as the console session the
manuscript prints under Fig. 4. Examples 5 and 6 are not listings and draw
nothing — they support claims made in Sections 2.1 and 4.

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

# Nothing is factored out into a constant. Each listing spells its arguments
# out literally, so that the .tex and this file can be diffed line by line; a
# listing that reads `when=JHU_DATE` here and `when='31/12/2021'` in the paper
# cannot be compared at all, which is the point of this file.
#
# No `tile=` either: the default is 'esri' (the first entry of listtile()), and
# it renders. An earlier draft passed 'positron' to avoid OpenStreetMap's
# blocked tiles, which only matters if 'openstreet' is asked for by name.


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
# Example 1 — comparing countries (Fig. 2)
# ---------------------------------------------------------------------------

def example_1(pf, vis: str) -> None:
    banner(1, "comparing countries", """
        import pyvoa.front as pf
        pf.setwhom('owid')            # Our World in Data, worldwide, by country
        pf.setvis('matplotlib')
        pf.plot(which='total_deaths', where='Western Europe',
                what='daily', option='smooth7')
    """)
    pf.setwhom('owid')
    pf.setvis(vis)
    pf.plot(which='total_deaths', where='Western Europe',
            what='daily', option='smooth7')
    save(pf, "fig2_timeseries_weu.pdf")


# ---------------------------------------------------------------------------
# Example 2 — mapping a grouping (Fig. 3)
# ---------------------------------------------------------------------------

def example_2(pf, vis: str) -> None:
    banner(2, "mapping a grouping", """
        pf.setwhom('jhu')             # Johns Hopkins CSSE, worldwide
        pf.map(which='tot_confirmed', where='G20', when='31/12/2021')
    """)
    pf.setvis(vis)
    pf.setwhom('jhu')
    # No what=: for a tot_ variable the cumulative value is what is mapped,
    # which is what the caption of Fig. 3 now claims.
    pf.map(which='tot_confirmed', where='G20', when='31/12/2021')
    save(pf, "fig3_map_g20.pdf")


# ---------------------------------------------------------------------------
# Example 3 — sub-national data, ranked and normalised by population (Fig. 4)
# ---------------------------------------------------------------------------

def example_3(pf, vis: str) -> None:
    banner(3, "sub-national data, normalised by population", """
        pf.setwhom('spf')    # Sante Publique France db
        pf.hist(which='cur_hosp',when='31/12/2021',
                option='normalize:pop1M')
    """)
    pf.setvis(vis)
    pf.setwhom('spf')
    pf.hist(which='cur_hosp',when='31/12/2021',option='normalize:pop1M')
    save(pf, "fig4_hist_spf.pdf")

    # The manuscript follows Fig. 4 with the frame the very same selection
    # returns, printed as a console session: the figure and the table behind it
    # are one example, not two. Printed here in the same >>> form so that the
    # pyout block of the .tex can be diffed against a real run rather than
    # trusted.
    banner(3, "the frame behind Fig. 4 (same listing, printed)", """
        pf.setwhom('spf')    # Sante Publique France db
        pdf = pf.get(which='cur_hosp', when='31/12/2021',
                option='normalize:pop1M', what='daily')
    """)
    pf.setwhom('spf')
    pdf = pf.get(which='cur_hosp', when='31/12/2021',
                 option='normalize:pop1M', what='daily')

    # get() advertises output='pandas' by default, but a database whose
    # geography pyvoa knows comes back with its geometry attached, hence a
    # GeoDataFrame. The manuscript prints the type for exactly that reason.
    #
    # One indicator column, not three: get() keeps only what was asked for, and
    # 'what' and 'option' compose its name, so the frame carries
    # 'cur_hosp daily normalize:pop1M' and neither the count it was derived
    # from nor the other twenty indicators of the database.
    #
    # The option context is what makes the printed frame the frame the paper
    # shows: pandas sizes its repr on the terminal, and elides every column
    # between 'date' and 'geometry' when it cannot measure one, which is the
    # case as soon as the output is redirected to a file.
    import pandas as pd

    print("    >>> type(pdf)")
    print(f"    {type(pdf)}")
    print()
    print("    >>> pdf.shape")
    print(f"    {pdf.shape}")
    print()
    print("    >>> pdf.head(4)")
    with pd.option_context('display.width', 80, 'display.max_columns', None):
        print(textwrap.indent(repr(pdf.head(4)), "    "))


# ---------------------------------------------------------------------------
# Example 4 — beyond COVID-19: Ebola in the DR Congo (Fig. 5)
# ---------------------------------------------------------------------------

def example_4(pf, vis: str) -> None:
    banner(4, "beyond COVID-19 (Ebola, DR Congo)", """
        pf.setwhom('ebolardc')
        pf.hist(which='tot_confirmed',typeofhist='pie')
    """)
    pf.setvis(vis)
    pf.setwhom('ebolardc')
    pf.hist(which='tot_confirmed',typeofhist='pie')
    save(pf, "fig5_ebola_drc.pdf")


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
        pg.GeoCountry('FRA').get_data().plot()
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

    # get_data() hands back a plain GeoDataFrame, so geopandas draws it with no
    # pyvoa backend involved — which is the point being made: the layer is
    # usable on its own. Nothing is saved; this is not a manuscript figure.
    fra.get_data().plot()
    print("    GeoCountry('FRA').get_data().plot() -> drawn by geopandas alone")


# ---------------------------------------------------------------------------
# Example 6 — Impact §4, point 1: a question needing multi-source reconciliation
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

    merged = waste.merge(cases, on=['date', 'where'],
                         suffixes=('_waste', '_cases'))
    print(f"    overlapping rows after the merge: {len(merged)}")
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
    was never in the catalogue, an option renamed in 0.4.0).

    Kept in step with the same cell of PaperExamples.ipynb: it checks what the
    listings actually use, and only that. A check that tests vocabulary no
    listing exercises passes while saying nothing.
    """
    failures: list[str] = []

    def want(label, value, allowed):
        if value in allowed:
            print(f"    ok   {label}: {value!r}")
        else:
            failures.append(f"{label}: {value!r} not in {sorted(allowed)}")
            print(f"    FAIL {label}: {value!r}")

    def want_ci(label, value, allowed):
        """As want(), case-insensitively: listwhere() answers in the source's
        own casing, which is not the casing a listing is written in."""
        want(label, value.upper(), {str(a).upper() for a in allowed})

    print("\n== vocabulary check ==")
    whom = set(pf.listwhom())
    for db in ('owid', 'jhu', 'spf', 'ebolardc', 'spfnational', 'sumeau'):
        want("database", db, whom)

    want("what",   'daily',           set(pf.listwhat()))
    want("what",   'current',         set(pf.listwhat()))
    want("option", 'smooth7',         set(pf.listoption()))
    want("option", 'normalize:pop1M', set(pf.listoption()))
    want("output", 'pandas',          set(pf.listoutput()))

    # listhist() reads the chart vocabulary of the selected backend, so it
    # raises until setvis() has been called. Only 'pie' is asked for by name;
    # the other three listings take the default chart of their method.
    want("vis", vis, set(pf.listvis()))
    pf.setvis(vis)
    want("typeofhist", 'pie', set(pf.listhist()))

    print("\n   indicators and groupings (needs setwhom, hence a download):")
    for db, indicators, groupings in (
            ('owid',        ('total_deaths',),  ('Western Europe',)),
            ('jhu',         ('tot_confirmed',), ('G20',)),
            ('spf',         ('cur_hosp',),      ()),
            ('ebolardc',    ('tot_confirmed',), ()),
            ('spfnational', ('cur_cas',),       ()),
            ('sumeau',      ('ratio',),         ())):
        try:
            pf.setwhom(db, reload=False)
            available = set(pf.listwhich())
            for ind in indicators:
                want(f"{db}.which", ind, available)
            for g in groupings:
                want_ci(f"{db}.where", g, pf.listwhere())
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
    5: example_5,   # the geolocation layer alone — not a manuscript listing
    6: example_6,   # wastewater vs incidence — not a manuscript listing
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
