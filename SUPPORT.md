# Getting help with pyvoa

pyvoa is developed and maintained by a small team of academics, on top of their
teaching and research duties. There is no support contract and no guaranteed
response time — but questions are genuinely welcome, including beginner ones.
Explaining is part of the purpose of this project.

## Where to ask

| You want to… | Go to |
|---|---|
| Ask how to do something with pyvoa | [GitHub Discussions](https://github.com/pyvoa/pyvoa/discussions) |
| Report a bug or unexpected output | [Open an issue](https://github.com/pyvoa/pyvoa/issues/new/choose) |
| Propose a new database | [Open an issue](https://github.com/pyvoa/pyvoa/issues/new/choose) — before writing code |
| Report a security or privacy concern | <contact@pyvoa.org> — please do not open a public issue |
| Reach the maintainers about anything else | <contact@pyvoa.org> |

Please search the [existing issues](https://github.com/pyvoa/pyvoa/issues) and
[discussions](https://github.com/pyvoa/pyvoa/discussions) first: data-source
problems in particular tend to affect everyone at once and are often already
reported.

## Before you report a bug

pyvoa reads data from about two dozen third-party providers. Those providers
change their file formats, column names and URLs without notice, and they
sometimes go offline. **A large share of the problems reported against pyvoa are
data-side, not code-side.** Three checks take a minute and save everyone time:

1. **Try another database.** If `setwhom('owid')` works and `setwhom('jhu')`
   does not, the problem is likely upstream of pyvoa.
2. **Clear the cache and retry.** Downloads are cached under
   `~/.cache/pyvoa.data_<username>/`; a truncated or stale file can produce
   confusing errors. Delete the relevant file, or the whole directory, and run
   again.
3. **Switch between the archived and the live data.** pyvoa reads a frozen
   Zenodo archive by default; `pf.setlive(True)` reads the providers' current
   files instead, `pf.setlive(False)` goes back, and `pf.getlive()` says which
   is in use. Call `setwhom()` again after switching. A problem with the live
   data only is most likely a change upstream.

If the problem survives all three, it is worth an issue.

## What to include

The issue form asks for these, and they are what makes a report actionable
(see also [CONTRIBUTING.md §2](CONTRIBUTING.md#2-reporting-a-bug)):

1. **Versions** — pyvoa, Python and the operating system. `pf.getversion()`
   gives the exact pyvoa you run, however it was installed, so please use it
   rather than `pyvoa.__version__`, which stays the same between two releases.
   In a notebook or a script:

   ```python
   import platform, sys
   import pyvoa.front as pf
   print(pf.getversion(), sys.version, platform.platform())
   ```

   or from a terminal, pasting the last line of the output (the lines before
   it are pyvoa's welcome banner):

   ```bash
   python -c "import platform, sys, pyvoa.front as pf; print(pf.getversion(), sys.version, platform.platform())"
   ```

   The version reads `v0.5.0` for a release, `v0.5.0-g512aefe` for a copy
   installed from GitHub (`pip install git+https://…`, at commit `512aefe`),
   and `v0.5.0-484-g512aefe` for a clone of the repository: 484 commits after
   0.5.0, at commit `512aefe`, followed by `-dirty` if the clone holds local
   changes.
2. **A minimal reproducible example** — the shortest snippet that triggers the
   problem, including the database (`setwhom`) and the visualisation backend
   (`setvis`).
3. **Expected result, observed result, and the full traceback.** Turning the
   verbosity up to debug first usually makes the cause visible:

   ```python
   import pyvoa.front as pf
   pf.set_verbose_mode(2)   # 0 = silent, 1 = info, 2 = debug
   ```
4. **The date you ran it**, since the upstream data changes from day to day.

## Documentation

- <https://pyvoa.github.io/pyvoa/> — the API documentation: every public
  function, its keywords and examples, built from the docstrings of the
  current `main`.
- [README.md](README.md) — installation, a first example, and the table of
  supported databases.
- [`examples/`](examples/) — Jupyter notebooks covering the common workflows,
  starting with `notebooks/PyvoaForBeginners.ipynb`, plus the same workflows as
  plain scripts under `pyfiles/`.
- <https://pyvoa.org> — project website.

## Contributing

If you would like to fix the problem yourself, or add a data source, see
[CONTRIBUTING.md](CONTRIBUTING.md). All participation is covered by our
[Code of Conduct](CODE_OF_CONDUCT.md).
