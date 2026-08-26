"""Offline unit tests for pyvoa.geo.

Only the part of the module that does not need a download is covered here.
``GeoRegion.__init__`` fetches about ten upstream pages (UN M49, several
Wikipedia articles, worldometers), and ``GeoManager()`` builds a GeoRegion,
so anything going through them lives in ``test_network.py`` instead.

Note that on a developer machine with a warm ``~/.cache/pyvoa.data_<user>``
those constructors *appear* to work offline; they do not on a fresh
checkout, which is why they are not exercised here.
"""

import geopandas as gpd
import pytest
import shapely.geometry as sg

from pyvoa import geo
from pyvoa.tools import PyvoaError

# --------------------------------------------------------------------------
# GeoManager : standards, without building a GeoRegion
# --------------------------------------------------------------------------

@pytest.fixture
def bare_manager():
    """Build a GeoManager without __init__, hence without any download."""
    return geo.GeoManager.__new__(geo.GeoManager)


@pytest.mark.parametrize("standard", ["iso2", "iso3", "name", "num"])
def test_set_standard_accepts_every_supported_standard(bare_manager, standard):
    assert bare_manager.set_standard(standard) == standard
    assert bare_manager.get_standard() == standard


def test_set_standard_rejects_an_unknown_standard(bare_manager):
    with pytest.raises(PyvoaError) as excinfo:
        bare_manager.set_standard("klingon")
    assert "not managed" in str(excinfo.value)


@pytest.mark.parametrize("standard", [3, None, ["iso3"]])
def test_set_standard_rejects_a_non_string(bare_manager, standard):
    with pytest.raises(PyvoaError) as excinfo:
        bare_manager.set_standard(standard)
    assert "must be a string" in str(excinfo.value)


def test_geomanager_advertises_its_standards(bare_manager):
    assert bare_manager.get_list_standard() == ["iso2", "iso3", "name", "num"]


def test_geomanager_default_standard_is_the_first_one(bare_manager):
    assert geo.GeoManager._list_standard[0] == "iso2"


def test_geomanager_advertises_its_outputs(bare_manager):
    assert bare_manager.get_list_output() == ["list", "dict", "pandas"]


def test_geomanager_advertises_its_databases(bare_manager):
    databases = bare_manager.get_list_db()
    assert databases[0] is None  # best-effort translation is the default
    assert "jhu" in databases
    assert "owid" in databases


# --------------------------------------------------------------------------
# GeoInfo : field catalogue
# --------------------------------------------------------------------------

@pytest.fixture
def bare_info():
    """Build a GeoInfo without __init__, hence without any download.

    ``GeoInfo(0)`` would build a GeoManager, and with it a GeoRegion. Both
    methods below only read the class-level ``_list_field``, so no instance
    state is needed.
    """
    return geo.GeoInfo.__new__(geo.GeoInfo)


def test_geoinfo_lists_its_fields(bare_info):
    fields = bare_info.get_list_field()
    assert fields == sorted(fields)
    assert {"population", "geometry", "capital"} <= set(fields)


def test_geoinfo_get_source_without_argument_returns_every_source(bare_info):
    sources = bare_info.get_source()
    assert set(sources) == set(bare_info.get_list_field())


def test_geoinfo_get_source_names_the_field(bare_info):
    source = bare_info.get_source("population")
    assert source.startswith("population : ")


def test_geoinfo_get_source_rejects_an_unknown_field(bare_info):
    with pytest.raises(PyvoaError) as excinfo:
        bare_info.get_source("not_a_field")
    assert "not_a_field" in str(excinfo.value)


# --------------------------------------------------------------------------
# GeoCountry : the checks performed before any download
# --------------------------------------------------------------------------

def test_geocountry_without_country_is_not_initialised():
    country = geo.GeoCountry(None)
    assert country.get_country() is None
    assert country.is_init() is False


def test_geocountry_test_is_init_complains_when_not_initialised():
    with pytest.raises(PyvoaError) as excinfo:
        geo.GeoCountry(None).test_is_init()
    assert "country is not set" in str(excinfo.value)


def test_geocountry_rejects_an_unsupported_country():
    with pytest.raises(PyvoaError) as excinfo:
        geo.GeoCountry("XXX")
    assert "not supported" in str(excinfo.value)


def test_geocountry_lists_the_supported_countries():
    countries = geo.GeoCountry(None).get_list_countries()
    assert countries == sorted(countries)
    assert {"FRA", "USA", "DEU", "ITA"} <= set(countries)


# --------------------------------------------------------------------------
# GeoCountry : the code <-> name converters
#
# The instance is built with __new__ and handed a small hand-written
# ``_country_data``, so no upstream page is fetched. That is enough for the
# region converters too: they go through ``get_region_list()``, which
# dissolves ``_country_data`` by its region columns.
#
# The conversion is positional: result[i] translates argument[i], whatever
# the order of the underlying frame, and a repeated entry is translated as
# many times as it appears. The tests below assert that exactly.
# --------------------------------------------------------------------------

CONVERTERS = [
    "from_subregion_codes_to_names",
    "from_subregion_names_to_codes",
    "from_region_codes_to_names",
    "from_region_names_to_codes",
]


@pytest.fixture
def fake_country():
    """Build a GeoCountry over two regions, the first holding two subregions.

    ``DEU`` is deliberate: ``get_data(region_version=True)`` special-cases
    FRA, ESP, PRT, USA and EUR, and none of that machinery is under test.
    """
    frame = gpd.GeoDataFrame(
        {
            "code_region": ["01", "01", "02"],
            "name_region": ["North", "North", "South"],
            "code_subregion": ["01A", "01B", "02A"],
            "name_subregion": ["Alpha", "Beta", "Gamma"],
        },
        geometry=_squares([1, 2, 3]),
        crs="epsg:4326",
    )
    country = geo.GeoCountry.__new__(geo.GeoCountry)
    country._country = "DEU"
    country._country_data = frame
    country._country_data_region = None
    country._country_data_subregion = None
    return country


def test_from_subregion_codes_to_names_converts_every_code(fake_country):
    names = fake_country.from_subregion_codes_to_names(["01A", "01B", "02A"])
    assert names == ["Alpha", "Beta", "Gamma"]


def test_from_subregion_codes_to_names_converts_a_single_code(fake_country):
    assert fake_country.from_subregion_codes_to_names(["01B"]) == ["Beta"]


def test_from_subregion_names_to_codes_converts_a_single_name(fake_country):
    assert fake_country.from_subregion_names_to_codes(["Gamma"]) == ["02A"]


def test_the_subregion_converters_round_trip(fake_country):
    codes = ["01A", "01B", "02A"]
    names = fake_country.from_subregion_codes_to_names(codes)
    assert fake_country.from_subregion_names_to_codes(names) == codes


def test_from_region_codes_to_names_converts_every_code(fake_country):
    names = fake_country.from_region_codes_to_names(["01", "02"])
    assert names == ["North", "South"]


def test_from_region_codes_to_names_converts_a_single_code(fake_country):
    assert fake_country.from_region_codes_to_names(["02"]) == ["South"]


def test_from_region_names_to_codes_converts_a_single_name(fake_country):
    assert fake_country.from_region_names_to_codes(["North"]) == ["01"]


def test_the_region_converters_round_trip(fake_country):
    codes = ["01", "02"]
    names = fake_country.from_region_codes_to_names(codes)
    assert fake_country.from_region_names_to_codes(names) == codes


# --- order and duplicates ------------------------------------------------

@pytest.mark.parametrize(
    "method, argument, expected",
    [
        ("from_subregion_codes_to_names", ["02A", "01A", "01B"],
         ["Gamma", "Alpha", "Beta"]),
        ("from_subregion_names_to_codes", ["Gamma", "Alpha", "Beta"],
         ["02A", "01A", "01B"]),
        ("from_region_codes_to_names", ["02", "01"], ["South", "North"]),
        ("from_region_names_to_codes", ["South", "North"], ["02", "01"]),
    ],
)
def test_the_converters_answer_in_the_order_of_the_argument(
    fake_country, method, argument, expected
):
    """Against the frame order, so a filtering implementation would fail."""
    assert getattr(fake_country, method)(argument) == expected


@pytest.mark.parametrize(
    "method, argument, expected",
    [
        ("from_subregion_codes_to_names", ["01A", "01A"], ["Alpha", "Alpha"]),
        ("from_subregion_names_to_codes", ["Beta", "Beta"], ["01B", "01B"]),
        ("from_region_codes_to_names", ["01", "01"], ["North", "North"]),
        ("from_region_names_to_codes", ["South", "South"], ["02", "02"]),
    ],
)
def test_the_converters_translate_a_repeated_entry_every_time(
    fake_country, method, argument, expected
):
    assert getattr(fake_country, method)(argument) == expected


def test_the_converters_name_the_offending_entry(fake_country):
    with pytest.raises(PyvoaError) as excinfo:
        fake_country.from_subregion_codes_to_names(["01A", "99Z", "88Y"])
    message = str(excinfo.value)
    assert "99Z" in message and "88Y" in message
    assert "01A" not in message  # the known one is not reported as missing


def test_a_region_gathers_its_subregions(fake_country):
    """Region 01 holds two subregions, so it must still convert as one code."""
    assert fake_country.from_region_codes_to_names(["01"]) == ["North"]


@pytest.mark.parametrize(
    "method, unknown",
    [
        ("from_subregion_codes_to_names", ["01A", "99Z"]),
        ("from_subregion_names_to_codes", ["Alpha", "Nowhere"]),
        ("from_region_codes_to_names", ["01", "99"]),
        ("from_region_names_to_codes", ["North", "Nowhere"]),
    ],
)
def test_the_converters_reject_an_unknown_entry(fake_country, method, unknown):
    with pytest.raises(PyvoaError) as excinfo:
        getattr(fake_country, method)(unknown)
    assert "do not exist" in str(excinfo.value)


@pytest.mark.parametrize("method", CONVERTERS)
@pytest.mark.parametrize("bad_input", ["01A", None, ("01A",)])
def test_the_converters_reject_a_non_list(fake_country, method, bad_input):
    with pytest.raises(PyvoaError) as excinfo:
        getattr(fake_country, method)(bad_input)
    assert "should be a list" in str(excinfo.value)


@pytest.mark.parametrize("method", CONVERTERS)
def test_the_converters_complain_when_the_country_is_not_set(method):
    with pytest.raises(PyvoaError) as excinfo:
        getattr(geo.GeoCountry(None), method)(["anything"])
    assert "country is not set" in str(excinfo.value)


@pytest.mark.parametrize("method", CONVERTERS)
def test_the_converters_accept_an_empty_list(fake_country, method):
    assert getattr(fake_country, method)([]) == []


# --------------------------------------------------------------------------
# pack_polygons_grid_by_area : pure geometry
# --------------------------------------------------------------------------

def _squares(sizes):
    return [sg.box(0, 0, size, size) for size in sizes]


def _frame(sizes):
    return gpd.GeoDataFrame({"name": list("abcdefgh")[: len(sizes)]},
                            geometry=_squares(sizes), crs="epsg:4326")


def test_pack_polygons_keeps_every_polygon_and_its_attributes():
    packed = geo.pack_polygons_grid_by_area(_frame([1, 2, 3, 4]))
    assert len(packed) == 4
    assert set(packed["name"]) == {"a", "b", "c", "d"}


def test_pack_polygons_preserves_the_shapes():
    packed = geo.pack_polygons_grid_by_area(_frame([1, 2, 3]))
    assert sorted(round(g.area, 6) for g in packed.geometry) == [1.0, 4.0, 9.0]


def test_pack_polygons_sorts_by_decreasing_area_by_default():
    packed = geo.pack_polygons_grid_by_area(_frame([1, 3, 2]))
    assert [round(g.area) for g in packed.geometry] == [9, 4, 1]


def test_pack_polygons_can_sort_by_increasing_area():
    packed = geo.pack_polygons_grid_by_area(_frame([1, 3, 2]), ascending=True)
    assert [round(g.area) for g in packed.geometry] == [1, 4, 9]


def test_pack_polygons_does_not_overlap_the_bounding_boxes():
    packed = geo.pack_polygons_grid_by_area(_frame([1, 2, 3, 4]), n_cols=2)
    boxes = [sg.box(*g.bounds) for g in packed.geometry]
    for i, first in enumerate(boxes):
        for second in boxes[i + 1:]:
            assert first.intersection(second).area == pytest.approx(0)


def test_pack_polygons_lays_out_the_requested_number_of_columns():
    packed = geo.pack_polygons_grid_by_area(_frame([4, 3, 2, 1]), n_cols=2)
    rows = {round(g.bounds[1], 6) for g in packed.geometry}
    assert len(rows) == 2  # 4 polygons over 2 columns is 2 rows


def test_pack_polygons_honours_the_gap():
    without = geo.pack_polygons_grid_by_area(_frame([1, 1, 1, 1]), n_cols=2)
    with_gap = geo.pack_polygons_grid_by_area(_frame([1, 1, 1, 1]), n_cols=2, gap=5)
    def span(p):
        return max(g.bounds[2] for g in p.geometry)
    assert span(with_gap) > span(without) + 4


def test_pack_polygons_applies_the_global_translation():
    reference = geo.pack_polygons_grid_by_area(_frame([1, 2]))
    shifted = geo.pack_polygons_grid_by_area(_frame([1, 2]), x=100, y=50)
    assert shifted.geometry.iloc[0].bounds[0] == pytest.approx(
        reference.geometry.iloc[0].bounds[0] + 100
    )
    assert shifted.geometry.iloc[0].bounds[1] == pytest.approx(
        reference.geometry.iloc[0].bounds[1] + 50
    )


def test_pack_polygons_returns_a_geoseries_for_a_geoseries():
    series = gpd.GeoSeries(_squares([1, 2, 3]), crs="epsg:4326")
    packed = geo.pack_polygons_grid_by_area(series)
    assert isinstance(packed, gpd.GeoSeries)
    assert len(packed) == 3


def test_pack_polygons_tolerates_empty_geometries():
    frame = gpd.GeoDataFrame(
        {"name": ["a", "b"]},
        geometry=[sg.Polygon(), sg.Polygon()],
        crs="epsg:4326",
    )
    packed = geo.pack_polygons_grid_by_area(frame)
    assert len(packed) == 2
    assert all(g.is_empty for g in packed.geometry)
