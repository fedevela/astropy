# ASCII RST header_rows architecture map (ASTRST-001, ASTRST-002, ASTRST-005, ASTRST-006)

## Scope

- Writer option support: `ascii.rst` write path accepts `header_rows` during writer construction.
- Deterministic multi-line header rendering for `ascii.rst` when `header_rows` contains ordered tokens.
- Shared column-width derivation for those header rows and all body rows.
- Reader/parser path untouched: no changes to parsing logic or read contracts.

## Requirement-to-architecture mapping

- `ASTRST-001` (`ascii.rst` write option support):
  - Logical pressure: ownership + contract
  - Architectural home: `astropy/io/ascii/rst.py` class `RST`
  - Primary seam: `RST.__init__(header_rows=None)` → `FixedWidth.__init__(..., header_rows=...)`
  - Contract: constructor must accept `header_rows` and pass it through as a formatting option.
  - Integration impact: only write-side path; no reader/parsing imports or callsites altered.

- `ASTRST-002` (ordered multiple header rows before data):
  - Logical pressure: boundary + ordering + interface sequence
  - Architectural home: `astropy/io/ascii/rst.py` method `RST.write`
  - Primary seam: fixed-width line buffer produced by parent writer (`self.data.write(lines)` equivalent)
    -> `RST.write` framing logic.
  - Contract:
    - Output header row sequence must preserve `header_rows` request order.
    - For `["name", "unit"]`, the first emitted header line is names, the second is units.
    - Both rows appear before the table body.
  - Dependency rule: `RST.write` is forbidden to re-interpret header tokens; it only inserts/render-orders
    already-materialized header lines from fixed-width formatter.

- `ASTRST-005` (stable width alignment across header rows and data):
  - Logical pressure: algorithmic state + stability + compatibility
  - Architectural home: `astropy/io/ascii/fixedwidth.py` method `FixedWidthData.write`
  - Primary seam: fixed-width column width calculation and emission path:
    - width vector computed from candidate rows and reused for `header_rows` formatting and body formatting.
    - header section emission order becomes `for token in header_rows`.
  - Contract:
    - Exactly one width derivation pass before rendering all rows.
    - Every rendered header/data row uses same width vector.
    - Border/divider position remains stable (`len(header_rows)` header lines before border/body transition).
  - Integration guard: no alternate width policy for header-only or token-only passes.

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
  - `RST.write` → `FixedWidthData.write` output contract (line vector shape and border position semantics).
- No new dependency from ASCII RST read/parsing path into `header_rows` handling.

## Integration seam skeletons

- Writer construction seam:
  - Input: optional `header_rows` from `ascii.write(..., Writer=ascii.RST, header_rows=...)`
  - Interface: constructor argument on `RST.__init__`
  - Output: forwarded option reaches `FixedWidth` writer implementation.

- Multi-header output seam:
  - Input: ordered `header_rows` list on `ascii.rst` formatter.
  - Step 1 (width authority): `FixedWidthData.write` owns width planning and emits row strings.
  - Step 2 (framing authority): `RST.write` owns placement of `header_rows` lines relative to `self.data.write(lines)` output.
  - Guarantee: header block length equals number of tokens; column geometry matches body.

- Verification seam:
  - Input: exact-output fixtures bound to `ASTRST_VERIFICATION_MAPPING`.
  - Contract points:
    - `ASTRST-002`: `test_astrst_002_rst_header_rows_name_unit_ordered_before_data`
    - `ASTRST-005`: `test_astrst_005_rst_multiple_header_rows_share_stable_widths_with_data`

- Regression seam:
  - Baseline tests remain the same pass-to-pass artifacts listed in `ASTRST_VERIFICATION_MAPPING`.

## Readiness signal

- Structural readiness is complete when:
  - all obligation pressure points above map to files/locations.
  - write/read boundaries remain separated.
  - contract artifacts remain requirement-traceable (`ASTRST_VERIFICATION_MAPPING`).
  - stable geometry contract is represented at least once in a write-path seam artifact (`FixedWidthData.write` + `RST.write`).

## Traceability manifest

- `astropy/io/ascii/tests/test_rst.py` → ASTRST-002, ASTRST-005 (test placeholders and mapping entries)
- `astropy/io/ascii/fixedwidth.py` → ASTRST-005 (shared width authority)
- `astropy/io/ascii/rst.py` → ASTRST-002 / ASTRST-005 (frame boundary and ordered insertion)
