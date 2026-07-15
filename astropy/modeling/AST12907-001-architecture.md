# Architecture: AST12907-001 — nested `CompoundModel` flattening in separability

Issue: `AST12907-001`
Goal: make separability dependency analysis invariant to `&` parenthesization by treating nested `CompoundModel` joins as structurally flattened during matrix assembly.

## Requirement-to-architecture map

| Requirement obligation | Ownership / locus | Architectural pressure | Structural action |
|---|---|---|---|
| `AST12907-001` Scenario 1: `A&(B&C)` ≡ `(A&B)&C` matrix equality | `astropy/modeling/separable.py` → `_separable` (CompoundModel branch), `_cstack`, `_operators` | Associativity-normalization pressure | Add/keep a deterministic join-normalization seam so every `&` composition is reduced to an ordered flattening pass before stack combine. |
| `AST12907-001` Scenario 2: no false cross-dependency from nesting | `astropy/modeling/separable.py` → `_cstack` and `_coord_matrix` | Boundary-pressure between composition and coordinate blocks | Preserve strict block ordering and dimensional contracts; avoid implicit cross-block rewrites or transpose-like coupling. |

## Module placement and ownership

- Keep the change local to `astropy/modeling/separable.py`.
  - Public entry points (`is_separable`, `separability_matrix`) remain unchanged.
  - Structural behavior lives entirely in private helpers (`_separable`, `_cstack`, `_operators`) where composition semantics are already owned.
- Tests stay in `astropy/modeling/tests/test_separable.py` as `AST12907_001_VERIFICATION`.

## Contract / seam inventory

### Core contracts to preserve
- `_cstack(left, right)` must remain the dedicated `&` composition seam:
  - Input: `left` and `right` are either model nodes or prebuilt coordinate matrices.
  - Output: block-stacked coordinate matrix with row/column ordering derived from logical left-to-right execution order.
- `_separable(transform)` is the recursive traversal seam for all compound nodes:
  - Contract: compute local matrix, then combine through `_operators[transform.op]`.
- `_operators` is the dispatch boundary between operator symbols and matrix builders and remains the only integration seam for operator-specific composition.

### Proposed structural skeleton for implementation
- Introduce private structural helpers at `separable.py` (same module, same ownership):
  - `_flatten_ampersand_chain(transform: CompoundModel) -> list[Model]`  
    Ordered flattening of consecutive `&`-chained `CompoundModel` nodes.
  - `_to_coord_operand(node: Model | ndarray, side: Literal["left", "right"], n_outputs: int) -> ndarray`  
    Input normalization and deterministic placement adapter for operand blocks.
- Keep these helpers optional in implementation order; only structural signature/placeholders are required for architecture completion.

## Dependency direction

1. API layer (`is_separable`, `separability_matrix`) depends on internal matrix recursion.
2. `_separable` depends on:
   - transform override hook (`_calculate_separability_matrix`)
   - model shape contract (`CompoundModel` topology + `Model` leaves)
   - `_operators` dispatch table.
3. `_operators['&']` depends on `_cstack`.
4. `_cstack` depends on `_coord_matrix` for model operands and deterministic placement assumptions.

This direction avoids cycles and keeps flattening as an input-shape normalization step, not a rewrite of public model semantics.

## Integration seam stubs

- Seams:
  - `_separable` compound branch (`CompoundModel` branch)
  - `_operators["&"]`
  - `_cstack`
- Planned integration:
  - Flattening policy is enforced in `_separable` before `_cstack` dispatch for nested `&`.
  - `_cstack` consumes the flattened or already-order-preserving operands without changing `transform` shape semantics.

## Completion check for this phase

- Every obligation has an architectural home:
  - Scenario 1 → `_separable` flattening contract + `_operators` dispatch.
  - Scenario 2 → `_cstack` boundary-preserving block composition contract.
- Traceability preserved via existing requirement map:
  - `AST12907_001_VERIFICATION` in `astropy/modeling/tests/test_separable.py`.
- At least one architecture artifact created: this file.
