# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Traceability artifact for WCS-001.

This module encodes contract coverage for the empty-input
`wcs_pix2world` obligations.
"""

import numpy as np

from ... import wcs


def _create_two_axis_wcs():
    return wcs.WCS(naxis=2)

WCS_001_REQUIREMENT_VERIFICATION_MAP = {
    "WCS-001": [
        "test_wcs_001_empty_list_inputs_origin_0_no_inconsistent_axis_types_error",
        "test_wcs_001_empty_list_inputs_origin_1_no_inconsistent_axis_types_error",
        "test_wcs_001_empty_axis_inputs_shape_noop_for_any_valid_origin",
    ]
}


def test_wcs_001_empty_list_inputs_origin_0_no_inconsistent_axis_types_error():
    """WCS-001: given empty per-axis inputs and origin=0, no error is raised."""
    w = _create_two_axis_wcs()

    x_world, y_world = w.wcs_pix2world([], [], 0)

    assert x_world.shape == (0,)
    assert y_world.shape == (0,)
    assert x_world.size == 0
    assert y_world.size == 0


def test_wcs_001_empty_list_inputs_origin_1_no_inconsistent_axis_types_error():
    """WCS-001: given empty per-axis inputs and origin=1, no error is raised."""
    w = _create_two_axis_wcs()

    x_world, y_world = w.wcs_pix2world([], [], 1)

    assert x_world.shape == (0,)
    assert y_world.shape == (0,)
    assert x_world.size == 0
    assert y_world.size == 0


def test_wcs_001_empty_axis_inputs_shape_noop_for_any_valid_origin():
    """WCS-001: empty input shape resolves to zero-length outputs for valid origin values."""
    w = _create_two_axis_wcs()
    empty_axis_inputs = np.empty((0, 2))

    result_origin_0 = w.wcs_pix2world(empty_axis_inputs, 0)
    result_origin_1 = w.wcs_pix2world(empty_axis_inputs, 1)

    assert result_origin_0.shape == (0, 2)
    assert result_origin_1.shape == (0, 2)
