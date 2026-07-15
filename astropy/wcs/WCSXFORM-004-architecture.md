# WCSXFORM-004 Architecture Map: Preserve non-empty `wcs_pix2world` behavior after empty-input changes

## Requirement traceability
- `GUID: WCSXFORM-004` — Given valid non-empty `wcs_pix2world` inputs, output values, axis ordering, container type, and shapes must remain unchanged after empty-input handling changes.
- `GUID: WCSXFORM-004` implementation checkpoints:
  - Verification owner: `astropy/wcs/tests/test_wcs.py`
    - `WCSXFORM_004_VERIFICATION_MAP`
    - `test_wcsxform_004_wcs_pix2world_non_empty_inputs_preserve_axes_order_shape_and_container_type`
    - `test_wcsxform_004_wcs_pix2world_mixed_scalar_list_array_outputs_remain_structurally_equivalent`
  - Implementation owner: `astropy/wcs/wcs.py`
    - `WCS._array_converter()` and nested helpers
    - `WCS.wcs_pix2world()`
    - `WCS._return_list_of_arrays()` / `WCS._return_single_array()` return-paths

## Obligation → Architecture pressure map

1. Preserve non-empty output value/axis semantics while allowing empty-input path only as a special-case branch.
- Type pressure: route/normalization invariance.
- Locus: `WCS._array_converter()` input-family dispatch.
- Contract: branching by argument arity remains `2` vs `naxis + 1`, with no additional pre/post transforms for non-empty cases.

2. Preserve axis ordering for list-of-axis return contracts.
- Type pressure: output reconstruction contract at shared helper boundary.
- Locus: `WCS._array_converter._return_list_of_arrays()`.
- Contract: non-empty transformed data is emitted in output column order `output[:, i]` with `i = [0..naxis-1]`, reshaped to the broadcast input shape.

3. Preserve return-container family for mixed scalar/list/array valid calls.
- Type pressure: boundary/interface compatibility.
- Locus: `WCS._array_converter._return_single_array()` and `WCS._array_converter()` branch conditions.
- Contract: scalar or NxN path returns ndarray, per-axis path returns list-per-axis; no family conversion is introduced for non-empty calls.

4. Keep API ownership and delegation boundary unchanged.
- Type pressure: public seam stability.
- Locus: `WCS.wcs_pix2world()`.
- Contract: `wcs_pix2world` remains thin delegator into `_array_converter` and preserves callable identity to wcslib kernel path (`lambda xy, o: self.wcs.p2s(xy, o)['world']`).

## Placement and ownership

- Primary owner: `astropy/wcs/wcs.py`
  - `WCS.wcs_pix2world()` is the public API boundary for this issue and owns method-level contract stability.
  - `WCS._array_converter()` owns input-family recognition, non-empty route, and output reconstruction policy.
  - `_return_list_of_arrays()` owns per-axis list output shape/order semantics.
  - `_return_single_array()` owns NxN/packed-array return semantics.

- Verification owner: `astropy/wcs/tests/test_wcs.py`
  - Maintains `WCSXFORM_004_VERIFICATION_MAP` and the two `test_wcsxform_004_*` placeholders in lockstep with requirement language.

## Boundary and contract model

- API boundary: `caller -> wcs_pix2world -> _array_converter -> wcslib callback`.
  - No public signature changes.
  - No new parameters or return types.

- Domain boundary:
  - `_array_converter` supports two legal input families: `([N, naxis], origin)` and `(axis_0, ... axis_{naxis-1}, origin)`.
  - Empty-fast-path contracts are allowed to skip wcslib, but only for fully-empty, non-mixed families (already enforced by existing helper logic).
  - All other non-empty valid branches preserve the existing transform sequence.

- Output-contract boundary:
  - Per-axis path returns one object per axis in order.
  - NxN path returns stacked ndarray.
  - Empty-success handling must not alter these return-family decisions for valid non-empty calls.

## Dependency direction

- `wcs.py` public API (`wcs_pix2world`) depends inward on `_array_converter` for argument normalization and return-shape preservation.
- `_array_converter` depends inward on NumPy broadcasting/array ops (`np.asarray`, `np.broadcast_arrays`, `hstack`) and the wcslib callback function passed in.
- Verification file consumes only public API behavior and maps each obligation to implementation loci.

## Integration seams

- Retain and formalize the unchanged seam:
  - `WCS.wcs_pix2world` -> `WCS._array_converter`.
- Constrain behavior changes to this issue at the contract boundary only when processing empty inputs; keep non-empty call chain fully unchanged.

## Structural completion check

- Every `WCSXFORM-004` obligation is mapped to both a verification locus and implementation locus.
- Requirement is represented via explicit output-family, axis-order, and delegation contracts.
- At least one concrete architecture artifact has been created and remains structurally focused on placement, boundaries, and dependencies.
