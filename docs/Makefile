# Minimal makefile for Sphinx documentation.
#
# -W turns warnings into errors, so a docstring that stops rendering fails the
# build rather than degrading it quietly; --keep-going reports every warning
# instead of stopping at the first.
SPHINXOPTS    ?= -W --keep-going
SPHINXBUILD   ?= python3 -m sphinx
SOURCEDIR     = .
BUILDDIR      = _build

# `html`, `linkcheck` and the rest are served by the match-anything rule at the
# bottom; a match-anything rule is not applied to a target declared .PHONY, so
# only `help` and `clean` are listed here.
.PHONY: help clean Makefile

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -rf "$(BUILDDIR)"

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
