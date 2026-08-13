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

**Status, 2026-08-10.** Tasks 1-6 of the original plan are done and shipped as
v0.5.0: the `shutil` fix, PEP 621 packaging, the offline pytest suite, GitHub
Actions, the community files, and the README. The release is live on PyPI
(0.5.0, both artifacts, 2026-08-06) and on Zenodo (concept
`10.5281/zenodo.21829901`, version `10.5281/zenodo.21829902`). Discussions,
issue labels, repository description, homepage and topics are all set on
GitHub. `CITATION.cff` has no placeholders left. `git log` and `CHANGELOG.md`
carry the detail; this file now tracks only what is still open.

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

| Field | Zenodo record | `CITATION.cff` |
|---|---|---|
| affiliations | `Université Paris Cité`, `Centre National de la Recherche Scientifique` | full UMR strings |
| keywords | 6 | 8 — `epidemiology` and `COVID-19` dropped |
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

`paper.md` and `paper.bib` are drafted outside this repository and are not in
the tree. They are the remaining deliverable for the submission itself.

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

## 4. Dependencies are unpinned, and CI now resolves pandas 3.0

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

---

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
