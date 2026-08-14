# The pyvoa software paper

The manuscript submitted to *SoftwareX* (Elsevier, ISSN 2352-7110), article type
*Original Software Publication*.

    paper/
    ├── README.md          this file
    ├── Makefile           make draft | make final | make figures | make clean
    ├── main.tex           the manuscript
    └── figures/           artwork: architecture.png is drawn, the rest produced

The listings and the examples are not duplicated here. They live where the rest
of the examples live, and the manuscript refers to them:

    examples/notebooks/PaperExamples.ipynb    the four listings, in order
    examples/pyfiles/paper_examples.py        the same, headless, plus --check

`make figures` runs that script; it writes every figure except
`architecture.png` (a drawing, not an output) straight into `figures/`, under
the names the .tex includes. Re-run it after any release, and after any change
to a listing.

## Why the manuscript is in this repository

Every factual claim the paper makes about pyvoa is derived from the code next to
it: the version in metadata C1, the database count in the abstract, the Python
floor and the dependency list in C7, the databases and the front-end calls the
listings use, the funding sentence `AUTHORS` requires, the title
`CITATION.cff` will cite. All of them drift silently when the code moves, and
all of them are checked by a reviewer in minutes.

`tests/test_paper.py` checks them on every push instead. It reads files only —
no import of the geospatial stack, no network — so it runs inside the existing
offline job and adds no dependency and no CI configuration. It skips itself when
`paper/main.tex` is absent, so a checkout without the manuscript is not a
failing checkout.

The second reason is ordinary: the manuscript then has the same history, the
same review path and the same tags as the software it describes. `v0.5.0` and
the text that describes `v0.5.0` are one commit away from each other.

## Building

    make draft     # with the editorial annotations, in red
    make final     # without them — the file to submit
    make clean

`make` needs a TeX distribution with `elsarticle` (TeX Live:
`texlive-publishers`; on a distribution that does not package it, the CTAN
source builds the class with `tex elsarticle.ins` and drops into
`~/texmf/tex/latex/elsarticle/`). `latexmk` is used when it is installed
(`texlive-extra-utils`) and three `pdflatex` passes otherwise — the
bibliography is a manual `thebibliography`, so there is no bibtex step.

The annotations are switched by a single toggle at the top of `main.tex`; the
Makefile sets it, nothing else differs between the two builds.

The class is `preprint,12pt,a4paper`, which is a reading layout, not the
published one: `make final` currently gives 13 pages. Recompiled with
`final,5p,times,twocolumn` — Elsevier's own two-column layout — the same source
is 6 pages including the metadata tables and the references, which is how the
6-page limit on sections 1-5 should be judged.

## Two things to be aware of

**Licence.** The repository's `LICENSE` is MIT, which is a software licence and
does not sensibly apply to a manuscript. The text in `main.tex` is *not* covered
by it. Until the article is published, treat it as © the authors, all rights
reserved; once published, SoftwareX articles are open access under CC BY, and
this file should then say so explicitly.

Elsevier permits preprints to be posted before and during review — a public
repository is a preprint server like any other — but the sharing terms for the
accepted and published versions differ from those for the submitted one. Check
the current policy at
<https://www.elsevier.com/about/policies/sharing> before replacing this file
with the accepted manuscript.

**The annotations are public.** `main.tex` carries editorial notes wrapped in
`\attn` and `\attnpar`, including a candid assessment of where the paper is
weak. They are invisible in `make final`, but anyone can read the source, and a
reviewer who follows the repository link in metadata C2 will land here.

That is a deliberate trade, and the same one `HANDOFF.md` already makes. If it
is judged too candid for the review period, the remedy is to move the notes into
`paper/notes.tex`, `\input` it under the same toggle, and gitignore that one
file — at the cost of the notes no longer sitting next to what they annotate.
Decide once, before submission.
