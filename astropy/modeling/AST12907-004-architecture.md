# AST12907-004 Architecture Artifact

Issue: `AST12907-004`  
Goal: preserve existing non-nested separability behavior while allowing the nested `&` fix to apply only to the targeted regression cases.

## Requirement-to-architecture map

| Requirement obligation | Ownership / locus | Structural pressure | Required structure |
|---|---|---|---|
| `AST12907-004` Scenario 1: preserve legacy non-nested behavior for `test_coord_matrix` | `astropy/modeling/separable.py` (`_coord_matrix`, `is_separable`, `separability_matrix`) + `astropy/modeling/tests/test_separable.py` (`test_coord_matrix`) | Guard for single-model matrix layout and one-to-many short-circuit semantics | Keep legacy entry points and matrix-shape/placement contracts untouched in existing helper/API flow |
| `AST12907-004` Scenario 1: preserve legacy non-nested behavior for `test_cdot` | `astropy/modeling/separable.py` (`_cdot`) + `astropy/modeling/tests/test_separable.py` (`test_cdot`) | Guard for composition operator preconditions and matrix shape behavior | Keep `_cdot` arity/shape conversion and exception behavior stable |
| `AST12907-004` Scenario 1: preserve legacy non-nested behavior for `test_cstack` | `astropy/modeling/separable.py` (`_cstack`, `_to_coord_operand`) + `astropy/modeling/tests/test_separable.py` (`test_cstack`) | Guard against cross-block coupling and ordering drift | Keep block append and input-column partition responsibilities inside `_cstack` boundary |
| `AST12907-004` Scenario 1: preserve legacy non-nested behavior for `test_arith_oper` | `astropy/modeling/separable.py` (`_arith_oper`) + `astropy/modeling/tests/test_separable.py` (`test_arith_oper`) | Guard for error path and non-separable output shape | Keep the compatibility path that derives arity and raises `ModelDefinitionError` unchanged |
| `AST12907-004` Scenario 1: preserve legacy non-nested behavior for `test_custom_model_separable` | `astropy/modeling/separable.py` (`_coord_matrix`) + `astropy/modeling/tests/test_separable.py` (`test_custom_model_separable`) | Guard for `Model.separable` as source of truth | Keep attribute-based branching for custom model contracts |
| `AST12907-004` Scenario 1: preserve legacy behavior for `compound_model0` through `compound_model5`, `7`, `8` | `astropy/modeling/separable.py` (`_separable`, `_operators`) + `astropy/modeling/tests/test_separable.py` (`test_separable`) | Guard for non-nested and previously passing compound-case matrices | Route all non-nested compound traversal through existing operator dispatch without behavioral drift |
| `AST12907-004` Scenario 1: preserve legacy behavior excluding `compound_model6` and `compound_model9` exceptions | `astropy/modeling/separable.py` (`_separable`, `_flatten_ampersand_chain`) + `astropy/modeling/tests/test_separable.py` (`AST12907_004_VERIFICATION`) | Scope containment of nested-chain change | Keep nested-chain normalization scoped to `_separable` `&` branch and preserve historical matrix outputs for all non-exception fixtures |

## Placement and ownership

- `astropy/modeling/separable.py` remains the implementation home for all separability contracts.
- `is_separable(transform)` remains the public entry point for output separability vectors.
- `separability_matrix(transform)` remains the public entry point for boolean dependency matrices.
- `_separable(transform)` remains the traversal root for all compound composition structure.
- `_coord_matrix(model, pos, noutp)` remains the leaf matrix contract for both Mapping and `Model.separable` branches.
- `_cdot`, `_cstack`, `_arith_oper` remain operator-level composition boundaries.
- `_operators` remains the single operator-dispatch seam.
- `astropy/modeling/tests/test_separable.py` remains the traceability shell via `AST12907_004_VERIFICATION`.

## Contract and boundary posture

- Public boundary:
  - Inputs are full `Model` graphs; outputs preserve existing ndarray dtypes and shapes.
  - `is_separable` and `separability_matrix` must remain source-compatible with existing callers.
- Internal boundary contracts:
  - `_coord_matrix`: Mapping branch, `model.separable == False`, and `model.separable == True` branches remain deterministic and non-cross-coupling.
  - `_cdot`: left/right conversion and failure path for mismatched matrix dimensions stays unchanged.
  - `_cstack`: block-concatenation for `&` remains responsible for row/column partition only.
  - `_arith_oper`: compatibility check + all-ones matrix return stays the default non-nested operator contract.
  - `_separable`: explicit non-`&` operator path remains unchanged so legacy compound cases regress only where explicitly scoped exceptions apply.

## Dependency direction

1. Public API functions depend on `_separable`.
2. `_separable` depends on `_flatten_ampersand_chain` and `_operators`.
3. `_operators` dispatches into `_coord_matrix`, `_cdot`, `_cstack`, `_arith_oper`.
4. `_coord_matrix` depends only on `Model`, `Mapping`, and scalar indexing contracts.
5. Tests depend on public and helper symbols only; there is no reverse dependency into tests.

## Integration seam skeletons

- **Seam S1**: `is_separable` / `separability_matrix` one-to-many short-circuit branch.
- **Seam S2**: `_separable` compound branch for `transform.op == '&'` and `_flatten_ampersand_chain`.
- **Seam S3**: `_operators` lookup for operator-specific matrix combination.
- **Seam S4**: `AST12907_004_VERIFICATION` to acceptance test names, including explicit non-inclusion of `compound_model6-result6` and `compound_model9-result9`.

## Completion status

- All traced AST12907-004 obligations have architectural homes in implementation and test artifacts.
- Requirement IDs are preserved in the traceability map in `test_separable.py`.
- One concrete architecture artifact created: `AST12907-004-architecture.md`.
