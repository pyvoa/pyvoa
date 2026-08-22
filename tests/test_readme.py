"""Consistency between README.md and the catalogue it advertises.

The table of supported databases is the list a user reads before installing
anything, and the manuscript takes its database count from it. Both drift the
moment a JSON descriptor is added or removed.

These tests read files only — no import of the heavy stack, no network — so
they run in the default offline job.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DATADIR = ROOT / "pyvoa" / "data"

READ_FROM = {"both", "archive only", "live only"}


@pytest.fixture(scope="module")
def readme() -> str:
    return README.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def rows(readme: str) -> dict[str, list[str]]:
    """The database table, as {key: [coverage, granularity, source, read from]}."""
    found = {}
    for line in readme.splitlines():
        m = re.match(r"^\|\s*`([^`]+)`\s*\|(.*)\|\s*$", line)
        if m:
            found[m.group(1)] = [c.strip() for c in m.group(2).split("|")]
    assert found, "no database table found in README.md"
    return found


def test_table_lists_every_shipped_database(rows: dict[str, list[str]]) -> None:
    shipped = {p.stem for p in DATADIR.glob("*.json")}
    assert set(rows) == shipped, (
        f"only in README: {sorted(set(rows) - shipped)}; "
        f"only in pyvoa/data/: {sorted(shipped - set(rows))}"
    )


def test_announced_count_matches_the_table(readme: str, rows: dict) -> None:
    m = re.search(r"(\d+)\s+databases are shipped with pyvoa", readme)
    assert m, "README no longer announces how many databases ship"
    assert int(m.group(1)) == len(rows), (
        f"README announces {m.group(1)} databases and tables {len(rows)}"
    )


def test_every_row_says_where_the_data_are_read_from(rows: dict[str, list[str]]) -> None:
    wrong = {db: cells[-1] for db, cells in rows.items() if cells[-1] not in READ_FROM}
    assert not wrong, f"unknown 'read from' value: {wrong}, expected one of {READ_FROM}"


def test_databases_with_no_mirror_are_marked_live_only(
    rows: dict[str, list[str]],
) -> None:
    """A descriptor whose urldata is not a Zenodo file has nothing archived.

    That half of the column is derivable, so it is checked rather than trusted;
    'archive only' is not, since it depends on an upstream server being gone.
    """
    for path in sorted(DATADIR.glob("*.json")):
        with open(path, encoding="utf-8") as handle:
            datasets = json.load(handle)["datasets"]
        mirrored = all("zenodo.org" in d["urldata"] for d in datasets)
        announced = rows[path.stem][-1]
        if not mirrored:
            assert announced == "live only", (
                f"{path.name} has no Zenodo mirror but README says {announced!r}"
            )
        else:
            assert announced != "live only", (
                f"{path.name} is mirrored on Zenodo but README says 'live only'"
            )
