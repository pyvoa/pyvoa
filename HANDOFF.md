# Handoff — pyvoa publication readiness

Context brief for an agent session run at the root of https://github.com/pyvoa/pyvoa.
Goal: bring the repository to the state expected by a software-paper review.
Target journal: **SoftwareX** (Elsevier, ISSN 2352-7110), article type *Original
Software Publication*. Guide for authors:
https://www.elsevier.com/journals/softwarex/23527110/guide-for-authors
(it was JOSS until 2026-08-13; the repository work carried over unchanged, only
the manuscript format did not).

This file tracks what is **still open**. What has already landed is in
`CHANGELOG.md` and in `git log`; how the code and the CI work is in
`CLAUDE.local.md`, which is machine-local and deliberately not checked in.

**Status, 2026-09-12.** CI is green — `lint`, the four-version `test` matrix,
`paper`, `minimum`, and `docs`. The suite is at 345 passed, 22 deselected;
`ruff check` on the tracked tree is clean. v0.5.0 is on PyPI (both artefacts,
2026-08-06) and on Zenodo (concept `10.5281/zenodo.21829901`, version
`10.5281/zenodo.21829902`). The API documentation is published at
<https://pyvoa.github.io/pyvoa/>. The manuscript is in `paper/`, builds, and is
3231 words against a limit of 4000.

## Still open, at a glance

| # | Open item | Blocking? |
|---|---|---|
| 3.1 | **The generative-AI declaration is an annotation, not a statement.** The guide requires it on submission, and the repository carries public traces of AI assistance a reviewer will find. | **yes, for submission** |
| 3 | The `\attn` items left in `main.tex`: the §4 adoption evidence, and moving the bibliography to BibTeX. | submission |
| 3.3 | The funding wording follows the journal and no longer matches `AUTHORS` to the letter. Confirm the funder accepts it, or revert to parentheses. | decision |
| 3.2 | Highlights (3–5 bullets, ≤85 characters, separate file) and a graphical abstract (531×1328 px). Both *encouraged*, neither written. | no |
| 1 | The Zenodo `0.5.0` record still differs from `CITATION.cff`. Edit it by hand, or let `0.5.1` be the first consistent deposit. | no |
| 1 | Whether to declare the IdEx award as a structured Zenodo `grants` entry. | no |
| 2 | Confirm the issue forms render on GitHub while signed in, and add the version placeholder in `bug_report.yml` to the release checklist. | no |
| 4 | Two documentation URLs now exist — `pyvoa.org` and `pyvoa.github.io/pyvoa`. Decide how they relate. | no |
| — | The template asks for a `Licence.txt`; the repository has `LICENSE`, no extension. Almost certainly fine, but "your paper will be returned if these are missing" is their wording. | no |
| — | `GeoRegion` resolves `'G20'` to twenty entries with `MEX` duplicated — nineteen distinct countries. | no |

---

## 1. The Zenodo 0.5.0 record still differs from `CITATION.cff`

`CONTRIBUTING.md` §9.3 requires this check at every release. Four differences
survive on record `21829902`, re-checked against the live record on 2026-08-26;
the divergence widened when `CITATION.cff`'s affiliations and keywords were
rewritten on 2026-08-25, which the deposit predates.

| Field | Zenodo record `21829902` | `CITATION.cff` |
|---|---|---|
| affiliations | `Université Paris Cité` (Beau, Browaeys), `Centre National de la Recherche Scientifique` (Dadoun) | `Université Paris Cité and Sorbonne Université, CNRS, LPNHE, F-75005 Paris, France` and the MSC equivalent |
| keywords | 6: `open data`, `data visualisation`, `geolocation`, `python`, `reproducible research`, `science education` | 8: adds `epidemiological data` and `COVID-19`, has `geospatial data` for `geolocation` and `Python` for `python` |
| `continues` | `https://pyvoa.org` | the pycoa repository |
| files archived | `pyvoa-0.5.0.tar.gz` only | wheel + sdist on the GitHub release |

`.zenodo.json` (alongside `codemeta.json` and `schemaorg.jsonld`) already carries
the correct affiliations, all eight keywords and
`continues → https://github.com/coa-project/pycoa`, so the **next** release is
correct by construction.

Decide, and record the decision here: edit the 0.5.0 record by hand in the
Zenodo UI, or leave it and let v0.5.1 be the first consistent deposit. Editing
metadata does not mint a new DOI; adding the wheel to an existing record does
require a new version.

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

The format the deposit documentation asks for is the one that no longer
resolves; the id that does resolve is InvenioRDM's ROR-based
`00rbzpz17::ANR-18-IDEX-0001`. Which of the two the GitHub-integration deposit
path accepts cannot be established without a real deposit, and a rejected
`grants` value fails the release. Attach the award through the Zenodo UI after
depositing instead — the form validates as you type. If a future release is to
declare it in the file, test it on **sandbox.zenodo.org** first.

## 2. Confirm the issue forms render on GitHub

All four files under `.github/ISSUE_TEMPLATE/` parse as YAML locally, and every
label they request (`bug`, `enhancement`, `new database`, `data`) exists on the
repository. But GitHub applies a stricter schema than a plain YAML parse, and
those errors only surface on the site; `https://github.com/pyvoa/pyvoa/issues/new/choose`
redirects for anonymous requests, so this cannot be checked from a clone.
Open the page while signed in and confirm the forms appear.

While there: `.github/ISSUE_TEMPLATE/bug_report.yml:38` hardcodes `pyvoa 0.5.0`
as the version placeholder, so it goes stale at every release — and the release
checklist in `CONTRIBUTING.md` §9 does not mention it. Add it there as a fifth
step, or the placeholder will drift again.

## 3. The SoftwareX paper

In `paper/`: `main.tex` (elsarticle), `Makefile`, `README.md`, `figures/`, the
LPPL-licensed `softwarex-osp-template.tex`, and the guide for authors as a PDF
— Elsevier copyright and **gitignored**: read it, cite it, do not push it.
`make draft` and `make final` both compile and `tests/test_paper.py` passes.
`main.tex` follows the template's metadata tables, headings, section order and
numbering. What remains is editorial: 3.1 to 3.3 below, plus the
third-party-adoption evidence for §4 and the move to BibTeX, both still `\attn`
annotations in the file.

Five things worth knowing before touching it again:

- **The figures are produced, not drawn.** `examples/pyfiles/paper_examples.py`
  writes all five into `paper/figures/` under the names the .tex includes;
  `make figures` runs it. `architecture.png` is the exception — a drawing,
  supplied by the authors. Re-run the script after any release and after any
  change to a listing, and run `--check` first, which validates every database,
  indicator and option against the installed version without plotting.
- **Page count.** `make final` gives 13 pages, but the class is
  `preprint,12pt,a4paper`, a reading layout. Recompiled with Elsevier's
  `final,5p,times,twocolumn`, the same source is 6 pages including the metadata
  tables and the references. That is the layout the 6-page limit refers to.
- **The metadata tables come from the template, not from memory.** Eight code
  rows, seven software rows, and the executable-software section sits after the
  bibliography because that is where the template puts it. Renumbering them
  moves the row `tests/test_paper.py` reads for the dependency check, which is
  C6.
- **elsarticle is not in every TeX Live.** It was absent here; the CTAN source
  builds the class with `tex elsarticle.ins`, and it drops into
  `~/texmf/tex/latex/elsarticle/`. `latexmk` was absent too, so the Makefile
  falls back to three `pdflatex` passes.
- **`CITATION.cff`'s commented `preferred-citation` title must equal the
  manuscript's** — the test enforces it. If the title changes at submission,
  change it in both.
- **Two traps when re-checking the word count.** The guide's PDF renders every
  digit as U+FFFD, so `pdftotext` and `pypdf` both report its limits as `����`
  — read those pages as images. And the counted region ends at the string
  `CRediT`: while the manuscript spelled it `CrediT` the count swept in the
  declarations, the acknowledgements and the whole bibliography, giving 4050
  against a true 3231.

### 3.1 The generative-AI declaration is still an annotation — blocking

`\section*{Declaration of generative AI and AI-assisted technologies in the
writing process}` exists and contains only an `\attnpar` telling the authors
what to write. The guide requires the declaration at submission; the suggested
wording is in the annotation itself.

Two things that annotation notes and that remain true. Use of assistants in the
*code* is not what this declaration covers — it is about the writing — but the
repository still carries public traces (this file, and the 0.3.1 changelog
entry recording that docstrings were written with LLM assistance), and a
reviewer will find them. The agent guidance file and the commit trailers that
also recorded it were removed from the history on 2026-09-12; anything already
cloned or cached elsewhere keeps them. And Elsevier has
revised the required wording twice: check it at submission rather than trusting
the annotation.

### 3.2 Highlights and a graphical abstract

Neither exists. Both are *encouraged*, not required, and both are submitted as
separate files rather than in the manuscript:

- **Highlights** — 3 to 5 bullet points, each at most 85 characters including
  spaces, in a file with "highlights" in its name.
- **Graphical abstract** — 531 x 1328 pixels (h x w) or proportionally larger,
  readable at 5 x 13 cm, as TIFF, EPS, PDF or an MS Office file.

`paper/figures/architecture.png` is close to what a graphical abstract wants and
is already the paper's own diagram; it is portrait, 1500 x 1934, so it would
need recomposing to the required aspect.

### 3.3 The funding wording no longer matches AUTHORS to the letter

The guide prescribes a literal form, `Funding: This work was supported by ...
[grant numbers xxxx]`, and the acknowledgements now use it. `AUTHORS` requires
its own sentence to be reused verbatim — with `(ANR-18-IDEX-0001)` in
parentheses — and says so as a condition of the grant. The two cannot both hold
to the word.

Every element the funder mandates is present, and
`test_funding_acknowledgement_is_present` checks those four fragments against
`AUTHORS`, so the repository's guard still holds. What is not settled is whether
the funder cares about the punctuation. If it does, revert to parentheses and
tell the journal why.

The acknowledgement itself: the IdEx « Université Paris Cité 2022 »
(ANR-18-IDEX-0001) and the « Institut Covid-19 Ad Memoriam » of Université
Paris Cité. `README.md` and `.zenodo.json` carry it too. `CITATION.cff` does
not, and cannot: CFF 1.2.0 has no funding key and its schema sets
`additionalProperties: false`, so adding one makes the file invalid.

## 4. Two documentation URLs now exist

`https://pyvoa.github.io/pyvoa/` went live on 2026-08-26, built from `docs/` by
`.github/workflows/docs.yml`. `https://pyvoa.org` was already live and is what
`CITATION.cff`, `codemeta.json`, `schemaorg.jsonld`, `.zenodo.json` and the
README all name as the project URL, and what the Zenodo record carries as
`isDocumentedBy`.

Nothing is broken by having both, but a reader should not have to guess which is
current, and the SoftwareX code metadata table asks for a documentation link.
Three ways out, none of them started:

- point `pyvoa.org` at the Pages site with a link or a redirect, and keep the
  metadata as it is;
- make `pyvoa.org` a custom domain for the Pages site (a `CNAME` in the
  published artefact plus a DNS record), so the two become one address;
- keep them separate, `pyvoa.org` as the project's front page and the Pages site
  as the API reference, and add the Pages URL to the metadata files.

Whichever is chosen, record it here and put the answer in the code metadata
table before submission.

## Decisions already taken — do not re-open

- **The manuscript word limit is 4000, not 3000**, and keywords may number 1 to
  7. Both have the guide and the template as their source, and
  `tests/test_paper.py` asserts them. The 3000 that stood there for a while had
  no source and was the whole of a long-running red CI.
- **Dependencies carry lower bounds only, no upper bounds.** Capping a library's
  dependencies propagates the cap into every environment that installs it, and
  is the usual cause of unresolvable installs. A new upstream major is caught by
  the `test` job, which always resolves to the newest release, and every floor is
  proved necessary by the `minimum` job.
- **`ruff format` is deliberately not run.** The tree is not format-clean and CI
  does not check formatting. `CONTRIBUTING.md` §5 tells contributors to match the
  surrounding style instead. Adopting a formatter is a separate decision with a
  large, purely cosmetic diff.
- **No `PULL_REQUEST_TEMPLATE.md`** — the checklist stays in `CONTRIBUTING.md` §4.
- **`CHANGELOG.md` does not follow Keep a Changelog.** It predates the project;
  `CONTRIBUTING.md` §4.7 documents its actual convention. Do not restructure it.
- **`requirements.txt` is kept, not deleted.** Since `df27b3a` it is a comment
  block plus a single `.`, which installs the project and lets pip resolve
  dependencies from the packaging metadata. It has to stay at the repository root
  because mybinder.org builds its environment from it, and `CONTRIBUTING.md` §3
  names Binder as a supported environment.
- **`SUPPORT.md` and `bug_report.yml` say "about two dozen" databases** rather
  than a number. The exact count lives in `README.md`'s table, which is the one
  place that has to stay in step with `pyvoa/data/`.
- **`tile='openstreet'` is not the default** and never was. `listtile()` is
  `['esri', 'positron', 'stamen', 'openstreet', None]`, first entry first, so
  maps are drawn on Esri tiles. OpenStreetMap returns "Access blocked" 403 images
  when asked for by name; that is a decision of theirs, not a bug here.

## Two traps in the git history

- **Every tag is an ancestor of `main` again, since 2026-09-12.** It was not so
  before: the early history had been rewritten, `main` carried its own copies of
  it under different hashes, and `v0.1.0` to `v0.3.0` pointed into the orphaned
  line, so a range like `v0.3.0..v0.4.0` silently included duplicates. The two
  lines differed only by a signature on the root commit, which the
  history rewrite of that day stripped, and git then saw them as one. Ranges
  measured from a tag are trustworthy now. Still true: two releases, **0.2.1 and
  0.3.1, were published to PyPI but never tagged at all**.
- **Commit hashes before 2026-08-05 are stable; the ones after are not.** That
  rewrite removed the agent guidance file and the AI attribution trailers from
  every commit, so everything from `30c950f` onward was given a new hash — the
  tags included, `v0.5.0` among them. A hash quoted in an issue, a notebook or a
  reviewer's notes from before that date still resolves; a later one does not.
  `pyvoa-before-rewrite-20260912.bundle`, kept beside the repository, holds the
  history as it stood.
- **Commit subjects do not always match what shipped.** The 0.4.0 rename table in
  `CHANGELOG.md` was built by diffing the front methods and the option vocabulary
  between the two trees, not by transcribing the log, and that caught two errors:
  a commit reads "change which to what", but `which` and `what` both exist before
  and after with different meanings, so no rename happened; and `getversion()`
  already existed at 0.3.1 rather than arriving in 0.4.0.
