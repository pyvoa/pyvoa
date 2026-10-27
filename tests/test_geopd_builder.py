"""Offline tests of the population normalisation, GPDBuilder.normbypop()."""

import pandas as pd
import pytest

import pyvoa.geo as coge
from pyvoa import geopd_builder
from pyvoa.geopd_builder import GPDBuilder
from pyvoa.tools import PyvoaError


class _Country(coge.GeoCountry):
    """A national geography of three zones, the INRB way: mixed-case codes."""

    def __init__(self, with_population=True):
        self._data = pd.DataFrame({
            'name_subregion': ['Bunia', 'Nizi', 'Kitona'],
            'code_subregion': ['GPI6I83O7L6', 'Nz4kQ', 'ADqfcJ05GHD'],
        })
        if with_population:
            self._data['population_subregion'] = [500000.0, 200000.0, None]

    def get_country(self):
        return 'COD'

    def get_list_properties(self):
        return list(self._data.columns)

    def get_data(self, region_version=False):
        return self._data


def _builder(country):
    builder = GPDBuilder.__new__(GPDBuilder)
    builder.db = 'ebolardc'
    builder.db_world = False
    builder.granularity = 'subregion'
    builder.geo = country
    builder._gi = country
    return builder


def _frame(where, codes):
    """Return two dates of a count, with the codes upper-cased as the parser does."""
    return pd.DataFrame({
        'date': pd.to_datetime(['2026-10-01', '2026-10-02']).repeat(len(where)),
        'where': where * 2,
        'code': [c.upper() for c in codes] * 2,
        'cases': [10.0, 20.0, 30.0][:len(where)] * 2,
    })


def test_normbypop_matches_mixed_case_codes(monkeypatch):
    # the parser upper-cases 'ADqfcJ05GHD': a plain join found one zone of 519
    monkeypatch.setattr(geopd_builder, 'PyvoaWarning', lambda message: None)
    frame = _frame(['Bunia', 'Nizi'], ['GPI6I83O7L6', 'Nz4kQ'])
    out = _builder(_Country()).normbypop(frame, 'cases', 'normalize:pop100k')
    last = out[out['date'] == out['date'].max()].set_index('where')
    assert last.loc['Bunia', 'cases normalize:pop100k'] == pytest.approx(10 / 500000 * 1e5)
    assert last.loc['Nizi', 'cases normalize:pop100k'] == pytest.approx(20 / 200000 * 1e5)


def test_normbypop_names_the_locations_asked_for_without_population(monkeypatch):
    warnings = []
    monkeypatch.setattr(geopd_builder, 'PyvoaWarning', warnings.append)
    builder = _builder(_Country())
    builder.normbypop(_frame(['Bunia', 'Nizi'], ['GPI6I83O7L6', 'Nz4kQ']), 'cases', 'normalize:pop')
    # Kitona has no population, but was not asked for: nothing to say
    assert warnings == []
    out = builder.normbypop(_frame(['Bunia', 'Kitona'], ['GPI6I83O7L6', 'ADqfcJ05GHD']),
                            'cases', 'normalize:pop')
    assert len(warnings) == 1 and 'Kitona' in warnings[0] and 'Bunia' not in warnings[0]
    assert out.loc[out['where'] == 'Kitona', 'cases normalize:pop'].isna().all()


def test_normbypop_says_when_a_geography_has_no_population():
    builder = _builder(_Country(with_population=False))
    with pytest.raises(PyvoaError, match='No population is known for the subregions of Congo, The Democratic Republic of the'):
        builder.normbypop(_frame(['Bunia'], ['GPI6I83O7L6']), 'cases', 'normalize:pop')
