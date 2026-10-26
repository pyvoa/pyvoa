#!/usr/bin/env python3
"""
stress_test.py — run many combinations of pyvoa options, and keep every chart.

The script twin of examples/notebooks/PyvoaFrontStressTest.ipynb, without its
memory problem: a notebook keeps every chart it displays, hundreds of them
here, while this script writes each one to a file and frees it before the
next. Each call is one *case*; a case either draws (``ok``), is refused by
pyvoa with an explicit ``PyvoaError`` (``refused``: a combination pyvoa does
not offer), or fails with any other exception (``error``: most likely a bug).

The sections are those of the notebook:

    databases  every database: plot, hist and map with bokeh, map with matplotlib
    regions    a time series of every region of the world (jhu)
    charts     every typeofplot, typeofhist and typeofmap on owid, both backends
    options    which x what x option x chart on one database (mpoxgh)
    sumall     the daily sum of every variable of every database
    get        every output, what and option of get()

Usage
-----
    python stress_test.py                          # everything, into stress_test_output/
    python stress_test.py -s databases charts      # some sections only
    python stress_test.py -s databases --db owid spf
    python stress_test.py --no-figures             # run, write no chart
    python stress_test.py --reload                 # parse the databases again

Then open stress_test_output/index.html: one row per case, its status, its
error if any, and its chart — a thumbnail for matplotlib, a link for bokeh.
report.csv holds the same table, log.txt what pyvoa printed. The exit code is
1 when a case ends in ``error``.

The first run downloads every database into ~/.cache/pyvoa.data_<user>/ and
takes a long while; later runs read the cache. Without ``--reload``, a
database already parsed on this machine is read back from its pickles.

Licence: MIT, as pyvoa itself.
"""

import argparse
import contextlib
import csv
import gc
import html
import io
import os
import random
import re
import time
import traceback
from pathlib import Path

# before pyplot is imported: no window, the charts go to files
os.environ.setdefault('MPLBACKEND', 'Agg')

import matplotlib.pyplot as plt

import pyvoa.front as pf
from pyvoa.tools import PyvoaError

SECTIONS = ['databases', 'regions', 'charts', 'options', 'sumall', 'get']


class StressTest:
    """Run the cases, write their charts and keep the report."""

    def __init__(self, outdir, figures=True):
        self.outdir = Path(outdir)
        self.figdir = self.outdir / 'figures'
        self.figdir.mkdir(parents=True, exist_ok=True)
        self.figures = figures
        self.rows = []
        # open for the whole run, closed by report()
        self.log = open(self.outdir / 'log.txt', 'w', encoding='utf-8')  # noqa: SIM115
        self.db = None

    def setwhom(self, section, db, reload=False):
        """Select a database, unless it is the current one; say whether it worked.

        A database that cannot be loaded is a case of its own, in error.
        """
        if db == self.db:
            return True
        try:
            with contextlib.redirect_stdout(self.log):
                pf.setwhom(db, reload=reload)
        except Exception as e:
            self.log.write(traceback.format_exc())
            self.rows.append({'n': len(self.rows) + 1, 'section': section, 'db': db, 'vis': '',
                              'call': f'setwhom({db!r})', 'status': 'error', 'seconds': '',
                              'file': '', 'detail': f'{type(e).__name__}: {e}'})
            print(f'[{len(self.rows):4d}] {section:9s} {db:13s} setwhom  -> error')
            self.db = None
            return False
        self.db = db
        return True

    def case(self, section, function, **kwargs):
        """Run one pyvoa call, write its chart, and record how it went."""
        n = len(self.rows) + 1
        label = ', '.join(f'{k}={v!r}' for k, v in kwargs.items())
        row = {'n': n, 'section': section, 'db': self.db, 'vis': pf.getvis(),
               'call': f'{function}({label})', 'status': 'ok', 'seconds': '',
               'file': '', 'detail': ''}
        print(f'[{n:4d}] {section:9s} {self.db or "":13s} {row["call"]}', end='', flush=True)
        self.log.write(f'\n===== [{n}] {self.db} {row["vis"]} {row["call"]}\n')
        start = time.perf_counter()
        try:
            with contextlib.redirect_stdout(self.log):
                result = getattr(pf, function)(**kwargs)
                if function == 'get':
                    row['detail'] = describe(result)
                elif self.figures:
                    row['file'] = self.save(n, function, kwargs)
        except PyvoaError as e:
            row['status'], row['detail'] = 'refused', str(e)
        except Exception as e:
            row['status'], row['detail'] = 'error', f'{type(e).__name__}: {e}'
            self.log.write(traceback.format_exc())
        finally:
            # the figures are what filled the memory of the notebook
            plt.close('all')
            pf.__pyvoafront_instance__.outcome = None
        row['seconds'] = f'{time.perf_counter() - start:.1f}'
        print(f'  -> {row["status"]}')
        self.rows.append(row)
        if n % 20 == 0:
            gc.collect()

    def save(self, n, function, kwargs):
        """Write the last chart with savefig(), and return its file name."""
        name = slug(f'{n:04d}_{self.db}_{pf.getvis()}_{function}_' + '_'.join(
            f'{k}-{v}' for k, v in kwargs.items()))
        if pf.getvis() == 'bokeh':
            pf.savefig(str(self.figdir / name))   # bokeh appends .html
            return f'figures/{name}.html'
        pf.savefig(str(self.figdir / f'{name}.png'))
        return f'figures/{name}.png'

    def report(self):
        """Write report.csv and index.html, and return the count per status."""
        fields = ['n', 'section', 'db', 'vis', 'call', 'status', 'seconds', 'file', 'detail']
        with open(self.outdir / 'report.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self.rows)
        counts = {s: sum(r['status'] == s for r in self.rows) for s in ('ok', 'refused', 'error')}
        lines = []
        for r in self.rows:
            if r['file'].endswith('.png'):
                chart = (f'<a href="{r["file"]}"><img src="{r["file"]}" loading="lazy" '
                         'width="240"></a>')
            elif r['file']:
                chart = f'<a href="{r["file"]}">bokeh chart</a>'
            else:
                chart = ''
            lines.append(
                f'<tr class="{r["status"]}"><td>{r["n"]}</td><td>{r["section"]}</td>'
                f'<td>{html.escape(str(r["db"]))}</td><td>{r["vis"]}</td>'
                f'<td><code>{html.escape(r["call"])}</code></td><td>{r["status"]}</td>'
                f'<td>{r["seconds"]}</td><td>{html.escape(r["detail"])}</td><td>{chart}</td></tr>')
        page = INDEX.format(
            summary=', '.join(f'{v} {k}' for k, v in counts.items()),
            rows='\n'.join(lines))
        (self.outdir / 'index.html').write_text(page, encoding='utf-8')
        self.log.close()
        return counts


INDEX = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>pyvoa stress test</title>
<style>
body {{ font-family: sans-serif; margin: 1em; }}
table {{ border-collapse: collapse; }}
td, th {{ border: 1px solid #ccc; padding: 4px; vertical-align: top; font-size: 13px; }}
tr.refused td {{ background: #fff6d5; }}
tr.error td {{ background: #fbd5d5; }}
#filter {{ margin-bottom: 1em; }}
</style></head><body>
<h1>pyvoa stress test</h1>
<p>{summary}. <em>refused</em>: pyvoa declined the combination with a
PyvoaError; <em>error</em>: any other exception, most likely a bug (its
traceback is in log.txt).</p>
<p id="filter">Show:
<label><input type="checkbox" value="ok" checked> ok</label>
<label><input type="checkbox" value="refused" checked> refused</label>
<label><input type="checkbox" value="error" checked> error</label></p>
<table><tr><th>#</th><th>section</th><th>db</th><th>vis</th><th>call</th>
<th>status</th><th>s</th><th>detail</th><th>chart</th></tr>
{rows}
</table>
<script>
document.querySelectorAll('#filter input').forEach(box => box.addEventListener('change', () =>
  document.querySelectorAll('tr.' + box.value).forEach(tr => tr.hidden = !box.checked)));
</script>
</body></html>
"""


def slug(text):
    """Turn a call into a file name."""
    return re.sub(r'[^A-Za-z0-9_.-]+', '-', text)[:150]


def describe(result):
    """Say what get() handed out, for the report."""
    if hasattr(result, 'shape'):
        return f'{type(result).__name__} {result.shape}'
    with contextlib.suppress(TypeError):
        return f'{type(result).__name__} of {len(result)}'
    return type(result).__name__


# --------------------------------------------------------------------------
# the sections, after the cells of the notebook
# --------------------------------------------------------------------------

def databases(t, dbs, reload, rng):
    """Draw every database: plot, hist and map with bokeh, map with matplotlib."""
    for db in dbs:
        if not t.setwhom('databases', db, reload=reload):
            continue
        pf.setvis('bokeh')
        where = pf.listwhere()
        if isinstance(where, list) and len(where) > 4:
            t.case('databases', 'plot', where=rng.sample(where, k=4))
        t.case('databases', 'plot')
        t.case('databases', 'hist')
        t.case('databases', 'map')
        pf.setvis('matplotlib')
        t.case('databases', 'map')


def regions(t, reload, rng):
    """Draw a time series of every region of the world."""
    import pyvoa.geo as pg

    pf.setvis('matplotlib')
    if not t.setwhom('regions', 'jhu', reload=reload):
        return
    for region in pg.GeoRegion().get_region_list():
        t.case('regions', 'plot', where=region)


def charts(t, reload, rng):
    """Draw every chart type of both backends on owid."""
    if not t.setwhom('charts', 'owid', reload=reload):
        return
    common = {'which': 'total_deaths', 'where': 'Western Europe', 'what': 'daily', 'option': 'smooth7'}
    for vis in ('matplotlib', 'bokeh'):
        pf.setvis(vis)
        for h in pf.listhist():
            t.case('charts', 'hist', **common, when='20/02/2022', typeofhist=h)
        for m in pf.listmap():
            t.case('charts', 'map', **common, when='20/02/2022', typeofmap=m)
        for p in pf.listplot():
            if p in ('versus', 'yearly', 'spiral'):
                continue
            t.case('charts', 'plot', **common, typeofplot=p)
        if vis == 'bokeh':
            t.case('charts', 'plot', which='total_deaths', where='france', what='daily',
                   option='smooth7', typeofplot='spiral')
        t.case('charts', 'plot', which='total_deaths', where='france', what='daily',
               option='smooth7', typeofplot='yearly')
        t.case('charts', 'plot', which=['total_deaths', 'cur_hosp_patients'],
               where='Western Europe', what='daily', option='smooth7', typeofplot='versus')


def options(t, reload, rng):
    """Cross which, what, option and every chart on mpoxgh, under matplotlib."""
    if not t.setwhom('options', 'mpoxgh', reload=reload):
        return
    pf.setvis('matplotlib')
    where = 'Brazil'
    for which in pf.listwhich():
        for what in pf.listwhat():
            for option in [o for o in pf.listoption() if o != 'nonneg'] + ['']:
                for p in pf.listplot():
                    if p in ('spiral', 'menulocation', 'versus'):
                        continue
                    if p == 'yearly':
                        if option == 'sumall':
                            t.case('options', 'plot', which=which, what=what, option=option,
                                   typeofplot=p, where=where)
                        continue
                    if option == 'sumall' and p == 'compare':
                        continue
                    t.case('options', 'plot', which=which, what=what, option=option, typeofplot=p)
                for h in pf.listhist():
                    t.case('options', 'hist', which=which, what=what, option=option, typeofhist=h)
                if option != 'sumall':
                    for m in pf.listmap():
                        for tile in pf.listtile():
                            t.case('options', 'map', which=which, what=what, option=option,
                                   typeofmap=m, tile=tile)
                for output in pf.listoutput():
                    t.case('options', 'get', which=which, what=what, option=option, output=output)


def sumall(t, dbs, reload, rng):
    """Draw the daily sum of every variable of every database."""
    pf.setvis('matplotlib')
    for db in dbs:
        if not t.setwhom('sumall', db, reload=reload):
            continue
        for which in pf.listwhich():
            t.case('sumall', 'plot', option='sumall', which=which, what='daily')


def get(t, reload, rng):
    """Read owid through every output, what and option of get()."""
    if not t.setwhom('get', 'owid', reload=reload):
        return
    for output in pf.listoutput():
        t.case('get', 'get', when='01/01/2023', output=output)
    for what in pf.listwhat():
        t.case('get', 'get', when='01/01/2023', what=what)
        for option in pf.listoption():
            t.case('get', 'get', when='01/01/2023', what=what, option=option)
        t.case('get', 'get', when='01/01/2023', what=what, option=pf.listoption()[0:4])


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('-o', '--outdir', default='stress_test_output',
                        help='where to write the charts and the report')
    parser.add_argument('-s', '--sections', nargs='+', choices=SECTIONS, default=SECTIONS)
    parser.add_argument('--db', nargs='+', help='the databases of the databases and sumall sections')
    parser.add_argument('--no-figures', action='store_true', help='draw, but write no chart')
    parser.add_argument('--reload', action='store_true', help='parse the databases again')
    parser.add_argument('--seed', type=int, default=0, help='for the locations drawn at random')
    args = parser.parse_args()

    with contextlib.redirect_stdout(io.StringIO()):     # the welcome banner
        pf.setbatch()
    pf.set_verbose_mode(0)
    rng = random.Random(args.seed)
    dbs = args.db or pf.listwhom()
    t = StressTest(args.outdir, figures=not args.no_figures)
    for section in args.sections:
        print(f'\n=== {section}')
        if section in ('databases', 'sumall'):
            globals()[section](t, dbs, args.reload, rng)
        else:
            globals()[section](t, args.reload, rng)
    counts = t.report()
    print(f'\n{len(t.rows)} cases: ' + ', '.join(f'{v} {k}' for k, v in counts.items()))
    print(f'report: {t.outdir / "index.html"}')
    raise SystemExit(1 if counts['error'] else 0)


if __name__ == '__main__':
    main()
