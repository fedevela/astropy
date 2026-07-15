# ASCII RST header_rows architecture map (ASTRST-001, ASTRST-002, ASTRST-003, ASTRST-004, ASTRST-005, ASTRST-006)

## Scope

- Writer option support: `ascii.rst` write path accepts `header_rows` during writer construction.
- Deterministic multi-line header rendering for `ascii.rst` when `header_rows` contains ordered tokens.
- Shared column-width derivation for those header rows and all body rows.
- Reader/parser path untouched: no changes to parsing logic or read contracts.
- Default output topology is preserved for `ascii.rst` calls without explicit `header_rows`.
- `=` border-row continuity and boundary alignment are required when `header_rows` are emitted.

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

- `ASTRST-003` (default topology preservation when `header_rows` is omitted):
  - Logical pressure: ownership, boundary, regression anchor
  - Architectural home:
    - `astropy/io/ascii/fixedwidth.py` class `FixedWidth.__init__`
    - `astropy/io/ascii/rst.py` class `RST.__init__`
    - `astropy/io/ascii/rst.py` class `RST.write`
  - Primary seam:
    - `RST.__init__(header_rows=None)` forwards formatting intent into `FixedWidth`.
    - `FixedWidth.__init__` normalizes unset `header_rows` to `["name"]`.
    - `RST.write` selects default header-block size only through `self.data.header_rows`.
  - Contract:
    - no `header_rows` argument keeps the pre-existing single-separator RST output shape.
    - existing `test_write_normal` remains the default baseline contract.
  - Integration impact: no reader/parsing seam is introduced.

- `ASTRST-004` (`=` border shape with header rows):
  - Logical pressure: geometry + alignment + contract seam
  - Architectural home:
    - `astropy/io/ascii/fixedwidth.py` class `FixedWidthData.write`
    - `astropy/io/ascii/rst.py` class `RST.write`
  - Primary seam:
    - `FixedWidthData.write` computes one width vector reused by every header/data row.
    - `RST.write` wraps the emitted lines with the same `=` border row at top/middle/bottom.
  - Contract:
    - every header/data line shares the same column boundary positions.
    - output includes valid simple-table border positions in `=` style.
    - the same border row can be reused for top/middle/bottom without style change.
  - Integration impact: no additional style options or read-path dependencies.

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
- Additional boundary invariants:
  - `FixedWidth.__init__` is the sole owner of default `header_rows` semantics.
  - `RST.write` owns border framing only and cannot change width calculation or column metadata.

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
  - `ASTRST-003`:
    - Baseline contract and regression anchor:
      - `test_astrst_003_rst_no_header_rows_defaults_preserve_rst_topology`
      - `test_write_normal`
  - `ASTRST-004`:
    - border geometry and alignment contracts:
      - `test_astrst_004_rst_header_rows_with_equals_borders_and_column_alignment`

- Regression seam:
  - Baseline tests remain the same pass-to-pass artifacts listed in `ASTRST_VERIFICATION_MAPPING`.

## Readiness signal

- Structural readiness is complete when:
  - all obligation pressure points above map to files/locations.
  - write/read boundaries remain separated.
  - contract artifacts remain requirement-traceable (`ASTRST_VERIFICATION_MAPPING`).
  - stable geometry contract is represented at least once in a write-path seam artifact (`FixedWidthData.write` + `RST.write`).

## Traceability manifest

- `astropy/io/ascii/tests/test_rst.py` → ASTRST-002, ASTRST-003, ASTRST-004, ASTRST-005 (test placeholders and mapping entries)
- `astropy/io/ascii/fixedwidth.py` → ASTRST-005 (shared width authority)
- `astropy/io/ascii/rst.py` → ASTRST-002 / ASTRST-003 / ASTRST-004 (frame boundary and top-line framing)
- `astropy/io/ascii/rst_architecture.md` → ASTRST-003 / ASTRST-004 (traceable seam and boundary declarations)
