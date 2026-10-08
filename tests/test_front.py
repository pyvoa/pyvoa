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
