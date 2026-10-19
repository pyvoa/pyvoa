"""The files the package reads at run time are in the wheel.

setuptools puts the python modules of pyvoa/ in the wheel by itself, and any
other file only when ``[tool.setuptools.package-data]`` names it. Nothing
fails at build time when one is missing: 0.5.0 was published without
pyvoa/js/, and a bokeh chart raised FileNotFoundError on every installed copy
while the test suite, run from the checkout, saw the files.
"""

from __future__ import annotations

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
