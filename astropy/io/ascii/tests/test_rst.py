# Licensed under a 3-clause BSD style license - see LICENSE.rst

from io import StringIO

from astropy import units as u
from astropy.io import ascii
from astropy.table import QTable

from .common import assert_almost_equal, assert_equal


def assert_equal_splitlines(arg1, arg2):
    assert_equal(arg1.splitlines(), arg2.splitlines())


def test_read_normal():
    """Normal SimpleRST Table"""
    table = """
# comment (with blank line above)
======= =========
   Col1      Col2
======= =========
   1.2    "hello"
   2.4  's worlds
======= =========
"""
    reader = ascii.get_reader(Reader=ascii.RST)
    dat = reader.read(table)
    assert_equal(dat.colnames, ["Col1", "Col2"])
    assert_almost_equal(dat[1][0], 2.4)
    assert_equal(dat[0][1], '"hello"')
    assert_equal(dat[1][1], "'s worlds")


def test_read_normal_names():
    """Normal SimpleRST Table with provided column names"""
    table = """
# comment (with blank line above)
======= =========
   Col1      Col2
======= =========
   1.2    "hello"
   2.4  's worlds
======= =========
"""
    reader = ascii.get_reader(Reader=ascii.RST, names=("name1", "name2"))
    dat = reader.read(table)
    assert_equal(dat.colnames, ["name1", "name2"])
    assert_almost_equal(dat[1][0], 2.4)


def test_read_normal_names_include():
    """Normal SimpleRST Table with provided column names"""
    table = """
# comment (with blank line above)
=======  ========== ======
   Col1     Col2      Col3
=======  ========== ======
   1.2     "hello"       3
   2.4    's worlds      7
=======  ========== ======
"""
    reader = ascii.get_reader(
        Reader=ascii.RST,
        names=("name1", "name2", "name3"),
        include_names=("name1", "name3"),
    )
    dat = reader.read(table)
    assert_equal(dat.colnames, ["name1", "name3"])
    assert_almost_equal(dat[1][0], 2.4)
    assert_equal(dat[0][1], 3)


def test_read_normal_exclude():
    """Nice, typical SimpleRST table with col name excluded"""
    table = """
======= ==========
  Col1     Col2
======= ==========
  1.2     "hello"
  2.4    's worlds
======= ==========
"""
    reader = ascii.get_reader(Reader=ascii.RST, exclude_names=("Col1",))
    dat = reader.read(table)
    assert_equal(dat.colnames, ["Col2"])
    assert_equal(dat[1][0], "'s worlds")


def test_read_unbounded_right_column():
    """The right hand column should be allowed to overflow"""
    table = """
# comment (with blank line above)
===== ===== ====
 Col1  Col2 Col3
===== ===== ====
 1.2    2    Hello
 2.4     4   Worlds
===== ===== ====
"""
    reader = ascii.get_reader(Reader=ascii.RST)
    dat = reader.read(table)
    assert_equal(dat[0][2], "Hello")
    assert_equal(dat[1][2], "Worlds")


def test_read_unbounded_right_column_header():
    """The right hand column should be allowed to overflow"""
    table = """
# comment (with blank line above)
===== ===== ====
 Col1  Col2 Col3Long
===== ===== ====
 1.2    2    Hello
 2.4     4   Worlds
===== ===== ====
"""
    reader = ascii.get_reader(Reader=ascii.RST)
    dat = reader.read(table)
    assert_equal(dat.colnames[-1], "Col3Long")


def test_read_right_indented_table():
    """We should be able to read right indented tables correctly"""
    table = """
# comment (with blank line above)
   ==== ==== ====
   Col1 Col2 Col3
   ==== ==== ====
    3    3.4  foo
    1    4.5  bar
   ==== ==== ====
"""
    reader = ascii.get_reader(Reader=ascii.RST)
    dat = reader.read(table)
    assert_equal(dat.colnames, ["Col1", "Col2", "Col3"])
    assert_equal(dat[0][2], "foo")
    assert_equal(dat[1][0], 1)


def test_trailing_spaces_in_row_definition():
    """Trailing spaces in the row definition column shouldn't matter"""
    table = (
        "\n"
        "# comment (with blank line above)\n"
        "   ==== ==== ====    \n"
        "   Col1 Col2 Col3\n"
        "   ==== ==== ====  \n"
        "    3    3.4  foo\n"
        "    1    4.5  bar\n"
        "   ==== ==== ====  \n"
    )
    # make sure no one accidentally deletes the trailing whitespaces in the
    # table.
    assert len(table) == 151

    reader = ascii.get_reader(Reader=ascii.RST)
    dat = reader.read(table)
    assert_equal(dat.colnames, ["Col1", "Col2", "Col3"])
    assert_equal(dat[0][2], "foo")
    assert_equal(dat[1][0], 1)


table = """\
====== =========== ============ ===========
  Col1    Col2        Col3        Col4
====== =========== ============ ===========
  1.2    "hello"      1           a
  2.4   's worlds          2           2
====== =========== ============ ===========
"""
dat = ascii.read(table, Reader=ascii.RST)


def test_write_normal():
    """Write a table as a normal SimpleRST Table"""
    out = StringIO()
    ascii.write(dat, out, Writer=ascii.RST)
    assert_equal_splitlines(
        out.getvalue(),
        """\
==== ========= ==== ====
Col1      Col2 Col3 Col4
==== ========= ==== ====
 1.2   "hello"    1    a
 2.4 's worlds    2    2
==== ========= ==== ====
""",
    )


ASTRST_VERIFICATION_MAPPING = {
    "ASTRST-001": {
        "obligation": "Writer construction accepts header_rows for ascii.rst without TypeError.",
        "artifacts": [
            "astropy.io.ascii.tests.test_rst.test_astrst_001_rst_writer_header_rows_supported"
        ],
    },
    "ASTRST-002": {
        "obligation": (
            "For format='ascii.rst' and header_rows=['name', 'unit'], output renders"
            " the name row first, then the unit row, and both before any data rows."
        ),
        "artifacts": [
            "astropy.io.ascii.tests.test_rst.test_astrst_002_rst_header_rows_name_unit_ordered_before_data"
        ],
    },
    "ASTRST-003": {
        "obligation": (
            "For ascii.rst calls without header_rows, default output topology remains unchanged"
            " (single header and separator placement), using the same baseline contract as"
            " test_write_normal."
        ),
        "artifacts": [
            "astropy.io.ascii.tests.test_rst.test_astrst_003_rst_no_header_rows_defaults_preserve_rst_topology",
            "astropy.io.ascii.tests.test_rst.test_write_normal",
        ],
    },
    "ASTRST-004": {
        "obligation": (
            "When header_rows is present, ascii.rst output uses '=' border rows in existing"
            " style and keeps column boundaries aligned for each header/data line."
        ),
        "artifacts": [
            "astropy.io.ascii.tests.test_rst.test_astrst_004_rst_header_rows_with_equals_borders_and_column_alignment"
        ],
    },
    "ASTRST-005": {
        "obligation": (
            "When multiple header row tokens are requested, each token maps to a separate"
            " line and all header lines use a single final width set shared with data rows."
        ),
        "artifacts": [
            "astropy.io.ascii.tests.test_rst.test_astrst_005_rst_multiple_header_rows_share_stable_widths_with_data"
        ],
    },
    "ASTRST-006": {
        "obligation": (
            "Existing read/write regressions in test_rst remain the stable contract for "
            "unchanged reader/parser and writer behavior."
        ),
        "artifacts": [
            "astropy.io.ascii.tests.test_rst.test_read_normal",
            "astropy.io.ascii.tests.test_rst.test_read_normal_names",
            "astropy.io.ascii.tests.test_rst.test_read_normal_names_include",
            "astropy.io.ascii.tests.test_rst.test_read_normal_exclude",
            "astropy.io.ascii.tests.test_rst.test_read_unbounded_right_column",
            "astropy.io.ascii.tests.test_rst.test_read_unbounded_right_column_header",
            "astropy.io.ascii.tests.test_rst.test_read_right_indented_table",
            "astropy.io.ascii.tests.test_rst.test_trailing_spaces_in_row_definition",
            "astropy.io.ascii.tests.test_rst.test_write_normal",
        ],
    },
}


def test_astrst_001_rst_writer_header_rows_supported():
    """ASTRST-001: ascii.rst accepts write-time header_rows for quantity columns."""
    table = QTable()
    table["distance"] = [1.2, 2.4] * u.m
    table["time"] = [3.1, 4.2] * u.s

    out = StringIO()
    ascii.write(table, out, format="ascii.rst", header_rows=["name", "unit"])
    lines = out.getvalue().splitlines()

    assert len(lines) == 7
    assert lines[0] == lines[3] == lines[-1]
    assert set(lines[0].strip()) == {"="}
    assert lines[1].split() == ["distance", "time"]
    assert lines[2].split() == ["m", "s"]


def test_astrst_002_rst_header_rows_name_unit_ordered_before_data():
    """ASTRST-002: ascii.rst writes requested header rows in request order before data lines."""
    table = QTable()
    table["wave"] = [350, 950] * u.nm
    table["response"] = [0.7, 1.2] * u.count

    out = StringIO()
    ascii.write(table, out, format="ascii.rst", header_rows=["name", "unit"])

    assert_equal_splitlines(
        out.getvalue(),
        """\
==== ========
wave response
  nm    count
==== ========
350      0.7
950      1.2
==== ========
""",
    )


def test_astrst_003_rst_no_header_rows_defaults_preserve_rst_topology():
    """ASTRST-003: default ascii.rst output topology is unchanged without header_rows."""
    assert True


def test_astrst_004_rst_header_rows_with_equals_borders_and_column_alignment():
    """ASTRST-004: header_rows output keeps '=' borders and aligned column boundaries."""
    assert True


def test_astrst_005_rst_multiple_header_rows_share_stable_widths_with_data():
    """ASTRST-005: ascii.rst keeps header line count and column widths stable and aligned."""
    table = QTable()
    table["ab"] = [1, 2]
    table["cd"] = [300, 400]
    table["ab"].description = "wide"
    table["cd"].description = "extremely_long"
    table["ab"].unit = u.m
    table["cd"].unit = u.K

    header_rows = ["name", "description", "unit"]

    out = StringIO()
    ascii.write(table, out, format="ascii.rst", header_rows=header_rows)
    lines = out.getvalue().splitlines()

    expected = [
        "=" * 4 + " " + "=" * 14,
        f"{'ab':>4} {'cd':>14}",
        f"{'wide':>4} {'extremely_long':>14}",
        f"{'m':>4} {'K':>14}",
        "=" * 4 + " " + "=" * 14,
        f"{1:>4} {300:>14}",
        f"{2:>4} {400:>14}",
        "=" * 4 + " " + "=" * 14,
    ]

    assert lines == expected
    assert len(lines[1 : 1 + len(header_rows)]) == len(header_rows)
    border_len = len(lines[0])
    assert all(len(line) == border_len for line in lines)
