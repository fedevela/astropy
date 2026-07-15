# Copyright 2026 The Open Source Astronomy Community.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Traceability artifact for DEXP-005 scope preservation."""

import io

import numpy as np

from ....io import fits

from . import FitsTestCase


DEXP_005_VERIFICATION = {
    "DEXP-005": [
        "test_dexp_005_only_d_branch_is_target_scope",
        "test_dexp_005_no_side_effect_path_outside_d_branch",
        "test_dexp_005_no_new_non_d_exponent_policy",
    ]
}


DEXP_005_ARCHITECTURE_PRESSURES = [
    {
        "requirement": "DEXP-005",
        "pressure": "branch_boundary",
        "obligation": (
            "Only the D-format replacement decision path in `_scale_back_ascii` may"
            " mutate output bytes."
        ),
        "locus": "astropy/io/fits/fitsrec.py::TableData::_scale_back_ascii",
        "type": "ownership",
    },
    {
        "requirement": "DEXP-005",
        "pressure": "non_d_stability",
        "obligation": (
            "Non-D branches preserve spacing, sign, decimal-point placement, and"
            " byte shape with no local substitutions."
        ),
        "locus": "astropy/io/fits/fitsrec.py::TableData::_scale_back_ascii",
        "type": "contract",
    },
    {
        "requirement": "DEXP-005",
        "pressure": "integration_stability",
        "obligation": (
            "Only `_prewriteto` consumes the staged output bytes; no pipeline"
            " refactor or extra adapter insertion."
        ),
        "loci": [
            "astropy/io/fits/fitsrec.py::TableData::_scale_back_ascii",
            "astropy/io/fits/hdu/table.py::_TableBaseHDU::_prewriteto",
        ],
        "type": "dependency_direction",
    },
]


DEXP_005_ARCHITECTURE = {
    "DEXP-005": {
        "owner": "astropy/io/fits/fitsrec.py",
        "contracts": {
            "scope_restriction": (
                "Limit behavior change to `if 'D' in format:` branch in "
                "`TableData::_scale_back_ascii`."
            ),
            "semantic_isolation": (
                "No non-D format branch semantics are changed by this issue."
            ),
            "policy_stability": (
                "No new D-exponent policy is introduced outside that branch."
            ),
        },
        "topology": [
            "astropy/io/fits/fitsrec.py::TableData::_scale_back_ascii",
            "astropy/io/fits/fitsrec.py::TableData::_scale_back",
            "astropy/io/fits/hdu/table.py::_TableBaseHDU::_prewriteto",
        ],
        "dependency_direction": [
            "TableData::_scale_back_ascii -> _TableBaseHDU::_prewriteto",
            "_scale_back -> _scale_back_ascii -> _TableBaseHDU::_prewriteto",
            "encode_ascii -> output_field.replace (branch-local only)",
        ],
        "ownership_boundary": {
            "serializer": "TableData::_scale_back_ascii owns local payload mutation in D branch.",
            "staging": "TableData::_scale_back stages per-column serialized arrays.",
            "handoff": "`_TableBaseHDU::_prewriteto` consumes staged payload."
        },
        "integration_seams": {
            "format_to_payload": {
                "producer": "TableData::_scale_back_ascii",
                "consumer": "TableData::_scale_back",
                "contract": "Only D-branch may rewrite exponent glyph from E to D.",
            },
            "payload_to_writer": {
                "producer": "_TableBaseHDU::_prewriteto",
                "consumer": "TableHDU stream/checksum emitters",
                "contract": "Payload bytes are consumed unchanged except for branch-local D replacement.",
            },
        },
        "readiness": {
            "scope_gate": "true",
            "non_d_stability_gate": "true",
            "cross_pipeline_refactor_gate": "true",
            "dependency_gate": "true",
        },
        "pressures": DEXP_005_ARCHITECTURE_PRESSURES,
        "verification": DEXP_005_VERIFICATION["DEXP-005"],
    },
}


DEXP_005_ARCHITECTURE_PLACEMENT = [
    {
        "requirement": "DEXP-005",
        "obligation": "only_d_format_replacement_branch_targeted",
        "locator": "astropy/io/fits/fitsrec.py::_scale_back_ascii",
        "pressure": "branch_boundary",
        "handoff_boundary": "serialized payload staging",
        "owner": "TableData::_scale_back_ascii",
        "adapter": "branch guard + `output_field[:] = output_field.replace(...)` assignment",
    },
    {
        "requirement": "DEXP-005",
        "obligation": "non_d_paths_remain_functionally_stable",
        "locator": "astropy/io/fits/hdu/table.py::_TableBaseHDU::_prewriteto",
        "pressure": "semantic_preservation",
        "handoff_boundary": "payload emission",
        "owner": "write pipeline boundary",
        "adapter": "`if 'D' in format: ... else: pass` branch split",
    },
    {
        "requirement": "DEXP-005",
        "obligation": "exponent_policy_outside_branch_unmodified",
        "locator": "astropy/io/fits/fitsrec.py::_scale_back_ascii",
        "handoff_boundary": "local branch decision",
        "pressure": "policy_stability",
        "owner": "formatter branch controller",
        "adapter": "no-op `else` branch",
    },
]


DEXP_005_REQUIREMENT_TO_ARCHITECTURE = {
    "DEXP-005": {
        "logic_obligations": [
            "scope_isolation_in_if_d_guard",
            "non_d_path_stability",
            "no_new_d_policy_beyond_branch",
        ],
        "artifact_loci": {
            "scope_isolation_in_if_d_guard": [
                "astropy/io/fits/fitsrec.py::_scale_back_ascii (if 'D' in format)",
                "astropy/io/fits/tests/test_dexp_005.py::DEXP_005_ARCHITECTURE_PRESSURES",
            ],
            "non_d_path_stability": [
                "astropy/io/fits/fitsrec.py::_scale_back_ascii (else pass)",
                "astropy/io/fits/tests/test_dexp_005.py::DEXP_005_ARCHITECTURE_PLACEMENT",
            ],
            "no_new_d_policy_beyond_branch": [
                "astropy/io/fits/fitsrec.py::_scale_back_ascii branch comment envelope",
                "astropy/io/fits/tests/test_dexp_005.py::DEXP_005_ARCHITECTURE",
            ],
        },
    },
}


class TestDEXP005Traceability(FitsTestCase):
    """Phase-5 placeholder contract verification for DEXP-005."""

    @staticmethod
    def _output_field(value, format_spec):
        values = np.array([value], dtype=np.float64)
        column = fits.Column(name="x", format=format_spec, array=values)
        hdu = fits.TableHDU.from_columns([column])
        output_field = hdu.data["x"].copy()
        hdu.data._scale_back_ascii(0, values, output_field)
        return output_field[0]

    @staticmethod
    def _first_ascii_data_line(payload):
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

    def test_dexp_005_only_d_branch_is_target_scope(self):
        """
        DEXP-005 Scope Restriction:
        Proposed change must be confined to D-format replacement branch.
        """
        d_output = self._output_field(1.2345e20, "D15.7")
        e_output = self._output_field(1.2345e20, "E15.7")

        assert b"E" not in d_output
        assert b"D" in d_output
        assert d_output == e_output.replace(b"E", b"D")

    def test_dexp_005_no_side_effect_path_outside_d_branch(self):
        """
        DEXP-005 No Semantic Side Effects:
        Unrelated non-D formatting behavior remains outside modified scope.
        """
        e_output = self._output_field(1.2345e20, "E15.7")
        f_output = self._output_field(1.0, "F15.0")

        assert b"D" not in e_output
        assert b"E" in e_output
        assert e_output == b"  1.2345000E+20"
        assert f_output == b"             1."

    def test_dexp_005_no_new_d_exponent_policy(self):
        """
        DEXP-005 D-Exponent Policy Stability:
        No new non-local D-exponent policy is introduced outside targeted branch.
        """
        hdu = fits.TableHDU.from_columns([
            fits.Column(name="x", format="D15.7", array=np.array([1.2345e20],
                                                                dtype=np.float64)),
            fits.Column(name="y", format="E15.7", array=np.array([1.2345e20],
                                                                dtype=np.float64)),
        ])
        stream = io.BytesIO()
        hdu.writeto(stream)
        payload = stream.getvalue()
        row = self._first_ascii_data_line(payload)

        assert row.count("D") == 1
        assert row.count("E") == 1
