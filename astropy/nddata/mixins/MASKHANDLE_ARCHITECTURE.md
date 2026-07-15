# MASKHANDLE-001 / MASKHANDLE-002 Architecture Artifact

## Scope
Issue: preserve non-`None` mask behavior for mixed-mask arithmetic when
`handle_mask=np.bitwise_or`.

## Requirement-to-architecture mapping

- `MASKHANDLE-001`
  - `[MASKHANDLE-001]` `astropy/nddata/mixins/ndarithmetic.py`:
    - `_arithmetic` mixed-mask branch that delegates mask composition.
    - `_arithmetic_mask` mixed-mask return policy.
- `MASKHANDLE-002`
  - `[MASKHANDLE-002]` `astropy/nddata/mixins/ndarithmetic.py`:
    - `_arithmetic_mask` no-`None` identity contract for callable paths.
  - `[MASKHANDLE-002]` `astropy/nddata/mixins/tests/test_ndarithmetic.py` placeholder contract tests.

## Ownership and boundary decisions

- `NDArithmeticMixin._arithmetic` owns **mask orchestration**:
  - Resolves handle strategy (`None`, `ff`, callable).
  - Delegates callable mask semantics to `_arithmetic_mask`.
  - Owns the boundary between "mask requested" and "mask emitted in kwargs".
- `NDArithmeticMixin._arithmetic_mask` owns **mask composition contract**:
  - Input boundary: `self.mask`, `operand.mask`, and `handle_mask`.
  - Output boundary: `None`, copied mask, or composed mask.

## Interfaces / contracts

- Contract A: mixed-mask identity (requirement-driven)
  - Inputs: `handle_mask` callable with one present/one missing mask.
  - Output: return deep copy of present mask.
  - Invariant: no call to `handle_mask` where either mask arg is `None`.
- Contract B: dual-mask branch
  - Inputs: both masks present.
  - Output: `handle_mask(self.mask, operand.mask, **kwds)`.
- Contract C: no-mask branch
  - Inputs: both masks absent or `handle_mask is None`.
  - Output: `None`.

## Dependency direction

- `_arithmetic` → `_arithmetic_mask` (one-way)
  - `_arithmetic_mask` must never call back into `_arithmetic`.
- `test_ndarithmetic` → `ndarithmetic`
  - Tests consume and lock down observable contracts; implementation remains in mixin.

## Integration-seam skeleton

- Add/keep seam label `handle_mask_callable` in `_arithmetic`:
  - Keeps call-site behavior centralized and allows swapping callable strategy.
- Add/keep seam label `_arithmetic_mask`:
  - Single point of truth for mask combination behavior in mixed and dual-mask cases.

## Completion status for this phase

- Requirement homes assigned.
- Structural readiness established through explicit ownership, boundaries, and
  contracts.
- Traceability preserved by linking to canonical test and implementation artifacts.
