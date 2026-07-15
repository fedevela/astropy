# AST12907-005 Architecture Artifact

Issue: `AST12907-005`  
Goal: keep separability matrix shape/type/order contracts stable for compound model inputs, including nested `&` trees.

## Requirement-to-architecture map

| Requirement obligation | Ownership / locus | Structural pressure | Required structure |
|---|---|---|---|
| `AST12907-005` Scenario 1: nested compound returns a 2D boolean matrix | `astropy/modeling/separable.py` (`separability_matrix`) + `astropy/modeling/tests/test_separable.py` (`test_AST12907_005_nested_compound_matrix_is_2d_boolean`) + `AST12907_005_VERIFICATION` | Boolean and rank contract at API boundary | Keep `separability_matrix` as the single public normalization boundary (`np.where(... != 0, True, False)`), so all upstream matrix shapes are rendered as 2D booleans before crossing module boundary |
| `AST12907-005` Scenario 2: matrix shape is exactly `(n_outputs, n_inputs)` | `astropy/modeling/separable.py` (`separability_matrix`, `_coord_matrix`, `_to_coord_operand`, `_cstack`, `_cdot`, `_arith_oper`) + `astropy/modeling/tests/test_separable.py` (`test_AST12907_005_nested_compound_matrix_shape_matches_output_input_counts`) + `AST12907_005_VERIFICATION` | Exact dimensional preservation under nested composition | Preserve fixed row/column ownership by operator boundaries (`_coord_matrix` and `_to_coord_operand`) and ensure all composition helpers (`_cdot`, `_cstack`, `_arith_oper`) remain row-major output/input emitters |
| `AST12907-005` Scenario 3: nested/flattened ordering is index-stable | `astropy/modeling/separable.py` (`_flatten_ampersand_chain`, `_separable`, `_to_coord_operand`, `_cstack`, `separability_matrix`) + `astropy/modeling/tests/test_separable.py` (`test_AST12907_005_nested_vs_flattened_ordering_stable_by_output_input_indices`) + `AST12907_005_VERIFICATION` | Deterministic row/column index semantics across equivalent representations | Keep canonical left-to-right traversal in `_flatten_ampersand_chain` and fold sequence in `_separable` so flattened and nested trees converge to one ordered operator trace |

## Placement and ownership

- **`astropy/modeling/separable.py`** remains the implementation home for separability contract shape/type ordering decisions.
  - `is_separable` and `separability_matrix` are the public contract boundaries.
  - `_separable` owns traversal and normalized composition shape flow across operator nodes.
  - `_flatten_ampersand_chain` owns nested `&` ordering normalization.
  - `_coord_matrix`, `_to_coord_operand`, `_cstack`, `_cdot`, `_arith_oper` remain local operator/leaf composition boundaries.
  - `_operators` remains the dispatch seam for all operator math.
- **`astropy/modeling/tests/test_separable.py`** remains the issue binding surface through placeholder tests and `AST12907_005_VERIFICATION`.

## Contract and boundary posture

- Public boundary remains unchanged:
  - Inputs: any `Model` graph (including `CompoundModel`), including nested `&` trees.
  - Outputs:
    - `separability_matrix(transform)` returns a 2D `bool` ndarray with row semantics mapped to outputs and column semantics mapped to inputs.
    - `is_separable(transform)` remains row reduction of `separability_matrix` behavior.
- Internal contract boundaries:
  - `_flatten_ampersand_chain`: returns deterministic ordered operands for `&` chains (left operand first then right).
  - `_coord_matrix` and `_to_coord_operand`: preserve canonical block placement for local and nested composition operands.
  - `_cstack`: enforces disjoint column partition and output-row partition for `&`.
  - `_cdot`: enforces composition preconditions and dot semantics while preserving error boundaries.
  - `_separable`: chooses traversal strategy, keeping nested `&` normalization local and preserving non-`&` branch behavior.

## Dependency direction

1. `is_separable` and `separability_matrix` depend on `_separable` to compute matrix semantics.
2. `_separable` depends on `_flatten_ampersand_chain` for nested `&` normalization and `_operators` for operator-specific matrix folding.
3. `_operators` dispatches to:
   - `_coord_matrix` / `_to_coord_operand` for leaf/operand normalization.
   - `_cstack` for `&` structure.
   - `_cdot` for `|`.
   - `_arith_oper` for arithmetic fallbacks.
4. Tests consume public helpers and `AST12907_005_VERIFICATION`; they do not participate in implementation control flow.

## Integration seam skeletons

- **Seam S1**: `separability_matrix` normalization seam for bool shape/type guarantees before contract exposure.
- **Seam S2**: `_separable` `transform.op == '&'` branch uses `_flatten_ampersand_chain` and folds left-to-right using `_operators['&']`.
- **Seam S3**: `_cstack` seam composes disjoint coordinate blocks with explicit left/right normalization.
- **Seam S4**: `AST12907_005_VERIFICATION` map in `test_separable.py` links three acceptance scenarios to future runtime assertions.

## Completion status

- All traced AST12907-005 obligations have architectural homes in implementation and test artifacts.
- Requirement traceability is preserved by existing verification mapping and explicit file-level mapping in this artifact.
- A concrete architecture artifact was created: `AST12907-005-architecture.md`.
