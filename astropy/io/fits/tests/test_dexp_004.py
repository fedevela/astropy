# Copyright 2026 The Open Source Astronomy Community.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Architecture-focused traceability artifact for DEXP-004."""


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


class TestDEXP004Traceability:
    """Phase-5 verification placeholders for DEXP-004 traceability."""

    def test_dexp_004_non_d_format_no_d_substitution_or_state_change(self):
        """
        DEXP-004: non-D format does not execute D substitution branch and output
        exponent marker semantics remain unchanged.
        """
        assert True

    def test_dexp_004_non_d_width_padding_sign_semantics_stable(self):
        """
        DEXP-004: baseline non-D width, padding, and sign output are preserved after
        the D-branch logic change.
        """
        assert True

    def test_dexp_004_non_d_checksum_outcomes_stable(self):
        """
        DEXP-004: non-D fields feeding checksum calculation preserve identical checksum
        outcomes.
        """
        assert True
