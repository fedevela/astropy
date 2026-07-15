# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Traceability artifact for WCS-002.

This module encodes contract coverage for multi-axis
`wcs_pix2world` obligations when all inputs are empty per axis.
"""

import numpy as np

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

    x_world, y_world, z_world = w.wcs_pix2world([], [], [], 0)

    assert x_world.shape == (0,)
    assert y_world.shape == (0,)
    assert z_world.shape == (0,)
    assert x_world.size == 0
    assert y_world.size == 0
    assert z_world.size == 0
    assert np.array_equal(x_world, np.array([]))
    assert np.array_equal(y_world, np.array([]))
    assert np.array_equal(z_world, np.array([]))


def test_wcs_002_n_axis_empty_input_tuples_return_n_empty_outputs_each_with_no_rows():
    """WCS-002: N-axis empty tuple inputs return N empty outputs and no inserted coordinate rows."""
    naxis = 5
    w = _create_multi_axis_wcs(naxis)

    result = w.wcs_pix2world(*([[]] * naxis), 0)

    assert len(result) == naxis

    for axis_output in result:
        assert axis_output.shape == (0,)
        assert axis_output.size == 0
        assert np.array_equal(axis_output, np.array([]))

def test_wcs_002_multi_origin_empty_input_calls_preserve_axis_cardinality():
    """WCS-002: repeated empty-input calls preserve per-axis output cardinality across origins."""
    w = _create_multi_axis_wcs(4)

    result_origin_0 = w.wcs_pix2world(*([[]] * 4), 0)
    result_origin_1 = w.wcs_pix2world(*([[]] * 4), 1)

    assert len(result_origin_0) == len(result_origin_1)
    for first_axis, second_axis in zip(result_origin_0, result_origin_1):
        assert first_axis.shape == (0,)
        assert second_axis.shape == (0,)
        assert first_axis.size == 0
        assert second_axis.size == 0
