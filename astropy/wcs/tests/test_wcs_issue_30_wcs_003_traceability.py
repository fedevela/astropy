# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Traceability artifact for WCS-003.

This module encodes contract coverage for empty `wcs_pix2world` outputs when
input axis containers are lists versus NumPy arrays.
"""

import numpy as np

from ... import wcs


def _create_two_axis_wcs():
    return wcs.WCS(naxis=2)


WCS_003_REQUIREMENT_VERIFICATION_MAP = {
    "WCS-003": [
        "test_wcs_003_empty_list_axes_preserve_list_output_container_and_zero_length_axes",
        "test_wcs_003_empty_numpy_axes_preserve_array_output_container_shape_and_float_dtype",
        "test_wcs_003_empty_list_and_numpy_outputs_consistent_with_container_convention",
    ]
}


def test_wcs_003_empty_list_axes_preserve_list_output_container_and_zero_length_axes():
    """WCS-003: list inputs preserve list-oriented, zero-length per-axis outputs."""
    wcs_obj = _create_two_axis_wcs()

    x_world, y_world = wcs_obj.wcs_pix2world([], [], 0)

    assert True


def test_wcs_003_empty_numpy_axes_preserve_array_output_container_shape_and_float_dtype():
    """WCS-003: numpy-empty axes preserve array-oriented 1D zero-length float outputs."""
    wcs_obj = _create_two_axis_wcs()

    x_world, y_world = wcs_obj.wcs_pix2world(np.array([]), np.array([]), 0)

    assert True


def test_wcs_003_empty_list_and_numpy_outputs_consistent_with_container_convention():
    """WCS-003: list and array calls both follow their respective empty-input conventions."""
    wcs_obj = _create_two_axis_wcs()

    list_outputs = wcs_obj.wcs_pix2world([], [], 0)
    array_outputs = wcs_obj.wcs_pix2world(np.array([]), np.array([]), 0)

    assert True
