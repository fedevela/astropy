# Licensed under a 3-clause BSD style license
"""
:Author: Simon Gibbons (simongibbons@gmail.com)
"""


from .core import DefaultSplitter
from .fixedwidth import (
    FixedWidth,
    FixedWidthData,
    FixedWidthHeader,
    FixedWidthTwoLineDataSplitter,
)


class SimpleRSTHeader(FixedWidthHeader):
    position_line = 0
    start_line = 1
    splitter_class = DefaultSplitter
    position_char = "="

    def get_fixedwidth_params(self, line):
        vals, starts, ends = super().get_fixedwidth_params(line)
        # The right hand column can be unbounded
        ends[-1] = None
        return vals, starts, ends


class SimpleRSTData(FixedWidthData):
    start_line = 3
    end_line = -1
    splitter_class = FixedWidthTwoLineDataSplitter


class RST(FixedWidth):
    """reStructuredText simple format table.

    See: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#simple-tables

    Example::

        ==== ===== ======
        Col1  Col2  Col3
        ==== ===== ======
          1    2.3  Hello
          2    4.5  Worlds
        ==== ===== ======

    Currently there is no support for reading tables which utilize continuation lines,
    or for ones which define column spans through the use of an additional
    line of dashes in the header.

    """

    _format_name = "rst"
    _description = "reStructuredText simple table"
    data_class = SimpleRSTData
    header_class = SimpleRSTHeader

    def __init__(self, header_rows=None):
        # ASTRST-001 state machine:
        # INPUT: header_rows passed by the writer factory (typically ascii.write(...)).
        # DECISION:
        #   - If caller provided a header_rows value, keep it as-is.
        #   - If caller omitted it, default to None.
        # ACTION: Pass only write-time formatting knobs to FixedWidth constructor.
        # OUTPUT: Writer instance configured with:
        #   delimiter_pad=None, bookend=False, header_rows=<provided_or_default>.
        # GUARD: This path must never call reader/parser components.
        # SUCCESS PATH: Construction returns without "unexpected keyword argument 'header_rows'".
        super().__init__(
            delimiter_pad=None, bookend=False, header_rows=header_rows
        )

    def write(self, lines):
        # ASTRST-006 write-path-only contract:
        # INPUT: list `lines` from FixedWidth write formatting.
        # TRANSITION:
        #   1) Keep parent's column-alignment behavior untouched.
        #   2) Build final framed output by prepending and appending divider row at the
        #      post-header separator position.
        # OUTPUT: rst body wrapped by identical border lines.
        # LIMIT: No reader parsing behavior, validation, or path branching.
        lines = super().write(lines)
        header_rows = getattr(self.data, "header_rows", ["name"])
        border = lines[len(header_rows)]
        lines = [border] + lines + [border]
        return lines
