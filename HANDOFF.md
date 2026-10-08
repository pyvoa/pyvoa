# Handoff — pyvoa publication readiness

Context brief for an agent session run at the root of https://github.com/pyvoa/pyvoa.
Goal: bring the repository to the state expected by a software-paper review.
Target journal: **SoftwareX** (Elsevier, ISSN 2352-7110), article type *Original
Software Publication*. Guide for authors:
https://www.elsevier.com/journals/softwarex/23527110/guide-for-authors

This file lists **what is still to study or decide**, and nothing else up front.
What has landed is in `CHANGELOG.md` and `git log`; how the code and the CI work
is in `CLAUDE.local.md`, machine-local and deliberately not checked in. The
decisions already taken, the notes for whoever edits the manuscript, and the
history of the repository are at the end.

**Status, 2026-10-08.** CI is green — `lint`, `test` on Python 3.10 to 3.14,
`minimum`, `paper` and `docs`. The suite is at 381 passed, 94 deselected
(network, 69 of them in `tests/test_sources.py`, which compares every database
with a direct read of its files); `ruff check` is clean. v0.5.0 is on PyPI and on Zenodo (concept
`10.5281/zenodo.21829901`). The API documentation is published at
<https://pyvoa.github.io/pyvoa/>. Archived data are read from Zenodo record
`23212632`.

## Still open, at a glance

| # | Open item | Blocking? |
|---|---|---|
| 1 | Manuscript: §4 adoption evidence, the 0.5.0 paragraph, highlights and graphical abstract. | submission |
| 2 | Merging locations sums raw dates as they are; none shipped is shown to suffer from it. | no |
| 3 | `ebolardc` has no mirror until the INSP agrees to one; the Ebola figure is pinned by `when='01/10/2026'` meanwhile. | no |
| 4 | Authors of the Zenodo community records: `rki` credited to Risklayer, `measles-usa` to us, the pyvoa team named three ways or not at all. | before release |
| 5 | Moving `contextily` from `pyvoa` to `pyvoa-full`: considered, to decide; `import pyvoa.front` breaks without matplotlib as things stand. | no |

---

## 1. The manuscript

All in `paper/main.tex`, as `\attn` / `\attnpar` annotations unless stated:

- **§4 adoption evidence** — third-party uses of pyvoa, still to document.
- **The 0.5.0 paragraph** (§ history) describes 0.5.0 but gives today's
  catalogue: "12 to 23 databases" holds for 0.5.0 by coincidence only — it
  shipped 23 too, but not the same ones (with sentinellesIRA and risklayer,
  without ebolardc and measles-usa). The figure follows today's catalogue
  only because `tests/test_paper.py` requires every database count
  to match `pyvoa/data/`. Rewrite it around the release actually submitted.
- **Highlights and a graphical abstract** — both *encouraged*, neither written,
  both submitted as separate files. Highlights: 3 to 5 bullets, at most 85
  characters each, in a file named with "highlights". Graphical abstract:
  531 x 1328 px (h x w) or proportionally larger, readable at 5 x 13 cm.
  `paper/figures/architecture.png` (portrait, 1500 x 1934) is the closest thing,
  and would need recomposing.

## 2. Merging locations: a merge sums the raw dates as they are

`replace` maps several raw locations onto one, and the parser sums the rows
sharing `(date, where)`. That is right when every location reports every day
(`jhu` provinces, `jhu-usa` and `measles-usa` counties, `dpc`, `moh`,
`covid19india`, `dgs`, `minciencia`, the age classes of `sciensano` and `spf`),
wrong for cumulative or stock series reported on different days. The case that
showed it, Serbia and Kosovo in `europa` (325 common dates only), is moot now
Kosovo is left out; no shipped merge has been shown to suffer from it, and
`europa`'s sums of regions are the one not checked. Every column is summed,
rates included, but no shipped merge sums a rate since the `GUF`/`PYF` merge of
`owid` went (see the decisions).

One source defect goes through the same sum: `owid` ships East Timor twice on
1014 dates and the Faroe Islands on 394. The rows are half empty, so the sum is
harmless except for `total_gdp_per_capita` of East Timor, which comes out
doubled (13 140.2 for 6 570.1).

**Options.** (1) A real merge in the parser: carry each raw location's last
value forward over the union of their dates before summing, sum only counts and
running totals, and mark the other columns in the JSON (an `"intensive": true`
column key, say) to give them a value that is not a sum. Increments
(`cumulative: true`) are summed as they are. It touches every existing merge:
run `pytest -m network tests/test_sources.py` afterwards. (2) Leave things as
they are.

## 3. The Ebola mirror

`ebolardc` is read from its provider only (*live only* in the README): its
`urldata` is the INRB/UMIE GitHub file, and the parser reads any dataset whose
`urldata` is not on Zenodo in live mode, whatever `setlive()` says. The reason
is the data's terms. The repository's MIT `LICENSE.md` covers its code; the
sitrep extracts pyvoa reads carry their own, in
`data/insp_sitrep/metadata.yaml`: *"reuse with attribution to INSP and citation
of the specific report number and date. Confirm distribution terms with INSP
before external republication."* (contact given: pierre.akilimali@insp.cd).

Zenodo record 23165598 (`ebolardc data`, owner account 1008528) was such a
republication; pyvoa no longer reads it, and it has been closed to the public
(embargoed, files no longer served) on 2026-10-07. With the INSP's written
agreement the mirror can come back, under the INSP's terms rather than MIT.
Meanwhile the Ebola listing of the manuscript carries `when='01/10/2026'`, so
that Fig. 5 does not follow the latest report; it would still change if the
provider revised past reports, or withdrew them. INRB/UMIE's own deposit (10.5281/zenodo.21223302, cited
as `bdbv2026`) is also labelled MIT; that is theirs to settle.

## 4. Authors of the Zenodo community records

Reviewed on 2026-10-07 against `AUTHORS`, `CITATION.cff`, `.zenodo.json` and
the source each database actually reads. Metadata edits mint no new version,
so none of this touches the code. At the least, fix the records pyvoa reads:
10082179 (jhu), 11222009 (mpoxgh), 11222014 (moh), 11222015 (jpnmhlw),
11222016 (imed), 11222017 (govcy), 11222020 (europa), 11222021
(escovid19data), 11222022 (dpc), 11222023 (dgs), 11267174 (jhu-usa), 18682655
(rki), 18772757 (phe), 18773580 (minciencia), 18788895 (covidtracking),
18788975 (covid19india), 18789975 (owid), 18790064 (sciensano), 18790282 (spf,
spfnational), 18790381 (sumeau), 23047588 (geo), 23165146 (measles-usa),
23212632 (Bulk).

**Data producers named as creators**, in order of urgency:

| Record | Creator now | Problem | Proposed |
|---|---|---|---|
| `rki` 18682655 | Risklayer | wrong: pyvoa reads `cases-rki-by-ags.csv` of jgehrcke/covid-19-germany-gae, RKI data (the Risklayer files there are `*-rl-crowdsource-*`) | Robert Koch-Institut; Jan-Philip Gehrcke as contributor (DataCollector) |
| `measles-usa` 23165146 | Beau, Tristan | the record's own description credits the JHU Measles Tracking Team | Johns Hopkins University Measles Tracking Team; Beau as DataCurator |
| `mpoxgh` 11222009 | Our World in Data | Global.health, the primary source, is missing | Global.health; Our World in Data |
| `covidtracking` 18788895 | "Covid Tracking Database" | not the project's name | The COVID Tracking Project at The Atlantic |
| `covid19india` 18788975 | "Covid 19 India" | idem | covid19india.org |
| `sumeau` 18790381 | "Sumeau" | data.gouv.fr gives Santé publique France as publisher | Santé publique France |
| `dgs` 11222023 | DSSG Portugal | right for the compilation; the DGS is absent | add Direção-Geral da Saúde (DataCollector, or in the description) |

The other records pyvoa reads name their producer correctly.

**The pyvoa team as contributor** is written three ways: the organisation
"PyCoa" (DataCurator) on every record of account 43047, the 2026 versions of
`spf` and `sciensano` included; "Pyvoa" on the 2026 versions of `owid` only;
nothing on `jhu-usa` nor on any record of account 1008528 (Chile,
covidtracking, covid19india, sumeau, measles-usa). One rule for all data
records: the three authors as DataCurator, with ORCID and affiliation — or,
failing that, the organisation "pyvoa", spelt alike everywhere.

**Our own identity.** Bulk (23212632 and its earlier versions) names "Beau,
Tristan", affiliation "pyvoa.org", no ORCID; `geo` and `measles-usa` carry the
ORCID but no affiliation. Bulk being a compilation of third-party files whose
credits its description gives per file, name the three authors as its
creators, with ORCID and affiliation as in `AUTHORS` — or at least complete
Beau's. `geo` is derived by us: Beau as creator is right, add the affiliation.

**The software record 21829902** has the right authors and ORCIDs but
shortened affiliations; it stays as it is (see the decisions), the next release
being the first consistent deposit.

**Lesser points.** Titles mix the database key (`dgs`, `sumeau`) and free
descriptions ("Covid 19 data for Chile", "Covid Tracking USA"); a common form
would be "`<key>` — `<description>` (mirror for pyvoa)". Publication dates are
mostly the deposit date, but some give the data period (18772757
`2020-09-05/2023-02-11`, 18682655 2023, Bulk 18773027 2021). `coadata`
11198165 is credited to "PyCoa", a PyCoA-era record: keep it as history, or
name the three authors.


## 5. Moving `contextily` to `pyvoa-full`

`contextily` is a hard dependency, imported once, inside the matplotlib map
(`visu_matplotlib.py`), for the basemap tiles; it is only needed once a chart
is asked for. Moving it to `pyvoa-full` would make `pip install pyvoa` truly
free of plotting libraries — what §2.2 of the manuscript claims — but
matplotlib reaches a plain `pip install pyvoa` through contextily alone
(geopandas and pandas ask for it as an extra only), so it would go too.
Considered on 2026-10-08, left for a later decision. What it takes:

1. **`import pyvoa.front` would fail.** `front.py` (l. 36) and `visualizer.py`
   (l. 20) import `matplotlib.pyplot` at module level, unconditionally. Make
   those imports lazy; `MATPLOTLIB_AVAILABLE` in `visualizer.py`, which can
   never be False today, would then mean something.
2. **matplotlib serves outside the charts.** The `tab20` colour map is read
   when `AllVisu` is built — which `get()` does on a user's own frame — and in
   the decorator of `front.py` that gives each location a colour. Hard-code the
   twenty colours, or defer the lookup.
3. **`pyvoa-full` must ship with it.** It lives in its own repository
   (`pyvoa/pyvoa_full`); 0.1.3 requires `pyvoa>=0.5.0`, `matplotlib>=3.8.4` and
   `bokeh>=3.1`, not contextily. Release a `pyvoa-full` adding `contextily>=1.3`
   and requiring the new pyvoa together with it: a 0.1.3 next to the new pyvoa
   would draw no tiles, and `tile='openstreet'` is the default. Raise a
   `PyvoaError` naming contextily when matplotlib is there without it.
4. **CI.** The `test` job installs `.[dev]`, and `tests/test_visualizer.py`
   imports `AllVisu`: add matplotlib and contextily to `dev` (or a `plot`
   extra). Keep a tested floor for contextily in the `minimum` job.
5. **Docs.** The build imports the real modules: add `matplotlib` and
   `contextily` to `autodoc_mock_imports` in `docs/conf.py`, or the `-W` build
   fails.
6. **Binder.** `requirements.txt` installs `.` only, and the notebooks draw:
   add matplotlib, bokeh and contextily there.
7. **Manuscript.** Row C6 lists contextily among the required dependencies,
   and `test_paper.py` checks C6 against `pyproject.toml`: update both. The
   §2.2 sentence on a lightweight core then becomes true as written.
8. **`pyvoa.geo` alone.** `GeoCountry('FRA').get_data().plot()`, shown in the
   paper notebook as drawn "by geopandas alone", needs matplotlib, which a
   plain `pip install pyvoa` would no longer bring.

Points 1, 2 and 4 to 7 are in this repository; 3 is in `pyvoa_full`, at
release time.

---

## Notes for whoever edits the manuscript

- **The figures are produced, not drawn.** `examples/pyfiles/paper_examples.py`
  writes them into `paper/figures/` (`make figures`); run `--check` first.
  `architecture.png` is the exception, a drawing supplied by the authors.
- **Page count.** `make final` gives a reading layout (`preprint,12pt`);
  Elsevier's `final,5p,times,twocolumn` gives 6 pages, the layout the limit
  refers to.
- **The metadata tables come from the template.** Renumbering them moves the row
  `tests/test_paper.py` reads for the dependency check (C6).
- **elsarticle and latexmk may be missing**: build the class from CTAN with
  `tex elsarticle.ins` into `~/texmf/tex/latex/elsarticle/`; the Makefile falls
  back to three `pdflatex` passes.
- **`CITATION.cff`'s commented `preferred-citation` title must equal the
  manuscript's** — the test enforces it.
- **Word count.** The guide's PDF renders digits as U+FFFD (read its limits as
  images), and the counted region ends at the string `CRediT`.
- **Every database count in the text must equal `pyvoa/data/`**
  (`test_paper.py`); `\attn` / `\attnpar` contents are not searched.

## Decisions already taken — do not re-open

- **The manuscript word limit is 4000, not 3000**, and keywords number 1 to 7;
  `tests/test_paper.py` asserts both.
- **Dependencies carry lower bounds only**; the `minimum` job proves every floor.
- **`ruff format` is deliberately not run**; contributors match the surrounding
  style (`CONTRIBUTING.md` §5).
- **No `PULL_REQUEST_TEMPLATE.md`** — the checklist stays in `CONTRIBUTING.md` §4.
- **`CHANGELOG.md` does not follow Keep a Changelog** (`CONTRIBUTING.md` §4.7).
- **`requirements.txt` is kept**: mybinder.org builds from it.
- **`SUPPORT.md` and `bug_report.yml` say "about two dozen" databases**; the
  exact count lives in the README's table.
- **French Guiana and French Polynesia are no longer merged into France** in
  `owid` and `mpoxgh`, and their rows are dropped (2026-10-08). OWID's France
  excludes them already: its cases follow metropolitan France (just under
  JHU's metropolitan row, 3.6 % under JHU's France with its overseas rows),
  and its rates divide by a metropolitan population, 64 277 411 as implied by
  `total_cases_per_million`. Only OWID's `population` column (67 813 000)
  takes the overseas departments in, and pyvoa does not read it. The merge
  counted nothing twice, but summed the rates.
- **Kosovo is left out of every database**, its independence not being
  recognised by the United Nations (2026-10-08). `owid` drops `OWID_KOS` (by
  the `OWID_` prefix), `europa` and `mpoxgh` drop `XKX`, `jhu` drops the
  `Kosovo` row, which used to be added into Serbia. The world borders file has
  no Kosovo polygon, its `SRB` polygon takes the territory in, so a map
  paints it with Serbia's value; the population pyvoa gives Serbia
  (6 641 964) excludes Kosovo, as the data now do.
- **`option='sumall'` on rates is set aside, not for the paper** (2026-10-08).
  It adds rates up (`total_cases_per_million` of France and Germany is
  summed), and its own branch for `cur_idx_`/`cur_tx_` names returns one
  location's value rather than a mean (0.14 for France 0.33 and Germany 0.14).
  A fix needs to know which columns are rates: the `"intensive"` column key of
  item 2 would serve both.
- **The Zenodo 0.5.0 record (`21829902`) stays as it is** (2026-10-08), though
  it differs from `CITATION.cff` and `.zenodo.json`: shorter affiliations
  (`Université Paris Cité` for Beau and Browaeys, `Centre National de la
  Recherche Scientifique` for Dadoun), 6 keywords instead of 8, `continues` and
  `isDocumentedBy` pointing at `https://pyvoa.org` instead of the pycoa
  repository and the Pages site, and the sdist alone without the wheel.
  `.zenodo.json` is right, so the next release is the first consistent deposit.
- **The IdEx award is a structured `grants` entry of `.zenodo.json`**,
  `00rbzpz17::ANR-18-IDEX-0001` (2026-10-08): the ROR id of the ANR, then the
  award number. Zenodo's awards vocabulary holds it (`/api/awards/` answers
  "Université de Paris", funder Agence Nationale de la Recherche), and the
  GitHub release reads `.zenodo.json` through Zenodo's legacy schema, whose
  `load_funding` takes `funder::award` and keeps a ROR id as it is
  (`zenodo-rdm`, `site/zenodo_rdm/legacy/deserializers/metadata.py`). The
  funder DOI form `10.13039/501100001665::...` would be mapped to the same ROR
  id. No manual step: the next release carries it. The free-text `notes`
  stay, for the Institut Covid-19 Ad Memoriam, which has no award id.
- **The generative-AI declaration is written** (2026-10-08), in the two places
  Elsevier's current policy asks for. The use in the software goes in §2.3 of
  the manuscript (`sec:history`): docstrings of 0.3.1 drafted with GitHub
  Copilot and Claude; in 2026, Claude through Claude Code for finalising and
  debugging the code and preparing the publication (metadata, PyPI,
  consistency checks). The use in the manuscript goes in the section
  "Declaration of generative AI and AI-assisted technologies in the manuscript
  preparation process" — the title Elsevier now uses — placed after the
  acknowledgements, just before the references: Claude for consistency checks
  and editing, ChatGPT for the English phrasing. Recheck Elsevier's page at
  submission; its wording has changed three times.
- **pyvoa dates from 2023** (2026-10-08): the project took the name in 2023
  and was developed in a branch of the pycoa repository until March 2025, when
  it moved to a repository of its own and the code took the name. The
  manuscript (§2.3), `AUTHORS`, `CITATION.cff` and the CHANGELOG say so alike;
  the "some 1900 commits" of PyCoA stay, unverifiable by a third party since
  the pycoa repository is private.
- **One funding sentence everywhere** (2026-10-08) — the manuscript, `AUTHORS`,
  the README and `.zenodo.json`: "This work was supported by the IdEx
  « Université Paris Cité 2022 », funded by the French State under the
  « Investissements d'avenir » programme [grant number ANR-18-IDEX-0001]; and by
  the « Institut Covid-19 Ad Memoriam » of Université Paris Cité." It is the
  journal's form (`Funding: ... [grant number ...]`) and carries every mention
  the funder requires, the « Investissements d'avenir » one included, which was
  missing before. The manuscript adds that the funders had no role in the
  design, the writing or the decision to submit, as the guide asks.
  `test_funding_acknowledgement_is_present` checks the fragments.
- **The issue forms are checked on GitHub, and the bug form's example answers
  are timeless** (2026-10-08): `pyvoa X.Y.Z`, `Python X.Y.Z` and
  `YYYY-MM-DD`, so that no release has to update them. The bug form also asks
  whether the problem shows with the archived or the live data
  (`pf.getlive()`, `pf.setlive()`), as SUPPORT.md's third check does.
- **`tile='openstreet'` is the default** of both backends; matplotlib sends a
  pyvoa User-Agent, without which OpenStreetMap serves a blocked image.
- **matplotlib maps are equal-area (Eckert IV) by default; bokeh stays Web
  Mercator**, its tiles existing in that projection only. An equal-area bokeh
  map would have no basemap: set aside on 2026-10-07.
- **`LICENSE` keeps its name**, although the SoftwareX template asks for a
  `Licence.txt` and the guide for authors for a `LICENSE.txt`: GitHub, the
  package metadata and `CITATION.cff` all go by `LICENSE` (2026-10-08).
- **The package stays in a flat layout (`pyvoa/` at the root), not under
  `src/`**, although the guide for authors asks for "source code in a
  repo/src directory": both layouts are standard for the PyPA and PyPI alike,
  numpy, pandas, scipy and matplotlib are flat, and CI tests the installed
  package (2026-10-08).
- **The Bulk archive keeps its reference files as they are**, those whose
  licence is restricted or unknown included (worldometers, worlddata.info, the
  WHO/Europe gateway, meteochile, the socrata USA geometry,
  johan/world.geo.json, the Belgian *arrondissements*, the Spanish provinces,
  the Malaysian states): the description of record 23212632 states each
  file's licence (2026-10-08). Revisiting one means a new Zenodo version,
  hence a new record id in `tools.get_local_from_url`.
- **The Japanese geography is credited in the Zenodo record only**, as every
  other file of the Bulk archive is (2026-10-08). `GeoCountry('JPN')` reads
  `dataofjapan/land`'s `japan.geojson`, archived in record 23212632, whose
  description gives the source: 地球地図日本 (Global Map Japan), GSI (国土地理院),
  under the Public Data License 1.0 (compatible with CC BY 4.0), GeoJSON
  conversion by dataofjapan/land. That repository has no licence of its own
  for what it added (English names, ids); not pursued.
- **pyvoa.org is the project's showcase site, the documentation is
  <https://pyvoa.github.io/pyvoa/>**, which pyvoa.org links to with the
  repository. The metadata follow suit: `Homepage` in `pyproject.toml` and the
  `url` of `CITATION.cff`, `codemeta.json` and `schemaorg.jsonld` give
  pyvoa.org; `Documentation` in `pyproject.toml` and `isDocumentedBy` in
  `.zenodo.json` give the Pages site (2026-10-08).

## History

- **The journal was JOSS until 2026-08-13**; the repository work carried over,
  only the manuscript format changed.
- **Every tag is an ancestor of `main` again, since 2026-09-12.** Before, `v0.1.0`
  to `v0.3.0` pointed into an orphaned copy of the early history. Two releases,
  **0.2.1 and 0.3.1, were published to PyPI but never tagged**.
- **Commit hashes before 2026-08-05 are stable; later ones are not.** The
  history was rewritten on 2026-09-12 and again on 2026-09-14, to remove the
  agent guidance file and the AI attribution trailers;
  `pyvoa-before-rewrite-20260912.bundle` and `…20260914.bundle`, beside the
  repository, hold the history as it stood. A clone made before 2026-09-14 must
  be re-cloned, not pulled: merging one back is what forced the second rewrite.
- **Commit subjects do not always match what shipped**: the 0.4.0 rename table
  in `CHANGELOG.md` was built by diffing the trees, which caught two subjects
  that described renames that never happened.
