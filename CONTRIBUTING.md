# Contributing to pyvoa

Thank you for your interest in [pyvoa](https://pyvoa.org) (*Python Virus Open
Analysis*). Contributions of every kind are welcome: bug reports, documentation,
new data sources, tests, teaching material, translations and code.

This document explains how to report problems, how to get support, and how to
submit changes. By participating in this project you agree to abide by our
[Code of Conduct](CODE_OF_CONDUCT.md).

---

## 1. Getting support

| Need | Where to go |
|---|---|
| A question about how to use pyvoa | [GitHub Discussions](https://github.com/pyvoa/pyvoa/discussions) or <contact@pyvoa.org> |
| A bug or unexpected behaviour | [Open an issue](https://github.com/pyvoa/pyvoa/issues/new/choose) |
| A new feature or a new database | Open an issue **before** writing code, so that the design can be discussed |
| A security or confidentiality concern | <contact@pyvoa.org> (please do not open a public issue) |

[SUPPORT.md](SUPPORT.md) describes these channels in more detail, and lists two
checks worth running before reporting a bug. Please search the
[existing issues](https://github.com/pyvoa/pyvoa/issues) before opening a new
one.

## 2. Reporting a bug

The [bug report form](https://github.com/pyvoa/pyvoa/issues/new/choose) asks for
each of the items below. A useful report contains:

1. the pyvoa version, the Python version and the operating system;
2. a **minimal reproducible example** — the shortest snippet that triggers the
   problem, including the database (`setwhom`) and the visualisation backend
   (`setvis`) used;
3. the expected result and the observed result, with the full traceback;
4. the date of execution, since upstream data providers change their files
   without notice — many issues are data-side rather than code-side.

## 3. Development setup

```bash
git clone https://github.com/pyvoa/pyvoa.git
cd pyvoa
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"     # editable install, with the test tools
```

The `dev` extra pulls in pytest and the pinned ruff used by CI, so the checks
below run exactly as they do on a pull request.

pyvoa requires Python >= 3.10 and is designed to run inside a
[Jupyter](https://jupyter.org/) environment, locally or on a remote server
(Google Colab, Binder). Please check that your change also works in a notebook,
using the examples in `examples/`.

## 4. Submitting a change

1. **Fork** the repository and create a topic branch from `main`:
   `git switch -c fix/owid-parser-encoding`.
   Suggested prefixes: `feat/`, `fix/`, `docs/`, `test/`, `refactor/`.
2. **Keep the change focused.** One pull request, one concern.
3. **Add tests** covering the new behaviour or the fixed bug.
4. **Run the checks locally** before pushing:

   ```bash
   pytest                 # test suite (offline; this is what CI runs)
   ruff check .           # linting; must report no findings
   ```

   The default selection is **offline by design**: `tests/conftest.py` makes any
   socket creation fail unless a test is marked `@pytest.mark.network`, so a
   test can never quietly start depending on an upstream server. Those marked
   tests are deselected by default; run them with `pytest -m network` if your
   change touches downloading or parsing, keeping in mind that they fail when a
   provider is down rather than when your code is wrong.

5. **Write a clear commit message.** We follow
   [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), e.g.
   `fix(dbparser): handle empty ISO-3166 field in OWID dataset`.
6. **Open a pull request** against `main`, describing *what* changes and *why*,
   and linking the related issue (`Closes #42`).
7. Add an entry to `CHANGELOG.md` under the *Unreleased* heading at the top of
   the file, in the style of the entries already there: one bullet per
   user-visible change, written for someone upgrading rather than for someone
   reading the diff, and prefixed with `fix:` when it is a bug fix. The file
   predates this project and does not follow *Keep a Changelog*; please match
   the surrounding entries rather than introducing a new structure.

A maintainer will review the pull request. Review comments are about the code,
never about the person; see the [Code of Conduct](CODE_OF_CONDUCT.md).

### Pull request checklist

- [ ] Tests added or updated, and the suite passes.
- [ ] New tests run offline, using a fixture rather than a live download.
- [ ] Public functions carry a docstring ([PEP 257](https://peps.python.org/pep-0257/)).
- [ ] User-facing documentation and notebook examples updated if relevant.
- [ ] `CHANGELOG.md` updated.
- [ ] The change is compatible with the supported Python versions.

## 5. Coding conventions

- Follow [PEP 8](https://peps.python.org/pep-0008/); linting is enforced in CI
  with [ruff](https://docs.astral.sh/ruff/), whose configuration and its
  deliberate exceptions are documented in `[tool.ruff]` in `pyproject.toml`.
  Formatting is *not* enforced: the existing code predates any formatter, so
  please match the style of the file you are editing rather than reformatting
  it, and keep formatting changes out of functional pull requests.
- Use explicit, English identifiers; keep the public API stable and documented.
- Docstrings follow the [NumPy
  convention](https://numpydoc.readthedocs.io/en/latest/format.html), enforced
  by ruff's `D` rules with `convention = "numpy"`: a one-line summary in the
  imperative mood ("Return the parsed frame.", not "Returns the parsed
  frame."), a blank line, then the prose and the underlined sections
  (`Parameters`, `Returns`, `Raises`). Every function and class in `pyvoa/`
  carries one, and `ruff check .` fails on a docstring that does not.
  A method whose public signature is produced by decorators — `get`, `plot`,
  `hist` and `map` in `front.py` — is documented on its innermost definition,
  because `functools.wraps` is what carries that docstring out to the caller.
- Type hints are encouraged on new or refactored code
  ([PEP 484](https://peps.python.org/pep-0484/)).
- Every new dependency must be justified in the pull request: pyvoa is meant to
  install cleanly in constrained environments such as school computers and free
  notebook services.

## 6. Adding a new database

pyvoa's value lies in exposing heterogeneous sources through a single
standardised interface. A new data provider should:

1. be **openly licensed and publicly accessible**, with a stable URL;
2. be documented in the pull request: provider, licence, update frequency,
   geographical granularity, known caveats;
3. expose geographical entities resolvable by the geolocation layer (ISO 3166
   codes wherever possible);
4. come with tests that do not depend on network availability (use a small
   fixture file rather than a live download);
5. be added to the table of supported databases in `README.md`, so that it is
   listed alongside the others and appears in `pf.listwhom()`.

## 7. Documentation and teaching material

Documentation contributions are as valuable as code: website, docstrings, and
the example notebooks under `examples/`. Please clear notebook outputs before
committing, unless the output is the point of the example.

## 8. Licence and authorship

- By contributing, you agree that your contribution is licensed under the
  [MIT License](LICENSE), like the rest of the project.
- All contributors are acknowledged in `CONTRIBUTORS.md`.
- The `AUTHORS` file lists the **authors of the software**, i.e. people who have
  made a substantial and sustained intellectual contribution to its design,
  implementation or scientific direction. We follow the
  [JOSS authorship policy](https://joss.readthedocs.io/en/latest/submitting.html#authorship)
  as our reference standard for this, whatever the venue a given paper is
  submitted to:
  purely financial or purely supervisory contributions do not qualify, whereas
  active project direction and non-code contributions do. Contributions are
  described with the [CRediT taxonomy](https://credit.niso.org/). Additions to
  `AUTHORS` are made by pull request and require the agreement of the current
  maintainers and of the person being listed.

## 9. Releases (maintainers)

1. Update `CHANGELOG.md` and the version number in `pyvoa/__version__.py` — the
   single source of truth, from which `pyproject.toml` reads it dynamically.
2. Tag the release: `git tag -a v0.4.3 -m "v0.4.3" && git push --tags`.
3. Publish on PyPI; check that the GitHub-Zenodo hook has minted a version DOI
   and that the Zenodo metadata (title, author list, ORCID) matches
   `CITATION.cff`.
4. Update `version`, `date-released` and the DOI in `CITATION.cff`, then check it
   with `pipx run cffconvert --validate`. Run it through `pipx` (or `uvx`):
   cffconvert requires `jsonschema<4` and will downgrade it in a shared
   environment.
