# ISSUE13-004 Architecture Artifact

## Requirement-to-Architecture Map
- ISSUE13-004 -> `astropy/io/ascii/qdp.py::_line_type` (command classification boundary for uppercase command tokens while preserving downstream data semantics).
- ISSUE13-004 -> `astropy/io/ascii/qdp.py::_get_type_from_list_of_lines` (table-shape/type inference boundary under uppercase command input).
- ISSUE13-004 -> `astropy/io/ascii/qdp.py::_interpret_err_lines` (ordered error-column naming/ordering contract tied to parsed indices).
- ISSUE13-004 -> `astropy/io/ascii/qdp.py::_get_tables_from_qdp_file` (FSM/table-boundary and token parsing order for comments/whitespace-preserving behavior).
- ISSUE13-004 -> `astropy/io/ascii/qdp.py::_get_lines_from_file` (input-source acquisition boundary; no behavior change to whitespace/comment treatment).
- ISSUE13-004 -> `astropy/io/ascii/qdp.py::_read_table_qdp` (table selection and return-shape contract).
- ISSUE13-004 -> `astropy/io/ascii/tests/test_qdp.py:REQUIREMENT_VERIFICATION_MAP` (traceability surface).

## File and Module Placement
- `astropy/io/ascii/qdp.py` remains the single ownership module for parser-semantics preservation across case-normalized command intake.
- `astropy/io/ascii/tests/test_qdp.py` remains the ownership surface for scenario-level traceability to test placeholders already added.
- No new modules are required because the concern is localized to existing parser seams and regression linkage.

## Ownership Boundaries
- `_line_type` owns command-token recognition and determines whether command lines are parsed as command, data, or comments.
- `_get_type_from_list_of_lines` owns table typing and table boundary handling derived from command/data line sequence.
- `_interpret_err_lines` owns conversion from normalized `serr/terr` index specs into explicit error-column names and ordering.
- `_get_tables_from_qdp_file` owns state transitions among comment, command, data, and `new`-table boundaries, including token-to-row accumulation behavior.
- `_get_lines_from_file` owns accepted input forms (`str` file path, inline string, iterable) and raw line iteration boundaries.
- `_read_table_qdp` owns table-id selection and final API boundary into caller space.

## Interface / Contract Artifacts
- Command parsing contract:
  - `READ` command classification remains case-insensitive only for supported tokens/branches.
  - Unrecognized lines must remain on existing failure semantics (`ValueError("Unrecognized QDP line: ...")`) without introducing new rewrite paths.
- Data typing and order contract:
  - `_get_type_from_list_of_lines` preserves row-wise numeric parsing precedence and resulting dtypes for equivalent inputs.
  - `_interpret_err_lines` must emit named error columns in existing order derived from parsed indices, with no reordering by parser case normalization.
- Non-command tokenization contract:
  - `_get_tables_from_qdp_file` retains current row token handling (including `NO`, int/float precedence) and does not alter behavior based on command token case.
- Whitespace and comment contract:
  - Neither `_get_lines_from_file` nor `_get_tables_from_qdp_file` may add new trimming/canonicalization that changes comment/blank handling, comment capture, or whitespace splitting behavior for existing valid uppercase fixtures.
- Read contract:
  - `_read_table_qdp` keeps exact indexing semantics (`table_id`) and returns the selected table without table-order mutation.

## Dependency Direction Notes
- `_line_type` → `_get_type_from_list_of_lines` → `_get_tables_from_qdp_file` → `_interpret_err_lines`.
- `_get_lines_from_file` → `_get_tables_from_qdp_file` → `_read_table_qdp`.
- `_read_table_qdp` is the top-level parser consumer and must not feed state back into upstream line-classification components.

## Integration-Seam Skeletons
- Integration seam 1: command-classification seam in `_line_type` (`astropy/io/ascii/qdp.py`).
  - Contract: keep uppercase command acceptance aligned to canonical command set while preserving all non-command and malformed-line branches.
- Integration seam 2: source-ingestion seam in `_get_lines_from_file` (`astropy/io/ascii/qdp.py`).
  - Contract: retain source-typing branches and no new whitespace/comment transformations.
- Integration seam 3: stream-state seam in `_get_tables_from_qdp_file` (`astropy/io/ascii/qdp.py`).
  - Contract: preserve comment, command, data, and `new`-table transitions and preserve token parsing order and masking behavior.
- Integration seam 4: table-contract seam in `_read_table_qdp` (`astropy/io/ascii/qdp.py`).
  - Contract: preserve output-table shape, column order, column dtypes, and value sets for equivalent inputs across case variants.

## Scenario-to-Placement Traceability
- Scenario 1 (uppercase table + shape/type/order/value parity) maps to:
  - `_line_type` -> `_get_type_from_list_of_lines` -> `_get_tables_from_qdp_file` -> `_interpret_err_lines` -> `_read_table_qdp`.
  - Data-flow must remain deterministic with preserved row count, inferred dtypes, column order, and parsed values.
- Scenario 2 (comments and mixed whitespace parity) maps to:
  - `_get_lines_from_file` -> `_get_tables_from_qdp_file`.
  - Parser boundary must keep comment token capture, whitespace splitting, and invalid-line behavior unchanged from baseline.

## Completion Gate Status
- All ISSUE13-004 logic obligations are assigned to concrete parser ownership boundaries and integration seams.
- Changes remain traceable through `ISSUE13-004` requirement hooks in `test_qdp.py`.
- New architecture artifact created: `astropy/io/ascii/qdp_issue13_004_architecture.md`.
- Structural readiness is preserved: ownership, boundary, dependency direction, and scenario traceability are now explicit.
