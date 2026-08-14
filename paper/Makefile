# Build the pyvoa software paper.
#
#   make draft   manuscript with the editorial annotations, in red
#   make final   manuscript without them: the file to submit
#   make figures re-run the examples that produce figures/
#   make check   run the paper/code consistency tests alone
#   make clean   remove build artefacts, keep the PDFs
#
# Needs a TeX distribution carrying elsarticle (TeX Live: texlive-publishers).
# latexmk is used when present (texlive-extra-utils), pdflatex otherwise.

LATEXMK ?= latexmk
PDFLATEX ?= pdflatex
PYTHON  ?= python3
MAIN     = main.tex

# latexmk is not in every TeX installation (Debian/Ubuntu ship it in
# texlive-extra-utils, separately from the class itself). Fall back to three
# pdflatex passes, which is what latexmk would run here: the bibliography is a
# manual thebibliography, so there is no bibtex step to get right.
HAVE_LATEXMK := $(shell command -v $(LATEXMK) 2>/dev/null)

.PHONY: all draft final check clean distclean

all: draft

draft:
ifdef HAVE_LATEXMK
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error $(MAIN)
else
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error $(MAIN)
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error $(MAIN)
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error $(MAIN)
endif
	@mv -f main.pdf pyvoa-softwarex-draft.pdf
	@echo "-> paper/pyvoa-softwarex-draft.pdf (annotations shown)"

# The toggle is the only difference between the two builds: it is set on the
# command line rather than by editing main.tex, so the submitted PDF and the
# annotated one are provably the same source.
final:
ifdef HAVE_LATEXMK
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error \
	  -pretex='\def\paperfinal{1}' -usepretex $(MAIN)
else
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error "\def\paperfinal{1}\input{$(MAIN)}"
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error "\def\paperfinal{1}\input{$(MAIN)}"
	$(PDFLATEX) -interaction=nonstopmode -halt-on-error "\def\paperfinal{1}\input{$(MAIN)}"
endif
	@mv -f main.pdf pyvoa-softwarex.pdf
	@echo "-> paper/pyvoa-softwarex.pdf (submit this one)"
	@echo "   check it: no red, and sections 1-5 within 6 pages."

check:
	cd .. && $(PYTHON) -m pytest tests/test_paper.py -v

# The figures are produced, not drawn: this is the command that makes every one
# of them, and the only one that keeps them in step with the listings.
figures:
	cd ../examples/pyfiles && $(PYTHON) paper_examples.py

clean:
ifdef HAVE_LATEXMK
	$(LATEXMK) -c $(MAIN)
else
	@rm -f main.aux main.log main.out main.fdb_latexmk main.fls main.spl
endif
	@rm -f main.bbl main.run.xml

distclean: clean
	@rm -f pyvoa-softwarex.pdf pyvoa-softwarex-draft.pdf
