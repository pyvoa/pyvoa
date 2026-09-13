"""Unit tests for pyvoa._banner.

The banner is the very first thing a user sees, and it is printed at import
time of :mod:`pyvoa.front`, so a failure there breaks the whole library for
everyone. Everything here is pure string work: the module imports nothing
heavier than the standard library, and none of these tests touches the
network.

The three rendering paths (HTML in a kernel, ANSI in a colour terminal,
plain text otherwise) are exercised through ``print_banner`` with the
environment faked, since in CI stdout is never a tty and there is never an
IPython kernel -- i.e. only the plain-text path would ever run on its own.
"""

import html as htmllib
import re
import subprocess
import sys
from pathlib import Path

import pytest

from pyvoa import _banner

SGR = re.compile(r"\033\[[0-9;]*m")
TAG = re.compile(r"<[^>]+>")

ROOT = Path(__file__).resolve().parents[1]


def visible(line):
    """Return an ANSI-coloured line stripped of its escape sequences."""
    return SGR.sub("", line)


def untagged(row):
    """Return an HTML row stripped of its tags, entities resolved."""
    return htmllib.unescape(TAG.sub("", row))


# --------------------------------------------------------------------------
# the icon itself
# --------------------------------------------------------------------------

def test_every_icon_row_has_the_same_visible_width():
    widths = {len(visible(line)) for line in _banner._ICON}
    assert len(widths) == 1, f"ragged icon: {widths}"


def test_icon_cells_are_block_glyphs_or_spaces():
    for line in _banner._ICON:
        for char in visible(line):
            assert char == " " or "▀" <= char <= "▟", repr(char)


def test_icon_only_uses_the_sgr_vocabulary_the_html_renderer_parses():
    # _icon_to_html_rows is deliberately not a general ANSI-to-HTML converter:
    # it understands a reset, a background reset and 24-bit colour, and would
    # silently drop anything else that crept into _ICON.
    for line in _banner._ICON:
        for codes in re.findall(r"\033\[([0-9;]*)m", line):
            parts = codes.split(";")
            assert parts[0] in ("", "0", "49", "38", "48"), codes
            if parts[0] in ("38", "48"):
                assert parts[1] == "2" and len(parts) == 5, codes


def test_every_icon_row_ends_neutral():
    for line in _banner._ICON:
        assert line.endswith(_banner._RESET), repr(line[-10:])


# --------------------------------------------------------------------------
# colour capability
# --------------------------------------------------------------------------

@pytest.fixture
def a_tty(monkeypatch):
    """Make stdout look like an interactive terminal with a colour-capable TERM."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)


def test_color_capable_on_a_colour_terminal(a_tty):
    assert _banner._color_capable() is True


def test_color_capable_honours_no_color(a_tty, monkeypatch):
    monkeypatch.setenv("NO_COLOR", "")
    assert _banner._color_capable() is False


def test_color_capable_refuses_a_dumb_terminal(a_tty, monkeypatch):
    monkeypatch.setenv("TERM", "dumb")
    assert _banner._color_capable() is False


def test_color_capable_refuses_a_pipe(a_tty, monkeypatch):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False, raising=False)
    assert _banner._color_capable() is False


def test_color_capable_survives_a_broken_stdout(a_tty, monkeypatch):
    def boom():
        raise ValueError("I/O operation on closed file")

    monkeypatch.setattr(sys.stdout, "isatty", boom, raising=False)
    assert _banner._color_capable() is False


# --------------------------------------------------------------------------
# kernel detection
# --------------------------------------------------------------------------

class FakeShell:
    """Stand-in for whatever IPython.get_ipython() returns."""

    def __init__(self, name):
        self.__class__ = type(name, (object,), {})


def fake_get_ipython(monkeypatch, shell):
    import IPython

    monkeypatch.setattr(IPython, "get_ipython", lambda: shell)


def test_not_in_jupyter_outside_any_shell(monkeypatch):
    fake_get_ipython(monkeypatch, None)
    assert _banner._in_jupyter() is False


def test_not_in_jupyter_in_a_terminal_shell(monkeypatch):
    fake_get_ipython(monkeypatch, FakeShell("TerminalInteractiveShell"))
    assert _banner._in_jupyter() is False


def test_in_jupyter_in_a_kernel(monkeypatch):
    fake_get_ipython(monkeypatch, FakeShell("ZMQInteractiveShell"))
    assert _banner._in_jupyter() is True


def test_not_in_jupyter_when_ipython_cannot_be_imported(monkeypatch):
    monkeypatch.setitem(sys.modules, "IPython", None)
    assert _banner._in_jupyter() is False


# --------------------------------------------------------------------------
# caption / icon zipping
# --------------------------------------------------------------------------

def test_rows_yields_one_pair_per_icon_row():
    rows = list(_banner._rows(_banner._ICON, _banner._CAPTION, "1.2.3"))
    assert len(rows) == len(_banner._ICON)
    assert [icon for icon, _ in rows] == _banner._ICON


def test_rows_centers_the_caption_vertically():
    icon = ["i0", "i1", "i2", "i3", "i4"]
    assert list(_banner._rows(icon, ["c0", "c1"], "x")) == [
        ("i0", ""),
        ("i1", "c0"),
        ("i2", "c1"),
        ("i3", ""),
        ("i4", ""),
    ]


def test_rows_substitutes_the_version():
    rows = list(_banner._rows(["a"], ["v{version}"], "9.9.9"))
    assert rows == [("a", "v9.9.9")]


def test_rows_truncates_a_caption_taller_than_the_icon():
    rows = list(_banner._rows(["a"], ["c0", "c1", "c2"], "x"))
    assert rows == [("a", "c0")]


# --------------------------------------------------------------------------
# ANSI rendering
# --------------------------------------------------------------------------

def test_render_ansi_has_one_line_per_icon_row():
    assert len(_banner.render_ansi("1.2.3").splitlines()) == len(_banner._ICON)


def test_render_ansi_advertises_the_version_and_the_url():
    out = visible(_banner.render_ansi("1.2.3"))
    assert "Pyvoa" in out
    assert "(version 1.2.3)" in out
    assert "https://pyvoa.org" in out
    assert "{version}" not in out


def test_render_ansi_keeps_the_icon_intact():
    rendered = _banner.render_ansi("1.2.3").splitlines()
    for line, icon in zip(rendered, _banner._ICON):
        assert visible(line).startswith(" " + visible(icon))


# --------------------------------------------------------------------------
# HTML rendering
# --------------------------------------------------------------------------

def test_icon_to_html_rows_matches_the_icon_glyph_for_glyph():
    rows = _banner._icon_to_html_rows()
    assert len(rows) == len(_banner._ICON)
    for row, line in zip(rows, _banner._ICON):
        assert untagged(row) == visible(line)


def test_icon_to_html_rows_leaves_no_escape_sequence_behind():
    assert "\033" not in "".join(_banner._icon_to_html_rows())


def test_icon_to_html_rows_translates_a_foreground_colour(monkeypatch):
    monkeypatch.setattr(_banner, "_ICON", ["\033[0m \033[49m\033[38;2;1;2;3m▄\033[0m"])
    assert _banner._icon_to_html_rows() == [
        '<span> </span><span style="color:rgb(1,2,3)">▄</span>'
    ]


def test_icon_to_html_rows_translates_a_background_colour(monkeypatch):
    monkeypatch.setattr(_banner, "_ICON", ["\033[48;2;9;8;7mX\033[0m"])
    assert _banner._icon_to_html_rows() == [
        '<span style="background-color:rgb(9,8,7)">X</span>'
    ]


def test_icon_to_html_rows_forgets_the_background_on_reset(monkeypatch):
    monkeypatch.setattr(_banner, "_ICON", ["\033[48;2;9;8;7m\033[49mX\033[0m"])
    assert _banner._icon_to_html_rows() == ["<span>X</span>"]


def test_render_html_is_one_div_per_icon_row():
    assert _banner.render_html("1.2.3").count("<div>") == len(_banner._ICON)


def test_render_html_advertises_the_version_and_the_url():
    out = _banner.render_html("1.2.3")
    assert "(version 1.2.3)" in out
    assert 'href="https://pyvoa.org"' in out
    assert "{version}" not in out


def test_render_html_carries_no_ansi_escape():
    assert "\033" not in _banner.render_html("1.2.3")


def test_render_html_escapes_the_version():
    out = _banner.render_html("<script>alert(1)</script>")
    assert "<script>" not in out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out


# --------------------------------------------------------------------------
# dispatch
# --------------------------------------------------------------------------

@pytest.fixture
def dispatch(monkeypatch):
    """Return a setter for the two conditions print_banner dispatches on."""
    def choose(jupyter=False, color=False):
        monkeypatch.setattr(_banner, "_in_jupyter", lambda: jupyter)
        monkeypatch.setattr(_banner, "_color_capable", lambda: color)

    return choose


def test_print_banner_displays_html_in_a_kernel(dispatch, capsys, monkeypatch):
    import IPython.display

    shown = []
    monkeypatch.setattr(IPython.display, "display", shown.append)
    dispatch(jupyter=True)
    _banner.print_banner("1.2.3")
    assert capsys.readouterr().out == ""
    assert len(shown) == 1
    assert "(version 1.2.3)" in shown[0].data


def test_print_banner_prints_ansi_on_a_colour_terminal(dispatch, capsys):
    dispatch(color=True)
    _banner.print_banner("1.2.3")
    out = capsys.readouterr().out
    assert out == _banner.render_ansi("1.2.3") + "\n"
    assert "\033[38;2;" in out


def test_print_banner_falls_back_to_plain_text(dispatch, capsys):
    dispatch()
    _banner.print_banner("1.2.3")
    out = capsys.readouterr().out
    assert "\033" not in out
    assert "1.2.3" in out
    assert "https://pyvoa.org" in out


# --------------------------------------------------------------------------
# wiring and import cost
# --------------------------------------------------------------------------

def test_front_prints_the_banner_at_import_time():
    source = (ROOT / "pyvoa" / "front.py").read_text(encoding="utf-8")
    assert re.search(r"^print_banner\(getversion\(\)\)", source, re.MULTILINE)


def test_importing_the_banner_pulls_in_nothing_heavy():
    # print_banner runs on every `import pyvoa.front`, so it must not add a
    # dependency of its own: IPython is imported inside _in_jupyter, and only
    # when there is a kernel to import it for.
    code = (
        "import sys; import pyvoa._banner; "
        "print([m for m in ('pandas', 'geopandas', 'numpy', 'IPython') "
        "if m in sys.modules])"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    assert out.strip() == "[]"
