# ASCII RST header_rows architecture map (ASTRST-001, ASTRST-006)

## Scope

- Writer option support: `ascii.rst` write path accepts `header_rows` during writer construction.
- Reader/parser path untouched: no changes to parsing logic or read contracts.

## Requirement-to-architecture mapping

- `ASTRST-001` (`ascii.rst` write option support):
  - Logical pressure: ownership + contract
  - Architectural home: `astropy/io/ascii/rst.py` class `RST`
  - Primary seam: `RST.__init__(header_rows=None)` → `FixedWidth.__init__(..., header_rows=...)`
  - Contract: constructor must accept `header_rows` and pass it through as a formatting option.
  - Integration impact: only write-side path; no reader/parsing imports or callsites altered.

- `ASTRST-006` (reader/parser stability):
  - Logical pressure: boundary + dependency direction
  - Architectural home: `astropy/io/ascii/tests/test_rst.py`
    - Regression-obligation map and placeholder contract artifacts anchor required unchanged behavior.
  - Primary seam: test suite includes unchanged `test_read_*` and `test_write_normal` expectations.
  - Contract: existing read/write behavior must remain unchanged unless `header_rows` path is exercised.

## Ownership and boundaries

- `RST` class owns reStructuredText formatting construction and output framing.
- `FixedWidth` owns shared write algorithms and line rendering.
- ASCII RST reader behavior remains owned by `RST.read` inheritance and sibling read-related tests in
  `astropy/io/ascii/tests/test_rst.py`; this issue introduces no new dependency from `RST` write constructor into reader modules.
- Boundary between write and read:
  - `RST.__init__` and `RST.write` are confined to output formatting concerns.
  - Parser entry points (reader constructors/parsers in `core.py` and `fixedwidth.py` read code paths) remain outside this ticket’s ownership.

## Dependency direction

- New/required dependency is one-way:
  - `RST` → `FixedWidth` (formatter constructor forwarding only).
- No new dependency from ASCII RST read/parsing path into `header_rows` handling.

## Integration seam skeletons

- Writer construction seam:
  - Input: optional `header_rows` from `ascii.write(..., Writer=ascii.RST, header_rows=...)`
  - Interface: constructor argument on `RST.__init__`
  - Output: forwarded option reaches `FixedWidth` writer implementation.
- Regression seam:
  - Baseline tests remain the same pass-to-pass artifacts listed in `ASTRST_VERIFICATION_MAPPING`.

## Readiness signal

- Structural readiness is complete when:
  - all obligation pressure points above map to files/locations.
  - write/read boundaries remain separated.
  - contract artifacts remain requirement-traceable (`ASTRST_VERIFICATION_MAPPING`).
