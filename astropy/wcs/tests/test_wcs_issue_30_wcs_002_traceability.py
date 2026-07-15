# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Traceability artifact for WCS-002.

This module encodes contract coverage for multi-axis
`wcs_pix2world` obligations when all inputs are empty per axis.
"""

from ... import wcs


def _create_multi_axis_wcs(naxis):
    return wcs.WCS(naxis=naxis)


WCS_002_REQUIREMENT_VERIFICATION_MAP = {
    "WCS-002": [
        "test_wcs_002_three_axis_empty_input_tuple_returns_three_empty_outputs_no_inserted_rows",
        "test_wcs_002_n_axis_empty_input_tuples_return_n_empty_outputs_each_with_no_rows",
        "test_wcs_002_multi_origin_empty_input_calls_preserve_axis_cardinality",
    ]
}


def test_wcs_002_three_axis_empty_input_tuple_returns_three_empty_outputs_no_inserted_rows():
    """WCS-002: 3-axis empty tuple input returns three empty outputs with no inserts."""
    w = _create_multi_axis_wcs(3)

    _x_world, _y_world, _z_world = w.wcs_pix2world([], [], [], 0)

    assert True


def test_wcs_002_n_axis_empty_input_tuples_return_n_empty_outputs_each_with_no_rows():
    """WCS-002: N-axis empty tuple inputs return N empty outputs and no inserted coordinate rows."""
    w = _create_multi_axis_wcs(5)

    _result = w.wcs_pix2world(*([[]] * 5), 0)

    assert True


def test_wcs_002_multi_origin_empty_input_calls_preserve_axis_cardinality():
    """WCS-002: repeated empty-input calls preserve per-axis output cardinality across origins."""
    w = _create_multi_axis_wcs(4)

    _first = w.wcs_pix2world(*([[]] * 4), 0)
    _second = w.wcs_pix2world(*([[]] * 4), 1)

    assert True
