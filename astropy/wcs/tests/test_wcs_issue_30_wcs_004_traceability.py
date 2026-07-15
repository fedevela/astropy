# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Traceability artifact for WCS-004.

This module encodes contract coverage for mixed `wcs_pix2world` calls where one
axis is non-empty and another is empty, ensuring validation errors remain the
governing path and are not replaced by empty-input short-circuit behavior.
"""

import numpy as np

import pytest

from ... import wcs


def _create_two_axis_wcs():
    return wcs.WCS(naxis=2)


WCS_004_REQUIREMENT_VERIFICATION_MAP = {
    "WCS-004": [
        "test_wcs_004_mixed_non_empty_and_empty_axes_keep_non_empty_validation_errors",
        "test_wcs_004_repeated_invalid_mixed_calls_continue_failing_without_empty_short_circuit",
        "test_wcs_004_valid_all_empty_call_after_invalid_mixed_input_uses_noop_empty_path",
    ]
}


def test_wcs_004_mixed_non_empty_and_empty_axes_keep_non_empty_validation_errors():
    """WCS-004: mixed input where one axis is empty preserves validation failure."""
    w = _create_two_axis_wcs()

    with pytest.raises(ValueError) as exc:
        w.wcs_pix2world([10.0], [], 0)
    assert exc.value.args[0] == (
        "Coordinate arrays are not broadcastable to each other"
    )


def test_wcs_004_repeated_invalid_mixed_calls_continue_failing_without_empty_short_circuit():
    """WCS-004: repeated invalid mixed-shape calls fail the same way each time."""
    w = _create_two_axis_wcs()

    for _ in range(2):
        with pytest.raises(ValueError) as exc:
            w.wcs_pix2world([10.0, 20.0], [], 1)
        assert exc.value.args[0] == (
            "Coordinate arrays are not broadcastable to each other"
        )


def test_wcs_004_valid_all_empty_call_after_invalid_mixed_input_uses_noop_empty_path():
    """WCS-004: valid all-empty call remains a no-op path after invalid mixed input."""
    w = _create_two_axis_wcs()

    with pytest.raises(ValueError):
        w.wcs_pix2world([10.0], [], 0)

    x_world, y_world = w.wcs_pix2world([], [], 0)

    assert x_world.shape == (0,)
    assert y_world.shape == (0,)
    assert np.array_equal(x_world, np.array([]))
    assert np.array_equal(y_world, np.array([]))
