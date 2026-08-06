# -*- coding: utf-8 -*-
"""Unit tests for pyvoa.jsondb_parser.

These tests run entirely offline. The most valuable one is
``test_every_shipped_database_description_is_valid``: it re-parses all the
JSON descriptions shipped in ``pyvoa/data/`` and fails as soon as one of
them stops matching the expected structure.
"""

import datetime
import json
from pathlib import Path

import pytest
import shapely.geometry as sg

import pyvoa.jsondb_parser as jsondb_parser
from pyvoa.jsondb_parser import MetaInfo
from pyvoa.tools import PyvoaError

DATA = Path(__file__).parent / "data"


# --------------------------------------------------------------------------
# structural validation
# --------------------------------------------------------------------------

def _load(name):
    with open(DATA / name) as handle:
        return json.load(handle)


def test_checkmetadatastructure_accepts_a_valid_description():
    sig, msg = MetaInfo.checkmetadatastructure(_load("good_db.json"))
    assert sig == 1
    assert "validated" in msg


@pytest.mark.parametrize(
    "fixture, missing",
    [
        ("no_geoinfo.json", "geoinfo"),
        ("no_locationmode.json", "locationmode"),
        ("unnamed_column.json", "name"),
    ],
)
def test_checkmetadatastructure_reports_the_missing_key(fixture, missing):
    sig, msg = MetaInfo.checkmetadatastructure(_load(fixture))
    assert sig == 0
    assert missing in msg


def test_checkmetadatastructure_requires_datasets():
    sig, msg = MetaInfo.checkmetadatastructure({"geoinfo": {}})
    assert sig == 0
    assert "datasets" in msg


# --------------------------------------------------------------------------
# parsejson
# --------------------------------------------------------------------------

def test_parsejson_returns_the_content_of_a_valid_file():
    parsed = MetaInfo.parsejson(str(DATA / "good_db.json"))
    assert list(parsed) == [1]
    assert parsed[1]["geoinfo"]["iso3"] == "FRA"


def test_parsejson_rejects_a_structurally_invalid_file():
    parsed = MetaInfo.parsejson(str(DATA / "no_geoinfo.json"))
    assert list(parsed) == [0]
    assert "incompatible" in parsed[0]


def test_parsejson_rejects_a_malformed_file():
    parsed = MetaInfo.parsejson(str(DATA / "malformed.json"))
    assert list(parsed) == [0]
    assert "Invalid json file" in parsed[0]


def test_parsejson_reports_a_missing_file():
    parsed = MetaInfo.parsejson(str(DATA / "no-such-file.json"))
    assert list(parsed) == [0]
    assert "do not exist" in parsed[0]


# --------------------------------------------------------------------------
# the shipped database descriptions
# --------------------------------------------------------------------------

def test_every_shipped_database_description_is_valid():
    """No database description in pyvoa/data/ may regress to BAD."""
    catalogue = MetaInfo.getallmetadata()
    invalid = catalogue.loc[catalogue.validejson != "GOOD"]
    assert invalid.empty, "invalid database descriptions: " + ", ".join(
        f"{row['name']} ({row.parsingjson})" for _, row in invalid.iterrows()
    )


def test_getallmetadata_lists_the_well_known_databases():
    names = set(MetaInfo.getallmetadata().name)
    assert {"jhu", "owid", "spf", "rki"} <= names


def test_getallmetadata_columns():
    assert list(MetaInfo.getallmetadata().columns) == [
        "name",
        "validejson",
        "parsingjson",
    ]


# --------------------------------------------------------------------------
# getcurrentmetadata / getcurrentmetadatawhich
# --------------------------------------------------------------------------

def test_getcurrentmetadata_returns_the_parsed_description():
    metadata = MetaInfo().getcurrentmetadata("spfnational")
    assert metadata["geoinfo"]["granularity"] == "country"
    assert metadata["datasets"]


@pytest.mark.parametrize("empty", [None, ""])
def test_getcurrentmetadata_rejects_an_empty_name(empty):
    with pytest.raises(PyvoaError):
        MetaInfo().getcurrentmetadata(empty)


@pytest.mark.xfail(
    reason="getcurrentmetadata indexes an empty selection for an unknown "
           "database, so numpy raises 'truth value of an empty array is "
           "ambiguous' instead of a PyvoaError naming the unknown database",
    strict=True,
)
def test_getcurrentmetadata_rejects_an_unknown_database():
    with pytest.raises(PyvoaError):
        MetaInfo().getcurrentmetadata("no-such-database")


def test_getcurrentmetadatawhich_lists_the_variables():
    meta = MetaInfo()
    which = meta.getcurrentmetadatawhich(_load("good_db.json"))
    assert which == ["tot_cases", "tot_deaths"]


def test_getcurrentmetadatawhich_drops_date_and_where():
    meta = MetaInfo()
    which = meta.getcurrentmetadatawhich(_load("good_db.json"))
    assert "date" not in which
    assert "where" not in which


def test_getcurrentmetadatawhich_includes_namedata():
    description = _load("good_db.json")
    description["datasets"][0]["namedata"] = "an_extra_variable"
    which = MetaInfo().getcurrentmetadatawhich(description)
    assert "an_extra_variable" in which


def test_getcurrentmetadatawhich_on_a_shipped_database():
    meta = MetaInfo()
    which = meta.getcurrentmetadatawhich(meta.getcurrentmetadata("spfnational"))
    assert "tot_dc_hosp" in which
    assert "date" not in which


# --------------------------------------------------------------------------
# DataParser, offline
# --------------------------------------------------------------------------
#
# The CSV -> pandas half of get_parsing() (column aliasing, date coercion,
# numeric coercion, aggregation, date filling) is genuine logic and is
# exercised here against a frozen 3-line payload.
#
# The geo half is not: normalising a location list needs GeoManager and
# GeoInfo, which download about ten upstream pages between them. Both are
# replaced by the small fakes below, whose return shapes were read off the
# real objects. They are collaborators of the parser, not the code under
# test; the real ones are exercised in test_network.py.


class _FakeGeoManager:
    """Stands in for coge.GeoManager, whose __init__ downloads region data."""

    _NAMES = {"FRA": "France"}

    def __init__(self, standard="name"):
        self.standard = standard

    def to_standard(self, w, output="list", db=None, **kwargs):
        names = {code: self._NAMES.get(code, code.title()) for code in w}
        if output == "dict":
            return names
        return list(names.values())


class _FakeGeoInfo:
    """Stands in for coge.GeoInfo, whose geometry field is a download."""

    def add_field(self, input=None, field=None, **kwargs):
        enriched = input.copy()
        enriched[field] = [
            sg.box(i, i, i + 1, i + 1) for i in range(len(enriched))
        ]
        return enriched


@pytest.fixture
def offline_parser(monkeypatch):
    """A DataParser built from tests/data/good_db.json and tests/data/tiny.csv."""
    with open(DATA / "good_db.json") as handle:
        metadata = json.load(handle)

    monkeypatch.setattr(
        MetaInfo, "getcurrentmetadata", lambda self, namedb: metadata
    )
    monkeypatch.setattr(
        jsondb_parser, "get_local_from_url",
        lambda url, *args, **kwargs: str(DATA / "tiny.csv"),
    )
    monkeypatch.setattr(jsondb_parser.coge, "GeoManager", _FakeGeoManager)
    monkeypatch.setattr(jsondb_parser.coge, "GeoInfo", _FakeGeoInfo)
    return jsondb_parser.DataParser("good_db")


def test_dataparser_builds_the_expected_columns(offline_parser):
    columns = set(offline_parser.get_maingeopandas().columns)
    assert {"date", "where", "code", "tot_cases", "tot_deaths"} <= columns


def test_dataparser_orders_the_leading_columns(offline_parser):
    assert list(offline_parser.get_maingeopandas().columns)[:3] == [
        "date",
        "where",
        "code",
    ]


def test_dataparser_applies_the_column_aliases(offline_parser):
    """The CSV ships location/cases/deaths, the json renames them."""
    columns = offline_parser.get_maingeopandas().columns
    assert "cases" not in columns
    assert "tot_cases" in columns


def test_dataparser_reads_every_row_of_the_payload(offline_parser):
    frame = offline_parser.get_maingeopandas()
    assert len(frame) == 3


def test_dataparser_parses_the_values_as_numbers(offline_parser):
    frame = offline_parser.get_maingeopandas().sort_values("date")
    assert list(frame["tot_cases"]) == [100, 150, 210]
    assert list(frame["tot_deaths"]) == [10, 12, 15]


def test_dataparser_parses_the_dates(offline_parser):
    dates = sorted(offline_parser.get_maingeopandas()["date"])
    assert dates[0] == datetime.date(2020, 5, 1)
    assert dates[-1] == datetime.date(2020, 5, 3)


def test_dataparser_exposes_its_locations(offline_parser):
    assert offline_parser.get_locations() == ["France"]


def test_dataparser_exposes_its_dates(offline_parser):
    assert len(offline_parser.get_dates()) == 3


def test_dataparser_exposes_the_database_name(offline_parser):
    assert offline_parser.get_db() == "good_db"


def test_dataparser_is_flagged_as_worldwide(offline_parser):
    assert offline_parser.get_world_boolean() is True


def test_dataparser_exposes_its_keywords(offline_parser):
    keywords = offline_parser.get_available_keywords()
    assert "tot_cases" in keywords
    assert "date" not in keywords
    assert "where" not in keywords


def test_dataparser_puts_a_total_keyword_first(offline_parser):
    assert offline_parser.get_available_keywords()[0].startswith("tot_")


def test_dataparser_exposes_the_keyword_definitions(offline_parser):
    assert "Cumulative" in offline_parser.get_keyword_definition("tot_cases")


def test_dataparser_rejects_an_unknown_keyword(offline_parser):
    with pytest.raises(PyvoaError):
        offline_parser.get_keyword_definition("not_a_keyword")


def test_dataparser_exposes_the_keyword_urls(offline_parser):
    assert offline_parser.get_keyword_url("tot_cases").startswith("https://")


def test_dataparser_exposes_the_parsed_urls(offline_parser):
    assert offline_parser.get_url() == ["https://example.org/frozen/tiny.csv"]


def test_dataparser_exposes_the_description(offline_parser):
    assert "minimal" in offline_parser.get_dbdescription()


def test_dataparser_fills_the_missing_dates(monkeypatch, tmp_path):
    """A payload with a one-day hole is padded by fill_missing_dates."""
    gappy = tmp_path / "gappy.csv"
    gappy.write_text(
        "date,location,cases,deaths\n"
        "2020-05-01,FRA,100,10\n"
        "2020-05-04,FRA,210,15\n"
    )
    with open(DATA / "good_db.json") as handle:
        metadata = json.load(handle)

    monkeypatch.setattr(
        MetaInfo, "getcurrentmetadata", lambda self, namedb: metadata
    )
    monkeypatch.setattr(
        jsondb_parser, "get_local_from_url",
        lambda url, *args, **kwargs: str(gappy),
    )
    monkeypatch.setattr(jsondb_parser.coge, "GeoManager", _FakeGeoManager)
    monkeypatch.setattr(jsondb_parser.coge, "GeoInfo", _FakeGeoInfo)

    frame = jsondb_parser.DataParser("good_db").get_maingeopandas()
    assert len(frame) == 4
    assert frame["tot_cases"].isna().sum() == 2
