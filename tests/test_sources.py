"""Every shipped database, against a direct read of the files it is parsed from.

The parser is checked here against a second reader of the same files, written
independently of it: ``read_raw`` takes the cached payload a database reads
and applies the rules of its JSON description (separator, selections, drop,
replace, melt, splitwhere, cumulative) with plain pandas. Three checks follow,
per database:

* dates: the raw date strings parse as the parser parses them, with no NaT,
  and none of them is a day-first date read month-first — the govcy defect;
* totals: summed over every location, each variable equals the raw file
  date by date. Summing over locations keeps the check free of the
  geographic name resolution;
* get: the last value ``get()`` hands out for each location is the last
  value of the parsed database.

Some sources ship rows that pyvoa leaves out on purpose — a national total
among the regions, a cruise ship among the countries. ``LEFT_OUT`` names them,
database by database, and the raw read drops them before the totals are
compared, so that the comparison stays exact. A location that stops resolving
shows up as a new gap rather than hiding behind a tolerance.

These tests parse all the databases, which downloads their payloads and takes
a few minutes: they are marked ``network`` and run in the scheduled job.
"""

from __future__ import annotations

import functools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.network

DATADIR = Path(__file__).resolve().parents[1] / "pyvoa" / "data"
DATABASES = sorted(p.stem for p in DATADIR.glob("*.json"))
RTOL = 1e-6

# the locations of a source that pyvoa leaves out, as the raw file spells them
LEFT_OUT = {
    # a national row shipped among the states, and cases with no state
    "covid19india": {"India", "State Unassigned"},
    # a national row, which holds most deaths (on 2022-05-16 it is the
    # opposite of the regions' sum, a slip of the source), Mount Athos, a
    # cruise ship and the points of entry
    "imed": {"ΕΛΛΑΔΑ", "ΑΥΤΟΒΟΥΛΩΣ", "ΚΡΟΥΑΖΙΕΡΟΠΛΟΙΟ", "ΠΥΛΕΣ ΕΙΣΟΔΟΥ"},
    # entities that are not countries
    "jhu": {"Antarctica", "Diamond Princess", "MS Zaandam",
            "Summer Olympics 2020", "Winter Olympics 2022"},
    # the two cruise ships listed among the states
    "jhu-usa": {"Diamond Princess", "Grand Princess"},
}


def _metadata(db):
    """Return the JSON description of a shipped database."""
    with open(DATADIR / f"{db}.json", encoding="utf-8") as handle:
        return json.load(handle)


@functools.cache
def _parsed(db):
    """Return the parsed database, selecting it once for the whole module."""
    import pyvoa.front as pf

    pf.setwhom(db)
    return pf.getdatabase()


def _is_week(dataset):
    """Tell whether a dataset is indexed by week rather than by day."""
    return any(c.get("alias") in ("semaine", "week") for c in dataset["columns"])


def _parse_dates(dates, dataset):
    """Parse date strings as jsondb_parser does."""
    from pyvoa.tools import week_to_date

    dates = pd.Series(dates)
    if _is_week(dataset):
        return pd.to_datetime(pd.Series([week_to_date(i) for i in dates]),
                              errors="coerce")
    return pd.to_datetime(dates, errors="coerce",
                          format=dataset.get("dateformat", "mixed"))


def read_raw(dataset, metadata):
    """Read one dataset as a long frame date / where / variables, without the parser.

    Parameters
    ----------
    dataset : dict
        one entry of the 'datasets' list of the JSON description.
    metadata : dict
        the whole JSON description, for its 'replace' and 'geoinfo' keys.

    Returns
    -------
    tuple
        the frame, all strings, and a dict telling for each variable whether
        the JSON asks for it to be cumulated.
    """
    from pyvoa.tools import get_live_mode, get_local_from_url

    url = dataset["urldata"]
    live = get_live_mode() or "zenodo.org" not in url
    if get_live_mode() and dataset.get("urlparent"):
        url = dataset["urlparent"]
    names = dataset.get("names")
    raw = pd.read_csv(get_local_from_url(url, 10000, live=live),
                      sep=dataset.get("separator", ";"), dtype=str,
                      keep_default_na=False, na_values=dataset.get("na_values", ""),
                      header=0 if names is None else None, names=names,
                      low_memory=False, comment="#")
    cols = dataset["columns"]
    alias = {c.get("alias", c["name"]): c["name"] for c in cols}

    for key, val in dataset.get("drop", {}).items():
        if key in raw.columns:
            for i in (val if isinstance(val, list) else [val]):
                raw = raw.dropna(subset=[key])
                raw = raw[~raw[key].str.startswith(i)]
    for key, val in dataset.get("selections", {}).items():
        # the json may give the value as a number, the raw read is all strings
        raw = raw.loc[raw[key] == str(val)]
    replace = {k: (np.nan if v == "np.nan" else v)
               for k, v in metadata.get("replace", {}).items()}
    if replace:
        # the parser reads numbers as numbers, so a rule such as spf's
        # '987' -> '980' only ever touches a location code or a date string
        # there; this read is all strings, so restrict the renaming rules to
        # those two columns, and apply the blanking ones everywhere
        keyed = [a for a, n in alias.items()
                 if n in ("where", "date") and a in raw.columns]
        blank = {k: v for k, v in replace.items() if pd.isna(v)}
        rename = {k: v for k, v in replace.items() if not pd.isna(v)}
        if blank:
            raw = raw.replace(blank)
        if rename and keyed:
            raw[keyed] = raw[keyed].replace(rename)

    if "namedata" in dataset:
        value = dataset.get("renamedata", dataset["namedata"])
        raw = raw.rename(columns=alias)
        if dataset.get("dropcolumns"):
            raw = raw.drop(columns=dataset["dropcolumns"])
        if "var_name" in dataset:
            if "11000" in raw.columns:
                # rki ships Berlin (11000) and its twelve districts, which
                # add up to it exactly: counting both would count Berlin twice
                raw = raw.drop(columns=[str(c) for c in range(11001, 11013)
                                        if str(c) in raw.columns])
            raw = raw.melt(id_vars="date", var_name="where", value_name=value)
        else:
            raw = raw.melt(id_vars="where", var_name="date", value_name=value)
        variables = {value: False}
    else:
        raw = raw[[a for a in alias if a in raw.columns]].rename(columns=alias)
        variables = {c["name"]: bool(c.get("cumulative")) for c in cols
                     if c["name"] not in ("date", "where")}
        if "where" not in raw.columns:
            raw["where"] = metadata["geoinfo"]["iso3"]
    if "splitwhere" in dataset:
        sw = dataset["splitwhere"]
        raw["where"] = (raw["where"].astype(str).str.split(sw.get("separator", ","))
                        .str[sw.get("keep", -1)].str.strip())
    return raw, variables


def raw_totals(raw, variables, dataset):
    """Return, for each date, the sum over every location of the raw file.

    Increments are cumulated where the JSON says so, and a running total is
    carried over the dates a sparse source has no row for, as the parsed
    database does.
    """
    raw = raw.copy()
    raw["date"] = _parse_dates(raw["date"], dataset).dt.normalize()
    if raw["date"].dt.tz is not None:
        # rki stamps its dates in UTC, the parsed database is tz-naive
        raw["date"] = raw["date"].dt.tz_localize(None)
    raw = raw.dropna(subset=["date"])
    for v in variables:
        raw[v] = pd.to_numeric(raw[v].astype(str).str.replace(",", ".", regex=False),
                               errors="coerce")
    raw = raw.groupby(["where", "date"])[list(variables)].sum(min_count=1).reset_index()
    raw = raw.sort_values(["where", "date"])
    cumulated = [v for v, cum in variables.items() if cum]
    if cumulated:
        raw[cumulated] = raw.groupby("where")[cumulated].cumsum()
        alldates = np.sort(raw["date"].unique())
        full = (raw.set_index(["where", "date"])[cumulated].unstack("where")
                .reindex(alldates).ffill())
        full = full.stack("where", future_stack=True).reset_index()
        raw = raw.drop(columns=cumulated).merge(full, on=["date", "where"], how="right")
    return raw.groupby("date")[list(variables)].sum(min_count=1)


def _datasets(db):
    """Yield each dataset of a database with its raw read."""
    metadata = _metadata(db)
    for dataset in metadata["datasets"]:
        raw, variables = read_raw(dataset, metadata)
        yield dataset, raw, variables


@pytest.mark.parametrize("db", DATABASES)
def test_raw_dates_parse_as_the_parser_reads_them(db):
    for dataset, raw, _ in _datasets(db):
        dates = pd.Series(pd.unique(raw["date"].astype(str)))
        dates = dates[dates.str.strip() != ""]
        parsed = _parse_dates(dates, dataset)
        assert parsed.notna().all(), (
            f"{db}: unparsed dates {list(dates[parsed.isna()][:5])}")
        if _is_week(dataset):
            continue
        # a day-first file read month-first scatters its dates over a longer
        # span than the day-first reading would: that is how govcy went wrong
        dayfirst = pd.to_datetime(dates, errors="coerce", format="mixed",
                                  dayfirst=True)
        differ = (parsed != dayfirst) & dayfirst.notna()
        if differ.any():
            span = (parsed.max() - parsed.min()).days
            span_dayfirst = (dayfirst.max() - dayfirst.min()).days
            assert span <= span_dayfirst, (
                f"{db}: dates look day-first, e.g. {dates[differ].iloc[0]!r} "
                f"read as {parsed[differ].iloc[0].date()}; set 'dateformat'")


@pytest.mark.parametrize("db", DATABASES)
def test_totals_equal_the_raw_file(db):
    parsed = _parsed(db).copy()
    parsed["date"] = pd.to_datetime(parsed["date"]).dt.normalize()
    for dataset, raw, variables in _datasets(db):
        raw = raw[~raw["where"].isin(LEFT_OUT.get(db, set()))]
        ref = raw_totals(raw, variables, dataset)
        mine = parsed.groupby("date")[[v for v in variables if v in parsed.columns]]\
            .sum(min_count=1)
        for v in variables:
            assert v in mine.columns, f"{db}: {v} missing from the parsed database"
            both = pd.concat([ref[v].rename("raw"), mine[v].rename("pyvoa")],
                             axis=1, join="inner").dropna()
            assert not both.empty, f"{db}: {v} has no date in common with the source"
            bad = both[~np.isclose(both.raw, both.pyvoa, rtol=RTOL, atol=1e-9)]
            assert bad.empty, (
                f"{db}: {v} differs from the source on {len(bad)} of "
                f"{len(both)} dates, first {bad.index[0].date()}: raw "
                f"{bad.raw.iloc[0]:.6g}, pyvoa {bad.pyvoa.iloc[0]:.6g}")


@pytest.mark.parametrize("db", DATABASES)
def test_get_hands_out_the_last_parsed_value(db):
    import pyvoa.front as pf

    parsed = _parsed(db)
    pf.setwhom(db, reload=False)
    variables = {v for dataset, _, variables in _datasets(db) for v in variables}
    for v in sorted(variables & set(parsed.columns)):
        got = pf.get(which=v)
        last_db = parsed.dropna(subset=[v]).sort_values("date").groupby("where")[v].last()
        last_get = got.sort_values("date").groupby("where")[v].last()
        both = pd.concat([last_db.rename("db"), last_get.rename("viaget")],
                         axis=1, join="inner").dropna()
        bad = both[~np.isclose(both.db, both.viaget, rtol=RTOL, atol=1e-9)]
        assert bad.empty, (
            f"{db}: get({v!r}) differs for {len(bad)} of {len(both)} locations, "
            f"e.g. {bad.index[0]}: database {bad.db.iloc[0]:.6g}, "
            f"get {bad.viaget.iloc[0]:.6g}")
