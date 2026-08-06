# Handoff — pyvoa publication readiness

Context brief for an agent session run at the root of https://github.com/pyvoa/pyvoa.
Goal: bring the repository to the state expected by a JOSS software-paper review.
Reference checklist: https://joss.readthedocs.io/en/latest/review_checklist.html

Files already drafted and downloaded into the repository root (do not rewrite from
scratch, review and integrate): `AUTHORS`, `CITATION.cff`, `CONTRIBUTING.md`,
`CODE_OF_CONDUCT.md`, `SUPPORT.md`, `pyproject.toml`, `tests/test_tools.py`,
`.github/workflows/ci.yml`, `.github/ISSUE_TEMPLATE/config.yml`.

Work on a branch, one commit per task, and open a single pull request.

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

- [ ] **Enable GitHub Discussions** (Settings → General → Features). Until then,
      the Discussions links in `README.md`, `SUPPORT.md`, `CONTRIBUTING.md` §1
      and `.github/ISSUE_TEMPLATE/config.yml` all 404.
- [ ] **Create the issue labels** used by the forms, or they are silently
      dropped: `bug`, `enhancement`, `new database`, `data`.
- [ ] **Confirm O. Dadoun's ORCID** — `0000-0002-2169-9725` in `AUTHORS` and
      `CITATION.cff`, unverified.
- [ ] **Confirm the mail domain** — `@u-pariscite.fr` for T. Beau and
      J. Browaeys; the institution also uses `@u-paris.fr`.
- [ ] **Mint the Zenodo concept DOI**, then replace the
      `10.5281/zenodo.0000000` placeholder in `CITATION.cff` and set
      `date-released` (currently the `2026-01-01` placeholder) to the date of
      the matching tagged release.
- [ ] **Check the rendered forms** once merged, at
      `https://github.com/pyvoa/pyvoa/issues/new/choose` — issue-form schema
      errors only surface on GitHub, not locally.

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
