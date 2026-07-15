import numpy as np
import pytest

from astropy.io import ascii
from astropy.io.ascii.qdp import _get_lines_from_file, _read_table_qdp, _write_table_qdp
from astropy.table import Column, MaskedColumn, Table
from astropy.utils.exceptions import AstropyUserWarning


def test_get_tables_from_qdp_file(tmp_path):
    example_qdp = """
    ! Swift/XRT hardness ratio of trigger: XXXX, name: BUBU X-2
    ! Columns are as labelled
    READ TERR 1
    READ SERR 2
    ! WT -- hard data
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   -0.212439       0.212439
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   0.000000        0.000000
    NO NO NO NO NO
    ! WT -- soft data
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   0.726155        0.583890
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   2.410935        1.393592
    NO NO NO NO NO
    ! WT -- hardness ratio
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   -0.292553       -0.374935
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   0.000000        -nan
    """

    path = tmp_path / "test.qdp"

    with open(path, "w") as fp:
        print(example_qdp, file=fp)

    table0 = _read_table_qdp(fp.name, names=["MJD", "Rate"], table_id=0)
    assert table0.meta["initial_comments"][0].startswith("Swift")
    assert table0.meta["comments"][0].startswith("WT -- hard data")
    table2 = _read_table_qdp(fp.name, names=["MJD", "Rate"], table_id=2)
    assert table2.meta["initial_comments"][0].startswith("Swift")
    assert table2.meta["comments"][0].startswith("WT -- hardness")
    assert np.isclose(table2["MJD_nerr"][0], -2.37847222222222e-05)


def test_roundtrip(tmp_path):
    example_qdp = """
    ! Swift/XRT hardness ratio of trigger: XXXX, name: BUBU X-2
    ! Columns are as labelled
    READ TERR 1
    READ SERR 2
    ! WT -- hard data
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   NO       0.212439
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   0.000000        0.000000
    NO NO NO NO NO
    ! WT -- soft data
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   0.726155        0.583890
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   2.410935        1.393592
    NO NO NO NO NO
    ! WT -- hardness ratio
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   -0.292553       -0.374935
    55045.099887 1.14467592592593e-05    -1.14467592592593e-05   0.000000        NO
    ! Add command, just to raise the warning.
    READ TERR 1
    ! WT -- whatever
    !MJD            Err (pos)       Err(neg)        Rate            Error
    53000.123456 2.37847222222222e-05    -2.37847222222222e-05   -0.292553       -0.374935
    NO 1.14467592592593e-05    -1.14467592592593e-05   0.000000        NO
    """

    path = str(tmp_path / "test.qdp")
    path2 = str(tmp_path / "test2.qdp")

    with open(path, "w") as fp:
        print(example_qdp, file=fp)
    with pytest.warns(AstropyUserWarning) as record:
        table = _read_table_qdp(path, names=["MJD", "Rate"], table_id=0)
    assert np.any(
        [
            "This file contains multiple command blocks" in r.message.args[0]
            for r in record
        ]
    )

    _write_table_qdp(table, path2)

    new_table = _read_table_qdp(path2, names=["MJD", "Rate"], table_id=0)

    for col in new_table.colnames:
        is_masked = np.array([np.ma.is_masked(val) for val in new_table[col]])
        if np.any(is_masked):
            # All NaN values are read as such.
            assert np.ma.is_masked(table[col][is_masked])

        is_nan = np.array(
            [(not np.ma.is_masked(val) and np.isnan(val)) for val in new_table[col]]
        )
        # All non-NaN values are the same
        assert np.allclose(new_table[col][~is_nan], table[col][~is_nan])
        if np.any(is_nan):
            # All NaN values are read as such.
            assert np.isnan(table[col][is_nan])
    assert np.allclose(new_table["MJD_perr"], [2.378472e-05, 1.1446759e-05])

    for meta_name in ["initial_comments", "comments"]:
        assert meta_name in new_table.meta


def test_read_example():
    example_qdp = """
        ! Initial comment line 1
        ! Initial comment line 2
        READ TERR 1
        READ SERR 3
        ! Table 0 comment
        !a a(pos) a(neg) b c ce d
        53000.5   0.25  -0.5   1  1.5  3.5 2
        54000.5   1.25  -1.5   2  2.5  4.5 3
        NO NO NO NO NO
        ! Table 1 comment
        !a a(pos) a(neg) b c ce d
        54000.5   2.25  -2.5   NO  3.5  5.5 5
        55000.5   3.25  -3.5   4  4.5  6.5 nan
        """
    dat = ascii.read(example_qdp, format="qdp", table_id=1, names=["a", "b", "c", "d"])
    t = Table.read(
        example_qdp, format="ascii.qdp", table_id=1, names=["a", "b", "c", "d"]
    )

    assert np.allclose(t["a"], [54000, 55000])
    assert t["c_err"][0] == 5.5
    assert np.ma.is_masked(t["b"][0])
    assert np.isnan(t["d"][1])

    for col1, col2 in zip(t.itercols(), dat.itercols()):
        assert np.allclose(col1, col2, equal_nan=True)


def test_roundtrip_example(tmp_path):
    example_qdp = """
        ! Initial comment line 1
        ! Initial comment line 2
        READ TERR 1
        READ SERR 3
        ! Table 0 comment
        !a a(pos) a(neg) b c ce d
        53000.5   0.25  -0.5   1  1.5  3.5 2
        54000.5   1.25  -1.5   2  2.5  4.5 3
        NO NO NO NO NO
        ! Table 1 comment
        !a a(pos) a(neg) b c ce d
        54000.5   2.25  -2.5   NO  3.5  5.5 5
        55000.5   3.25  -3.5   4  4.5  6.5 nan
        """
    test_file = tmp_path / "test.qdp"

    t = Table.read(
        example_qdp, format="ascii.qdp", table_id=1, names=["a", "b", "c", "d"]
    )
    t.write(test_file, err_specs={"terr": [1], "serr": [3]})
    t2 = Table.read(test_file, names=["a", "b", "c", "d"], table_id=0)

    for col1, col2 in zip(t.itercols(), t2.itercols()):
        assert np.allclose(col1, col2, equal_nan=True)


def test_roundtrip_example_comma(tmp_path):
    example_qdp = """
        ! Initial comment line 1
        ! Initial comment line 2
        READ TERR 1
        READ SERR 3
        ! Table 0 comment
        !a,a(pos),a(neg),b,c,ce,d
        53000.5,0.25,-0.5,1,1.5,3.5,2
        54000.5,1.25,-1.5,2,2.5,4.5,3
        NO,NO,NO,NO,NO
        ! Table 1 comment
        !a,a(pos),a(neg),b,c,ce,d
        54000.5,2.25,-2.5,NO,3.5,5.5,5
        55000.5,3.25,-3.5,4,4.5,6.5,nan
        """
    test_file = tmp_path / "test.qdp"

    t = Table.read(
        example_qdp, format="ascii.qdp", table_id=1, names=["a", "b", "c", "d"], sep=","
    )
    t.write(test_file, err_specs={"terr": [1], "serr": [3]})
    t2 = Table.read(test_file, names=["a", "b", "c", "d"], table_id=0)

    # t.values_equal(t2)
    for col1, col2 in zip(t.itercols(), t2.itercols()):
        assert np.allclose(col1, col2, equal_nan=True)


def test_read_write_simple(tmp_path):
    test_file = tmp_path / "test.qdp"
    t1 = Table()
    t1.add_column(Column(name="a", data=[1, 2, 3, 4]))
    t1.add_column(
        MaskedColumn(
            data=[4.0, np.nan, 3.0, 1.0], name="b", mask=[False, False, False, True]
        )
    )
    t1.write(test_file, format="ascii.qdp")
    with pytest.warns(UserWarning) as record:
        t2 = Table.read(test_file, format="ascii.qdp")
    assert np.any(
        [
            "table_id not specified. Reading the first available table"
            in r.message.args[0]
            for r in record
        ]
    )

    assert np.allclose(t2["col1"], t1["a"])
    assert np.all(t2["col1"] == t1["a"])

    good = ~np.isnan(t1["b"])
    assert np.allclose(t2["col2"][good], t1["b"][good])


def test_read_write_simple_specify_name(tmp_path):
    test_file = tmp_path / "test.qdp"
    t1 = Table()
    t1.add_column(Column(name="a", data=[1, 2, 3]))
    # Give a non-None err_specs
    t1.write(test_file, format="ascii.qdp")
    t2 = Table.read(test_file, table_id=0, format="ascii.qdp", names=["a"])
    assert np.all(t2["a"] == t1["a"])


def test_get_lines_from_qdp(tmp_path):
    test_file = str(tmp_path / "test.qdp")
    text_string = "A\nB"
    text_output = _get_lines_from_file(text_string)
    with open(test_file, "w") as fobj:
        print(text_string, file=fobj)
    file_output = _get_lines_from_file(test_file)
    list_output = _get_lines_from_file(["A", "B"])
    for i, line in enumerate(["A", "B"]):
        assert file_output[i] == line
        assert list_output[i] == line
        assert text_output[i] == line


# Requirement-to-verification mapping for traceability in SPARC phase 05.
REQUIREMENT_VERIFICATION_MAP = {
    "ISSUE13-001": [
        "test_issue13_001_case_insensitive_read_serr_command_verb_dispatch",
        "test_issue13_001_case_insensitive_read_command_sub_key_dispatch",
    ],
    "ISSUE13-002": [
        "test_issue13_002_issue_spec_reads_mixed_case_read_serr_and_succeeds",
        "test_issue13_002_issue_spec_columns_and_error_semantics_match_uppercase_reference",
    ],
    "ISSUE13-003": [
        "test_issue13_003_issue_spec_rejects_normalized_unknown_command_via_unrecognized_qdp_line",
        "test_issue13_003_issue_spec_rejects_invalid_read_subkey_after_case_normalization",
    ],
    "ISSUE13-004": [
        "test_issue13_004_issue_spec_preserves_uppercase_qdp_table_shape_type_order_and_values_after_case_insensitive_read_path",
        "test_issue13_004_issue_spec_preserves_comments_and_whitespace_semantics_with_uppercase_qdp_and_mixed_spacing",
    ],
}


def test_issue13_001_case_insensitive_read_serr_command_verb_dispatch():
    """ISSUE13-001: mixed-case READ command verbs dispatch via same handler path."""
    qdp = """
    ReAd SeRr 1 2
    10 20 30 40
    11 21 31 41
    """

    qdp_upper = """
    READ SERR 1 2
    10 20 30 40
    11 21 31 41
    """

    lower = Table.read(qdp, format="ascii.qdp", table_id=0, names=["x", "y"])
    upper = Table.read(qdp_upper, format="ascii.qdp", table_id=0, names=["x", "y"])

    assert lower.colnames == upper.colnames
    assert np.allclose(lower["x_err"], upper["x_err"])
    assert np.allclose(lower["y_err"], upper["y_err"])
    assert np.allclose(lower["x"], upper["x"])
    assert np.allclose(lower["y"], upper["y"])


def test_issue13_001_case_insensitive_read_command_sub_key_dispatch():
    """ISSUE13-001: mixed-case READ sub-keys dispatch via same recognized sub-key path."""
    qdp = """
    READ SeRr 1 2
    100 200 300 400
    101 201 301 401
    """

    qdp_upper = """
    READ SERR 1 2
    100 200 300 400
    101 201 301 401
    """

    lower = Table.read(qdp, format="ascii.qdp", table_id=0, names=["x", "y"])
    upper = Table.read(qdp_upper, format="ascii.qdp", table_id=0, names=["x", "y"])

    assert lower.colnames == upper.colnames
    assert np.allclose(lower["x_err"], upper["x_err"])
    assert np.allclose(lower["y_err"], upper["y_err"])
    assert np.allclose(lower["x"], upper["x"])
    assert np.allclose(lower["y"], upper["y"])


def test_issue13_002_issue_spec_reads_mixed_case_read_serr_and_succeeds():
    """ISSUE13-002: lowercase/mixed-case read serr command succeeds with ascii.qdp parsing."""
    lower_case = """
    read serr 1 2
    1 0.5 1 0.5
    """
    mixed_case = """
    ReAd SeRr 1 2
    1 0.5 1 0.5
    """
    expected = Table.read(mixed_case, format="ascii.qdp", names=["x", "y"], table_id=0)
    result = Table.read(lower_case, format="ascii.qdp", names=["x", "y"], table_id=0)

    assert result.colnames == ["x", "x_err", "y", "y_err"]
    assert len(result) == 1
    assert np.allclose(result["x"], [1])
    assert np.allclose(result["x_err"], [0.5])
    assert np.allclose(result["y"], [1])
    assert np.allclose(result["y_err"], [0.5])
    assert result.colnames == expected.colnames
    assert [name for name in result.colnames if name.endswith("_err")] == ["x_err", "y_err"]
    assert np.ma.allequal(result["x"], expected["x"])
    assert np.ma.allequal(result["x_err"], expected["x_err"])
    assert np.ma.allequal(result["y"], expected["y"])
    assert np.ma.allequal(result["y_err"], expected["y_err"])


def test_issue13_002_issue_spec_columns_and_error_semantics_match_uppercase_reference():
    """ISSUE13-002: mixed-case read serr output matches READ SERR output for columns and errors."""
    qdp_lower = """
    read serr 1 2
    1 0.5 1 0.5
    2 0.75 2 0.75
    """
    qdp_upper = """
    READ SERR 1 2
    1 0.5 1 0.5
    2 0.75 2 0.75
    """
    table_lower = Table.read(qdp_lower, format="ascii.qdp", names=["x", "y"], table_id=0)
    table_upper = Table.read(qdp_upper, format="ascii.qdp", names=["x", "y"], table_id=0)

    assert table_lower.colnames == table_upper.colnames
    assert len(table_lower) == len(table_upper) == 2
    for name in table_lower.colnames:
        assert np.ma.allequal(table_lower[name], table_upper[name])
    assert "_err" in table_lower.colnames
    assert "x_err" in table_lower.colnames
    assert "y_err" in table_lower.colnames


def test_issue13_003_issue_spec_rejects_normalized_unknown_command_via_unrecognized_qdp_line():
    """ISSUE13-003: unknown command should follow Unrecognized QDP line path after normalization."""
    qdp = """
    READD SERR 1 2
    1 2 3
    """

    with pytest.raises(ValueError, match="Unrecognized QDP line"):
        Table.read(qdp, format="ascii.qdp", table_id=0, names=["x", "y"])


def test_issue13_003_issue_spec_rejects_invalid_read_subkey_after_case_normalization():
    """ISSUE13-003: misspelled READ sub-key should remain rejected after case normalization."""
    qdp = """
    READ SeRrR 1 2
    1 2 3
    """

    with pytest.raises(ValueError, match="Unrecognized QDP line"):
        Table.read(qdp, format="ascii.qdp", table_id=0, names=["x", "y"])


def test_issue13_004_issue_spec_preserves_uppercase_qdp_table_shape_type_order_and_values_after_case_insensitive_read_path():
    """ISSUE13-004: Scenario 1 - preserve uppercase parsing behavior and table metadata-free shape/type/order."""
    uppercase_qdp = """
    ! Baseline uppercase fixture
    READ SERR 1
    1    10.5   100
    2    20     200
    NO NO NO
    """
    mixed_case_qdp = """
    ! Baseline uppercase fixture
    ReAd sErR 1
    1    10.5   100
    2    20     200
    NO NO NO
    """

    table_upper = Table.read(
        uppercase_qdp, format="ascii.qdp", table_id=0, names=["x", "y"]
    )
    table_mixed = Table.read(
        mixed_case_qdp, format="ascii.qdp", table_id=0, names=["x", "y"]
    )

    assert table_upper.colnames == ["x", "x_err", "y"] == table_mixed.colnames
    assert len(table_upper) == len(table_mixed) == 2
    assert table_upper["x"].dtype == table_mixed["x"].dtype
    assert table_upper["x_err"].dtype == table_mixed["x_err"].dtype
    assert table_upper["y"].dtype == table_mixed["y"].dtype
    assert np.ma.allequal(table_upper["x"], table_mixed["x"])
    assert np.ma.allequal(table_upper["x_err"], table_mixed["x_err"])
    assert np.ma.allequal(table_upper["y"], table_mixed["y"])
    assert np.allclose(table_upper["x"], [1, 2])
    assert np.allclose(table_upper["y"], [100, 200])


def test_issue13_004_issue_spec_preserves_comments_and_whitespace_semantics_with_uppercase_qdp_and_mixed_spacing():
    """ISSUE13-004: Scenario 2 - preserve comments and whitespace parsing semantics for uppercase inputs."""
    qdp = """
    !  initial comment
    !\tsecond comment with tabs
    READ    SERR   1
    !\ttable comment
    1 \t\t 10.5   100
    2   \t20      \t200
    NO    NO   NO
    """

    table = Table.read(qdp, format="ascii.qdp", table_id=0)

    assert table.meta["initial_comments"] == [
        "initial comment",
        "second comment with tabs",
    ]
    assert table.meta["comments"] == ["table comment"]
    assert table.colnames == ["col1", "col1_err", "col2"]
    assert len(table) == 2
    assert np.allclose(table["col1"], [1, 2])
    assert np.ma.allequal(table["col1_err"], np.ma.array([10.5, 20.0]))
    assert np.allclose(table["col2"], [100, 200])
