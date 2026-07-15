# WCSXFORM-001 Architecture Map: Empty-input handling in `wcs_pix2world`

## Requirement traceability
- `GUID: WCSXFORM-001` — Empty input handling for `wcs_pix2world` must return empty outputs in the existing return-family (no exception, especially no `InconsistentAxisTypesError`) for fully-empty required-axis inputs.
- `GUID: WCSXFORM-001` implementation checkpoints:
  - Tests (placeholder currently): `astropy/wcs/tests/test_wcs.py`
    - `test_wcsxform_001_returns_empty_family_for_list_inputs_origin_0`
    - `test_wcsxform_001_returns_empty_family_for_list_inputs_origin_1`
    - `test_wcsxform_001_returns_empty_family_for_numpy_empty_axes_origin_0`

## Obligation → Architecture pressure map

1. Preserve return-family shape for success-empty cases.
   - Type pressure: output contract ownership.
   - Locus: `WCS._array_converter()`
     - Branch families:
       - single NxN argument path
       - per-axis argument path

2. Bypass transform path on fully-empty required-axis inputs.
   - Type pressure: call-sequence boundary and failure isolation.
   - Locus: `WCS._array_converter()` nested helpers:
     - `_return_list_of_arrays(axes, origin)`
     - `_return_single_array(xy, origin)`

3. Keep error behavior for malformed, non-empty, and mixed-shape inputs unchanged.
   - Type pressure: error contract consistency at API boundary.
   - Locus: `WCS._array_converter()` top-level dispatch + conversion/shape checks.

4. Surface requirement at API entrypoint without changing public signatures.
   - Type pressure: public API boundary stability.
   - Locus: `WCS.wcs_pix2world()`

## Placement and ownership

- Primary owner: `astropy/wcs/wcs.py`
  - `WCS.wcs_pix2world` remains sole API entry for this obligation.
  - `WCS._array_converter` is the structural owner for input-family normalization and empty-input routing.
  - Nested helpers inside `_array_converter` are boundary-specific owners for shape-preserving output reconstruction.
- Verification owner: `astropy/wcs/tests/test_wcs.py`
  - Keeps requirement-scoped regressions colocated with existing WCS API tests.

## Boundary and contract model

- API boundary:
  - Caller -> `WCS.wcs_pix2world(*args, **kwargs)` -> `_array_converter`.
  - No new public interfaces; no signature/keyword changes.

- Domain boundary:
  - `_array_converter` receives heterogenous input forms and dispatches to exactly one of:
    - single-array contract (`[N, naxis]` input shape),
    - per-axis contract (`(axis_0, axis_1, ..., axis_{n-1}, origin)`).

- Output-contract boundary (current family preservation):
  - Per-axis contract returns one output per axis.
  - NxN contract returns `[N, naxis]` output.
  - Empty inputs must emit zero-length outputs in the same contract shape.

- Integration seam:
  - `WCS.wcs_pix2world` delegates transformation to `self.wcs.p2s(... )['world']` through `_array_converter`.
  - Empty fast-paths should terminate before this seam to avoid raising axis-type conversion exceptions for fully-empty input sets.

## Dependency direction

- `wcs.py` public method depends on `_array_converter` for normalization and family routing.
- `_array_converter` depends inward on NumPy broadcasting/stacking and the WCS low-level core call.
- No outward dependency changes are required for this issue.

## Structural completion check

- Architectural readiness criteria for `WCSXFORM-001`:
  - Traced requirement has a named owning locus in implementation (`wcs.py`) and tests (`test_wcs.py`).
  - Output-shape contract boundaries and API stability constraints are documented in a single architecture artifact.
  - The implementation seam (`wcs_pix2world` -> `_array_converter` -> `p2s` transform) is explicitly preserved with an empty-input exit condition point.
