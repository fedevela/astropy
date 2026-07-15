# AST12907-003 Architecture Artifact

## Requirement-to-architecture map

| Requirement obligation | Ownership / locus | Structural pressure | Required structure |
|---|---|---|---|
| `AST12907-003` Scenario 1: baseline stability for `test_separable[compound_model6-result6]` | `astropy/modeling/separable.py` (`_flatten_ampersand_chain`, `_separable` `&` branch) + `astropy/modeling/tests/test_separable.py` (`test_AST12907_003_compound_model6_result6_nested_compound_case_remains_stable_after_flattening_fix`) | Regression risk from nested `&` traversal order changing behavior | Keep flattening behavior as traversal normalization, not semantic rewrite, inside existing traversal seam |
| `AST12907-003` Scenario 2: baseline stability for `test_separable[compound_model9-result9]` | `astropy/modeling/separable.py` (`_flatten_ampersand_chain`, `_separable` `&` branch, `_operators`) + `astropy/modeling/tests/test_separable.py` (`test_AST12907_003_compound_model9_result9_nested_compound_case_remains_stable_after_flattening_fix`) | Regression risk from stacked composition introducing coupling | Ensure nested and flat `&` forms share the same `_operators['&']` composition path |

## Placement and ownership

- **`astropy/modeling/separable.py`** owns all separability-semantics computation.
  - `_flatten_ampersand_chain` owns ordered flattening policy for consecutive `&` operands.
  - `_separable` owns operator traversal and combines nested `&` through deterministic recursion.
  - `_cstack` owns row/column block composition and has no direct dependency on compound-tree shape beyond normalized operands.
- **`astropy/modeling/tests/test_separable.py`** owns executable issue binding through `AST12907_003_VERIFICATION`.
  - No new behavioral assertions are required in this phase; placeholders preserve mapping and scenario labels.

## Contract / boundary posture

- Public boundary remains unchanged:
  - `is_separable(transform)` and `separability_matrix(transform)` continue to accept full models and return matrices as before.
- Internal seams for AST12907-003:
  - `_flatten_ampersand_chain(transform) -> list[Model|ndarray]` (ordered, side-effect free traversal contract).
  - `_separable(transform)` branch for `transform.op == '&'` (delegates nested chains to flattening before folding with `_operators['&']`).
  - `_operators['&']` as the single structural composition entry point.

## Dependency direction

1. Public APIs (`is_separable`, `separability_matrix`) depend on `_separable`.
2. `_separable` depends on `_flatten_ampersand_chain` and `_operators`.
3. `_operators['&']` depends on `_cstack`/`_coord_matrix`.
4. `test` module depends on public and helper names only, not vice versa.

This keeps the change one-way and localized to internal traversal composition logic.

## Integration seams

- **Seam S1**: `_separable` (`&` branch) → `_flatten_ampersand_chain` for nested chain normalization.
- **Seam S2**: `_operators['&']` → `_cstack` for deterministic matrix concatenation with ordered blocks.
- **Seam S3**: `AST12907_003_VERIFICATION` binding in `test_separable.py` for traceability.

## Completion status

- Both obligations have architectural homes.
- Requirement references are present across implementation and test artifacts.
- One concrete architecture artifact is created: `AST12907-003-architecture.md`.
