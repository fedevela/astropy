# AST12907-002 Architecture Artifact

## Requirement to Architecture Map

- **AST12907-002.S1**
  - Requirement: For `m.Pix2Sky_TAN() & (m.Linear1D(10) & m.Linear1D(5))`, matrix positions `(2, 3)` and `(3, 2)` must remain `False`.
  - Structural home:
    - `astropy/modeling/separable.py::_flatten_ampersand_chain`
    - `astropy/modeling/separable.py::_separable` (`transform.op == '&'` branch)
    - `astropy/modeling/separable.py::_cstack`
    - `astropy/modeling/tests/test_separable.py` (test binding: `test_AST12907_002_nested_pix2sky_tan_nested_linear1d_block_false_coupling_positions`)
- **AST12907-002.S2**
  - Requirement: `m.Pix2Sky_TAN() & (m.Linear1D(10) & m.Linear1D(5))` and `m.Pix2Sky_TAN() & m.Linear1D(10) & m.Linear1D(5)` must produce identical matrices with an independent Linear block.
  - Structural home:
    - `astropy/modeling/separable.py::_flatten_ampersand_chain`
    - `astropy/modeling/separable.py::_separable`
    - `astropy/modeling/separable.py::_cstack`
    - `astropy/modeling/tests/test_separable.py` (test binding: `test_AST12907_002_nested_pix2sky_tan_and_flattened_pair_equivalent_blocked_matrix`)

## File and Module Placement

- **`astropy/modeling/separable.py`** owns matrix-shape/structure computation for compound models.
  - `'_flatten_ampersand_chain'` owns flattening normalization for nested `&` composition.
  - `'_separable'` owns traversal and dispatch for all compound operators.
  - `'_cstack'` owns coordinate-block stacking semantics and output/input boundary assignment.
- **`astropy/modeling/tests/test_separable.py`** owns executable traceability for acceptance scenarios.
- Cross-module ownership boundary:
  - `core.py` and `mappings.py` types are consumed by `separable.py`, but coupling rules are not defined there.

## Interface / Contract Boundaries

- `separable.py` public boundary:
  - `is_separable(transform: Model) -> np.ndarray[bool]`
  - `separability_matrix(transform: Model) -> np.ndarray[bool]`
  - These functions consume full transform graphs and return dependency matrices, so any nested flattening behavior must preserve these contracts.
- Internal boundary contracts for this issue:
  - `_flatten_ampersand_chain(transform)` returns a left-to-right iterable of operands with no semantic side effects.
  - `_cstack(left, right)` owns row/column partition contract for concatenated output blocks; it must not create cross-block coupling between operand groups.
  - `_separable(transform)` owns operator dispatch contract and must reduce nested `&` chains through deterministic normalization before block composition.

## Dependency Direction

- Dependency direction is intentionally one-way:
  - `separable.py` depends on `core.py`/`mappings.py` model metadata.
  - `tests/test_separable.py` depends on `separable.py` APIs and helper internals.
  - No dependency inversion is introduced for this issue; flatten semantics stay in `separable.py`.

## Integration Seams (Skeleton)

- **Seam S1: Flatten-Separable Contract**
  - Location: `_separable(transform.op == '&')` -> `_flatten_ampersand_chain`.
  - Responsibility: convert nested `&` AST structures into ordered linear operands before folding.
- **Seam S2: Block Composition Contract**
  - Location: `_cstack`.
  - Responsibility: preserve output/input block independence when composing neighbor blocks.
- **Seam S3: Regression Binding**
  - Location: `test_AST12907_002_*` and `AST12907_002_VERIFICATION`.
  - Responsibility: keep issue scenarios bound to explicit matrix positions and flatten-equivalence validation.

## Topology / Boundary Integrity Notes

- Do not move coupling policy into model classes; keep it centralized in `separable.py`.
- Do not add new public symbols for this issue. The structural change is localized to traversal and composition internals plus traceability artifacts.
- For AST12907-002, the only required boundary extension is normalization-before-folding for `&` chains; the flattened and nested forms must share one deterministic composition path.

## Completion Readiness

- All AST12907-002 obligations are assigned to concrete code/test loci.
- Traceability is preserved via requirement IDs on both implementation and test artifacts.
- At least one architecture artifact has been created and updated for this phase.
