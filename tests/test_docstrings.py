"""Consistency of the docstrings with the code they document.

Ruff's pydocstyle rules check that a docstring exists and is shaped like a
numpydoc one; they say nothing about whether what it claims is true. These
tests check the two claims that can be verified mechanically, both of which
had drifted in the past: a documented parameter must exist, and a docstring
must not be followed by the string it replaced.

They read the source with ``ast`` -- no import of the package, no network --
so they run in the default offline job.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1] / "pyvoa"
MODULES = sorted(PACKAGE.glob("*.py"))

# The four entry points of front are defined with the signature of the innermost
# function of their decorator chain -- plot(self, fig) -- while the callable a
# user reaches takes keyword arguments only, and documents those. docs/conf.py
# rewrites the same four signatures to (**kwargs) for the same reason.
DECORATED = {"get", "plot", "hist", "map"}

# Every module of the package signs off with this block, and has done since
# before the docstrings were rewritten. examples/ and tests/ deliberately do
# not: they are not the library.
HEADER = """Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/"""

SECTIONS = {
    "Parameters", "Returns", "Yields", "Raises", "Notes", "Examples",
    "See Also", "Attributes", "Other Parameters", "References", "Warns",
}


def definitions(module: Path):
    """Yield every function, method and class defined in a module."""
    tree = ast.parse(module.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node


def documented_parameters(doc: str) -> list[str]:
    """Return the names listed in the Parameters section of a numpydoc string."""
    lines = doc.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "Parameters" and i + 1 < len(lines) and set(lines[i + 1].strip()) == {"-"}:
            break
    else:
        return []
    indent = len(line) - len(line.lstrip())
    names = []
    for entry in lines[i + 2:]:
        if not entry.strip():
            continue
        if len(entry) - len(entry.lstrip()) < indent or entry.strip() in SECTIONS:
            break
        if len(entry) - len(entry.lstrip()) == indent:
            m = re.match(r"([*\w, ]+?)\s*(:|$)", entry.strip())
            if m:
                names += [n.strip().lstrip("*") for n in m.group(1).split(",") if n.strip()]
    return names


def signature_parameters(node) -> list[str]:
    """Return the parameter names of a function, self and cls excluded."""
    a = node.args
    names = [p.arg for p in a.posonlyargs + a.args + a.kwonlyargs]
    if a.vararg:
        names.append(a.vararg.arg)
    if a.kwarg:
        names.append(a.kwarg.arg)
    return [n for n in names if n not in ("self", "cls")]


@pytest.mark.parametrize("module", MODULES, ids=lambda p: p.name)
def test_documented_parameters_exist(module: Path):
    # A function taking **kwargs documents the keys it reads under their own
    # names -- that is how get(), plot() and the backends are written, and the
    # docs rewrite those signatures to (**kwargs) on purpose -- so the check
    # only applies to functions with a fixed signature.
    wrong = []
    for node in definitions(module):
        if isinstance(node, ast.ClassDef):
            continue
        doc = ast.get_docstring(node)
        if not doc:
            continue
        actual = signature_parameters(node)
        if "kwargs" in actual or (module.name == "front.py" and node.name in DECORATED):
            continue
        ghosts = [p for p in documented_parameters(doc) if p not in actual]
        if ghosts:
            wrong.append(f"{module.name}:{node.lineno} {node.name}{tuple(actual)} documents {ghosts}")
    assert not wrong, "documented parameters that do not exist:\n" + "\n".join(wrong)


@pytest.mark.parametrize("module", MODULES, ids=lambda p: p.name)
def test_no_string_left_after_a_docstring(module: Path):
    # geo.py used to carry, under most of its docstrings, the older docstring
    # that had been replaced: a bare string expression, which python evaluates
    # and drops, and no tool reads. They are gone; this keeps them gone.
    leftovers = []
    for node in definitions(module):
        if len(node.body) < 2 or not ast.get_docstring(node):
            continue
        second = node.body[1]
        if isinstance(second, ast.Expr) and isinstance(second.value, ast.Constant) \
                and isinstance(second.value.value, str):
            leftovers.append(f"{module.name}:{second.lineno} in {node.name}")
    assert not leftovers, "dead string after a docstring:\n" + "\n".join(leftovers)


@pytest.mark.parametrize("module", MODULES, ids=lambda p: p.name)
def test_module_header_is_the_common_one(module: Path):
    doc = ast.get_docstring(ast.parse(module.read_text(encoding="utf-8")))
    assert doc, f"{module.name} has no module docstring"
    assert doc.strip().endswith(HEADER), (
        f"{module.name} does not end with the common header block:\n"
        + "\n".join(doc.strip().splitlines()[-5:])
    )


@pytest.mark.parametrize("module", MODULES, ids=lambda p: p.name)
def test_module_docstring_opens_the_file(module: Path):
    # A blank line before the docstring, or several after it, is the kind of
    # drift that survives every other check: ruff's D rules and sphinx both
    # read the docstring, not its surroundings.
    lines = module.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith('"""'), f"{module.name} does not open with its docstring"
    tree = ast.parse("\n".join(lines))
    if len(tree.body) < 2:
        return
    end = tree.body[0].end_lineno
    blanks = 0
    while lines[end + blanks].strip() == "":
        blanks += 1
    assert blanks == 1, f"{module.name} has {blanks} blank lines after its docstring, not 1"
