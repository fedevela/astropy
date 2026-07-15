# MASKHANDLE-001 to MASKHANDLE-005 Architecture Artifact

## Scope
Issue family: keep `NDArithmeticMixin` behavior stable for
`handle_mask=np.bitwise_or` in all non-mixed-mask branches while isolating the
mixed-mask-vs-mask correction to its owning seam.

## Requirement-to-architecture mapping

- `MASKHANDLE-001`
  - `astropy/nddata/mixins/ndarithmetic.py`
    - `_arithmetic` mixed-mask call boundary and branch dispatch.
  - `astropy/nddata/mixins/tests/test_ndarithmetic.py`
    - `MASKHANDLE_001...` regression artifact.
- `MASKHANDLE-002`
  - `astropy/nddata/mixins/ndarithmetic.py`
    - `_arithmetic_mask` non-none identity guard.
  - `astropy/nddata/mixins/tests/test_ndarithmetic.py`
    - `MASKHANDLE_002...` regression artifact.
- `MASKHANDLE-003`
  - `astropy/nddata/mixins/ndarithmetic.py`
    - `_arithmetic` and `_arithmetic_mask` both-unmasked transition.
  - `astropy/nddata/mixins/tests/test_ndarithmetic.py`
    - `MASKHANDLE_003...` regression artifact.
- `MASKHANDLE-004`
  - `astropy/nddata/mixins/ndarithmetic.py`
    - `_arithmetic_mask` both-masked transition.
  - `astropy/nddata/mixins/tests/test_ndarithmetic.py`
    - `MASKHANDLE_004...` regression artifact.
- `MASKHANDLE-005`
  - `astropy/nddata/mixins/ndarithmetic.py`
    - `_arithmetic` call-site boundary around mixed-mask policy.
    - `_arithmetic_data`, `_arithmetic_uncertainty`, `_arithmetic_wcs`,
      `_arithmetic_meta` as unchanged-seams.
  - `astropy/nddata/mixins/tests/test_ndarithmetic.py`
    - `MASKHANDLE_005...` regression artifact.

## Ownership and boundary decisions

- `NDArithmeticMixin._arithmetic` owns **mask propagation policy orchestration**:
  - Chooses handling mode (`None`, `ff`, callable).
  - Owns boundaries into `kwargs` assembly (data/uncertainty/WCS/meta assembly
    already delegated).
  - Policy adjustment for this issue is limited to the mixed-mask branch.
- `NDArithmeticMixin._arithmetic_mask` owns **mask composition contract**:
  - Input boundary: `self.mask`, `operand.mask`, `handle_mask`, `kwds`.
  - Output boundary: `None`, deep-copied mask, or composed mask.
  - Non-mixed branches remain contract-fixed.

## Interfaces / contracts

- Contract A: mixed-mask identity
  - Inputs: `handle_mask` callable, exactly one operand mask present.
  - Output: existing present mask copy.
  - Pressure: `MASKHANDLE-002`, `MASKHANDLE-005`.
- Contract B: no-mask output
  - Inputs: both masks absent or `handle_mask is None`.
  - Output: `None`.
  - Pressure: `MASKHANDLE-003`.
- Contract C: dual-mask output
  - Inputs: both masks present.
  - Output: `handle_mask(self.mask, operand.mask, **kwds)`.
  - Pressure: `MASKHANDLE-004`.

## Dependency direction

- `_arithmetic` → `_arithmetic_mask` (strict one-way).
  - `_arithmetic_mask` must remain a pure boundary function for mask-state decisions.
- `_arithmetic` → `_arithmetic_data` / `_arithmetic_uncertainty` / `_arithmetic_wcs` /
  `_arithmetic_meta` (one-way).
  - These are intentionally untouched by `MASKHANDLE-003`/`004`/`005`.
- `test_ndarithmetic` → `ndarithmetic` (test-to-implementation traceability).

## Integration-seam skeleton

- `handle_mask_callable` seam in `_arithmetic`
  - Primary point where mixed-mask policy can be altered.
- `_arithmetic_mask` seam
  - Central policy point for mask state transitions: both-none, exactly-one, both-present.
- Non-mixed preservation seam
  - Marker seam across `_arithmetic_data`, `_arithmetic_uncertainty`,
    `_arithmetic_wcs`, `_arithmetic_meta` to ensure no behavior drift.

## Completion status

- Requirement homes are assigned to owning files and boundaries.
- Architecture now records the precise mixed-mask mutation boundary and explicitly
  seals non-mixed behavior paths.
- Traceability is preserved through canonical map entries and placeholder test
  artifacts.
