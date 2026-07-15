# ISSUE13-005 Architecture Artifact

## Requirement-to-Architecture Map
- ISSUE13-005 -> `astropy/io/ascii/qdp.py::QDP.read` (public call-path preservation on `ascii.qdp`).
- ISSUE13-005 -> `astropy/io/ascii/qdp.py::_read_table_qdp` (single fixed parser handoff boundary from API entry).
- ISSUE13-005 -> `astropy/io/ascii/qdp.py::_line_type` (raw command-line intake and case-insensitive command matching without global pre-normalization).
- ISSUE13-005 -> `astropy/io/ascii/qdp.py::_get_tables_from_qdp_file` (raw command-line capture and delayed sub-key canonicalization only).
- ISSUE13-005 -> `astropy/io/ascii/tests/test_qdp.py:REQUIREMENT_VERIFICATION_MAP` (traceability for scenario-level verification artifacts).

## File and Module Placement
- `astropy/io/ascii/qdp.py` remains the owning module for all public-entry and parser-semantics obligations for this requirement.
- `astropy/io/ascii/tests/test_qdp.py` remains the verification and traceability ownership surface.
- No new modules or adapters are introduced because the requirement constrains internal parser boundaries only.

## Ownership Boundaries
- `QDP.read` owns the reader registration boundary where external format dispatch enters the QDP reader.
- `_read_table_qdp` owns the API-to-parser handoff contract and `table_id` return-table selection for this format.
- `_line_type` owns raw line classification (comment/data/command/new) and command recognition gate.
- `_get_tables_from_qdp_file` owns table-state transitions and command block accumulation, including preservation of raw command text.

## Interface / Contract Artifacts
- Public interface contract:
  - Keep `Table.read(..., format="ascii.qdp")` and `QDP.read` as the direct entry path.
  - Preserve behavior with no caller-facing preprocessing flag or utility step.
- Internal call-path contract:
  - `QDP.read` → `_read_table_qdp` → `_get_tables_from_qdp_file` with no alternate case-normalization branch.
- Command parsing contract:
  - `_line_type` may apply case-insensitive matching only for command syntax validation.
  - Sub-key dispatch in downstream parsing continues to use canonical `lower()` only for comparison.
  - No caller-side or global pre-normalization of the input line stream is introduced.
- Error/shape contract:
  - Parsing acceptance/rejection follows existing branches (e.g., `ValueError("Unrecognized QDP line: ...")`) and existing shape/dtype flow is unchanged.

## Dependency Direction Notes
- `Table.read(format="ascii.qdp")`/`QDP.read` depend on `_read_table_qdp`; parser internals do not feed back into registration.
- `_read_table_qdp` depends on `_get_tables_from_qdp_file`; it returns `tables[table_id]` only.
- `_get_tables_from_qdp_file` depends on `_line_type` for deterministic typing and receives raw lines, then internally normalizes only sub-key tokens for dispatch.

## Integration-Seam Skeletons
- Integration seam 1: external parser entry (`QDP.read`).
  - Owner: `astropy/io/ascii/qdp.py`
  - Contract: fixed route for `ascii.qdp`; no pre-normalization wrapper.
- Integration seam 2: read boundary (`_read_table_qdp`).
  - Owner: `astropy/io/ascii/qdp.py`
  - Contract: direct delegation into `_get_tables_from_qdp_file` and stable table selection by index.
- Integration seam 3: command-classification seam (`_line_type`).
  - Owner: `astropy/io/ascii/qdp.py`
  - Contract: classify from raw, stripped line; command acceptance can be case-insensitive, non-command tokenization remains strict.
- Integration seam 4: command-dispatch seam (`_get_tables_from_qdp_file`).
  - Owner: `astropy/io/ascii/qdp.py`
  - Contract: store command lines unchanged; normalize only `command[1]` for serr/terr checks.

## Scenario-to-Placement Traceability
- Scenario 1 (lowercase command file via `Table.read(format="ascii.qdp")`):
  - Maps to `QDP.read` -> `_read_table_qdp` -> `_get_tables_from_qdp_file` -> `_line_type` -> data assembly.
  - Acceptance is satisfied by existing read route and parser command case tolerance.
- Scenario 2 (lowercase/mixed-case and uppercase command files through same read shape):
  - Maps to same call-path above; `_line_type` and downstream sub-key handling must provide equivalent parse outcomes.

## Completion Gate Status
- All ISSUE13-005 logic obligations are assigned to explicit ownership boundaries and seams.
- Requirement traceability remains in `astropy/io/ascii/tests/test_qdp.py` through existing mapping entries.
- Architecture artifact updated/created: `astropy/io/ascii/qdp_issue13_005_architecture.md`.
- Structural readiness is met for implementation: boundary, ownership, dependency direction, and scenario traceability are explicit.
