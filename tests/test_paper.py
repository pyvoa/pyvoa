"""Consistency between the software paper and the code it describes.

The manuscript in ``paper/`` states facts that are derived from this repository:
the version number, how many databases ship, which Python it needs, which
dependencies it declares, which front-end calls and which databases the
listings use. Every one of those drifts silently the moment the code moves,
and a reviewer checks them in minutes.

These tests read files only — no import of the heavy stack, no network — so
they run in the default offline job alongside the rest of the suite. They skip
themselves entirely when ``paper/main.tex`` is absent, so a checkout without
the manuscript is not a failing checkout.

The SoftwareX limits enforced at the end come from the guide for authors:
https://www.elsevier.com/journals/softwarex/23527110/guide-for-authors
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "main.tex"

pytestmark = pytest.mark.skipif(
    not PAPER.exists(), reason="no manuscript in paper/, nothing to check"
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tex() -> str:
    return PAPER.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def body(tex: str) -> str:
    """The manuscript with the draft annotations removed.

    Annotations are French editorial notes wrapped in ``\\attn`` / ``\\attnpar``
    and are not part of the submitted text; they must not be searched for
    claims, nor counted in the word budget.
    """
    out = tex
    for macro in (r"\\attnpar", r"\\attn"):
        out = _strip_macro(out, macro)
    return out


def _strip_macro(text: str, macro: str) -> str:
    """Remove ``macro{...}`` occurrences, honouring nested braces."""
    out = []
    i = 0
    pattern = re.compile(macro + r"\{")
    while True:
        m = pattern.search(text, i)
        if m is None:
            out.append(text[i:])
            return "".join(out)
        out.append(text[i : m.start()])
        depth, j = 1, m.end()
        while j < len(text) and depth:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        i = j


@pytest.fixture(scope="module")
def listings(tex: str) -> list[str]:
    found = re.findall(
        r"\\begin\{lstlisting\}\[style=python\](.*?)\\end\{lstlisting\}", tex, re.DOTALL
    )
    assert found, "the manuscript has no Python listing; expected at least four"
    return found


@pytest.fixture(scope="module")
def pyproject() -> dict:
    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover - only on the oldest supported interpreter
        pytest.importorskip("tomli")
        import tomli as tomllib  # type: ignore[no-redef]
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# the numbers the manuscript asserts
# ---------------------------------------------------------------------------


def test_version_matches_the_package(tex: str) -> None:
    """C1 and S1 must name the version this checkout actually is."""
    # Read rather than import: pyvoa/__version__.py is the single source of
    # truth (pyproject reads it dynamically), and parsing it keeps this test
    # free of the geospatial stack.
    source = (ROOT / "pyvoa" / "__version__.py").read_text(encoding="utf-8")
    m = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)", source, re.MULTILINE)
    assert m, "cannot read __version__ from pyvoa/__version__.py"
    version = m.group(1)

    for field in ("C1", "S1"):
        row = _metadata_row(tex, field)
        assert version in row, (
            f"metadata {field} does not mention version {version}: {row!r}"
        )


def test_database_count_matches_the_catalogue(body: str) -> None:
    """The count claimed in the abstract and the text is len(pyvoa/data/*.json)."""
    shipped = len(list((ROOT / "pyvoa" / "data").glob("*.json")))

    claims = re.findall(r"(\d+)\s+(?:open\s+)?(?:epidemiological\s+)?databases", body)
    claims += re.findall(r"``Sources'':|\\textbf\{pyvoa\}\s*&[^&]*&\s*(\d+)", body)
    numeric = {int(c) for c in claims if c.isdigit()}
    assert numeric, "no numeric database count found in the manuscript"
    assert numeric == {shipped}, (
        f"manuscript claims {sorted(numeric)} databases, pyvoa/data/ ships {shipped}"
    )

    # The word form used in the running text must agree with the digits.
    words = {
        "twelve": 12, "thirteen": 13, "twenty": 20, "twenty-one": 21,
        "twenty-two": 22, "twenty-three": 23, "twenty-four": 24,
        "twenty-five": 25, "thirty": 30,
    }
    for word, value in words.items():
        if re.search(rf"\b{word}\s+databases\b", body, re.IGNORECASE):
            assert value == shipped, (
                f"manuscript spells out '{word} databases', "
                f"pyvoa/data/ ships {shipped}"
            )


def test_python_floor_matches_pyproject(tex: str, pyproject: dict) -> None:
    declared = pyproject["project"]["requires-python"]          # e.g. '>=3.10'
    floor = declared.lstrip(">=~^ ")
    row = _metadata_row(tex, "C7")
    assert floor in row, (
        f"metadata C7 does not state Python {floor} (pyproject says {declared!r})"
    )


def test_declared_dependencies_are_all_listed(tex: str, pyproject: dict) -> None:
    """SoftwareX asks for the dependency requirements; C7 must not omit one."""
    row = _metadata_row(tex, "C7").lower()
    missing = []
    for spec in pyproject["project"]["dependencies"]:
        name = re.split(r"[<>=!~\[; ]", spec, maxsplit=1)[0].strip().lower()
        # a dependency may be written with either separator in prose
        if name not in row and name.replace("_", "-") not in row:
            missing.append(name)
    assert not missing, f"metadata C7 omits declared dependencies: {missing}"


# ---------------------------------------------------------------------------
# the listings
# ---------------------------------------------------------------------------


def test_listings_use_existing_databases(listings: list[str]) -> None:
    catalogue = {p.stem for p in (ROOT / "pyvoa" / "data").glob("*.json")}
    used = set()
    for listing in listings:
        used |= set(re.findall(r"setwhom\(\s*'([^']+)'", listing))
    assert used, "no setwhom() call found in the listings"
    unknown = used - catalogue
    assert not unknown, (
        f"listings select databases absent from pyvoa/data/: {sorted(unknown)}"
    )


def test_listings_use_existing_front_functions(listings: list[str]) -> None:
    """Guards against an API renamed under the manuscript's feet."""
    front = (ROOT / "pyvoa" / "front.py").read_text(encoding="utf-8")
    defined = set(re.findall(r"^\s*def\s+(\w+)", front, re.MULTILINE))
    defined |= set(re.findall(r"^(\w+)\s*=", front, re.MULTILINE))     # module-level aliases

    called = set()
    for listing in listings:
        called |= set(re.findall(r"\bpf\.(\w+)\s*\(", listing))
    assert called, "no pf.<call> found in the listings"
    unknown = called - defined
    assert not unknown, (
        f"listings call front functions that do not exist: {sorted(unknown)}"
    )


def test_each_listing_selects_its_own_database(listings: list[str]) -> None:
    """A listing that inherits setwhom() from an earlier one is not runnable
    on its own, and breaks the moment a reader executes it in a notebook."""
    offenders = []
    for n, listing in enumerate(listings, 1):
        queries = re.findall(r"\bpf\.(plot|map|hist|get)\s*\(", listing)
        if queries and "setwhom(" not in listing:
            offenders.append(n)
    assert not offenders, (
        f"listing(s) {offenders} query a database without selecting one; "
        "add the setwhom() call so the snippet stands alone"
    )


# ---------------------------------------------------------------------------
# what the repository requires the paper to say
# ---------------------------------------------------------------------------


def test_funding_acknowledgement_is_present(body: str) -> None:
    """AUTHORS makes this sentence a condition of the funding, to be reused
    verbatim in any publication. It is the one string that must not drift."""
    authors = (ROOT / "AUTHORS").read_text(encoding="utf-8")
    for fragment in (
        "IdEx",
        "Université Paris Cité 2022",
        "ANR-18-IDEX-0001",
        "Institut Covid-19 Ad Memoriam",
    ):
        assert fragment in authors, f"AUTHORS no longer contains {fragment!r}"
        assert fragment in body, (
            f"the manuscript omits {fragment!r}, required by AUTHORS "
            "as a condition of the funding"
        )


def test_authors_match_the_citation_file(body: str) -> None:
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    families = set(re.findall(r"family-names:\s*[\"']?([^\"'\n]+)", cff))
    missing = [f for f in families if f.strip() and f.strip() not in body]
    assert not missing, f"CITATION.cff lists authors absent from the paper: {missing}"


def test_title_agrees_with_the_preferred_citation(body: str) -> None:
    """CITATION.cff carries a commented preferred-citation block for SoftwareX.
    Its title is what every downstream citation will use, so it and the
    manuscript title have to be the same string."""
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    block = re.search(
        r"preferred-citation:(.*?)(?:\n[a-z-]+:|\Z)", cff, re.DOTALL | re.IGNORECASE
    )
    if block is None:
        pytest.skip("CITATION.cff has no preferred-citation block")

    titles = re.findall(r"title:\s*\"([^\"]+)\"", block.group(1))
    if not titles:
        pytest.skip("preferred-citation carries no title yet")

    paper_title = re.search(r"\\title\{(.*?)\n?\}", body, re.DOTALL)
    assert paper_title, "no \\title{} in the manuscript"
    normalised = " ".join(paper_title.group(1).split())

    assert any(" ".join(t.split()) == normalised for t in titles), (
        "the manuscript title and CITATION.cff's preferred-citation title "
        f"differ.\n  paper: {normalised}\n  cff:   {titles[0]}"
    )


def test_release_dois_are_the_project_ones(tex: str) -> None:
    zenodo = (ROOT / ".zenodo.json").read_text(encoding="utf-8")
    for doi in re.findall(r"10\.5281/zenodo\.(\d+)", tex):
        assert doi in zenodo or doi in (ROOT / "CITATION.cff").read_text(
            encoding="utf-8"
        ), f"the paper cites Zenodo {doi}, which no repository metadata mentions"


# ---------------------------------------------------------------------------
# SoftwareX limits
# ---------------------------------------------------------------------------


def test_within_softwarex_limits(body: str) -> None:
    figures = len(re.findall(r"\\begin\{figure\}", body))
    assert figures <= 6, f"SoftwareX allows 6 figures, the manuscript has {figures}"

    keywords = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", body, re.DOTALL)
    assert keywords, "no \\begin{keyword} block"
    n_kw = len([k for k in keywords.group(1).split(r"\sep") if k.strip()])
    assert n_kw <= 6, f"SoftwareX allows 6 keywords, the manuscript has {n_kw}"

    assert _word_count(body) <= 3000, (
        f"SoftwareX allows 3000 words for the abstract and sections 1-5; "
        f"the manuscript has about {_word_count(body)}"
    )


def test_every_citation_resolves(body: str, tex: str) -> None:
    cited = set()
    for m in re.finditer(r"\\cite\{([^}]*)\}", body):
        cited |= {k.strip() for k in m.group(1).split(",")}
    defined = set(re.findall(r"\\bibitem\{([^}]*)\}", tex))

    assert not (cited - defined), f"cited but not in the bibliography: {sorted(cited - defined)}"
    assert not (defined - cited), (
        f"in the bibliography but never cited (SoftwareX does not accept "
        f"uncited references): {sorted(defined - cited)}"
    )


# ---------------------------------------------------------------------------
# internals
# ---------------------------------------------------------------------------


def _metadata_row(tex: str, field: str) -> str:
    """Return the text of one row of the code/software metadata tables, with
    LaTeX escapes undone: ``pycountry\\_convert`` in the source is the package
    ``pycountry_convert``, and comparing the two must not depend on typesetting.
    """
    m = re.search(rf"^\s*{field}\s*&(.*?)\\\\", tex, re.DOTALL | re.MULTILINE)
    assert m, f"no metadata row {field} in the manuscript"
    return re.sub(r"\\([_&%#$])", r"\1", m.group(1))


def _word_count(body: str) -> int:
    """Abstract plus sections 1-5, the way SoftwareX counts: running text,
    captions and footnotes; not the title block, the metadata tables, the
    listings or the references."""
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, re.DOTALL)
    sections = body.split(r"\section{Motivation and significance}")
    text = (abstract.group(1) if abstract else "") + sections[-1].split(
        r"\section*{CRediT"
    )[0]

    for pattern in (
        r"\\begin\{lstlisting\}.*?\\end\{lstlisting\}",
        r"\\begin\{tabular\}.*?\\end\{tabular\}",
        r"\\begin\{equation\}.*?\\end\{equation\}",
    ):
        text = re.sub(pattern, "", text, flags=re.DOTALL)
    text = re.sub(r"%.*", "", text)
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", text)
    return len(re.findall(r"[A-Za-zÀ-ÿ0-9'’-]+", text))
