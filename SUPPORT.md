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
data-side, not code-side.** Two checks take a minute and save everyone time:

1. **Try another database.** If `setwhom('owid')` works and `setwhom('jhu')`
   does not, the problem is likely upstream of pyvoa.
2. **Clear the cache and retry.** Downloads are cached under
   `~/.cache/pyvoa.data_<username>/`; a truncated or stale file can produce
   confusing errors. Delete the relevant file, or the whole directory, and run
   again.

If the problem survives both, it is worth an issue.

## What to include

The issue form asks for these, and they are what makes a report actionable
(see also [CONTRIBUTING.md §2](CONTRIBUTING.md#2-reporting-a-bug)):

1. **Versions** — pyvoa (`python -c "import pyvoa; print(pyvoa.__version__)"`),
   Python, and the operating system.
2. **A minimal reproducible example** — the shortest snippet that triggers the
   problem, including the database (`setwhom`) and the visualisation backend
   (`setvis`).
3. **Expected result, observed result, and the full traceback.** Turning the
   verbosity up to debug first usually makes the cause visible:

   ```python
   from pyvoa.tools import set_verbose_mode
   set_verbose_mode(2)   # 0 = silent, 1 = info, 2 = debug
   ```
4. **The date you ran it**, since the upstream data changes from day to day.

## Documentation

- [README.md](README.md) — installation and a first example.
- [`examples/`](examples/) — Jupyter notebooks covering the common workflows.
- <https://pyvoa.org> — project website.

## Contributing

If you would like to fix the problem yourself, or add a data source, see
[CONTRIBUTING.md](CONTRIBUTING.md). All participation is covered by our
[Code of Conduct](CODE_OF_CONDUCT.md).
