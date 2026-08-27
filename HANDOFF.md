# Handoff — pyvoa publication readiness

Context brief for an agent session run at the root of https://github.com/pyvoa/pyvoa.
Goal: bring the repository to the state expected by a software-paper review.
Target journal: **SoftwareX** (Elsevier, ISSN 2352-7110), article type *Original
Software Publication*. Guide for authors:
https://www.elsevier.com/journals/softwarex/23527110/guide-for-authors

The target was JOSS until 2026-08-13. Most of the work carries over unchanged —
open licence, public repository, documentation, tests, CI, a citable archived
release — since those are what any software-paper venue asks for. What changes
is the paper itself; see section 3.

## Still open, at a glance

Updated 2026-08-26, after the guide for authors and the LaTeX template were
added to `paper/`. **CI is green.** Detail in the numbered sections below.

| # | Open item | Blocking? |
|---|---|---|
| 3.2 | **The generative-AI declaration is an annotation, not a statement.** The guide requires the declaration on submission, and the repository carries public traces of AI assistance a reviewer will find. | **yes, for submission** |
| 3.3 | Highlights (3–5 bullets, ≤85 characters, separate file) and a graphical abstract (531×1328 px). Both *encouraged*, neither written. | no |
| 3.4 | The funding wording now follows the journal and no longer matches `AUTHORS` to the letter. Confirm the funder accepts it, or revert to parentheses. | decision |
| 3 | The `\attn` items still inside `main.tex`: the §4 adoption evidence, and moving the bibliography to BibTeX before submission. | submission |
| 1 | The Zenodo `0.5.0` record still differs from `CITATION.cff` — affiliations, keywords, `continues`, and the wheel is not archived. Decide: edit by hand, or let `0.5.1` be the first consistent deposit. | no |
| 1 | Whether to declare the IdEx award as a structured Zenodo `grants` entry. Attach through the UI; test on the sandbox before putting it in the file. | no |
| 2 | Confirm the four issue forms render on GitHub while signed in, and add the version placeholder in `bug_report.yml` to the release checklist. | no |
| 5 | Two documentation URLs now exist — `pyvoa.org` and `pyvoa.github.io/pyvoa`. Decide how they relate. | no |
| 6 | `front.merger()` has never been callable. Implement or remove before the paper claims an API. | no |
| — | The template asks for a `Licence.txt`; the repository has `LICENSE`, no extension. Almost certainly fine, but "your paper will be returned if these are missing" is their wording. | no |
| — | `GeoRegion` resolves `'G20'` to twenty entries with `MEX` duplicated — nineteen distinct countries. | no |

### Closed since the previous revision

- **The word limit is 4000, not 3000.** The guide says so and the template
  repeats it. `tests/test_paper.py` asserted 3000 with no source, which failed
  every pytest job and the paper/code job on a manuscript that was inside the
  real limit throughout. Keywords likewise: the guide allows 1 to 7, the test
  demanded 6 or fewer. Both corrected, and the figure limit of six now has the
  template as its source. This was the whole of the red CI.
- **The reproducible-capsule cells are no longer a blocker.** The current
  template has eight code-metadata rows and no such row at all; the manuscript
  was carrying a table from an older edition. Both C3 and S3 are gone, and the
  tables now follow the template, headings included, with the executable
  software version after the bibliography where the template puts it.
- **The subsections of §3 are numbered** 3.1 to 3.4, as the guide asks, and a
  stale reference to a deleted "Example 5" was found and fixed in §4.
- **The funding statement** is in the journal's prescribed `Funding: ...`
  form — see 3.4 above for what that cost.
- **`tile='openstreet'` was never the default.** This file said it was, twice.
  `listtile()` is `['esri', 'positron', 'stamen', 'openstreet', None]` and the
  first entry is the default, so maps are drawn on Esri tiles and render
  correctly. The 403 applies only when `'openstreet'` is asked for by name.

**Status, 2026-08-10.** Tasks 1-6 of the original plan are done and shipped as
v0.5.0: the `shutil` fix, PEP 621 packaging, the offline pytest suite, GitHub
Actions, the community files, and the README. The release is live on PyPI
(0.5.0, both artifacts, 2026-08-06) and on Zenodo (concept
`10.5281/zenodo.21829901`, version `10.5281/zenodo.21829902`). Discussions,
issue labels, repository description, homepage and topics are all set on
GitHub. `CITATION.cff` has no placeholders left. `git log` and `CHANGELOG.md`
carry the detail; this file tracks what is still open, summarised in *Still
open, at a glance* above.

The documentation pass of 2026-08-07 is committed. So is the fix for the red
CI: the four `GeoInfo` tests built a real `GeoInfo(0)`, whose `gm=0` makes
`GeoInfo.__init__` construct a `GeoManager()` (`pyvoa/geo.py:542`) and download
about ten upstream pages, so they tripped `conftest.py`'s socket guard on a
runner and passed locally only on a warm `~/.cache/pyvoa.data_<user>`. They now
share a `bare_info` fixture built with `GeoInfo.__new__`, mirroring
`bare_manager` next to it; both methods under test read only the class-level
`_list_field`.

**Landed since, 2026-08-10 and 2026-08-11.** Seven changes, each green on CI at
the time of the push. The suite is at 218 passed, 17 deselected; `ruff check .`
is clean.

- **Python 3.13** is declared (trove classifier) and tested. The matrix is now
  3.10/3.11/3.12/3.13 (#27); `requires-python` stays `>=3.10`, and the
  single-version `lint` and `network` jobs stay on 3.12. The suite passes on
  3.13 on a real runner, not only in a resolver check. Note that the PyPI
  Python badge reads the published classifiers, so it keeps advertising
  3.10-3.12 until 0.6.0 ships.
- **The `lint` job had been red on `main`** since `9492bf9`, which deleted the
  only reader of `datesunique` in `pyvoa/geopd_builder.py` and left an F841
  behind. Fixed in #26 by commenting the assignment out, per the convention in
  `CLAUDE.md`. The test jobs were green throughout.
- **`GeoCountry` gained four code <-> name converters** —
  `from_subregion_codes_to_names`, `from_subregion_names_to_codes`,
  `from_region_names_to_codes`, `from_region_codes_to_names` — with 42 offline
  tests. They share a `_translate_list` helper: the conversion is positional,
  so `result[i]` translates `argument[i]` and the two lists can be zipped, a
  repeated entry is translated as many times as it appears, and an absent
  entry raises a `PyvoaError` naming the offenders. The tests build the
  `GeoCountry` with `__new__` over a hand-written `_country_data`, which
  reaches the region converters too, so nothing is downloaded.
- **`README.md` carries the Zenodo concept-DOI badge** (`10.5281/zenodo.21829901`),
  which had been recorded in `CITATION.cff` and `codemeta.json` but never
  surfaced. A ruff badge was considered and rejected: the standard one is
  static and says nothing about whether the lint passes, which the CI badge
  already covers.
- **The machine-local git note left `CLAUDE.md`** for an ignored
  `CLAUDE.local.md`; it described one contributor's setup, and `CLAUDE.md` is
  read by every contributor.
- **`CHANGELOG.md` now covers every release.** The 0.5.0 entry described the
  publication-readiness work of its last two days and nothing of the eight
  months before it; it was rewritten from all 220 non-merge commits since
  v0.4.2 and grouped into data sources and caching, geography, visualization,
  data handling, errors and verbosity, packaging and process. Its opening no
  longer claims the analysis API is unchanged, because `setvisu()`,
  `get_echoinfo()` and the axis-type option were all renamed in 0.5.0, so it is
  not a drop-in upgrade from 0.4.2.
- **The entries for 0.1.0 to 0.4.2 were filled out** from their own ranges of
  the log; 0.4.1 and 0.4.2 are separate sections now. 0.4.0 is the substantial
  one — five months, 359 commits — and carries a verified rename table for the
  front-end API and the chart options.

Two things learned while doing that, both worth knowing before the next release
or any archival work:

- **The `v0.1.0`, `v0.2.0`, `v0.2.2` and `v0.3.0` tags are not ancestors of
  `main`.** The early history was rewritten and `main` carries its own copies
  under different hashes, so a range like `v0.3.0..v0.4.0` silently includes
  rewritten duplicates — 397 commits, against 378 for the same span measured
  from `main`'s own 0.3.0 release commit (`638bce2..v0.4.0`). Use `main`'s
  release commits as boundaries. Two releases, **0.2.1 and
  0.3.1, were published to PyPI but never tagged at all**; 0.3.1 was prepared
  in `3384862`.
- **Commit subjects do not always match what shipped.** The 0.4.0 rename list
  was built by diffing the front methods and the option vocabulary between the
  two trees, not by transcribing the log, and that caught two errors: a commit
  reads "change which to what", but `which` and `what` both exist before and
  after with different meanings, so no rename happened; and `getversion()`
  already existed at 0.3.1 rather than arriving in 0.4.0.

**Landed 2026-08-13, while producing the manuscript figures.** Running the
paper's own examples end to end found four defects in the plotting path, none of
which any test covered, all fixed with the figures as evidence:

- `plt.cm.get_cmap`, removed in matplotlib 3.9, made **every matplotlib map
  raise** (`visu_matplotlib.py`).
- `front.plot()` assigned `self.outcome` inside its `if not self.batch` branch,
  so **`savefig()` after `setbatch()` failed** on a plot — the headless path a
  script uses. `map()` and `hist()` already did it correctly.
- `matplotlib_map` overrode every frame's CRS to Lambert-93 and used a 10 km
  minimum extent, which is 10 000 degrees on a lon/lat frame: the **dense French
  map drew metropolitan France as a speck** in a world-sized box. The units are
  now read off the extent and handed to contextily.
- The map/histogram title printed the end of the requested range rather than the
  **date actually drawn**, so `when='01/12/2022'` was titled `09/03/2023`.

Two things found and *not* changed, because they are decisions rather than bugs:
`tile='openstreet'` returns OpenStreetMap's "Access blocked" 403 images (the
paper passed `tile='positron'` to avoid it, and now passes nothing, `'esri'`
being the default — this entry originally said openstreet was the default,
which it is not), and
`contextily` — a required dependency — itself requires `matplotlib`, so a plain
`pip install pyvoa` always has matplotlib, whatever "optional backend" means
elsewhere.

**Landed 2026-08-25 and 2026-08-26.** Authorship metadata, the docstrings, and
the documentation site. The suite is at 250 passed, 22 deselected, with one
known failure — see section 3, which is now the only thing keeping CI red.
`ruff check` on the tracked tree is clean.

- **Authorship metadata is aligned across the repository.** `AUTHORS` and
  `paper/main.tex` carry the affiliations in the form the journal expects, and
  `CITATION.cff`, `.zenodo.json`, `codemeta.json` and `schemaorg.jsonld` now
  repeat them verbatim, with Olivier Dadoun's `dadoun@in2p3.fr` and the paper's
  keywords. The same pass brought the two schema files back in step with
  `pyproject.toml` (`beautifulsoup4`, python 3.13) and put the three people in
  `[project] authors`, where the project address had stood, so
  `importlib.metadata.metadata("pyvoa")["Author"]` and `pyvoa.__author__` agree.
  `maintainers` stays `contact@pyvoa.org`. Build requirements dropped `wheel`
  and gained the `setuptools>=64` floor the `attr:` version read needs.
- **`pyvoa/__version__.py` documents what reads it** — setuptools statically,
  and `tests/test_paper.py` as text — and therefore why it must stay a plain
  literal with no imports. It described a `setup.py` that has not existed since
  the move to PEP 621.
- **`saveoutput()` wrote `pycoa.ut.xlsx`.** A `pycoa` rename had run through
  the default string itself; it is `pyvoa_out` now. Called before `setwhom()`
  it raised a bare `AttributeError` on `None`, and raises `PyvoaError` now.
- **Every function and class in `pyvoa/` has a docstring**, 274 of them, up
  from 176. Worst case were the four chart methods: `functools.wraps` carries
  the *innermost* docstring out to the caller, so `pf.get` had none at all and
  `pf.plot` and `pf.hist` advertised a `fig` parameter no caller can pass. The
  public contract is written on the innermost definition, which is what reaches
  `pf.plot?`.
- **Docstrings are NumPy style throughout, and ruff enforces it.** 135 Google
  sections converted, 87 summaries put in the imperative mood, five class
  `Methods` sections dropped as duplicating autodoc. `pyproject.toml` selects
  `D` with `convention = "numpy"`; `examples/*` is exempt entirely and
  `tests/*` from `D100`-`D104` only. The tree is at zero `D` findings, so a
  docstring that drifts now fails CI.
- **The API documentation is generated and published.** `docs/` is a Sphinx
  tree read by napoleon; `.github/workflows/docs.yml` builds it on every pull
  request and deploys from `main` to GitHub Pages, live at
  <https://pyvoa.github.io/pyvoa/>. `make html` passes `-W`, so a docstring
  that stops rendering fails the build. The landing page carries two figures
  from `paper/figures/`.

Three things worth knowing before touching the docs again:

- **A module added to or renamed in `pyvoa/` needs its `.rst` in `docs/api/`.**
  This already bit once: `kwarg_options.py` became `kwargs_options.py` and the
  docs build went red, which under `-W` is how a silently missing page
  surfaces. `sphinx-apidoc` would generate the stubs automatically, at the cost
  of the hand-written grouping in `backends.rst` and `front.rst`.
- **`docs/_static` is kept in git by a `.gitkeep`.** `conf.py` names it in
  `html_static_path` and Sphinx warns fatally under `-W` when it is missing.
  Git does not track empty directories, so without that file the build passed
  locally and failed on CI alone. Rehearse a docs change from `git archive`,
  never from a copied working tree.
- **The four optional backends are mocked** (`bokeh`, `seaborn`, `folium`,
  `branca`) in `autodoc_mock_imports`: none is a hard dependency, so none is
  present in the environment the workflow builds from. autodoc still reads the
  real `pyvoa` modules.

Sections 1-3 below were last re-verified against GitHub, PyPI and Zenodo on
2026-08-07. Of those, only the two Zenodo DOIs were re-checked on 2026-08-10,
while adding the badge: both resolve, and `21829902` is the 0.5.0 version
record.

---

## 1. The Zenodo 0.5.0 record still differs from `CITATION.cff`

`CONTRIBUTING.md` §9.3 requires this check at every release. Four differences
survive on record `21829902`; the other five noted earlier (Beau's missing
ORCID, `dadoun, olivier` lowercased, `v0.5.0` vs `0.5.0`, publication date, the
concept DOI) have since been corrected on Zenodo or in `CITATION.cff`.

Re-checked against the live record on 2026-08-26. The divergence has widened
slightly, because `CITATION.cff`'s affiliations and keywords were rewritten on
2026-08-25 and the deposit predates that.

| Field | Zenodo record `21829902` | `CITATION.cff` |
|---|---|---|
| affiliations | `Université Paris Cité` (Beau, Browaeys), `Centre National de la Recherche Scientifique` (Dadoun) | `Université Paris Cité and Sorbonne Université, CNRS, LPNHE, F-75005 Paris, France` and the MSC equivalent |
| keywords | 6: `open data`, `data visualisation`, `geolocation`, `python`, `reproducible research`, `science education` | 8: adds `epidemiological data` and `COVID-19`, has `geospatial data` for `geolocation` and `Python` for `python` |
| `continues` | `https://pyvoa.org` | the pycoa repository |
| files archived | `pyvoa-0.5.0.tar.gz` only | wheel + sdist on the GitHub release |

`.zenodo.json` now exists in the repository (alongside `codemeta.json` and
`schemaorg.jsonld`) and already carries the correct affiliations, all eight
keywords and `continues → https://github.com/coa-project/pycoa`, so the **next**
release is correct by construction. The 0.5.0 record predates it.

Decide, and record the decision here: either edit the 0.5.0 record by hand in
the Zenodo UI, or leave it and let v0.5.1 be the first consistent deposit.
Editing metadata does not mint a new DOI; adding the wheel to an existing
record does require a new version.

### The IdEx grant, and why `.zenodo.json` does not declare it

The funding acknowledgement is in `.zenodo.json` as free-text `notes` only. A
structured `grants` entry would link the deposit to the funder in Zenodo and in
OpenAIRE, and the award does exist — but do not add one blind, because the
documentation and the live API disagree. Checked on 2026-08-12:

| check | result |
|---|---|
| `GET /api/awards/00rbzpz17::ANR-18-IDEX-0001` | **200**, titled "Université de Paris" — the former name of Université Paris Cité, so this is the right award |
| `GET /api/funders/00rbzpz17` | 200, Agence Nationale de la Recherche, carrying both the ROR `00rbzpz17` and the funder DOI `10.13039/501100001665` |
| `GET /api/grants/10.13039/501100001665::ANR-18-IDEX-0001` | **404** |
| `GET /api/grants/?q=ANR` | **404** — the whole legacy grants API is gone |
| developers.zenodo.org | still documents `grants` as `[{"id": "10.13039/…::<code>"}]` |

So the format the deposit documentation asks for is the one that no longer
resolves, and the id that does resolve is InvenioRDM's ROR-based
`00rbzpz17::ANR-18-IDEX-0001`. Which of the two the GitHub-integration deposit
path accepts cannot be established without attempting a real deposit, and a
rejected `grants` value fails the release.

Attach the award through the Zenodo UI after depositing instead: the form
validates as you type, so a wrong value costs nothing there. If a future
release is to declare it in the file, test it on the Zenodo **sandbox**
(sandbox.zenodo.org) first, never on a real release.

## 2. Confirm the issue forms render on GitHub

All four files under `.github/ISSUE_TEMPLATE/` parse as YAML locally, and every
label they request (`bug`, `enhancement`, `new database`, `data`) exists on the
repository. But GitHub applies a stricter schema than a plain YAML parse, and
those errors only surface on the site; `https://github.com/pyvoa/pyvoa/issues/new/choose`
redirects for anonymous requests, so this cannot be checked from a clone.
Open the page while signed in and confirm the three forms appear.

While there: `.github/ISSUE_TEMPLATE/bug_report.yml:38` hardcodes `pyvoa 0.5.0`
as the version placeholder, so it goes stale at every release — and the release
checklist in `CONTRIBUTING.md` §9 does not mention it. Add it to §9 as a fifth
step, or the placeholder will drift again.

## 3. The SoftwareX paper

**In the tree since 2026-08-13**, as `paper/main.tex` (elsarticle), `paper/Makefile`,
`paper/README.md`, `paper/figures/` and `tests/test_paper.py`. It builds: `make
draft` and `make final` both compile, and all thirteen consistency tests pass.

Since 2026-08-26 the two authorities are in `paper/` as well:
`softwarex-osp-template.tex`, which is LPPL-licensed and committed, and the
guide for authors as a PDF, which is Elsevier copyright and **gitignored** —
read it, cite it, do not push it. `main.tex` has been checked against both and
now follows the template's metadata tables, headings, section order and
numbering. What remains is editorial: §3.2 to §3.4 below, plus the
third-party-adoption evidence for Section 4 and the move to BibTeX, both still
`\attn` annotations in the file.

Five things worth knowing before touching it again:

- **The figures are produced, not drawn.** `examples/pyfiles/paper_examples.py`
  writes all five of them into `paper/figures/` under the names the .tex
  includes; `make figures` runs it. `architecture.png` is the exception — it is
  a drawing, supplied by the authors. Re-run the script after any release and
  after any change to a listing, and run `--check` first, which validates every
  database, indicator and option against the installed version without plotting.
- **Page count.** `make final` gives 13 pages, but the class is
  `preprint,12pt,a4paper`, a reading layout. Recompiled with Elsevier's
  `final,5p,times,twocolumn`, the same source is 6 pages including the metadata
  tables and the references. That is the layout the 6-page limit refers to.
- **The word count is fine, and always was.** 3231 against 4000. See §3.1; the
  "about 2400 of 3000" recorded here on 2026-08-13 was two errors cancelling —
  a counter reading the wrong region, against a limit that was never the
  journal's.
- **The metadata tables come from the template, not from memory.** Eight code
  rows, seven software rows, and the executable-software section sits after the
  bibliography because that is where the template puts it. Renumbering them
  moves the row `tests/test_paper.py` reads for the dependency check, which is
  C6.
- **elsarticle is not in every TeX Live.** It was absent here; the CTAN source
  builds the class with `tex elsarticle.ins`, and it drops into
  `~/texmf/tex/latex/elsarticle/`. `latexmk` was absent too, so the Makefile
  falls back to three `pdflatex` passes.
- **`CITATION.cff`'s commented `preferred-citation` title was changed** to the
  manuscript's, since the two must be the same string and the test enforces it.
  If the title changes at submission, change it in both.

### 3.1 The word count — closed

The manuscript is 3231 words against a limit of **4000**, and CI is green.

The limit had been asserted at 3000 in `tests/test_paper.py`, with no source,
and that one number failed all five pytest jobs and the paper/code consistency
job for as long as this file has existed. The guide for authors, now in
`paper/`, says "A short descriptive paper of 4000-word limit"; the template
repeats it as "Our word limit is 4,000 words". Nothing was ever wrong with the
manuscript's length.

Two traps for anyone re-checking this. The guide's PDF renders **every digit**
as U+FFFD, so `pdftotext` and `pypdf` both report the limits as `����` — the
pages have to be read as images. And the counted region depends on the CRediT
heading being spelled `CRediT`: the test ends the region at that string, and
while the manuscript spelled it `CrediT` the count swept in the declarations,
the acknowledgements and the whole bibliography, giving 4050.

Section 3 was also shortened, from five examples to four, when the figures were
reworked. That was worth doing on its own merits but was not, in the end,
necessary to fit.

### 3.2 The generative-AI declaration is still an annotation — blocking

`\section*{Declaration of generative AI and AI-assisted technologies in the
writing process}` exists and contains only an `\attnpar` telling the authors
what to write. The guide requires the declaration at submission. The suggested
wording is in the annotation itself.

Two things the annotation already notes and that remain true. Use of assistants
in the *code* is not what this declaration covers — it is about the writing —
but the repository carries public traces either way (`CLAUDE.md`, this file,
and the 0.3.1 changelog entry recording that docstrings were written with LLM
assistance), and a reviewer will find them. And Elsevier has revised the
required wording twice; check it at submission rather than trusting the
annotation.

### 3.3 Highlights and a graphical abstract

Neither exists. Both are *encouraged*, not required, and both are submitted as
separate files rather than in the manuscript:

- **Highlights** — 3 to 5 bullet points, each at most 85 characters including
  spaces, in a file with "highlights" in its name.
- **Graphical abstract** — 531 x 1328 pixels (h x w) or proportionally larger,
  readable at 5 x 13 cm, as TIFF, EPS, PDF or an MS Office file.

`paper/figures/architecture.png` is close to what a graphical abstract wants
and is already the paper's own diagram; it is portrait, 1500 x 1934, so it
would need recomposing to the required aspect.

### 3.4 The funding wording no longer matches AUTHORS to the letter

The guide prescribes a literal form, `Funding: This work was supported by ...
[grant numbers xxxx]`, and the acknowledgements now use it. `AUTHORS` requires
its own sentence to be reused verbatim — with `(ANR-18-IDEX-0001)` in
parentheses — and says so as a condition of the grant. The two cannot both
hold to the word.

Every element the funder mandates is present, and
`test_funding_acknowledgement_is_present` checks those four fragments against
`AUTHORS`, so the repository's guard still holds. What is not settled is
whether the funder cares about the punctuation. If it does, revert to
parentheses and tell the journal why.

### The original text of this section

`paper.md` and `paper.bib` were drafted outside this repository. They are
superseded by `paper/main.tex`; the notes below are kept for the venue
requirements they record.

They were drafted for JOSS, and SoftwareX is not the same deliverable. Known
differences, from the guide for authors:

- the manuscript goes on **Elsevier's SoftwareX template**, not JOSS's
  `paper.md` + `paper.bib`. The prose can be reused; the format cannot.
- SoftwareX requires a **code metadata table** in the manuscript. Take the
  field list from the current template rather than from any summary of it —
  it asks for things this repository already has (permanent link to the code,
  licence, versioning, languages and tools, compilation and dependency
  requirements, link to the documentation, support contact), so filling it is
  transcription rather than new work. The exact fields could not be retrieved
  here: sciencedirect.com serves 403 to automated fetches, so download the
  template from the guide-for-authors page above.
- the review is ordinary Elsevier peer review, not the public GitHub-issue
  review JOSS runs, so there is no reviewer checklist to pre-satisfy.
- the published article gets a DOI under `10.1016/j.softx.…` and an article
  number rather than page numbers. `CITATION.cff` carries a commented-out
  `preferred-citation` block ready for it.

The paper must carry the funding acknowledgement, in an acknowledgements
section: the IdEx « Université Paris Cité 2022 » (ANR-18-IDEX-0001) and the
« Institut Covid-19 Ad Memoriam » of Université Paris Cité. The sentence to
reuse verbatim is in the *Funding* section of `AUTHORS`; `README.md` and
`.zenodo.json` carry it too. `CITATION.cff` does not, and cannot: CFF 1.2.0 has
no funding key and its schema sets `additionalProperties: false`, so adding one
makes the file invalid.

## 4. Dependencies are unpinned, and CI now resolves pandas 3.0 — **done**

Settled on 2026-08-13: lower bounds on every direct dependency, no upper
bounds, and a `minimum` CI job that installs the floors on python 3.10 with
`uv pip install --resolution lowest-direct` and runs the offline suite, so a
floor that is not true fails CI instead of a user's install. The floors were
picked as the oldest release with a wheel for python 3.10 in the API era the
code is written against, then verified: 218 passed on 3.10 and on 3.12, and
`import pyvoa.front` works on both. `bs4` became `beautifulsoup4`, since `bs4`
is a thin forwarding package whose own versions are `0.0.x` and cannot carry a
meaningful bound.

No upper bounds, deliberately. Capping a library's dependencies propagates the
cap into every environment that installs it, and is the usual cause of
unresolvable installs; a new upstream major is caught by the `test` job, which
always resolves to the newest release. The original text follows, for the
reasoning.



`pyproject.toml` lists `pandas`, `geopandas`, `numpy` and the rest with no
bounds at all, so every CI run installs whatever is newest that day — as of
2026-08-10 that is pandas 3.0.5 and numpy 2.5.2, on every matrix entry. The
suite passes on them, so nothing is broken. The exposure is that a major
release upstream can turn `main` red without a commit, which is the same
failure mode the pinned ruff version already guards against, and it also means
a reviewer cannot reproduce a run from the metadata alone — and SoftwareX asks
for the dependency requirements explicitly, in the code metadata table.

Not urgent and not obviously worth a wide pin: a floor on the majors that are
actually supported (`pandas>=2`, `numpy>=1.24`, …) would cost little and say
something true, whereas upper bounds would need maintenance at every upstream
release. Decide before 0.6.0 and record the decision here.

## 5. Two documentation URLs now exist

`https://pyvoa.github.io/pyvoa/` went live on 2026-08-26, built from `docs/` by
`.github/workflows/docs.yml`. `https://pyvoa.org` was already live and is what
`CITATION.cff`, `codemeta.json`, `schemaorg.jsonld`, `.zenodo.json` and the
README all name as the project URL, and what the Zenodo record carries as
`isDocumentedBy`.

Nothing is broken by having both, but a reader should not have to guess which
is current, and the SoftwareX code metadata table asks for a documentation
link. Three ways out, none of them started:

- point `pyvoa.org` at the Pages site with a link or a redirect, and keep the
  metadata as it is;
- make `pyvoa.org` a custom domain for the Pages site (a `CNAME` in the
  published artefact plus a DNS record), so the two become one address;
- keep them separate, `pyvoa.org` as the project's front page and the Pages
  site as the API reference, and add the Pages URL to the metadata files.

Whichever is chosen, record it here and put the answer in the code metadata
table before submission.

## Decisions already taken — do not re-open

- **`ruff format` is deliberately not run.** The tree is not format-clean
  (22 files) and CI does not check formatting. `CONTRIBUTING.md` §5 tells
  contributors to match the surrounding style instead. Adopting a formatter is
  a separate decision with a large, purely cosmetic diff.
- **No `PULL_REQUEST_TEMPLATE.md`** — the checklist stays in `CONTRIBUTING.md` §4.
- **`CHANGELOG.md` does not follow Keep a Changelog.** It predates the project;
  `CONTRIBUTING.md` §4.7 documents its actual convention. Do not restructure it.
- **`requirements.txt` is kept, not deleted.** It no longer duplicates
  `pyproject.toml` — since `7e04993` it is a comment block plus a single `.`,
  which installs the project and lets pip resolve dependencies from the
  packaging metadata. It has to stay at the repository root because
  mybinder.org builds its environment from it, and `CONTRIBUTING.md` §3 names
  Binder as a supported environment.
- **`SUPPORT.md` and `bug_report.yml` say "about two dozen" databases** rather
  than 23. That is intentional — the exact count lives in `README.md`'s table,
  which is the one place that has to stay in step with `pyvoa/data/`.
