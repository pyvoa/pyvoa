"""Tests that genuinely reach upstream servers.

Every test here is marked ``network`` and is therefore deselected by the
default ``addopts`` in pyproject.toml. Run them explicitly with::

    pytest -m network

They are meant for the scheduled CI job: they are the only place where the
geographic normalisation and the database parsers are exercised end to end
against the real payloads, so a change of upstream format shows up here
rather than in a user's notebook.

Beware when running these locally: pyvoa caches every download under
``~/.cache/pyvoa.data_<user>``, so a passing run may only prove the cache
is warm. Clear that directory to test a cold start.
"""

import datetime

import pandas as pd
import pytest

from pyvoa import geo
from pyvoa.jsondb_parser import DataParser
from pyvoa.tools import exists_from_url, get_local_from_url

pytestmark = pytest.mark.network


# --------------------------------------------------------------------------
# downloads
# --------------------------------------------------------------------------

def test_exists_from_url_finds_a_live_url():
    assert exists_from_url("https://zenodo.org/") is True


def test_get_local_from_url_returns_a_readable_file(tmp_path, monkeypatch):
    from pyvoa import tools

    monkeypatch.setattr(tools, "tmpdir", str(tmp_path))
    path = get_local_from_url(
        "https://raw.githubusercontent.com/owid/covid-19-data/master/README.md"
    )
    with open(path, "rb") as handle:
        assert len(handle.read()) > 0


# --------------------------------------------------------------------------
# GeoManager / GeoRegion
# --------------------------------------------------------------------------

def test_to_standard_converts_country_names_to_iso3():
    manager = geo.GeoManager("iso3")
    assert manager.to_standard(["France", "Italy"]) == ["FRA", "ITA"]


def test_to_standard_accepts_a_single_string():
    assert geo.GeoManager("iso3").to_standard("France") == ["FRA"]


def test_to_standard_is_insensitive_to_case_and_accents():
    manager = geo.GeoManager("iso3")
    assert manager.to_standard(["cote d'ivoire"]) == ["CIV"]


def test_to_standard_can_return_a_dict():
    result = geo.GeoManager("iso3").to_standard(["France"], output="dict")
    assert result == {"France": "FRA"}


def test_to_standard_can_return_a_pandas():
    result = geo.GeoManager("iso3").to_standard(["France"], output="pandas")
    assert isinstance(result, pd.DataFrame)


def test_to_standard_expands_a_region():
    countries = geo.GeoManager("iso3").to_standard(
        ["European Union"], interpret_region=True
    )
    assert "FRA" in countries
    assert len(countries) > 20


def test_georegion_lists_its_regions():
    regions = geo.GeoRegion().get_region_list()
    assert len(regions) > 0


def test_georegion_recognises_a_region():
    region = geo.GeoRegion()
    assert region.is_region("Europe")


def test_georegion_returns_the_countries_of_a_region():
    countries = geo.GeoRegion().get_countries_from_region("europe")
    assert "fra" in [c.lower() for c in countries]


# --------------------------------------------------------------------------
# GeoCountry
# --------------------------------------------------------------------------

def test_geocountry_france_is_initialised():
    country = geo.GeoCountry("FRA")
    assert country.is_init() is True
    assert country.get_country() == "FRA"


def test_geocountry_france_has_regions_and_subregions():
    country = geo.GeoCountry("FRA")
    assert len(country.get_region_list()) > 0
    assert len(country.get_subregion_list()) > 0


def test_geocountry_france_knows_its_departments():
    country = geo.GeoCountry("FRA")
    assert country.is_subregion("Ain") or country.is_subregion("01")


def test_geocountry_drc_maps_its_health_zones():
    """COD is the geography the DRC Ebola sitreps are indexed by."""
    country = geo.GeoCountry("COD")
    data = country.get_data()
    # 519 health zones grouped in the 26 provinces of the country
    assert len(data) == 519
    assert len(country.get_region_list()) == 26
    assert country.is_subregion("bunia") == "Bunia"
    # every province is resolved to its ISO 3166-2:CD code
    assert data["code_region"].str.startswith("CD-").all()
    # WorldPop count, of the order of the population of the country
    assert 80e6 < data["population_subregion"].sum() < 140e6


# --------------------------------------------------------------------------
# GeoInfo
# --------------------------------------------------------------------------

def test_geoinfo_adds_a_population_column():
    info = geo.GeoInfo()
    frame = pd.DataFrame({"where": ["France", "Italy"]})
    enriched = info.add_field(input=frame, field="population", geofield="where")
    assert "population" in enriched.columns
    assert enriched["population"].notna().all()


# --------------------------------------------------------------------------
# database parsers, end to end
# --------------------------------------------------------------------------

@pytest.mark.parametrize("database", ["spfnational", "owid", "ebolardc"])
def test_dataparser_builds_a_usable_frame(database):
    parser = DataParser(database)
    frame = parser.get_maingeopandas()
    assert not frame.empty
    assert {"date", "where", "code", "geometry"} <= set(frame.columns)
    assert isinstance(frame["date"].iloc[0], datetime.date)
    assert parser.get_locations()
    assert parser.get_available_keywords()


def test_ebolardc_matches_the_upstream_sitreps():
    """The health-zone series must carry the values of the source csv."""
    from pyvoa.tools import set_live_mode

    set_live_mode(True)
    try:
        frame = DataParser("ebolardc").get_maingeopandas()
    finally:
        set_live_mode(False)

    assert {"tot_confirmed", "tot_deaths"} <= set(frame.columns)
    # the outbreak started in Ituri, and Bunia is its main health zone
    bunia = frame.loc[frame["where"] == "Bunia", "tot_confirmed"].dropna()
    assert not bunia.empty
    assert bunia.is_monotonic_increasing  # a cumulative count never decreases
    assert bunia.iloc[-1] > 1000
