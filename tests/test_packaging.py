"""The files the package reads at run time are in the wheel.

setuptools puts the python modules of pyvoa/ in the wheel by itself, and any
other file only when ``[tool.setuptools.package-data]`` names it. Nothing
fails at build time when one is missing: 0.5.0 was published without
pyvoa/js/, and a bokeh chart raised FileNotFoundError on every installed copy
while the test suite, run from the checkout, saw the files.
"""

from __future__ import annotations

import ast
import fnmatch
import subprocess
import sys
from pathlib import Path

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def tracked_data_files() -> list[str]:
    """Return the files git tracks under pyvoa/ that are not python, relative to it."""
    try:
        listed = subprocess.run(
            ["git", "ls-files", "pyvoa"], cwd=ROOT, capture_output=True,
            text=True, check=True,
        ).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    return [f.removeprefix("pyvoa/") for f in listed if not f.endswith(".py")]


def test_every_data_file_of_the_package_is_in_package_data():
    with open(ROOT / "pyproject.toml", "rb") as f:
        globs = tomllib.load(f)["tool"]["setuptools"]["package-data"]["pyvoa"]
    left_out = [f for f in tracked_data_files()
                if not any(fnmatch.fnmatch(f, g) for g in globs)]
    assert not left_out, (
        "files of pyvoa/ the wheel would leave out, to add to "
        f"[tool.setuptools.package-data]: {left_out}")


def test_every_text_file_of_the_package_is_opened_with_an_encoding():
    """open() in text mode names its encoding, or Windows decodes with cp1252.

    pyvoa's json descriptions, its javascript callbacks and the pages it
    scrapes are utf-8. Without ``encoding=``, open() decodes them with the
    locale's encoding, which is utf-8 on Linux and macOS and cp1252 on most
    Windows machines, where ``import pyvoa.front`` failed.
    """
    unnamed = []
    for path in sorted((ROOT / "pyvoa").rglob("*.py")):
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue  # .ipynb_checkpoints and the like, not part of the package
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "open"):
                continue
            mode = node.args[1] if len(node.args) > 1 else next(
                (k.value for k in node.keywords if k.arg == "mode"), None)
            if isinstance(mode, ast.Constant) and "b" in str(mode.value):
                continue
            if len(node.args) < 4 and not any(k.arg == "encoding" for k in node.keywords):
                unnamed.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert not unnamed, f"open() in text mode without an encoding: {unnamed}"
