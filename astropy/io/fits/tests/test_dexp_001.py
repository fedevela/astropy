# Copyright 2026 The Open Source Astronomy Community.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Regression verification for DEXP-001."""

import io
import re

import numpy as np

from ....io import fits

from . import FitsTestCase


DEXP_001_VERIFICATION = {
    "DEXP-001": [
        "test_dexp_001_assigns_replace_result_to_output_field",
        "test_dexp_001_uses_replaced_output_field_for_serialization",
        "test_dexp_001_emits_d_separator_for_d_format_fields",
    ]
}

# Architecture-level placement for DEXP-001.
DEXP_001_ARCHITECTURE = {
    "DEXP-001": {
        "topology": [
            "astropy/io/fits/fitsrec.py::TableData::_scale_back_ascii",
        ],
        "ownership": {
            "module": "astropy/io/fits/fitsrec.py",
            "boundary": [
                "ASCII field serializer computes format string from Column definitions",
                "writes into output_field bytes before bytes are handed to column writer",
            ],
        },
        "contracts": {
            "active_payload": (
                "If 'D' in format, output_field must be rebound to a payload "
                "where all encoded 'E' exponent bytes are replaced by 'D'."
            ),
            "validation": (
                "No behavior change in width/precision checks and pre-branch "
                "formatting checks."
            ),
        },
        "dependency_direction": [
            "TableData._scale_back_ascii -> encode_ascii",
            "TableData._scale_back_ascii -> numpy ndarray operations",
            "Column format metadata (self._coldefs) -> branch decision",
        ],
        "integration_seams": [
            "TableData._scale_back_ascii output_field return value is consumed by "
            "the same serializer pipeline that writes row bytes",
            "Branch visibility remains local to D-exponent formatting path",
        ],
        "verification": DEXP_001_VERIFICATION["DEXP-001"],
    },
}


class TestDEXP001Traceability(FitsTestCase):
    @staticmethod
    def _table_payload(hdu):
        stream = io.BytesIO()
        hdu.writeto(stream)
        stream.seek(0)
        return stream.getvalue()

    @staticmethod
    def _first_ascii_data_line(payload):
        text = payload.decode('ascii')
        lines = text.splitlines()

        try:
            end_idx = lines.index('END')
        except ValueError:
            raise AssertionError('Expected ASCII table header to include END.')

        for line in lines[end_idx + 1:]:
            if line.strip():
                return line

        raise AssertionError('Expected ASCII table data row in written payload.')

    def test_dexp_001_assigns_replace_result_to_output_field(self):
        """
        Ensure D-format conversion stores the normalized value with ``D`` into the
        table output field.
        """

        array = np.array([1.2345e20], dtype=np.float64)
        column = fits.Column(name='x', format='D15.7', array=array)
        hdu = fits.TableHDU.from_columns([column])

        output_field = hdu.data['x'].copy()
        hdu.data._scale_back_ascii(0, array, output_field)

        assert b'D' in output_field[0]
        assert b'E' not in output_field[0]

    def test_dexp_001_uses_replaced_output_field_for_serialization(self):
        """
        Validate that serialized ASCII-table output uses the updated payload.
        """

        array = np.array([1.2345e20], dtype=np.float64)
        column = fits.Column(name='x', format='D15.7', array=array)
        hdu = fits.TableHDU.from_columns([column])

        payload = self._table_payload(hdu)
        row = self._first_ascii_data_line(payload)

        assert 'D' in row
        assert 'E' not in row

    def test_dexp_001_emits_d_separator_for_d_format_fields(self):
        """
        Ensure an ASCII-table field formatted with ``D`` emits ``D`` exponent
        separators in output bytes.
        """

        array = np.array([6.02e23], dtype=np.float64)
        column = fits.Column(name='x', format='D15.7', array=array)
        hdu = fits.TableHDU.from_columns([column])

        payload = self._table_payload(hdu)
        row = self._first_ascii_data_line(payload).strip()

        assert re.search(r'D[+-]\d\d', row)
        assert 'E' not in row
