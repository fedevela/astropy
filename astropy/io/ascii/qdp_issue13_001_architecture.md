# ISSUE13-001 Architecture Artifact

## Requirement-to-Architecture Map
- ISSUE13-001 -> `astropy/io/ascii/qdp.py::_line_type` (command line classification boundary).
- ISSUE13-001 -> `astropy/io/ascii/qdp.py::_get_tables_from_qdp_file` (command dispatch-to-state boundary).
- ISSUE13-001 -> `astropy/io/ascii/tests/test_qdp.py:REQUIREMENT_VERIFICATION_MAP` (traceability boundary).

## File and Module Placement
- `astropy/io/ascii/qdp.py` owns parser ownership for QDP command token intake and dispatch routing.
- `astropy/io/ascii/tests/test_qdp.py` owns requirement linkage and scenario-level verification entry points.
- No new module is required for this obligation because behavior remains within the existing parser module seams.

## Ownership Boundaries
- ` _line_type` owns lexical classification only: raw line normalization and route classification.
- `_get_type_from_list_of_lines` owns sequence typing orchestration.
- `_get_tables_from_qdp_file` owns command block interpretation and transfer into `err_specs`.
- `_interpret_err_lines` remains the downstream owner of column-name expansion based on `err_specs`.

## Interface / Contract Artifacts
- `Issue13-001` introduces an explicit command token normalization contract:
  - command verb matching in `line_type` must be case-insensitive for supported verbs.
  - command sub-key matching in dispatch must be case-insensitive for supported keys (`serr`, `terr`) before storing into `err_specs`.
- Existing `err_specs` contract remains stable:
  - accepted keys: `serr` (symmetric) and `terr` (two-sided).
  - unknown or unsupported sub-keys keep the existing behavior (no new acceptance/rejection path in this issue).

## Dependency Direction Notes
- `_line_type` depends on regex compilation helpers and returns `{"comment","command","new","data,n"}` only.
- `_get_tables_from_qdp_file` depends on `_get_type_from_list_of_lines` and later consumes `_interpret_err_lines`.
- Dispatch decisions in `_get_tables_from_qdp_file` are the only incoming source for `err_specs`.
- `_interpret_err_lines` remains downstream and does not influence parser classification.

## Integration-Seam Stubs
- Integration seam 1: command classification seam in `_line_type`.
  - owner: `astropy/io/ascii/qdp.py`
  - contract: classify command tokens independent of text case.
- Integration seam 2: command-dispatch seam in `_get_tables_from_qdp_file`.
  - owner: `astropy/io/ascii/qdp.py`
  - contract: map command sub-key token to canonical keys (`serr`, `terr`) before `err_specs` population.

## Scenario-to-Placement Traceability
- Scenario 1 (`ReAd SeRr 1 2`) maps to:
  - `_line_type` command recognition branch,
  - `_get_tables_from_qdp_file` command-block accumulation and `err_specs` population.
- Scenario 2 (mixed-case recognized sub-key in a valid shape) maps to:
  - `_line_type` command route guard,
  - `_get_tables_from_qdp_file` sub-key normalization and downstream `err_specs` handoff.

## Completion Gate Status
- All traced obligations in `ISSUE13-001` have concrete architectural homes.
- Existing parser and test files provide direct requirement links.
- One architecture artifact has been added: `astropy/io/ascii/qdp_issue13_001_architecture.md`.
