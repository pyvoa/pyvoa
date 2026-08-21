"""Shared fixtures for the pyvoa test suite.

Two invariants are enforced here for every test that is *not* marked
``network``:

* no socket may be opened, so the default selection can never depend on
  the availability of an upstream server;
* the pyvoa cache directory points inside the test's own tmp_path, so a
  test run never reads nor pollutes ``~/.cache/pyvoa.data_<user>``.
"""

import socket
from pathlib import Path

import pytest

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
