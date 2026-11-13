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

[SUPPORT.md](SUPPORT.md) describes these channels in more detail, and lists the
[checks worth running before reporting a bug](SUPPORT.md#before-you-report-a-bug).
Please search the
[existing issues](https://github.com/pyvoa/pyvoa/issues) before opening a new
one.

## 2. Reporting a bug

The [bug report form](https://github.com/pyvoa/pyvoa/issues/new/choose) asks for
each of the items below. A useful report contains:

1. the pyvoa version as `pf.getversion()` gives it — the release, or the
   commit for a copy installed from GitHub or a clone — the Python version and
   the operating system ([SUPPORT.md](SUPPORT.md#what-to-include) gives the
   code);
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

Line by line:

1. `git clone …` downloads the repository, with its whole history, into a new
   `pyvoa/` directory. If you mean to submit a change, clone your own fork
   instead (see §4).
2. `cd pyvoa` moves into that directory; the remaining commands are run from it.
3. `python -m venv .venv` creates a *virtual environment*, a private copy of
   Python in `.venv/`, so that pyvoa and its dependencies are installed apart
   from the system Python and from your other projects. `source
   .venv/bin/activate` (or `.venv\Scripts\activate` on Windows) switches the
   current shell to it: `python` and `pip` now refer to that environment until
   you run `deactivate` or close the shell. Activate it again in every new
   shell.
4. `python -m pip install --upgrade pip` updates pip itself inside the
   environment; the copy `venv` provides can be too old to install a project
   described by `pyproject.toml` alone, as pyvoa is.
5. `python -m pip install -e ".[dev]"` installs pyvoa from the current
   directory (`.`) together with its dependencies. `-e` (*editable*) links the
   environment to your working tree instead of copying the package, so a change
   to a file of `pyvoa/` takes effect at the next `import` without
   reinstalling. `[dev]` adds the optional group of development tools declared
   in `pyproject.toml`. The quotes keep shells such as zsh from reading the
   brackets as a filename pattern.

Writing `python -m pip` rather than `pip` makes sure the pip that runs belongs
to the `python` you are using, i.e. to the activated environment.

The `dev` extra installs the tools the continuous integration uses, so that the
checks below run exactly as they do on a pull request, and you know before
opening one whether it will pass:

- **pytest** runs the test suite (`pytest`; see §4 for what it selects).
- **pytest-cov** measures how much of the code the tests cover; CI uses it for
  the coverage report written to the job summary and the `coverage.xml`
  artefact.
- **ruff** checks the style and the NumPy-convention docstrings
  (`ruff check .`). Its version is pinned, as in the CI workflow, because a new
  ruff release widens its default rule set and would start failing the check
  without any change to the code.
- **tomli** is installed on Python 3.10 only, whose standard library lacks
  `tomllib`. `tests/test_paper.py` needs it to read `pyproject.toml` and check
  the manuscript against the declared dependencies; without it those tests
  would be skipped silently.
- **nodejs-wheel-binaries** ships a node executable. `tests/test_js.py` uses it
  to run the bokeh callbacks of `pyvoa/js/` and check that they compute the
  same thing as their Python counterparts, without depending on a node
  installed on the machine.

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
4. **Run the checks locally** before pushing. Both tools come with the `dev`
   extra installed in §3 (into `.venv/bin/`, or `.venv\Scripts\` on Windows),
   so run them from a shell where that environment is activated:

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

5. **Write a clear commit message.** The subject line names the part of the
   project the commit touches — a module, a database, `docs`, `tests`,
   `examples`, `paper` — then says what the commit does, in the present tense:
   `sumeau: read from Odissé, the archive refreshed to October 2026`, or
   `get: carry values forward only`. A bug fix may say `fix:` instead
   (`fix: sumall with normalize hands out the normalised sum`). The body
   explains why, in full sentences.
6. **Open a pull request** against `main`, describing *what* changes and *why*,
   and linking the related issue (`Closes #42`).
7. Add an entry to `CHANGELOG.md` under the *Unreleased* heading at the top of
   the file, in the style of the entries already there: one bullet per
   user-visible change, written for someone upgrading rather than for someone
   reading the diff, and prefixed with `fix:` when it is a bug fix. The file
   predates these guidelines and does not follow *Keep a Changelog*: entries go
   under `## Unreleased`, grouped by theme as in the entries already there, and
   each release becomes a dated `## X.Y.Z — YYYY-MM-DD` section (see §9).

A maintainer will review the pull request. Review comments are about the code,
never about the person; see the [Code of Conduct](CODE_OF_CONDUCT.md).

### Pull request checklist

- [ ] Tests added or updated, and the suite passes.
- [ ] New tests run offline, using a fixture rather than a live download.
- [ ] Public functions carry a docstring following the NumPy convention (§5),
      and `ruff check .` reports no findings.
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

1. be **publicly accessible**, with a stable URL, and **openly licensed** — or
   at least reusable with attribution for non-commercial purposes, as `imed`
   (CC BY-NC 4.0) is. The licence goes in the README table, whatever it is. A
   provider who asks to be consulted before any republication can be read live
   but not mirrored on Zenodo, as `ebolardc` is;
2. be documented in the pull request: provider, licence, update frequency,
   geographical granularity, known caveats;
3. expose geographical entities resolvable by the geolocation layer (ISO 3166
   codes wherever possible);
4. come with tests that do not depend on network availability (use a small
   fixture file rather than a live download);
5. be added to the table of supported databases in `README.md`, with its
   source, licence and availability, and the count announced above the table
   updated: `tests/test_readme.py` checks both against `pyvoa/data/`. The
   database itself appears in `pf.listwhom()` as soon as its JSON description
   is in `pyvoa/data/`.

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

1. In `CHANGELOG.md`, turn the `## Unreleased` heading into
   `## X.Y.Z — YYYY-MM-DD` and open a new, empty `## Unreleased` above it;
   update the version number in `pyvoa/__version__.py` — the single source
   of truth, from which `pyproject.toml` reads it dynamically — and rows C1,
   S1 and S2 of `paper/main.tex`, which `tests/test_paper.py` checks against it.
2. Reserve the version DOI: open a new version of the latest pyvoa record on
   Zenodo (concept DOI `10.5281/zenodo.21829901`) and reserve its DOI, without
   publishing. No GitHub-Zenodo hook is installed: the deposit is made by hand.
3. Update `version`, `date-released` and the version DOI in `CITATION.cff`,
   `version` and `datePublished` in `codemeta.json` and `schemaorg.jsonld`,
   the archived release in row C2 of `paper/main.tex`, and the version in the
   title and the version DOI — not the concept DOI, which follows the latest
   release — of the `pyvoa_github` entry of `paper/references.bib`; check
   `CITATION.cff` with `pipx run cffconvert --validate`. Run it through
   `pipx` (or `uvx`): cffconvert requires `jsonschema<4` and will downgrade it
   in a shared environment. Commit, push, and wait for CI to pass.
4. Build the sdist and the wheel from that commit (`python -m build`), check
   them with `twine check`, and make sure the wheel holds `pyvoa/js/` and
   `pyvoa/data/`.
5. Tag the release, annotated so that Software Heritage gives it a
   `swh:1:rel:` identifier: `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin
   vX.Y.Z`; then publish a GitHub release for the tag, its notes taken from the
   changelog.
6. Publish the sdist and the wheel on PyPI.
7. Upload the same two files to the Zenodo draft, its metadata taken from
   `.zenodo.json` (creators, keywords, funding, related identifiers, the
   `isSupplementTo` link pointing at the tag), and publish it.
8. Ask Software Heritage to "Save code now" `https://github.com/pyvoa/pyvoa`,
   read the `swh:1:rel:` of the new tag from the latest visit's snapshot, and
   put it in `CITATION.cff`, in row C2 of `paper/main.tex` and in the
   `pyvoa_github` entry of `paper/references.bib`.
9. Whenever a new version of the code or of the paper is submitted, check
   the archives themselves, not only the files that cite them:
   - the version DOI resolves to a *published* Zenodo record of this version,
     and the concept DOI `10.5281/zenodo.21829901` now resolves to it;
   - the two files of that record are byte for byte those of PyPI (same size,
     same md5: `https://zenodo.org/api/records/<id>` and
     `https://pypi.org/pypi/pyvoa/X.Y.Z/json`);
   - the `swh:1:rel:` identifier exists
     (`https://archive.softwareheritage.org/api/1/release/<hash>/`), is named
     `vX.Y.Z`, and is the annotated tag itself — `git rev-parse vX.Y.Z` prints
     the same hash, its target being `git rev-parse vX.Y.Z^{}`;
   - every file carries the same identifiers: rows C1, C2, S1 and S2 of
     `paper/main.tex`, the `pyvoa_github` entry of `paper/references.bib`,
     `CITATION.cff`, `codemeta.json`, `schemaorg.jsonld`, `README.md`.
