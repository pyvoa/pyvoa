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

**Status, 2026-10-07.** CI is green — `lint`, `test` on Python 3.10 to 3.14,
`minimum`, `paper` and `docs`. The suite is at 378 passed, 23 deselected
(network); `ruff check` is clean. v0.5.0 is on PyPI and on Zenodo (concept
`10.5281/zenodo.21829901`). The API documentation is published at
<https://pyvoa.github.io/pyvoa/>. Archived data are read from Zenodo record
`23198224`.

## Still open, at a glance

| # | Open item | Blocking? |
|---|---|---|
| 1 | **The generative-AI declaration is an annotation, not a statement.** | **yes, for submission** |
| 2 | Manuscript: §4 adoption evidence, BibTeX, the Zenodo-community placeholder, the 0.5.0 paragraph, highlights and graphical abstract, the funding wording. | submission |
| 3 | Merging locations sums raw dates and adds up rates; Kosovo waits on it. | no |
| 4 | The Japanese geography (GSI data) is credited nowhere. | before release |
| 5 | The Zenodo `0.5.0` record differs from `CITATION.cff`; the IdEx award is not a structured grant. | no |
| 6 | The issue forms are unchecked on GitHub, and their version placeholder goes stale. | no |
| 7 | Two documentation URLs, `pyvoa.org` and `pyvoa.github.io/pyvoa`. | no |
| 8 | `listwhere()` returns ISO3 codes beside names for the world databases. | no |
| 9 | Folium is untested since the empty geometries were introduced. | no |
| 10 | `Licence.txt` asked for by the template; the repository has `LICENSE`. | no |
| 11 | `essai_govcy.py` and `essai_alldb.py`, untracked: keep them, or not. | no |

---

## 1. The generative-AI declaration — blocking

`\section*{Declaration of generative AI and AI-assisted technologies in the
writing process}` in `paper/main.tex` holds only an `\attnpar` telling the
authors what to write; the guide requires the declaration at submission. It is
about the *writing*, not the code, but the repository carries public traces of
AI assistance a reviewer will find (this file, and the 0.3.1 changelog entry
recording that docstrings were written with LLM assistance). Elsevier has
revised the required wording twice: check it at submission rather than trusting
the annotation.

## 2. The manuscript

All in `paper/main.tex`, as `\attn` / `\attnpar` annotations unless stated:

- **§4 adoption evidence** — third-party uses of pyvoa, still to document.
- **BibTeX** — the bibliography is a hand-written `thebibliography`; move it to
  BibTeX (`elsarticle-num`).
- **The Zenodo-community placeholder** — l. 428 reads
  `(****http://zenodo.org/communities/pyvoa****)`.
- **The 0.5.0 paragraph** (§ history) describes 0.5.0 but gives today's
  catalogue: "12 to 24 databases" is wrong for 0.5.0, which shipped 23. The
  figure is 24 only because `tests/test_paper.py` requires every database count
  to match `pyvoa/data/`. Rewrite it around the release actually submitted.
- **Highlights and a graphical abstract** — both *encouraged*, neither written,
  both submitted as separate files. Highlights: 3 to 5 bullets, at most 85
  characters each, in a file named with "highlights". Graphical abstract:
  531 x 1328 px (h x w) or proportionally larger, readable at 5 x 13 cm.
  `paper/figures/architecture.png` (portrait, 1500 x 1934) is the closest thing,
  and would need recomposing.
- **The funding wording** follows the journal's literal form, `Funding: This
  work was supported by ... [grant numbers xxxx]`, where `AUTHORS` asks for its
  own sentence verbatim, with `(ANR-18-IDEX-0001)` in parentheses, as a
  condition of the grant. Every element the funder mandates is present, and
  `test_funding_acknowledgement_is_present` checks them. Confirm the funder
  accepts the journal's form, or revert to parentheses and tell the journal why.

## 3. Merging locations: what a merge does to the numbers, and Kosovo

**Problem 1 — a merge sums the raw dates as they are.** `replace` maps several
raw locations onto one, and the parser sums the rows sharing `(date, where)`.
That is right when every location reports every day (`jhu`), wrong for
cumulative or stock series reported on different days. In `europa`, Serbia and
Kosovo share only 325 dates: on 29 only Kosovo reports, and a merged Serbia
would drop from about 16 000 deaths to Kosovo's 3139; on 409 only Serbia does.
A naive `XKX → SRB` was tried and reverted.

**Problem 2 — a merge adds up rates.** Every column is summed, `owid`'s rates
included (`*_per_million`, `*_per_hundred`, `positive_rate`,
`reproduction_rate`, `gdp_per_capita`, `excess_mortality*`). The `GUF`/`PYF` →
`FRA` merge of `owid`, kept on purpose, gives France on 2022-06-01 a
`total_cases_per_million` of 981 527 — the sum of France's 443 388, French
Guiana's 278 065 and French Polynesia's 260 074. The counts are right; the rates
are not.

**Kosovo.** The world borders file has no Kosovo and its `SRB` polygon contains
Pristina, so in the world databases Kosovo belongs with Serbia. Today `jhu`
merges it (the name resolves to `SRB`), `owid` drops it (`OWID_KOS`, by the
`drop` of the `OWID_` prefix), `europa` drops it (`XKX`, explicit `drop`);
`risklayer` keeps it, its EUR geography having a Kosovo polygon (`RS002`).

**Options.** (1) A real merge in the parser: carry each raw location's last
value forward over the union of their dates before summing, sum only counts and
running totals, and mark the other columns in the JSON (an `"intensive": true`
column key, say) to give them a value that is not a sum. Increments
(`cumulative: true`) are summed as they are. It touches every existing merge
(`dpc` Bolzano + Trento, `covid19india` Telangana and Ladakh, `escovid19data`,
the county sums of `measles-usa` and `jhu-usa`): run the raw-versus-parsed
sweep (`essai_alldb.py`) afterwards. (2) Leave things as they are. (3) Option 1,
then map `OWID_KOS` and `XKX` to `SRB` — for `owid`, the `drop` of `OWID_` runs
before `replace`, so either the order changes or `OWID_KOS` is spared.

## 4. Credit the Japanese geography

`GeoCountry('JPN')` (database `jpnmhlw`) reads
`raw.githubusercontent.com/dataofjapan/land/master/japan.geojson`, archived in
Zenodo record `23198224`. Its source is **地球地図日本 (Global Map Japan)** of
the GSI (国土地理院), whose content terms now apply the **Public Data License
1.0**: commercial use and redistribution allowed, compatible with CC BY 4.0,
attribution required (`出典：国土地理院ウェブサイト（URL）`) and modifications to
be stated. The dataofjapan repository has **no licence** of its own; its README
asks for credit to Global Map Japan, and, for commercial use, a report to the
copyright holder — a condition of the old GSI terms, now superseded.

To do: credit the source in the documentation of the Japanese geography (or the
README) and in the Zenodo record — "Prefectures of Japan: 地球地図日本 (Global
Map Japan), GSI, PDL 1.0; GeoJSON conversion by dataofjapan/land". What
dataofjapan added (English names, ids) carries no licence: ask its authors for
one, or rebuild the GeoJSON from Global Map Japan v2.2 downloaded from the GSI.

## 5. The Zenodo 0.5.0 record, and the IdEx grant

Four differences survive between record `21829902` and `CITATION.cff`:

| Field | Zenodo record `21829902` | `CITATION.cff` |
|---|---|---|
| affiliations | `Université Paris Cité` (Beau, Browaeys), `Centre National de la Recherche Scientifique` (Dadoun) | `Université Paris Cité and Sorbonne Université, CNRS, LPNHE, F-75005 Paris, France` and the MSC equivalent |
| keywords | 6 | 8: adds `epidemiological data` and `COVID-19`, `geospatial data` for `geolocation` |
| `continues` | `https://pyvoa.org` | the pycoa repository |
| files | `pyvoa-0.5.0.tar.gz` only | wheel + sdist on the GitHub release |

`.zenodo.json` is already right, so the next release is correct by
construction. Decide: edit the 0.5.0 record by hand (metadata edits mint no new
DOI; adding the wheel does), or let 0.5.1 be the first consistent deposit.

The IdEx award is in `.zenodo.json` as free-text `notes` only. A structured
`grants` entry would link the deposit to the funder, but the documented id
format (`10.13039/501100001665::ANR-18-IDEX-0001`) returns 404 — the legacy
grants API is gone — while the ROR-based `00rbzpz17::ANR-18-IDEX-0001` resolves
(checked 2026-08-12). A rejected `grants` value fails the release: attach the
award in the Zenodo UI after depositing, or test on sandbox.zenodo.org first.

## 6. The issue forms

The four files under `.github/ISSUE_TEMPLATE/` parse as YAML and every label
they request exists, but GitHub applies a stricter schema only visible on the
site: open `https://github.com/pyvoa/pyvoa/issues/new/choose` while signed in
and confirm the forms appear. `bug_report.yml` hardcodes `pyvoa 0.5.0` as its
version placeholder, and the release checklist in `CONTRIBUTING.md` §9 does not
mention it: add it there, or it drifts at every release.

## 7. Two documentation URLs

`https://pyvoa.github.io/pyvoa/` (built from `docs/` by
`.github/workflows/docs.yml`) and `https://pyvoa.org`, which the metadata files
and the README name as the project URL and Zenodo carries as `isDocumentedBy`.
Choose: point `pyvoa.org` at the Pages site; make `pyvoa.org` its custom domain
(`CNAME` plus a DNS record); or keep both, the Pages site as the API reference,
and add its URL to the metadata. Put the answer in the code metadata table of
the manuscript.

## 8. ISO3 codes in `listwhere()`

For a world database, `listwhere()` returns each country under its ISO3 code and
its name (`owid`: 546 entries, `ABW`, `AFG`, … beside the names). Commit
`0c24066` is titled "remove iso3 from listwhere": either that intent was
dropped, or the removal is incomplete. Decide which, then document it.

## 9. Folium

Folium is not installed where the recent work was checked. Untested with it:
the empty geometries (filtered out of the GeoJSON in `AllVisu.map`, as for
bokeh, which fails on them), and the keywords `pyvoalogo` and `projection`.

## 10. `Licence.txt`

The template asks for a `Licence.txt`; the repository has `LICENSE`, no
extension. Almost certainly fine, but "your paper will be returned if these are
missing" is the journal's wording.

## 11. The comparison scripts

`essai_govcy.py` and `essai_alldb.py`, untracked at the repository root, compare
each database with a direct read of its source (run them from outside the
root, with `PYTHONPATH` pointing at the checkout). They found every data defect
fixed in October 2026. Keep them (under `scripts/`, say) or drop them.

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
- **French Guiana and French Polynesia are merged into France** in `owid` and
  `mpoxgh`: overseas territories, not countries. What the merge does to rates
  is item 3: fix the merge, do not remove it.
- **`tile='openstreet'` is the default** of both backends; matplotlib sends a
  pyvoa User-Agent, without which OpenStreetMap serves a blocked image.
- **matplotlib maps are equal-area (Eckert IV) by default; bokeh stays Web
  Mercator**, its tiles existing in that projection only. An equal-area bokeh
  map would have no basemap: set aside on 2026-10-07.

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
