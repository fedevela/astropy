# Copyright 2026 The Open Source Astronomy Community.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Traceability test skeleton for DEXP-003."""

import io

import numpy as np

from ....io import fits

from . import FitsTestCase


DEXP_003_VERIFICATION = {
    "DEXP-003": [
        "test_dexp_003_positive_exponent_raw_row_contains_d_separator",
        "test_dexp_003_negative_exponent_raw_row_contains_d_separator",
        "test_dexp_003_regression_observes_e_when_d_not_replaced",
    ]
}


DEXP_003_ARCHITECTURE = {
    "DEXP-003": {
        "topology": [
            "astropy/io/fits/hdu/table.py::_TableBaseHDU::_prewriteto",
            "astropy/io/fits/hdu/table.py::TableHDU::_writedata_internal",
            "astropy/io/fits/fitsrec.py::TableData::_scale_back_ascii",
        ],
        "contracts": {
            "positive_exponent_path": (
                "A float field declared with format containing D serializes through "
                "the ASCII-table payload pipeline and preserves a D separator for "
                "positive-exponent samples."
            ),
            "negative_exponent_path": (
                "The same ASCII-table path preserves a D separator for "
                "negative-exponent samples."
            ),
            "failure_mode_surface": (
                "On the pre-fix behavior, the raw serialized payload for D-format "
                "inputs would include E when D replacement is not applied."
            ),
        },
        "verification": DEXP_003_VERIFICATION["DEXP-003"],
    }
}


DEXP_003_PSEUDOCODE = {
    "DEXP-003": [
        {
            "requirement": "DEXP-003",
            "logic_obligation": "positive_exponent_raw_row_contains_d_separator",
            "owner": "astropy/io/fits/hdu/table.py::_TableBaseHDU::_prewriteto",
            "handoff_to": "astropy/io/fits/hdu/table.py::TableHDU::_writedata_internal",
            "input": "ASCII float field with format='D15.7' and value magnitude > 1",
            "state_transitions": [
                "serialize_table_hdu -> bytes_payload",
                "decode_payload -> locate_END",
                "locate_first_data_row -> raw_row_bytes",
            ],
            "decision": "verify raw_row_bytes contains 'D' separator and not fallback exponent 'E'",
            "failure_path": "if separator is 'E', regression remains unresolved; test must fail",
        },
        {
            "requirement": "DEXP-003",
            "logic_obligation": "negative_exponent_raw_row_contains_d_separator",
            "owner": "astropy/io/fits/hdu/table.py::_TableBaseHDU::_prewriteto",
            "handoff_to": "astropy/io/fits/hdu/table.py::TableHDU::_writedata_internal",
            "input": "ASCII float field with format='D15.7' and value magnitude < 1",
            "state_transitions": [
                "serialize_table_hdu -> bytes_payload",
                "decode_payload -> locate_END",
                "locate_first_data_row -> raw_row_bytes",
            ],
            "decision": "verify raw_row_bytes contains 'D' separator and not fallback exponent 'E'",
            "failure_path": "if separator is 'E' (or missing), regression remains unresolved; test must fail",
        },
        {
            "requirement": "DEXP-003",
            "logic_obligation": "regression_observes_e_when_d_not_replaced",
            "owner": "astropy/io/fits/hdu/table.py::_writedata_internal",
            "handoff_to": "raw-bytes assertion surface",
            "input": "legacy behavior path with D-format exponent conversion not preserved",
            "state_transitions": [
                "serialize_table_hdu -> bytes_payload",
                "decode_payload -> locate_END",
                "locate_first_data_row -> raw_row_bytes",
                "raw_row_bytes -> expected_legacy_marker_check",
            ],
            "decision": "expected observation in legacy code path is 'E' present in raw_row_bytes",
            "failure_path": "if 'D' appears before fix, this guard is no longer representative of pre-fix behavior",
        },
    ],
}


class TestDEXP003Traceability(FitsTestCase):
    """Contract-oriented placeholder coverage for DEXP-003."""

    @staticmethod
    def _table_payload(hdu):
        # Pseudocode path (DEXP-003):
        # - Input: constructed ASCII TableHDU
        # - Action: serialize HDU into in-memory stream
        # - Action: rewind stream
        # - Output: raw binary payload bytes for deterministic downstream checks
        stream = io.BytesIO()
        hdu.writeto(stream)
        stream.seek(0)
        return stream.getvalue()

    @staticmethod
    def _first_ascii_data_line(payload):
        # Pseudocode path (DEXP-003):
        # - Decode bytes payload with ASCII codec
        # - Split logical lines and locate END marker (header terminator)
        # - Return first non-blank post-END row as raw row candidate
        # - Failure path: missing END or missing data row raises assertion
        text = payload.decode("ascii")
        lines = text.splitlines()

        try:
            end_idx = lines.index("END")
        except ValueError as exc:
            raise AssertionError("Expected ASCII table header to include END.") from exc

        for line in lines[end_idx + 1 :]:
            if line.strip():
                return line

        raise AssertionError("Expected ASCII table data row in written payload.")

    @staticmethod
    def _d_table_hdu(value):
        # Pseudocode path (DEXP-003):
        # - Build one-row numpy scalar array for deterministic width/precision
        # - Define Column(name='x', format='D15.7', array=[value])
        # - Return TableHDU owned by ASCII table writer path
        column = fits.Column(name="x", format="D15.7", array=np.array([value]))
        return fits.TableHDU.from_columns([column])

    def test_dexp_003_positive_exponent_raw_row_contains_d_separator(self):
        """
        DEXP-003: positive exponent D-format serialization retains a D separator
        in raw ASCII row bytes.
        """
        # Decision flow (DEXP-003):
        # - Given value magnitude > 1 to force positive exponent formatting
        # - Serialize to bytes and extract first data row
        # - Assert row_state contains 'D' in exponent region
        # - Assert legacy path marker 'E' is absent
        # - If assertion fails, branch into regression-not-fixed failure mode.
        hdu = self._d_table_hdu(1.2345e20)
        payload = self._table_payload(hdu)
        row = self._first_ascii_data_line(payload)

        # TODO(DEXP-003): assert payload row uses D and not E once implementation is complete.
        # Pseudocode decision:
        # IF "D" in row AND "E" not in row:
        #     PASS
        # ELSE:
        #     FAIL legacy_exponent_not_replaced

    def test_dexp_003_negative_exponent_raw_row_contains_d_separator(self):
        """
        DEXP-003: negative exponent D-format serialization retains a D separator
        in raw ASCII row bytes.
        """
        # Decision flow (DEXP-003):
        # - Given value magnitude < 1 to force negative exponent formatting
        # - Serialize to bytes and extract first data row
        # - Assert row_state contains 'D' in exponent separator
        # - Assert legacy marker 'E' is absent
        # - If assertion fails, branch into regression-not-fixed failure mode.
        hdu = self._d_table_hdu(1.2345e-20)
        payload = self._table_payload(hdu)
        row = self._first_ascii_data_line(payload)

        # TODO(DEXP-003): assert payload row uses D for negative exponent path once implementation is complete.
        # Pseudocode decision:
        # IF "D" in row AND "E" not in row:
        #     PASS
        # ELSE:
        #     FAIL legacy_exponent_not_replaced

    def test_dexp_003_regression_observes_e_when_d_not_replaced(self):
        """
        DEXP-003 failure-mode trace: current pre-fix behavior would expose E in raw bytes.
        """
        # Decision flow (DEXP-003):
        # - Use same writer path as positive exponent case to maximize failure sensitivity
        # - Serialize and extract first data row
        # - In legacy behavior, observe exponent marker "E"
        # - Mark this as expected-failure-surface assertion, not as required success state
        hdu = self._d_table_hdu(1.2345e20)
        payload = self._table_payload(hdu)
        row = self._first_ascii_data_line(payload)

        # TODO(DEXP-003): replace with an explicit negative assertion for legacy E output during implementation.
        # Pseudocode decision:
        # IF "E" in row:
        #     PASS legacy_regression_observed
        # ELSE:
        #     FAIL: current test fixture no longer captures pre-fix behavior
