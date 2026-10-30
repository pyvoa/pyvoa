import matplotlib.pyplot as plt
import pandas as pd
import pytest

import pyvoa.front as pf


@pytest.fixture
def in_house_frame(cache_dir):
    """Return a small in-house frame, and close the figures drawn from it."""
    yield pd.DataFrame({
        'date': pd.to_datetime(['2021-03-17', '2021-03-17',
                                '2021-03-18', '2021-03-18']),
        'where': ['Ain', 'Aisne', 'Ain', 'Aisne'],
        'cur_rea': [1.0, 2.0, 3.0, 4.0],
    })
    plt.close('all')


def test_a_frame_from_get_can_be_plotted_back(in_house_frame):
    z = pf.get(input=in_house_frame, which='cur_rea')
    # get() hands 'where' out as a Categorical, which plot() used to choke on
    assert isinstance(z['where'].dtype, pd.CategoricalDtype)
    pf.setvis('matplotlib')
    pf.plot(input=z, which='cur_rea')


def test_get_and_plot_leave_the_caller_frame_untouched(in_house_frame):
    before = in_house_frame.copy()
    z = pf.get(input=in_house_frame, which='cur_rea')
    pd.testing.assert_frame_equal(in_house_frame, before)
    z_before = z.copy()
    pf.setvis('matplotlib')
    pf.plot(input=z, which='cur_rea')
    pd.testing.assert_frame_equal(z, z_before)


def test_when_cuts_an_in_house_frame(cache_dir):
    days = pd.date_range('2021-03-01', '2021-03-10')
    frame = pd.DataFrame({
        'date': days.repeat(2),
        'where': ['Ain', 'Aisne'] * len(days),
        'cur_rea': range(2 * len(days)),
    })
    z = pf.get(input=frame, which='cur_rea', when='03/03/2021:05/03/2021')
    assert sorted(z['date'].unique()) == list(pd.date_range('2021-03-03', '2021-03-05'))
    # the case first reported: a frame from get(), cut afterwards
    z = pf.get(input=frame, which='cur_rea', option='sumall', what='daily')
    z = pf.get(input=z, when='03/03/2021:05/03/2021')
    assert sorted(z['date'].unique()) == list(pd.date_range('2021-03-03', '2021-03-05'))


@pytest.mark.parametrize('lister', [pf.listtile, pf.listprojection])
def test_map_listers_ask_for_setvis_first(monkeypatch, lister):
    # used to fail on self.av.pdcharts[None] with a bare KeyError
    monkeypatch.setattr(pf.__pyvoafront_instance__, 'vis', None)
    with pytest.raises(pf.PyvoaError, match='Vis has not be set'):
        lister()


@pytest.mark.parametrize('vis', ['matplotlib', 'bokeh'])
def test_plot_refuses_the_dateslider(in_house_frame, vis):
    # a time series draws every date already: plot() used to take the keyword
    # and ignore it
    if vis == 'bokeh':
        pytest.importorskip('bokeh')
    pf.setvis(vis)
    z = pf.get(input=in_house_frame, which='cur_rea')
    with pytest.raises(pf.PyvoaError, match='dateslider'):
        pf.plot(input=z, which='cur_rea', dateslider=True)


def test_where_selects_the_locations_of_an_in_house_frame(in_house_frame):
    # 'where' was ignored for a table of one's own: every location came back
    z = pf.get(input=in_house_frame, which='cur_rea', where='Ain')
    assert list(z['where'].astype(str).unique()) == ['Ain']
    # compared upper-cased, as the locations of a database are
    z = pf.get(input=in_house_frame, which='cur_rea', where=['aisne'])
    assert list(z['where'].astype(str).unique()) == ['Aisne']


def test_sumall_adds_up_the_selected_locations_of_an_in_house_frame(in_house_frame):
    frame = pd.concat([in_house_frame, in_house_frame.assign(
        where='Allier', cur_rea=in_house_frame['cur_rea'] * 10)], ignore_index=True)
    z = pf.get(input=frame, which='cur_rea', where=['Ain', 'Aisne'], option='sumall')
    assert list(z['where'].unique()) == ['Ain,Aisne']
    assert z.set_index('date')['cur_rea sumall'].tolist() == [3.0, 7.0]


@pytest.fixture
def late_frame(cache_dir):
    """Return a frame where Aisne starts reporting four days after Ain."""
    days = pd.date_range('2021-03-01', '2021-03-14')
    yield pd.DataFrame({
        'date': days.repeat(2),
        'where': ['Ain', 'Aisne'] * len(days),
        'cur_rea': [v for d in range(len(days))
                    for v in (float(d + 1), float('nan') if d < 4 else 10.0 * d)],
    })
    plt.close('all')


def test_get_gives_no_value_before_a_series_starts(late_frame):
    # the days before Aisne's first value used to take that first value
    z = pf.get(input=late_frame, which='cur_rea')
    aisne = z[z['where'] == 'Aisne'].set_index('date')['cur_rea']
    assert aisne[:'2021-03-04'].isna().all()
    assert aisne['2021-03-05':].tolist() == [10.0 * d for d in range(4, 14)]
    ain = z[z['where'] == 'Ain'].set_index('date')['cur_rea']
    assert ain.tolist() == [float(d) for d in range(1, 15)]


@pytest.mark.parametrize('kwargs, column', [
    ({'what': 'daily'}, 'cur_rea daily'),
    ({'what': 'weekly'}, 'cur_rea weekly'),
    ({'option': 'smooth7'}, 'cur_rea smooth7'),
])
def test_daily_and_smooth7_give_no_value_before_a_series_starts(late_frame, kwargs, column):
    z = pf.get(input=late_frame, which='cur_rea', **kwargs)
    aisne = z[z['where'] == 'Aisne'].set_index('date')[column]
    assert aisne[:'2021-03-04'].isna().all()
    assert aisne['2021-03-05':].notna().all()


def test_daily_takes_the_next_difference_on_a_series_first_day(late_frame):
    z = pf.get(input=late_frame, which='cur_rea', what='daily')
    aisne = z[z['where'] == 'Aisne'].set_index('date')['cur_rea daily']
    # 40 on 5 March has nothing before it: it takes the difference of 6 March
    assert aisne['2021-03-05':].tolist() == [10.0] * 10


def test_sumall_adds_only_the_series_already_started(late_frame):
    z = pf.get(input=late_frame, which='cur_rea', option='sumall')
    total = z.set_index('date')['cur_rea sumall']
    assert total[:'2021-03-04'].tolist() == [1.0, 2.0, 3.0, 4.0]
    assert total['2021-03-05'] == 5.0 + 40.0


def test_where_names_what_an_in_house_frame_lacks(in_house_frame):
    with pytest.raises(pf.PyvoaError, match='Not in your table: Paris'):
        pf.get(input=in_house_frame, which='cur_rea', where=['Ain', 'Paris'])
