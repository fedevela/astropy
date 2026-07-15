# Licensed under a 3-clause BSD style license - see PYFITS.rst

"""Verification traceability for DEXP-002."""

import io
import re

import numpy as np

from ....io import fits
from ..header import _pad_length

from . import FitsTestCase


DEXP_002_VERIFICATION = {
    "DEXP-002": [
        "test_dexp_002_write_output_observes_d_conversion",
        "test_dexp_002_checksum_path_observes_d_conversion",
        "test_dexp_002_no_local_only_transformation_for_d_conversion",
    ]
}

# Traceability for DEXP-002.
DEXP_002_ARCHITECTURE = {
    "DEXP-002": {
        "topology": [
            "astropy/io/fits/fitsrec.py::TableData::_scale_back_ascii",
            "astropy/io/fits/fitsrec.py::TableData::_scale_back",
            "astropy/io/fits/hdu/table.py::_TableBaseHDU::_prewriteto",
            "astropy/io/fits/hdu/table.py::TableHDU::_writedata_internal",
            "astropy/io/fits/hdu/table.py::TableHDU::_calculate_datasum",
            "astropy/io/fits/hdu/base.py::_update_checksum",
            "astropy/io/fits/hdu/base.py::_calculate_datasum",
            "astropy/io/fits/tests/test_checksum.py::TestChecksumFunctions",
        ],
        "ownership": {
            "module": {
                "serialization": "astropy/io/fits/fitsrec.py",
                "write_and_checksum": "astropy/io/fits/hdu/table.py",
                "checksum_fallback": "astropy/io/fits/hdu/base.py",
            },
            "boundary": [
                "TableData::_scale_back_ascii owns ASCII field serialization and performs D-exponent normalization in `output_field`.",
                "TableHDU payload writer/checksum logic owns the in-memory serialized payload produced by `_scale_back`.",
                "BaseHDU checksum contract remains the fallback source-of-truth when data is not in-memory.",
            ],
        },
        "contracts": {
            "write_path": (
                "The downstream writer consumes a serialized field value that was "
                "already converted to `D` exponent notation in `output_field`, then "
                "consumed as `self.data`/byte-view in `_writedata_internal`."
            ),
            "checksum_path": (
                "Checksum calculations must use bytes from the same post-conversion "
                "serialized field stream used by the writer and include FITS block padding."
            ),
            "local_state": (
                "No later stage in the serialization/checksum pipeline may read from "
                "a stale pre-conversion local temporary."
            ),
        },
        "dependency_direction": [
            "TableData::_scale_back_ascii -> TableData::_scale_back (in-place `raw_field` payload finalization)",
            "TableData::_scale_back -> _TableBaseHDU::_prewriteto (canonical serialized bytes for this HDU)",
            "._prewriteto -> TableHDU::_writedata_internal (write consumes serialized payload bytes)",
            "_TableBaseHDU::_prewriteto -> BaseHDU._update_checksum (checksum decision happens after staging)",
            "BaseHDU._update_checksum -> BaseHDU._calculate_datasum (data-source branching by `_data_loaded`)",
            "TableHDU::_calculate_datasum -> BaseHDU::_calculate_datasum (non-ASCII table fallback)",
        ],
        "integration_seams": {
            "write": {
                "producer": "TableData::_scale_back",
                "transformer": "TableData::_scale_back_ascii",
                "consumer": "TableHDU::_writedata_internal",
                "contract": "single canonical serialized byte-array flows through all stages, never a detached temporary local copy.",
            },
            "checksum": {
                "producer": "TableData::_scale_back",
                "transformer": "BaseHDU._update_checksum -> _calculate_datasum",
                "consumer": "header keyword update (`CHECKSUM` / `DATASUM`)",
                "contract": "checksum input for in-memory path is `self.data` bytes after D-normalization.",
            },
        },
        "verification": DEXP_002_VERIFICATION["DEXP-002"],
        "readiness": {
            "local_source_eliminated": "true",
            "write_and_checksum_byte_sources_aligned": "true",
            "ownership_boundary_resolved": [
                "fitsrec.py owns field-level serialization ownership",
                "table.py owns HDU-level payload staging",
                "base.py owns checksum source routing",
            ],
        },
    },
}

DEXP_002_POC_PLACEMENT = {
    "logic_obligation": [
        {
            "requirement": "DEXP-002",
            "pressure": "output_field ownership",
            "locator": "astropy/io/fits/fitsrec.py::_scale_back_ascii",
            "artifact_class": "format layer contract",
            "justification": "Only place where ASCII payload bytes are normalized.",
        },
        {
            "requirement": "DEXP-002",
            "pressure": "write/checksum coupling",
            "locator": "astropy/io/fits/hdu/table.py::_TableBaseHDU::_prewriteto",
            "artifact_class": "handoff boundary",
            "justification": "Serialization must complete before checksum/write are triggered.",
        },
        {
            "requirement": "DEXP-002",
            "pressure": "checksum source-of-truth",
            "locator": "astropy/io/fits/hdu/base.py::_calculate_datasum",
            "artifact_class": "data-source routing",
            "justification": "Fallback branch must keep parity with staged payload when used.",
        },
    ]
}


class TestDEXP002Traceability(FitsTestCase):
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

    @staticmethod
    def _d_table_hdu(value):
        column = fits.Column(name='x', format='D15.7', array=np.array([value]))
        return fits.TableHDU.from_columns([column])

    def test_dexp_002_write_output_observes_d_conversion(self):
        """
        DEXP-002 Scenario: Write output observes D conversion.
        """
        hdu = self._d_table_hdu(1.2345e20)

        payload = self._table_payload(hdu)
        row = self._first_ascii_data_line(payload)

        assert 'D' in row
        assert 'E' not in row
        assert re.search(r'D[+-]\d\d', row)

    def test_dexp_002_checksum_path_observes_d_conversion(self):
        """
        DEXP-002 Scenario: Checksum path observes D conversion.
        """
        hdu = self._d_table_hdu(1.2345e20)

        observed = {}

        original_compute_checksum = hdu._compute_checksum

        def capture_compute_checksum(data, sum32=0):
            observed['data_bytes_len'] = len(data)
            observed['data_bytes'] = bytes(data)
            observed['data_sum'] = original_compute_checksum(data, sum32)
            return observed['data_sum']

        hdu._compute_checksum = capture_compute_checksum.__get__(hdu, type(hdu))
        hdu.writeto(io.BytesIO(), checksum='datasum')

        assert observed['data_bytes_len'] == hdu.size + _pad_length(hdu.size)
        assert b'D' in observed['data_bytes']
        assert b'E' not in observed['data_bytes']
        assert int(hdu.header['DATASUM']) == observed['data_sum']

    def test_dexp_002_no_local_only_transformation_for_d_conversion(self):
        """
        DEXP-002 Scenario: No local-only transformation remains.
        """
        hdu = self._d_table_hdu(1.2345e20)

        hdu.data._scale_back()

        row = str(hdu.data['x'][0])
        assert 'D' in row
        assert 'E' not in row
