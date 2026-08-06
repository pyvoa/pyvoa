# Handoff — pyvoa publication readiness

Context brief for an agent session run at the root of https://github.com/pyvoa/pyvoa.
Goal: bring the repository to the state expected by a JOSS software-paper review.
Reference checklist: https://joss.readthedocs.io/en/latest/review_checklist.html

Files already drafted and downloaded into the repository root (do not rewrite from
scratch, review and integrate): `AUTHORS`, `CITATION.cff`, `CONTRIBUTING.md`,
`CODE_OF_CONDUCT.md`, `SUPPORT.md`, `pyproject.toml`, `tests/test_tools.py`,
`.github/workflows/ci.yml`, `.github/ISSUE_TEMPLATE/config.yml`.

Work on a branch, one commit per task, and open a single pull request.

**Status, 2026-08-07: tasks 1-5 are done and released as v0.5.0** (see
"Release v0.5.0" below). `joss-readiness` was merged into `main` directly
rather than through a pull request. Task 6 and the JOSS paper remain.

## Task 1 — Fix the missing `shutil` import (blocking, 1 line)

`pyvoa/error.py` calls `shutil.get_terminal_size()` but never imports `shutil`.
Outside a TTY (script, cron, CI) `os.popen('stty size')` returns an empty string,
the fallback branch runs, and every pyvoa error surfaces as
`UnboundLocalError: cannot access local variable 'shutil'` instead of the intended
`PyvoaError`.

Reproduce: `python -c "import pyvoa.tools as t; t.check_valid_date('2020-05-01')" > /dev/null`

- Add `import shutil` at the top of `pyvoa/error.py`.
- Keep the regression test `test_error_display_works_without_a_tty` in
  `tests/test_tools.py` green.
- Open the corresponding issue on GitHub and reference it in the commit message.

## Task 2 — Packaging metadata (PEP 621)

- Replace the current `pyproject.toml` with the drafted one, delete `setup.py`.
- Check that `pip install -e ".[dev]"` and `python -m build` both succeed, and that
  the version resolves from `pyvoa/__version__.py` (single source of truth).
- `pyvoa/__init__.py` currently contains only `#nothing`: re-export `__version__`
  so that `python -c "import pyvoa; print(pyvoa.__version__)"` works, without
  importing heavy dependencies at package import time.
- Reconcile `__email__` in `pyvoa/__version__.py` (`support@pyvoa.org`) with the
  address used everywhere else (`contact@pyvoa.org`).
- Decide the minimum Python version: `setup.py` says 3.8, which is end-of-life;
  the draft assumes 3.9.

## Task 3 — Test suite

- Keep `tests/test_tools.py` (validated against 0.4.2, 9 passing + 1 regression test).
- Extend coverage to `pyvoa/geo.py`, `pyvoa/jsondb_parser.py` and the database
  parsers, using **frozen fixtures** in `tests/data/` (a few lines of real upstream
  payload) and `monkeypatch` on `pyvoa.tools.get_local_from_url`. No test in the
  default selection may hit the network.
- Mark any genuinely live test with `@pytest.mark.network`; it is deselected by
  default and only run by the weekly CI job.
- Target: every public function of `pyvoa/tools.py` covered.

## Task 4 — Continuous integration

- Add `.github/workflows/ci.yml`, check that lint and test jobs pass on the matrix.
- Fix or explicitly ignore the ruff findings; do not disable the linter wholesale.
- Add CI and coverage badges to `README.md`.
- `git rm -r --cached __pycache__` and add it to `.gitignore` (currently committed).

## Task 5 — Community files

- Integrate `AUTHORS`, `CITATION.cff`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SUPPORT.md`. Validate the citation file with `cffconvert --validate`.
- Add `.github/ISSUE_TEMPLATE/config.yml` and a `bug_report.yml` form mirroring
  the four items required in `CONTRIBUTING.md` §2.
- Link Discussions and SUPPORT from `README.md`.
- Human-only steps, to be listed in the pull request description rather than
  automated: enable GitHub Discussions, confirm O. Dadoun's ORCID, confirm the
  `@u-pariscite.fr` mail domain, mint the Zenodo concept DOI and paste it into
  `CITATION.cff`.

### Status: done — human-only steps to paste into the pull request

Copy this checklist into the PR description. Nothing below can be done from a
clone; each item is a setting or an external account.

- [X] **Enable GitHub Discussions** (Settings → General → Features). Until then,
      the Discussions links in `README.md`, `SUPPORT.md`, `CONTRIBUTING.md` §1
      and `.github/ISSUE_TEMPLATE/config.yml` all 404.
- [X] **Create the issue labels** used by the forms, or they are silently
      dropped: `bug`, `enhancement`, `new database`, `data`.
- [X] **Confirm O. Dadoun's ORCID** — `0000-0002-2169-9725` in `AUTHORS` and
      `CITATION.cff`, unverified.
- [X] **Confirm the mail domain** — `@u-pariscite.fr` for T. Beau and
      J. Browaeys; the institution also uses `@u-paris.fr`.
- [ ] **Mint the Zenodo concept DOI**, then replace the
      `10.5281/zenodo.0000000` placeholder in `CITATION.cff`. `date-released`
      is no longer a placeholder: it was set to `2026-08-06` with the v0.5.0
      release, and `version` to `0.5.0`. The concept DOI is the last remaining
      placeholder in that file.
- [ ] **Check the rendered forms**, now possible since `main` carries them:
      `https://github.com/pyvoa/pyvoa/issues/new/choose` — issue-form schema
      errors only surface on GitHub, not locally.

## Release v0.5.0 — done, 2026-08-07

Cut from the merged `joss-readiness` work. The analysis API did not change;
0.5.0 is the version that packages tasks 1-5.

- [X] **Version bumped to 0.5.0** in `pyvoa/__version__.py`. `pyvoa/help.py`
      used to carry a second, independently hardcoded `__version__` and
      `__author__` — it imports them now, so `pyvoa/__version__.py` is really
      the single source of truth. Also bumped: `CITATION.cff` (`version`,
      `date-released`) and the version placeholder in `bug_report.yml`.
- [X] **`CHANGELOG.md`** has a 0.5.0 section, written from the branch's
      fourteen commits and matching the file's existing style.
- [X] **Merged to `main`** as a `--no-ff` merge (`efd1a47`), so the branch
      stays visible in the history, and pushed.
- [X] **Tagged `v0.5.0`** (annotated, on the merge commit) and pushed.
- [X] **GitHub release** published at
      `https://github.com/pyvoa/pyvoa/releases/tag/v0.5.0`, notes taken from
      the changelog section, with `pyvoa-0.5.0-py3-none-any.whl` and
      `pyvoa-0.5.0.tar.gz` attached. Created through the REST API: `gh` is not
      installed on the release machine.
- [ ] **PyPI upload** — still pending, the only unfinished release step. The
      artifacts are built and `twine check`-clean in `dist/`; the machine has
      no `~/.pypirc`, no `TWINE_*` variables and an empty keyring, so the
      upload needs a token typed interactively:

      python -m twine upload dist/pyvoa-0.5.0-py3-none-any.whl dist/pyvoa-0.5.0.tar.gz

      List the two files explicitly: `dist/` still holds the 0.4.2 artifacts,
      and a wildcard would try to re-upload them and fail the batch.

Verified before tagging: 176 tests pass, `ruff check pyvoa/ tests/` clean, both
artifacts pass `twine check`, the wheel carries all 23 database JSON files and
the 3 PNGs, and it installs into a fresh venv reporting 0.5.0. The only ruff
findings in the tree are in `test.py`, which is untracked and invisible to CI.

## Todo the zenodo concept DOI
  Two ways round it

  A. Keep Zenodo, drop GitHub entirely — manual upload. The GitHub integration does exactly one thing: on each release it downloads
  https://github.com/pyvoa/pyvoa/archive/refs/tags/v0.5.0.tar.gz and creates a deposit from it. You can upload that same tarball yourself. The resulting record, DOIs included,
  is indistinguishable. This is what I'd do — it's a handful of clicks once every release, and pyvoa releases a few times a year, not weekly.

  B. Link GitHub afterwards, without signing up through it. Worth knowing in case you assumed otherwise: you can create a Zenodo account with ORCID (you have one, and so do
  Julien and Olivier) or plain email, and then attach GitHub under Settings → Linked accounts → Connect. Signing up with GitHub and linking GitHub are separate things. Only take
  this route if you want the automation.

  Route A, step by step

  Create the Zenodo account with ORCID or email if you don't have one. Then:

  1. Get the artifact. Done already: the v0.5.0 release page carries both
  dist/pyvoa-0.5.0.tar.gz (the sdist, the thing PyPI serves — prefer this one) and GitHub's own
  auto-generated source tarball. Either is fine; they are also still in dist/ locally.

  2. Zenodo → New upload, drop the tarball in.
  3. Fill the metadata, straight out of CITATION.cff so the two agree — JOSS editors do check this:

  - Resource type: Software
  - Title: pyvoa: Python Virus Open Analysis
  - Creators: Beau, Browaeys, Dadoun — each with their ORCID and affiliation (CITATION.cff:29-46)
  - Description: the abstract block, CITATION.cff:9-16
  - License: MIT
  - Version: 0.5.0
  - Keywords: the eight from CITATION.cff:48-56
  - Related works: "is supplement to" → https://github.com/pyvoa/pyvoa (this is what the integration sets)

  4. Publish. The record page then shows both DOIs; the concept one sits under "Cite all versions" and is the lower number. That's the one for CITATION.cff:62, along with the
  real release date on line 19, which is already correct.
  5. For 0.5.1 and later: open the record → New version → upload the new tarball → publish. The concept DOI carries over unchanged, which is the whole point of it.

  One caveat on the "Reserve DOI" button in the upload form: it reserves the version DOI so you can bake it into the files before publishing. It does not give you the concept
  DOI early — that only exists after the first publish. So the order stays: publish, then patch CITATION.cff.


Deferred deliberately, not forgotten:

- `ruff format` is **not** run: the tree is not format-clean (22 files) and CI
  does not check it. `CONTRIBUTING.md` §4 no longer claims otherwise, and §5
  now tells contributors to match the surrounding style. Adopting a formatter
  is a separate decision with a large, purely cosmetic diff.
- No `PULL_REQUEST_TEMPLATE.md`: the checklist stays in `CONTRIBUTING.md` §4.

## Task 6 — README and documentation

- The `README.md` install section still points at the pycoa wiki
  (`github.com/coa-project/pycoa/wiki/Installation`); replace with current
  instructions.
- Add: minimal usage example, list of supported databases, link to `examples/`,
  licence, citation, community files.

## Out of scope for this session

The JOSS `paper.md` and `paper.bib` — drafted separately.
