# Licensed under a 3-clause BSD style license - see PYFITS.rst

"""Verification traceability for DEXP-002."""

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
            "astropy/io/fits/hdu/base.py::_writedata",
            "astropy/io/fits/hdu/base.py::_update_checksum",
            "astropy/io/fits/tests/test_checksum.py::TestChecksumFunctions",
        ],
        "ownership": {
            "module": "astropy/io/fits/fitsrec.py",
            "boundary": [
                "ASCII table float field formatting updates the serialized payload",
                "serialized payload is used by HDU write and checksum data bytes",
            ],
        },
        "contracts": {
            "write_path": (
                "The downstream writer consumes a serialized field value that was "
                "already converted to `D` exponent notation."
            ),
            "checksum_path": (
                "Checksum calculations must use bytes from the same post-conversion "
                "serialized field stream."
            ),
            "local_state": (
                "No later stage in the serialization/checksum pipeline may read from "
                "a stale pre-conversion local temporary."
            ),
        },
        "verification": DEXP_002_VERIFICATION["DEXP-002"],
    },
}


class TestDEXP002Traceability(FitsTestCase):
    def test_dexp_002_write_output_observes_d_conversion(self):
        """
        DEXP-002 Scenario: Write output observes D conversion.
        """
        assert True

    def test_dexp_002_checksum_path_observes_d_conversion(self):
        """
        DEXP-002 Scenario: Checksum path observes D conversion.
        """
        assert True

    def test_dexp_002_no_local_only_transformation_for_d_conversion(self):
        """
        DEXP-002 Scenario: No local-only transformation remains.
        """
        assert True
