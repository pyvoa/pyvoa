"""Document the bokeh callbacks of ``pyvoa/js/`` from their header comments.

autodoc reads python only. The callbacks open on a ``/* */`` comment written
like a numpydoc module docstring -- ``tests/test_docstrings.py`` keeps it so --
which napoleon turns into reST as it would a docstring. Each file becomes a
``js:function`` of Sphinx's own javascript domain, named after the file and
taking the names it is handed, followed by its source.

The ``jscallbacks`` directive lists every file of the directory, so that a
new callback is documented without a page of its own.
"""

from __future__ import annotations

import re
from pathlib import Path

from sphinx.ext.napoleon.docstring import NumpyDocstring
from sphinx.util.docutils import SphinxDirective

JS = Path(__file__).resolve().parents[2] / "pyvoa" / "js"

# The common block closing every header; the page states it once instead.
BLOCK = "\nProject :"


def header(path: Path) -> str:
    """Return the header comment of a callback, less the common block."""
    text = path.read_text(encoding="utf-8")
    comment = text[text.index("/*") + 2:text.index("*/")].strip("\n")
    return comment.split(BLOCK)[0].rstrip()


class JSCallbacks(SphinxDirective):
    """List every callback of pyvoa/js/, its documentation and its source."""

    has_content = False

    def run(self):
        """Return the nodes documenting each callback."""
        lines = []
        for path in sorted(JS.glob("*.js")):
            self.env.note_dependency(str(path))
            body = str(NumpyDocstring(header(path), self.config, self.env.app,
                                      what="function", name=path.stem)).splitlines()
            names = []
            for line in body:
                m = re.match(r":param ([^:]+):", line)
                if m:
                    names += [n.strip() for n in m.group(1).split(",")]
            lines += [f".. js:function:: {path.stem}({', '.join(names)})", ""]
            lines += ["   " + line if line else "" for line in body]
            lines += [
                "",
                f"   Source: ``pyvoa/js/{path.name}``, the comment left out.",
                "",
                f"   .. literalinclude:: /../pyvoa/js/{path.name}",
                "      :language: javascript",
                "      :tab-width: 4",
                "      :start-after: */",
                "",
            ]
        return self.parse_text_to_nodes("\n".join(lines))


def setup(app):
    """Register the directive."""
    app.add_directive("jscallbacks", JSCallbacks)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
