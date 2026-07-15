# Copyright 2026 The Open Source Astronomy Community.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Architecture-focused traceability artifact for DEXP-004."""

import io

import numpy as np

from ....io import fits
from ..header import _pad_length

from . import FitsTestCase


DEXP_004_VERIFICATION = {
    "DEXP-004": [
        "test_dexp_004_non_d_format_no_d_substitution_or_state_change",
        "test_dexp_004_non_d_width_padding_sign_semantics_stable",
        "test_dexp_004_non_d_checksum_outcomes_stable",
    ]
}


DEXP_004_ARCHITECTURE_PRESSURES = [
    {
        "requirement": "DEXP-004",
        "pressure": "decision_boundary",
        "obligation": (
            "Format lacks D marker => no exponent-substitution branch executes."
        ),
        "locus": "astropy/io/fits/fitsrec.py::TableData::_scale_back_ascii",
        "type": "ownership+contract",
    },
    {
        "requirement": "DEXP-004",
        "pressure": "formatting_semantics",
        "obligation": (
            "Width, padding, and sign behavior for non-D paths remains identical."
        ),
        "loci": [
            "astropy/io/fits/fitsrec.py::TableData::_scale_back_ascii",
            "astropy/io/fits/hdu/table.py::_TableBaseHDU::_prewriteto",
        ],
        "type": "boundary+dependency",
    },
    {
        "requirement": "DEXP-004",
        "pressure": "checksum_stability",
        "obligation": (
            "Checksum input bytes for non-D serialization remain unchanged."
        ),
        "loci": [
            "astropy/io/fits/hdu/table.py::TableHDU::_writedata_internal",
            "astropy/io/fits/hdu/table.py::TableHDU::_calculate_datasum",
        ],
        "type": "integration_seam",
    },
]


DEXP_004_ARCHITECTURE = {
    "DEXP-004": {
        "topology": [
            "astropy/io/fits/fitsrec.py::TableData::_scale_back_ascii",
            "astropy/io/fits/fitsrec.py::TableData::_scale_back",
            "astropy/io/fits/hdu/table.py::_TableBaseHDU::_prewriteto",
            "astropy/io/fits/hdu/table.py::TableHDU::_writedata_internal",
            "astropy/io/fits/hdu/table.py::TableHDU::_calculate_datasum",
            "astropy/io/fits/hdu/base.py::_update_checksum",
            "astropy/io/fits/hdu/base.py::_calculate_datasum",
        ],
        "ownership": {
            "module": {
                "serialization_non_d": "astropy/io/fits/fitsrec.py",
                "write_path": "astropy/io/fits/hdu/table.py",
                "checksum_path": "astropy/io/fits/hdu/base.py",
            },
            "boundary": [
                "Serialization branching remains inside `_scale_back_ascii`.",
                "Writer and checksum consumers must read from `_prewriteto` staged `self.data` bytes.",
            ],
        },
        "contracts": {
            "skip_branch": (
                "When format does not include D, D-branch replacement is never executed."
            ),
            "semantics_stability": (
                "Width, padding, and sign behavior for non-D formatting remains unchanged."
            ),
            "checksum_stability": (
                "Payload bytes for non-D paths remain identical through writer and "
                "DATASUM inputs."
            ),
            "invariants": (
                "No per-field detached transformation occurs after `_scale_back_ascii` "
                "for non-D data when building write/checksum streams."
            ),
        },
        "dependency_direction": [
            "TableData::_scale_back -> _scale_back_ascii",
            "_scale_back_ascii -> _TableBaseHDU::_prewriteto",
            "_prewriteto -> TableHDU::_writedata_internal",
            "_prewriteto -> BaseHDU::_update_checksum -> BaseHDU::_calculate_datasum",
        ],
        "integration_seams": {
            "format_to_payload": {
                "producer": "TableData::_scale_back_ascii",
                "consumer": "TableData::_scale_back (staged `raw_field`)",
                "contract": "Only D marker rewrite can alter formatted exponent bytes.",
            },
            "write_checksum_alignment": {
                "producer": "_TableBaseHDU::_prewriteto",
                "consumer": "TableHDU::_writedata_internal / _calculate_datasum",
                "contract": (
                    "Both consumers share the exact staged in-memory payload "
                    "with no local temporary replacements."
                ),
            },
        },
        "readiness": {
            "placement_complete": "true",
            "boundary_preserved": "true",
            "dependency_single_source": "true",
            "verification_mapping_ready": "true",
            "checksum_path_aligned_with_write_path": "true",
        },
        "pressures": DEXP_004_ARCHITECTURE_PRESSURES,
        "verification": DEXP_004_VERIFICATION["DEXP-004"],
    },
}


DEXP_004_ARCHITECTURE_PLACEMENT = [
    {
        "requirement": "DEXP-004",
        "obligation": "non_d_substitution_or_state_change",
        "pressure": "ownership + branch boundary",
        "owning_artifact": "astropy/io/fits/fitsrec.py::TableData::_scale_back_ascii",
        "integration_seam": "format->payload",
        "adapter": "non-D branch guard comment in implementation",
    },
    {
        "requirement": "DEXP-004",
        "obligation": "width_padding_sign_stability",
        "pressure": "semantic conservation",
        "owning_artifact": "astropy/io/fits/hdu/table.py::_TableBaseHDU::_prewriteto",
        "integration_seam": "payload_staging_for_write",
        "adapter": "self.data._scale_back staged payload",
    },
    {
        "requirement": "DEXP-004",
        "obligation": "checksum_outcomes_stable",
        "pressure": "source equivalence",
        "owning_artifact": "astropy/io/fits/hdu/table.py::TableHDU::_calculate_datasum",
        "integration_seam": "in-memory_checksum_source",
        "adapter": "byte-view of staged `_scale_back` payload",
    },
]


class TestDEXP004Traceability(FitsTestCase):
    """Phase-5 verification placeholders for DEXP-004 traceability."""

    @staticmethod
    def _table_payload(hdu):
        # Build a byte-level payload for a deterministic row-by-row semantic check.
        stream = io.BytesIO()
        hdu.writeto(stream)
        stream.seek(0)
        return stream.getvalue()

    @staticmethod
    def _first_ascii_data_line(payload):
        # Parse the first non-empty ASCII row following the header END marker.
        text = payload.decode("ascii")
        lines = text.splitlines()

        try:
            end_idx = lines.index("END")
        except ValueError as exc:
            raise AssertionError("Expected ASCII table header to include END.") from exc

        for line in lines[end_idx + 1:]:
            if line.strip():
                return line

        raise AssertionError("Expected ASCII table data row in written payload.")

    @staticmethod
    def _non_d_output_field(value, format_spec):
        # Execute the non-D formatting branch directly.
        values = np.array([value], dtype=np.float64)
        column = fits.Column(name="x", format=format_spec, array=values)
        hdu = fits.TableHDU.from_columns([column])
        output_field = hdu.data["x"].copy()
        hdu.data._scale_back_ascii(0, values, output_field)
        return output_field[0]

    def test_dexp_004_non_d_format_no_d_substitution_or_state_change(self):
        """
        DEXP-004: non-D format does not execute D substitution branch and output
        exponent marker semantics remain unchanged.
        """
        output = self._non_d_output_field(1.2345e20, "E15.7")
        assert b"D" not in output
        assert b"E" in output
        assert output == b"  1.2345000E+20"

    def test_dexp_004_non_d_width_padding_sign_semantics_stable(self):
        """
        DEXP-004: baseline non-D width, padding, and sign output are preserved after
        the D-branch logic change.
        """
        output_positive = self._non_d_output_field(1.2345e20, "E15.7")
        output_negative = self._non_d_output_field(-1.2345e20, "E15.7")
        output_zero_prec = self._non_d_output_field(1.0, "F15.0")

        assert output_positive == b"  1.2345000E+20"
        assert output_negative == b" -1.2345000E+20"
        assert output_zero_prec == b"             1."

    def test_dexp_004_non_d_checksum_outcomes_stable(self):
        """
        DEXP-004: non-D fields feeding checksum calculation preserve identical checksum
        outcomes.
        """
        hdu = fits.TableHDU.from_columns([
            fits.Column(name="x", format="E15.7", array=np.array([1.2345e20], dtype=np.float64))
        ])
        hdu.data._scale_back()
        expected = bytes(hdu.data.view(np.ubyte)) + b" " * _pad_length(hdu.data.nbytes)

        observed = {}
        original_compute_checksum = hdu._compute_checksum

        def capture_compute_checksum(data, sum32=0):
            observed["data_bytes"] = bytes(data)
            observed["data_sum"] = original_compute_checksum(data, sum32)
            return observed["data_sum"]

        hdu._compute_checksum = capture_compute_checksum.__get__(hdu, type(hdu))
        hdu.writeto(io.BytesIO(), checksum="datasum")

        assert observed["data_bytes"] == expected
        assert b"D" not in observed["data_bytes"]
        assert b"E" in observed["data_bytes"]
        assert int(hdu.header["DATASUM"]) == observed["data_sum"]
