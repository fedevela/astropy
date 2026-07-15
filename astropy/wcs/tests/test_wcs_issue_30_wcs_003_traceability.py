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

    empty_list_outputs = wcs_obj.wcs_pix2world([], [], 0)
    non_empty_list_outputs = wcs_obj.wcs_pix2world([1, 2], [3, 4], 0)
    x_world, y_world = empty_list_outputs
    non_empty_x_world, non_empty_y_world = non_empty_list_outputs

    assert isinstance(empty_list_outputs, list)
    assert type(empty_list_outputs) is type(non_empty_list_outputs)
    assert len(empty_list_outputs) == len(non_empty_list_outputs) == 2
    assert x_world.shape == (0,)
    assert y_world.shape == (0,)
    assert x_world.size == 0
    assert y_world.size == 0
    assert np.issubdtype(x_world.dtype, np.floating)
    assert np.issubdtype(y_world.dtype, np.floating)
    assert non_empty_x_world.shape == (2,)
    assert non_empty_y_world.shape == (2,)


def test_wcs_003_empty_numpy_axes_preserve_array_output_container_shape_and_float_dtype():
    """WCS-003: numpy-empty axes preserve array-oriented 1D zero-length float outputs."""
    wcs_obj = _create_two_axis_wcs()

    empty_array_outputs = wcs_obj.wcs_pix2world(
        np.array([], dtype=float), np.array([], dtype=float), 0)
    non_empty_array_outputs = wcs_obj.wcs_pix2world(
        np.array([1.0, 2.0]), np.array([3.0, 4.0]), 0)
    x_world, y_world = empty_array_outputs
    non_empty_x_world, non_empty_y_world = non_empty_array_outputs

    assert len(empty_array_outputs) == len(non_empty_array_outputs) == 2
    assert x_world.shape == (0,)
    assert y_world.shape == (0,)
    assert x_world.size == 0
    assert y_world.size == 0
    assert np.issubdtype(x_world.dtype, np.floating)
    assert np.issubdtype(y_world.dtype, np.floating)
    assert non_empty_x_world.shape == (2,)
    assert non_empty_y_world.shape == (2,)


def test_wcs_003_empty_list_and_numpy_outputs_consistent_with_container_convention():
    """WCS-003: list and array calls both follow their respective empty-input conventions."""
    wcs_obj = _create_two_axis_wcs()

    list_outputs = wcs_obj.wcs_pix2world([], [], 0)
    array_outputs = wcs_obj.wcs_pix2world(np.array([]), np.array([]), 0)
    non_empty_list_outputs = wcs_obj.wcs_pix2world([1, 2], [3, 4], 0)
    non_empty_array_outputs = wcs_obj.wcs_pix2world(
        np.array([1.0, 2.0]), np.array([3.0, 4.0]), 0)

    assert type(list_outputs) is type(non_empty_list_outputs)
    assert len(list_outputs) == len(non_empty_list_outputs) == 2
    assert type(array_outputs) is type(non_empty_array_outputs)
    assert len(array_outputs) == len(non_empty_array_outputs) == 2
