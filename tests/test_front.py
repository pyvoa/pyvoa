import shutil
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import pyvoa
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


def test_getversion_is_git_describe_in_a_checkout():
    root = Path(pf.__file__).resolve().parent.parent
    if not (root / '.git').exists() or shutil.which('git') is None:
        pytest.skip('not a git checkout of pyvoa')
    expected = subprocess.run(
        ['git', '-C', str(root), 'describe', '--tags', '--always', '--dirty'],
        capture_output=True, encoding='utf-8', check=True,
    ).stdout.strip()
    assert pf.getversion() == expected


def test_getversion_falls_back_to_the_release_number_without_git(monkeypatch):
    def no_git(*args, **kwargs):
        raise FileNotFoundError('git')
    monkeypatch.setattr(pf.subprocess, 'run', no_git)
    assert pf.getversion() == 'v' + pyvoa.__version__


@pytest.mark.parametrize('requested, expected', [
    ('', '-g512aefe'),
    ('main', '-g512aefe'),
    ('v' + pyvoa.__version__, ''),
])
def test_getversion_names_the_commit_pip_installed_from_git(monkeypatch, requested, expected):
    monkeypatch.setattr(pf, '_git_describe', lambda root: '')
    monkeypatch.setattr(pf, '_pip_git_commit',
                        lambda here: ('512aefe842db700c34334cde9da0fa6159a3aaf8', requested))
    assert pf.getversion() == 'v' + pyvoa.__version__ + expected


class FakeDistribution:
    """Stand in for the importlib.metadata view of an installed pyvoa."""

    def __init__(self, front, direct_url):
        self.front, self.direct_url = front, direct_url

    def locate_file(self, path):
        """Return where the installation keeps ``path``."""
        return self.front

    def read_text(self, name):
        """Return the ``direct_url.json`` pip wrote, or None."""
        return self.direct_url


GIT_URL = '{"url": "https://github.com/pyvoa/pyvoa.git", "vcs_info": {"vcs": "git", %s}}'


@pytest.mark.parametrize('direct_url, expected', [
    (GIT_URL % '"commit_id": "512aefe842db", "requested_revision": "main"', ('512aefe842db', 'main')),
    (GIT_URL % '"commit_id": "512aefe842db"', ('512aefe842db', '')),
    ('{"url": "file:///home/someone/pyvoa", "dir_info": {}}', ('', '')),
    (None, ('', '')),
])
def test_pip_git_commit_reads_direct_url(monkeypatch, tmp_path, direct_url, expected):
    front = tmp_path / 'pyvoa' / 'front.py'
    monkeypatch.setattr(pf.metadata, 'distribution', lambda name: FakeDistribution(front, direct_url))
    assert pf._pip_git_commit(front.resolve()) == expected


def test_pip_git_commit_ignores_another_copy(monkeypatch, tmp_path):
    direct_url = '{"vcs_info": {"vcs": "git", "commit_id": "512aefe842db"}}'
    monkeypatch.setattr(pf.metadata, 'distribution',
                        lambda name: FakeDistribution(tmp_path / 'other' / 'front.py', direct_url))
    assert pf._pip_git_commit((tmp_path / 'pyvoa' / 'front.py').resolve()) == ('', '')
