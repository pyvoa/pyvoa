"""Shared fixtures for the pyvoa test suite.

Two invariants are enforced here for every test that is *not* marked
``network``:

* no socket may be opened, so the default selection can never depend on
  the availability of an upstream server;
* the pyvoa cache directory points inside the test's own tmp_path, so a
  test run never reads nor pollutes ``~/.cache/pyvoa.data_<user>``.

matplotlib draws on the non-interactive Agg backend for the whole suite, so
a test that draws a chart never opens a window a terminal run would wait on.
For the same reason pyvoa is kept in batch mode: under bokeh, a chart shown
outside a notebook is written to an html file and opened in the browser.
Selecting Agg is not enough on its own: ``visu_matplotlib()`` picks TkAgg
outside a notebook, at every chart, unless ``MPLBACKEND`` names a backend, so
the variable is set as well.
"""

import os
import socket
from pathlib import Path

import matplotlib
import pytest

# before pyplot is imported anywhere: conftest is read before the test modules
os.environ["MPLBACKEND"] = "Agg"
matplotlib.use("Agg")

from pyvoa import tools

DATA = Path(__file__).parent / "data"


@pytest.fixture(autouse=True)
def no_network(request, monkeypatch):
    """Forbid any socket creation unless the test is marked ``network``."""
    if request.node.get_closest_marker("network"):
        return

    def guard(*args, **kwargs):
        raise RuntimeError(
            "This test tried to reach the network. Offline tests must stub "
            "get_local_from_url (in the module that imported it), or be "
            "marked with @pytest.mark.network."
        )

    monkeypatch.setattr(socket, "socket", guard)
    monkeypatch.setattr(socket, "create_connection", guard)


@pytest.fixture(autouse=True)
def quiet_verbosity():
    """Restore the global verbosity after each test that changes it."""
    previous = tools.get_verbose_mode()
    tools.set_verbose_mode(0)
    yield
    tools.set_verbose_mode(previous)


@pytest.fixture(autouse=True)
def batch_charts(monkeypatch):
    """Draw the charts without showing them, as setbatch() does."""
    import pyvoa.front as pf

    monkeypatch.setattr(pf.__pyvoafront_instance__, "batch", True)


@pytest.fixture(autouse=True)
def archived_data_source():
    """Restore the global data source mode after each test that changes it."""
    previous = tools.get_live_mode()
    tools.set_live_mode(False)
    yield
    tools.set_live_mode(previous)


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    """Redirect the pyvoa download/pickle cache into a temporary directory."""
    cache = tmp_path / "pyvoa-cache"
    cache.mkdir()
    monkeypatch.setattr(tools, "tmpdir", str(cache))
    monkeypatch.setattr(tools, "pklpath", str(cache))
    return cache
