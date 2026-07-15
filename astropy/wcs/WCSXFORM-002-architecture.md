# WCSXFORM-002 Architecture Map: Empty-input success for shared-array transform helpers

## Requirement traceability
- `GUID: WCSXFORM-002` — For helper-path transform methods that route through `_array_converter` / `_return_list_of_arrays`, fully-empty required-axis inputs must return zero-length outputs with no `InconsistentAxisTypesError`, while preserving existing signatures and non-empty behavior.
- `GUID: WCSXFORM-002` implementation checkpoints:
  - Tests (placeholder scope): `astropy/wcs/tests/test_wcs.py`
    - `test_wcsxform_002_wcs_world2pix_empty_required_axes_return_zero_length_without_axis_errors`
    - `test_wcsxform_002_all_world2pix_empty_3axis_inputs_return_empty_family`
    - `test_wcsxform_002_wcs_world2pix_empty_then_non_empty_keeps_contract`

## Obligation → Architecture pressure map

1. Shared-helper empty-input short-circuit for required axes
  - Type pressure: invariant preservation at shared boundary (`_array_converter`).
  - Locus: `WCS._array_converter()` and `WCS._array_converter._return_list_of_arrays()`.
  - Structural intent: all-zero-size axis lists must resolve to shaped empty outputs at the helper boundary before wcslib dispatch.

2. Coverage across all helper-path methods (3-axis family included)
  - Type pressure: behavior consistency and interface inheritance.
  - Locus: method-level entrypoints that already call `_array_converter`:
    - `WCS.wcs_pix2world()`
    - `WCS.wcs_world2pix()`
    - `WCS.all_pix2world()`
    - `WCS.all_world2pix()`
  - Structural intent: single shared contract means one empty-input normalization path, no per-method forks.

3. State integrity across empty -> non-empty sequencing
  - Type pressure: object boundary and call-sequence safety.
  - Locus: no new state is written inside `_array_converter` or method entrypoints.
  - Structural intent: empty calls must be read-only and side-effect free so the same instance preserves normal non-empty behavior afterward.

4. Non-goals isolation
  - Type pressure: surface stability.
  - Locus: no additional methods/signatures are altered; only existing helper-path methods remain under contract.

## Placement and ownership

- Primary owning module: `astropy/wcs/wcs.py`
  - `WCS._array_converter()` owns input normalization, broadcasting, return-family reconstruction, and empty-output routing.
  - `_return_list_of_arrays()` is the explicit shape-preserving empty-output constructor for per-axis API family.
  - `WCS._return_single_array()` is the NxN contract owner and should remain a non-empty-only transform path.
  - Public entrypoints (`wcs_pix2world`, `wcs_world2pix`, `all_pix2world`, `all_world2pix`) remain thin delegators.

- Verification owner: `astropy/wcs/tests/test_wcs.py`
  - Keeps all acceptance criteria anchored in method-level regressions.

## Boundary and contract model

- API boundary:
  - Caller -> `wcs_*` / `all_*` method -> `_array_converter` -> wcslib kernel method.
  - Public signatures remain unchanged (positional/keyword compatibility preserved).

- Domain boundary:
  - `_array_converter` has two legal input families:
    - NxN coordinate arrays with origin.
    - Per-axis sequence with `naxis+1` arguments ending in origin.

- Output-contract boundary:
  - Per-axis contract returns one array per required axis.
  - NxN contract returns a stacked `[N, naxis]` result.
  - Empty required-axis inputs map to the same contract shape with zero-length containers.

- Integration seam (non-failing path):
  - `wcs.py` public methods -> `_array_converter`.
  - `_array_converter` should only invoke wcslib (`func`) when non-empty path is selected.
  - Empty path bypasses wcslib to avoid axis-type conversion exceptions.

## Dependency direction

- API methods depend inward on `_array_converter`.
- `_array_converter` depends inward on NumPy shape utilities and the low-level wcslib callback (`func`).
- Tests consume only public APIs and do not couple to internal state details.
- No new external dependencies or outward dependency edges are introduced.

## Structural completion check

- Each obligation has at least one owning locus in implementation and one verification locus.
- Empty-input contract is centralized to shared helper boundaries (`_array_converter` + `_return_list_of_arrays`) and fan-out to helper-path entrypoints.
- Public API stability is explicitly preserved by delegating through existing methods and signatures.
- Method state safety is maintained by avoiding state mutation in fast-path handling.
