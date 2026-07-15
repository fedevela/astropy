# WCSXFORM-003 Architecture Map: Preserve validation on mixed-empty axis-count/shape mismatches

## Requirement traceability
- `GUID: WCSXFORM-003` — Existing validation failures for axis-count/shape inconsistencies (including mixed emptiness across axes in alignment-required paths) must be preserved; no mixed-empty success branch is introduced.
- `GUID: WCSXFORM-003` implementation checkpoints:
  - Validation owner: `astropy/wcs/wcs.py`
    - `_array_converter()` and `_return_list_of_arrays()` broadcast/error path.
    - `wcs_pix2world()` delegation contract.
    - `wcs_world2pix()` mixed-empty preservation contract.
    - `all_world2pix()` alignment-path preservation contract.
  - Verification owner: `astropy/wcs/tests/test_wcs.py`
    - `WCSXFORM_003_VERIFICATION_MAP`
    - `test_wcsxform_003_wcs_pix2world_axis_count_mismatch_with_empty_axis_raises_shape_validation`
    - `test_wcsxform_003_wcs_world2pix_one_axis_empty_one_non_empty_preserves_malformed_shape_behavior`
    - `test_wcsxform_003_all_world2pix_mixed_empty_non_empty_alignment_path_rejects_empty_success_branch`

## Obligation → Architecture pressure map

1. Preserve malformed axis-count/shape validation semantics
- Type pressure: exception contract at normalization boundary.
- Locus: `WCS._array_converter()` + `np.broadcast_arrays` in `_return_list_of_arrays()`.
- Rule: do not create a new branch that converts mixed-size inputs into the zero-length success family; broadcasting/malformed-shape `ValueError` remains the canonical failure path.

2. Mixed-empty must not trigger empty-success short-circuit
- Type pressure: branch discrimination in shared helper.
- Locus: `WCS._array_converter()` inner helper `_return_list_of_arrays()`.
- Rule: only all-of-axes empty checks (`all(axis.size == 0 for axis in axes)`) are allowed to route to empty-output construction.

3. Keep API method contracts and exception propagation intact
- Type pressure: API boundary stability and behavior inheritance.
- Loci:
  - `WCS.wcs_pix2world()` delegator comments and return path.
  - `WCS.wcs_world2pix()` delegator comments and return path.
- Rule: maintain current conversion/type exceptions for `wcs_pix2world([], [1.0], 0)` and related inconsistent-axis invocations.

4. Preserve alignment-required helper behavior under mixed emptiness
- Type pressure: iterative path integration seam.
- Locus: `WCS.all_world2pix()` pre-delegation alignment handling.
- Rule: mixed empty/non-empty per-axis inputs remain in existing fail mode; do not add new zero-length fast-path there.

## Placement and ownership

- Primary owner: `astropy/wcs/wcs.py`
  - `WCS._array_converter()` owns input normalization, broadcast checking, and empty/all-empty recognition.
  - `_return_list_of_arrays()` owns shape alignment checks and per-axis output reconstruction.
  - `WCS.wcs_pix2world()`, `WCS.wcs_world2pix()`, and `WCS.all_world2pix()` are structural entrypoints for this requirement class.
- Verification owner: `astropy/wcs/tests/test_wcs.py`
  - Holds all requirement-labeled obligations for `WCSXFORM-003` in one place.

## Boundary and contract model

- API boundary:
  - Caller -> public method (`wcs_*` / `all_*`) -> `_array_converter` -> low-level wcslib callback.
  - No new public signature or new public seam.

- Domain boundary:
  - `_array_converter` has exactly two legal input families and is responsible for deciding whether the empty fast path is legal.
  - Empty success is allowed only for full-family emptiness; mixed emptiness stays in domain validation failure.

- Error/empty contract boundary:
  - Empty success contract: all required axes empty -> shaped empty return with unchanged family (per-axis or NxN).
  - Mixed-empty/shape inconsistency contract: propagate current `ValueError`/`TypeError` behavior (including shape/broadcast mismatch messages).

## Dependency direction

- `wcs.py` public methods depend inward on `_array_converter` for all request family normalization and guard policy.
- `_array_converter` depends inward on NumPy (`np.asarray`, `np.broadcast_arrays`) and inward wcslib callbacks (`func`).
- Tests consume public API and remain decoupled from internal transformation details.

## Integration-seam note

- Seams to retain unchanged:
  - `wcs.py` methods -> `_array_converter` seam remains the sole normalizing boundary.
  - `_array_converter` -> wcslib callback seam (`func`) remains unchanged for non-all-empty valid inputs.

## Structural completion check

- All traced obligations are mapped to a owning locus in implementation and a verification locus in tests.
- No new modules/interfaces were introduced; only boundary/branch ownership was clarified as explicit architecture.
- Requirement behavior is represented as explicit contracts at helper/input-family boundaries with unchanged external API integration.
