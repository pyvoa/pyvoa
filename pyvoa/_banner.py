"""Terminal / notebook banner shown when :mod:`pyvoa.front` is imported.

``_ICON`` is a 24-bit ("truecolor") ANSI rendering of the pyvoa icon -- the
swirl + dotted mark from the project logo
(https://pyvoa.org/wp-content/uploads/2024/07/logo-pyvoa-1030x325.png, also
shipped as ``pyvoa/data/logo-pyvoa.png``). It was pre-rendered once,
offline, so importing :mod:`pyvoa.front` needs neither Pillow/numpy nor
network access at runtime.

It uses Unicode "quadrant" block characters (2x2 sub-pixels per character
cell -- https://en.wikipedia.org/wiki/Block_Elements) rather than plain
half-blocks (1x2): the icon has two spiral shapes (the swirl itself, and
the ring of dots), and a 1x2 sampling grid was too coarse to keep either
readable at a compact character footprint. Quadrant blocks double the
resolution in *both* directions for the same footprint, at the cost of one
colour per cell instead of two: each cell's "on" sub-pixels (alpha above a
threshold) are averaged into a single SGR "38;2;r;g;b" foreground colour
and drawn with the glyph matching their on/off pattern (e.g. "▖" for
"only the bottom-left sub-pixel is on"); "off" sub-pixels are simply not
drawn by the glyph, letting the terminal's own background show through,
which matches the source PNG's transparency. It was produced with, in
essence::

    from PIL import Image
    im = Image.open("pyvoa/data/logo-pyvoa.png").convert("RGBA")
    icon = im.crop((0, 64, 270, 213))          # icon only, wordmark dropped
    h = round(icon.height * 16 / icon.width)
    icon = icon.resize((32, 2 * h), Image.LANCZOS)  # alpha pre-multiplied, see below
    # then, per 2x2 block of pixels, threshold each sub-pixel's alpha to
    # on/off, look up the matching quadrant glyph, and colour it with the
    # average of its "on" sub-pixels.

The resize premultiplies alpha before scaling and un-premultiplies after
(as ImageMagick's -alpha Associate/Unassociate do), otherwise the fully
transparent background bleeds pale colour into the small red dots once the
icon is downscaled this far.

Two renderers share this single ``_ICON`` source of truth:

* :func:`render_ansi` -- raw ANSI escapes, for a real terminal.
* :func:`render_html` -- the same cells re-emitted as inline-styled
  ``<span>`` elements, for Jupyter/IPython front-ends.

Why two renderers instead of always emitting ANSI: ``sys.stdout`` inside an
IPython kernel is ``ipykernel.iostream.OutStream``, whose ``isatty()``
always returns ``False`` even though the front-end fully renders SGR colour
-- a long-standing, still-open upstream quirk
(https://github.com/ipython/ipykernel/issues/268,
https://github.com/ipython/ipykernel/issues/680). Detecting the kernel and
special-casing it would only fix half the problem: several notebook
front-ends have, at various times, rendered 24-bit ANSI incorrectly or not
at all (e.g. https://github.com/jupyterlab/jupyterlab/issues/3773), because
each one ships its own ANSI-to-HTML converter of varying completeness.
Building the HTML ourselves and pushing it with
``IPython.display.display(HTML(...))`` sidesteps that entirely: it only
depends on the ``text/html`` rich-display MIME type, which is a stable,
universally-implemented part of the Jupyter messaging protocol
(https://ipython.readthedocs.io/en/stable/config/integrating.html#rich-display),
rather than on any particular ANSI parser.

Project : pyvoa
Authors : Tristan Beau, Julien Browaeys, Olivier Dadoun
Copyright ©pyvoa_org
License : see the joint LICENSE file
https://pyvoa.org/
"""

import html
import os
import re
import sys

_RESET = "\033[0m"
_SGR_RE = re.compile(r"\033\[([0-9;]*)m")

# fmt: off
_ICON = [
    '\x1b[0m \x1b[49m\x1b[38;2;201;35;98m▄\x1b[49m\x1b[38;2;184;27;74m▛\x1b[49m\x1b[38;2;145;21;58m▀\x1b[49m\x1b[38;2;200;31;86m▙\x1b[49m\x1b[38;2;231;34;95m▖\x1b[0m \x1b[0m \x1b[0m \x1b[49m\x1b[38;2;149;22;60m▗\x1b[49m\x1b[38;2;164;37;76m█\x1b[49m\x1b[38;2;180;29;76m█\x1b[49m\x1b[38;2;255;37;111m▖\x1b[0m \x1b[0m \x1b[0m \x1b[0m',
    '\x1b[49m\x1b[38;2;136;20;56m▗\x1b[49m\x1b[38;2;200;34;91m▌\x1b[0m \x1b[0m \x1b[0m \x1b[49m\x1b[38;2;192;29;77m▜\x1b[0m \x1b[0m \x1b[49m\x1b[38;2;162;23;65m▗\x1b[49m\x1b[38;2;161;24;65m█\x1b[49m\x1b[38;2;203;43;98m█\x1b[49m\x1b[38;2;183;37;77m▀\x1b[0m \x1b[49m\x1b[38;2;255;13;45m▘\x1b[49m\x1b[38;2;255;0;0m▖\x1b[0m \x1b[0m',
    '\x1b[49m\x1b[38;2;195;28;79m█\x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[49m\x1b[38;2;249;36;100m▝\x1b[49m\x1b[38;2;237;34;100m▌\x1b[0m \x1b[49m\x1b[38;2;176;27;75m█\x1b[49m\x1b[38;2;163;24;65m▘\x1b[49m\x1b[38;2;255;0;2m▖\x1b[49m\x1b[38;2;255;0;0m▐\x1b[49m\x1b[38;2;255;0;0m▗\x1b[0m \x1b[49m\x1b[38;2;255;0;0m▗\x1b[0m \x1b[0m',
    '\x1b[49m\x1b[38;2;142;21;57m▌\x1b[0m \x1b[49m\x1b[38;2;255;43;114m▌\x1b[0m \x1b[0m \x1b[49m\x1b[38;2;231;36;94m▗\x1b[49m\x1b[38;2;243;43;119m▌\x1b[49m\x1b[38;2;204;33;87m▐\x1b[49m\x1b[38;2;160;24;64m▛\x1b[49m\x1b[38;2;255;0;1m▗\x1b[49m\x1b[38;2;255;0;0m▘\x1b[0m \x1b[49m\x1b[38;2;255;0;0m▝\x1b[0m \x1b[49m\x1b[38;2;255;0;0m▝\x1b[0m \x1b[0m',
    '\x1b[49m\x1b[38;2;183;27;74m█\x1b[0m \x1b[49m\x1b[38;2;232;35;92m▚\x1b[0m \x1b[0m \x1b[49m\x1b[38;2;175;26;70m▞\x1b[0m \x1b[49m\x1b[38;2;176;27;73m█\x1b[49m\x1b[38;2;187;25;73m▘\x1b[49m\x1b[38;2;255;0;0m▝\x1b[0m \x1b[49m\x1b[38;2;255;0;0m▖\x1b[0m \x1b[49m\x1b[38;2;255;0;0m▘\x1b[49m\x1b[38;2;255;0;0m▝\x1b[49m\x1b[38;2;255;0;0m▘\x1b[0m',
    '\x1b[49m\x1b[38;2;174;25;70m▐\x1b[49m\x1b[38;2;200;37;96m▌\x1b[0m \x1b[49m\x1b[38;2;243;35;99m▀\x1b[49m\x1b[38;2;238;36;97m▀\x1b[0m \x1b[49m\x1b[38;2;192;29;77m▟\x1b[49m\x1b[38;2;175;26;70m▛\x1b[0m \x1b[49m\x1b[38;2;255;0;0m▀\x1b[0m \x1b[49m\x1b[38;2;255;0;0m▘\x1b[49m\x1b[38;2;255;0;0m▀\x1b[0m \x1b[49m\x1b[38;2;255;0;0m▐\x1b[0m \x1b[0m',
    '\x1b[0m \x1b[49m\x1b[38;2;173;26;70m▜\x1b[49m\x1b[38;2;182;28;77m▙\x1b[49m\x1b[38;2;201;30;82m▄\x1b[49m\x1b[38;2;190;27;77m▄\x1b[49m\x1b[38;2;164;24;65m▟\x1b[49m\x1b[38;2;169;25;68m▛\x1b[0m \x1b[0m \x1b[0m \x1b[49m\x1b[38;2;255;0;0m▌\x1b[0m \x1b[0m \x1b[49m\x1b[38;2;255;0;0m▗\x1b[49m\x1b[38;2;255;0;0m▖\x1b[0m \x1b[0m',
    '\x1b[0m \x1b[0m \x1b[49m\x1b[38;2;198;29;79m▝\x1b[49m\x1b[38;2;143;21;58m▀\x1b[49m\x1b[38;2;144;21;58m▀\x1b[49m\x1b[38;2;207;29;84m▘\x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[49m\x1b[38;2;255;0;0m▀\x1b[49m\x1b[38;2;255;0;0m▝\x1b[0m \x1b[0m \x1b[0m \x1b[0m',
    '\x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m \x1b[0m',
]
# fmt: on

_CAPTION = [
    "",
    "\033[1m\033[38;2;235;40;40mPyvoa\033[0m  \033[2m(version {version})\033[0m",
    "\033[2mPython Virus Open Analysis\033[0m",
    "",
    "\033[4mhttps://pyvoa.org\033[0m",
    "",
]


def _in_jupyter() -> bool:
    """Return whether we are running inside an active Jupyter/IPython kernel.

    Uses the class-name check documented across the IPython ecosystem
    (``get_ipython().__class__.__name__ == "ZMQInteractiveShell"``, the
    class ipykernel actually installs as ``sys.stdout`` -- see
    https://github.com/ipython/ipykernel/blob/main/ipykernel/zmqshell.py)
    rather than the ``JPY_PARENT_PID`` environment variable alone: that
    variable is inherited by ordinary subprocesses launched from a notebook
    cell even though their stdout has nothing to do with the kernel's
    rich-display channel, which would wrongly send them down the HTML path.
    This heuristic is standard but not airtight -- ipykernel itself notes a
    misdetection case with cluster job schedulers that bypass IPKernelApp,
    see the comment and linked tqdm fix in ``ipykernel/zmqshell.py`` above.
    """
    try:
        from IPython import get_ipython
    except Exception:
        return False
    shell = get_ipython()
    return shell is not None and shell.__class__.__name__ == "ZMQInteractiveShell"


def _color_capable() -> bool:
    """Return whether stdout can be trusted to render 24-bit ANSI colour.

    Follows the same conservative checks as mainstream CLIs: no colour when
    ``NO_COLOR`` is set (https://no-color.org/), when ``TERM=dumb``, or when
    stdout is not an interactive terminal (piped to a file, captured by CI,
    ...).
    """
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _rows(icon_lines, caption, version):
    """Zip an icon (its rows) with a vertically-centered caption, row by row."""
    cap = [line.format(version=version) for line in caption]
    offset = max((len(icon_lines) - len(cap)) // 2, 0)
    for i in range(len(icon_lines)):
        j = i - offset
        yield icon_lines[i], cap[j] if 0 <= j < len(cap) else ""


def render_ansi(version: str) -> str:
    """Return the ANSI-art welcome banner as a single, ready-to-print string."""
    return "\n".join(f" {icon}   {cap}" for icon, cap in _rows(_ICON, _CAPTION, version))


def _ansi_line_to_html(line):
    """Re-emit one SGR-coloured line as inline-styled ``<span>`` HTML.

    Parses only the small, fixed vocabulary of codes this module itself
    generates (plain reset, background reset, 24-bit fg/bg) -- not a general
    ANSI-to-HTML converter -- so there is no dependency on how any given
    notebook front-end would otherwise interpret the escapes.
    """
    spans, fg, bg, pos, buf = [], None, None, 0, ""

    def flush():
        nonlocal buf
        if buf:
            style = ";".join(
                s for s in (
                    f"color:rgb({fg[0]},{fg[1]},{fg[2]})" if fg else "",
                    f"background-color:rgb({bg[0]},{bg[1]},{bg[2]})" if bg else "",
                ) if s
            )
            attr = f' style="{style}"' if style else ""
            spans.append(f"<span{attr}>{html.escape(buf)}</span>")
            buf = ""

    for m in _SGR_RE.finditer(line):
        buf += line[pos:m.start()]
        flush()
        codes = m.group(1).split(";") if m.group(1) else ["0"]
        i = 0
        while i < len(codes):
            c = codes[i]
            if c in ("", "0"):
                fg = bg = None
            elif c == "49":
                bg = None
            elif c == "38" and codes[i + 1] == "2":
                fg = tuple(int(v) for v in codes[i + 2:i + 5])
                i += 4
            elif c == "48" and codes[i + 1] == "2":
                bg = tuple(int(v) for v in codes[i + 2:i + 5])
                i += 4
            i += 1
        pos = m.end()
    buf += line[pos:]
    flush()
    return "".join(spans)


def _icon_to_html_rows():
    """Return the whole ``_ICON``, one HTML row per icon line."""
    return [_ansi_line_to_html(line) for line in _ICON]


def render_html(version: str) -> str:
    """Return the welcome banner as a self-contained HTML snippet."""
    icon_rows = _icon_to_html_rows()
    caption = [
        "",
        (
            f'<b style="color:rgb(235,40,40)">Pyvoa</b>&nbsp;&nbsp;'
            f'<span style="opacity:.6">(version {html.escape(version)})</span>'
        ),
        '<span style="opacity:.6">Python Virus Open Analysis</span>',
        "",
        '<a href="https://pyvoa.org">https://pyvoa.org</a>',
        "",
    ]
    body = "".join(
        f'<div>{icon}<span style="display:inline-block;width:1.4em"></span>{cap}</div>'
        for icon, cap in _rows(icon_rows, caption, version)
    )
    return (
        '<div style="font-family:ui-monospace,Menlo,Consolas,monospace;'
        f'line-height:1.15;white-space:pre">{body}</div>'
    )


def print_banner(version: str) -> None:
    """Show the pyvoa welcome banner (ASCII icon + version + URL).

    Dispatches to whichever of the three renderers actually applies:
    rich HTML in a Jupyter/IPython kernel, ANSI art in a real colour
    terminal, or a plain two-line fallback otherwise (piped output, CI
    logs, ``NO_COLOR``, ``TERM=dumb``).
    """
    if _in_jupyter():
        from IPython.display import HTML, display

        display(HTML(render_html(version)))
    elif _color_capable():
        print(render_ansi(version))
    else:
        print(f"Welcome to PyVOA (version {version})\nSee https://pyvoa.org")
