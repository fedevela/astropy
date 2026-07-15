# ISSUE13-003 Architecture Artifact

## Requirement-to-Architecture Map
- ISSUE13-003 -> `astropy/io/ascii/qdp.py::_line_type` (command validation boundary).
- ISSUE13-003 -> `astropy/io/ascii/qdp.py::_get_tables_from_qdp_file` (dispatch boundary for parsed command keys).
- ISSUE13-003 -> `astropy/io/ascii/qdp.py::_read_table_qdp` (read entry preserves upstream validation failures).
- ISSUE13-003 -> `astropy/io/ascii/tests/test_qdp.py:REQUIREMENT_VERIFICATION_MAP` (traceability surface).

## File and Module Placement
- `astropy/io/ascii/qdp.py` remains the single ownership module for invalid-command protection after normalization.
- `astropy/io/ascii/tests/test_qdp.py` remains the ownership surface for scenario-level acceptance traceability.
- No new module is needed; both obligations are local to existing parser seams and regression-test hooks already in place.

## Ownership Boundaries
- `_line_type` owns all command-line lexical classification and is responsible for preserving the existing invalid-command failure path.
- `_get_tables_from_qdp_file` owns command-line capture and conversion into `command_key`/`err_specs` state, with acceptance constrained to canonical keys.
- `_read_table_qdp` remains the upstream caller boundary that relays parser failures (e.g., `Unrecognized QDP line`) unchanged.
- `Table.read(..., format="ascii.qdp")` remains outside parser internals and must treat all non-localized validation errors as terminal.

## Interface / Contract Artifacts
- Command-classification contract:
  - `_line_type` uses the command regex with case-insensitive matching for supported verbs.
  - Any line that does not conform exactly to supported command grammar (`READ [TS]ERR <indices...>`) must follow the existing `ValueError("Unrecognized QDP line: ...")` path.
  - Unknown verbs (for example, `READD`) and misspelled command sub-keys must not be normalized into a supported handler path.
- Command-dispatch contract:
  - `_get_tables_from_qdp_file` lowercases parsed sub-keys for canonical comparison only after command lines are accepted by `_line_type`.
  - Only `("serr", "terr")` are permitted to populate `err_specs`; all other keys must remain no-op for dispatch.
- Error-propagation contract:
  - Failures remain on the existing invalid-command line, not rerouted into `serr`/`terr` semantics or alternative handlers.

## Dependency Direction Notes
- `_line_type` → `_get_type_from_list_of_lines` → `_get_tables_from_qdp_file` → `_interpret_err_lines`.
- `_read_table_qdp` depends on `_get_tables_from_qdp_file` only; parse-rejection semantics flow one-way from `qdp.py` to caller.
- No reverse dependency from `err_specs` back into line-type recognition; parsing controls are directional and remain local to `_line_type`.

## Integration-Seam Skeletons
- Integration seam 1: command-classification seam in `_line_type`.
  - owner: `astropy/io/ascii/qdp.py`
  - contract: strict command-token grammar and unchanged invalid-command error emission.
- Integration seam 2: command-dispatch seam in `_get_tables_from_qdp_file`.
  - owner: `astropy/io/ascii/qdp.py`
  - contract: permissive lowercasing only for key comparison, hard allow-list of `serr` and `terr`.
- Integration seam 3: parser-call boundary in `_read_table_qdp`.
  - owner: `astropy/io/ascii/qdp.py`
  - contract: propagate `ValueError` from parser path without fallback/coercion for unknown commands.

## Scenario-to-Placement Traceability
- Scenario 1 (`READD SERR 1 2 ...`) maps to:
  - `_line_type` strict command grammar validation,
  - direct `ValueError("Unrecognized QDP line: ...")` failure path,
  - no transition into `_get_tables_from_qdp_file` dispatch.
- Scenario 2 (valid command verb with misspelled sub-key) maps to:
  - `_line_type` rejection in strict grammar check, or if any command token reaches downstream,
  - `_get_tables_from_qdp_file` allow-list gate (`"serr"|"terr"` only),
  - no execution of any valid handler.

## Completion Gate Status
- All logic obligations for `ISSUE13-003` are assigned to specific modules, functions, and integration seams.
- The mapping remains requirement-traceable via existing test entries plus this architecture artifact.
- One architecture artifact was created: `astropy/io/ascii/qdp_issue13_003_architecture.md`.
- Parser topology and dependency direction stay intentionally unchanged for runtime behavior.
