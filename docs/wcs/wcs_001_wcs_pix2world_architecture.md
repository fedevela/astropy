# WCS-001 Architecture: `wcs_pix2world` empty-axis no-op

## Requirement

- `GUID: WCS-001` — empty per-axis input vectors passed to
  `WCS.wcs_pix2world` must not raise `InconsistentAxisTypesError`; outputs
  remain axis-complete and zero-length for both scalar-origin call styles.

## Requirement-to-architecture mapping

- `WCS-001` → `astropy/wcs/wcs.py` → `WCS.wcs_pix2world`
- `WCS-001` → `astropy/wcs/wcs.py` → `WCS._array_converter`
- `WCS-001` → `astropy/wcs/wcs.py` → `_return_list_of_arrays` path inside `_array_converter`
- `WCS-001` → `astropy/wcs/wcs.py` → `_return_single_array` path inside `_array_converter`
- Verification traceability placeholder in `astropy/wcs/tests/test_wcs_issue_30_wcs_001_traceability.py`

## Module placement and ownership

- Public API contract belongs to `WCS` (`astropy/wcs/wcs.py`), method
  `wcs_pix2world`.
- Input-shape normalization and route selection belongs to internal
  coordinator `WCS._array_converter`.
- Axis-wise payload assembly and no-op/edge branches belong to
  `_array_converter` private helpers:
  - list-style route: `_return_list_of_arrays`
  - NxN route: `_return_single_array`
- Core transformation implementation remains owned by `_wcs.Wcsprm` via
  the callback in `wcs_pix2world` (`self.wcs.p2s`) and is not part of
  the empty-input decision.

## Contracts and interfaces

### Public boundary

- `WCS.wcs_pix2world(*args, **kwargs) -> tuple|list-like`
  - Must retain signature and return shape conventions.
  - Must preserve both `origin` and `ra_dec_order` behavior.

### Internal conversion boundary

- `_array_converter(func, sky, *args, ra_dec_order=False)`
  - Inputs are either:
    - `(coords: ndarray[N, naxis], origin)` or
    - `(axis1: 1-D array, axis2: 1-D array, ..., axisN, origin)`
  - Outputs are delegated from helper paths, with per-call shape preservation.

### WCS-001 no-op contracts

- Empty list-style axis contract:
  - If all axis inputs are empty (regardless of declared shapes),
    route to explicit empty outputs, do not synthesize coordinates.
  - Output contract is axis-complete, zero-length for each axis.
  - No `InconsistentAxisTypesError` from lower transform layer.

- Empty NxN contract:
  - If single-array input has zero rows with compatible axis width
    (`xy.shape[-1] == self.naxis`), route to explicit empty output shape.
  - Return value shape follows existing method contract for return arity and
    axis count.

## Dependency direction notes

- `WCS.wcs_pix2world` depends on `_array_converter` for all dispatch and validation.
- `_array_converter` depends on `np.broadcast_arrays` and `self.wcs.p2s` through
  injected callbacks, but **must gate the callback in the empty-input branch**.
- Downstream `self.wcs` (`_wcs.Wcsprm`) remains the only source of numeric WCS
  transformation for non-empty paths.

## Integration-seam skeleton

- Keep seam ownership unchanged:
  - Public call seam: `WCS.wcs_pix2world`
  - Conversion seam: `_array_converter`
  - Transform seam: callback `lambda xy, o: self.wcs.p2s(xy, o)['world']`
- Implement by filling empty-input branches in `_return_list_of_arrays` and
  `_return_single_array` while preserving existing non-empty behavior and errors
  (`ValueError` shape checks).

## Completion status

- Structural artifact added.
- Traceability now includes one concrete architecture artifact for WCS-001 and
  explicit mapping of all obligations to owning module/function seams.
