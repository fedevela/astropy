# ISSUE13-002 Architecture Artifact

## Requirement-to-Architecture Map
- ISSUE13-002 -> `astropy/io/ascii/qdp.py::_line_type` (command token normalization for mixed/lowercase `read serr`).
- ISSUE13-002 -> `astropy/io/ascii/qdp.py::_get_tables_from_qdp_file` (command capture and `err_specs` canonicalization boundary).
- ISSUE13-002 -> `astropy/io/ascii/qdp.py::_interpret_err_lines` (error-column expansion contract).
- ISSUE13-002 -> `astropy/io/ascii/qdp.py::_read_table_qdp` (read-boundary selection contract).
- ISSUE13-002 -> `astropy/io/ascii/tests/test_qdp.py:REQUIREMENT_VERIFICATION_MAP` (verification traceability surface).

## File and Module Placement
- `astropy/io/ascii/qdp.py` remains the ownership module for parsing semantics and table-shaping for QDP `READ SERR`.
- `astropy/io/ascii/tests/test_qdp.py` remains the ownership module for scenario-level traceability for `ISSUE13-002`.
- No new modules are required; all obligations are already scoped to the existing parser seams.

## Ownership Boundaries
- `_line_type` owns lexical command recognition boundaries and must remain neutral to case.
- `_get_type_from_list_of_lines` owns line-type sequencing but does not interpret command meaning.
- `_get_tables_from_qdp_file` owns command-block capture, `command_lines` parsing, and `err_specs` handoff.
- `_interpret_err_lines` owns expansion from `err_specs` into column names and output column layout.
- `_read_table_qdp` owns final output-table selection and returns the already-normalized parser result.

## Interface / Contract Artifacts
- Command contract:
  - command lines beginning with `READ` + `SERR`/`TERR` are classified by `_line_type` independent of lexical case.
  - `READ` sub-key matching in `_get_tables_from_qdp_file` normalizes to canonical lower-case keys (`serr`, `terr`).
- Error-semantic contract:
  - `_interpret_err_lines` derives `_err` for `serr` entries and `_perr`/`_nerr` for `terr` entries.
  - the derived names and count must match canonical uppercase path for functionally equivalent input.
- Numeric/token contract:
  - value coercion uses numeric parsing rules that are not coupled to command casing.
  - `NO` remains a masked sentinel after normalization of parser state.

## Dependency Direction Notes
- `_line_type` consumes no parser-local state and emits type tokens to `_get_type_from_list_of_lines`.
- `_get_type_from_list_of_lines` depends on `_line_type` and passes `ncol` to downstream stages.
- `_get_tables_from_qdp_file` depends on both `_get_type_from_list_of_lines` and `_interpret_err_lines`.
- `_interpret_err_lines` is downstream-only from command capture and feeds `Table` construction.
- `_read_table_qdp` is a top-level entry that depends on `_get_tables_from_qdp_file` only; no other parser contract direction is inverted.

## Integration-Seam Skeletons
- Integration seam 1: command-classification seam in `_line_type`.
  - owner: `astropy/io/ascii/qdp.py`
  - contract: regex and command-token route must accept mixed/lowercase `READ SERR` and `READ TERR` as valid command classes.
- Integration seam 2: command-dispatch seam in `_get_tables_from_qdp_file`.
  - owner: `astropy/io/ascii/qdp.py`
  - contract: `serr`/`terr` detection and index capture must canonicalize tokens so mixed-case input yields a canonical `err_specs` map.
- Integration seam 3: column-shape seam in `_interpret_err_lines`.
  - owner: `astropy/io/ascii/qdp.py`
  - contract: output columns and names for a given `err_specs` map are invariant across command case variants.

## Scenario-to-Placement Traceability
- Scenario 1 (`read serr 1 2`) maps to:
  - `_line_type` for command detection,
  - `_get_tables_from_qdp_file` for table-state capture and `err_specs`,
  - `_interpret_err_lines` for resulting column expansion.
- Scenario 2 (`READ SERR 1 2` vs `ReAd SeRr 1 2`) maps to:
  - `_line_type` (case-insensitive command classification),
  - `_get_tables_from_qdp_file` (`command_key = lower()` canonicalization before `err_specs`),
  - `_read_table_qdp` (single output contract for parsed table identity/shape).

## Completion Gate Status
- All traced obligations in `ISSUE13-002` now have concrete architectural homes.
- Traceability exists through parser + test entry points.
- One architecture artifact has been created: `astropy/io/ascii/qdp_issue13_002_architecture.md`.
