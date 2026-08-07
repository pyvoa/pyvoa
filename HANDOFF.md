# Handoff — pyvoa publication readiness

Context brief for an agent session run at the root of https://github.com/pyvoa/pyvoa.
Goal: bring the repository to the state expected by a JOSS software-paper review.
Reference checklist: https://joss.readthedocs.io/en/latest/review_checklist.html

**Status, 2026-08-07.** Tasks 1-6 of the original plan are done and shipped as
v0.5.0: the `shutil` fix, PEP 621 packaging, the offline pytest suite, GitHub
Actions, the community files, and the README. The release is live on PyPI
(0.5.0, both artifacts, 2026-08-06) and on Zenodo (concept
`10.5281/zenodo.21829901`, version `10.5281/zenodo.21829902`). Discussions,
issue labels, repository description, homepage and topics are all set on
GitHub. `CITATION.cff` has no placeholders left. `git log` and `CHANGELOG.md`
carry the detail; this file now tracks only what is still open.

Everything below was re-verified against GitHub, PyPI and Zenodo on 2026-08-07.

---

## 1. CI is red on `main` — fix this first

Three runs of `ci.yml` exist and all three failed (latest: run 31167114418 on
`7e04993`). `ruff` is green; `pytest` fails on 3.10, 3.11 and 3.12 alike. The
red badge sits at the top of `README.md`, which is the first thing a JOSS
reviewer sees.

The cause is the trap that `tests/test_geo.py`'s own module docstring warns
about. Five call sites build `geo.GeoInfo(0)`:

    tests/test_geo.py:73, 79, 80, 84, 90

`gm=0` makes `GeoInfo.__init__` construct a `GeoManager()` (`pyvoa/geo.py:542`),
which downloads about ten upstream pages, so the tests trip `conftest.py`'s
socket guard on a runner. They pass locally only because
`~/.cache/pyvoa.data_<user>` is warm — `pytest` is green on this machine
(176 passed, 17 deselected) and fails with a cold `HOME`.

Fix: substitute `geo.GeoInfo.__new__(geo.GeoInfo)` for `geo.GeoInfo(0)` at all
five sites, mirroring the `bare_manager` fixture already at
`tests/test_geo.py:25`. Both methods under test only read the class-level
`_list_field`, so no instance state is needed. Verify under a cold cache
(`HOME=$(mktemp -d) pytest tests/test_geo.py`), not just a warm one.

## 2. The Zenodo 0.5.0 record still differs from `CITATION.cff`

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

## 3. `requirements.txt` duplicates `pyproject.toml`

It is tracked, and it restates the runtime dependencies plus `setuptools` and
`wheel`. Since packaging moved to PEP 621 there is no consumer of it in the
repository, and a second dependency list will drift from the real one. Delete
it, or reduce it to a one-line pointer at `pip install -e ".[dev]"`.

## 4. Confirm the issue forms render on GitHub

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

## 5. The JOSS paper

`paper.md` and `paper.bib` are drafted outside this repository and are not in
the tree. They are the remaining deliverable for the submission itself.

## 6. Uncommitted work in the tree

The documentation pass of 2026-08-07 is staged in the working tree but not
committed: `README.md` (installation, first example, the 23-database table),
`SUPPORT.md`, `CONTRIBUTING.md`, `CHANGELOG.md` (`Unreleased` section) and this
file. Every code line in the new README was executed against a live `owid`
before being written down. Commit them before starting anything above.

---

## Decisions already taken — do not re-open

- **`ruff format` is deliberately not run.** The tree is not format-clean
  (22 files) and CI does not check formatting. `CONTRIBUTING.md` §5 tells
  contributors to match the surrounding style instead. Adopting a formatter is
  a separate decision with a large, purely cosmetic diff.
- **No `PULL_REQUEST_TEMPLATE.md`** — the checklist stays in `CONTRIBUTING.md` §4.
- **`CHANGELOG.md` does not follow Keep a Changelog.** It predates the project;
  `CONTRIBUTING.md` §4.7 documents its actual convention. Do not restructure it.
- **`SUPPORT.md` and `bug_report.yml` say "about two dozen" databases** rather
  than 23. That is intentional — the exact count lives in `README.md`'s table,
  which is the one place that has to stay in step with `pyvoa/data/`.
