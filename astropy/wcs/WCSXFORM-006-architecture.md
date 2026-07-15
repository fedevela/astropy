# WCSXFORM-006 Architecture Map: Repeated empty-input calls are stable and side-effect free

## Requirement traceability
- `GUID: WCSXFORM-006` — Given valid `WCS` instances, repeated empty-input transform invocations must remain independent, emit empty outputs, and avoid stateful side effects that affect later non-empty work.
- `GUID: WCSXFORM-006` implementation checkpoints:
  - Verification owner: `astropy/wcs/tests/test_wcs.py`
    - `WCSXFORM_006_VERIFICATION_MAP`
    - `test_wcsxform_006_wcs_pix2world_repeated_empty_inputs_remain_empty_and_state_free`
    - `test_wcsxform_006_empty_nonempty_empty_sequence_keeps_contract_on_one_instance`
    - `test_wcsxform_006_equivalent_fresh_wcs_instances_preserve_empty_nonempty_empty_contract`
  - Implementation owner: `astropy/wcs/wcs.py`
    - `WCS._array_converter()` and nested `_return_list_of_arrays()`
    - `WCS.wcs_pix2world()`
    - `WCS.wcs_world2pix()`
    - `WCS.all_pix2world()`
    - `WCS.all_world2pix()`

## Requirement-to-architecture pressure map

1. Repeated empty-input stability on same instance
- Type pressure: re-entrancy and local-state boundary in shared converter seam.
- Locus: `WCS._array_converter` plus `WCS._array_converter._return_list_of_arrays()`.
- Constraint: all-axis-empty paths must always be computed from current normalized `axis.size` and must not read or write call-history.
- Contract: each call returns zero-length outputs per axis family, with `np.empty(axis.shape, dtype=float)`-equivalent semantics.

2. Empty -> non-empty -> empty sequence determinism on same instance
- Type pressure: API boundary sequencing under mixed call phases.
- Locus: `WCS.wcs_pix2world()`, `WCS._array_converter`.
- Constraint: method-level guards stay unchanged; every invocation delegates to `_array_converter`, and only non-empty calls reach wcslib callback path.
- Contract: empty-success branch and normal transform branch are mutually exclusive based on current inputs, so middle non-empty call remains unaffected by prior empty invocation.

3. Fresh instance equivalence with identical execution sequence
- Type pressure: peer-path parity and construction-independent behavior.
- Locus: `WCS.wcs_pix2world()`, `WCS.wcs_world2pix()`, `WCS.all_pix2world()`, `WCS.all_world2pix()`.
- Constraint: all peer transforms share the same `_array_converter` empty-vs-non-empty branching, so behavior is instance-local and not object-history-dependent.
- Contract: equivalent WCS construction should yield equivalent outputs/error behavior in repeated empty/non-empty/empty sequences.

## Placement and ownership
- Primary owner for sequence control and branch purity: `astropy/wcs/wcs.py`.
- Structural API owner for the requirement: `WCS.wcs_pix2world()` (baseline contract).
- Shared helper owner for branch legality and contract shape: `WCS._array_converter()`.
- Return-shape owner for all-empty fast-path output construction: `WCS._array_converter._return_list_of_arrays()`.
- Cross-path parity owner: `WCS.wcs_world2pix()`, `WCS.all_pix2world()`, `WCS.all_world2pix()` via existing shared helper invocation.
- Verification owner: `astropy/wcs/tests/test_wcs.py`, with placeholders in `WCSXFORM_006_VERIFICATION_MAP`.

## Boundary and contract model
- API boundary: caller → public WCS method (`wcs_pix2world`, `wcs_world2pix`, `all_pix2world`, `all_world2pix`) → `_array_converter` → callback seam.
- `_array_converter` boundary: branch into empty path only when all normalized required axes are empty; mixed non-empty/mixed-empty inputs continue on validation/error or non-empty transform flow.
- No-cache boundary: no mutable per-call cache, sticky flag, or memoization object is owned in this path; any future stateful mechanism must be introduced through a new module and explicit dependency contract, which is out of scope here.
- Return boundary: all-empty branch returns per-axis family outputs as requested form; no container-type conversion is introduced.

## Dependency-direction notes
- Public WCS methods depend inward on `_array_converter` for argument normalization, branch choice, and output reconstruction.
- `_array_converter` depends inward on:
  - NumPy normalization and broadcast primitives (`np.asarray`, `np.broadcast_arrays`, `np.hstack`, `np.empty`)
  - The callback passed by each public method (`p2s`, `s2p`, `_all_pix2world`, `_all_world2pix`)
- `test_wcs.py` depends outward-only on public API behavior and maps obligations to method/internal loci.

## Integration-seam skeletons
- Keep seam `wcs_*` method → `_array_converter` unchanged in signature and invocation contract.
- Keep callback seam (`func(xy, origin)` identity) unchanged for non-empty execution path.
- Keep error/empty-branch seam in `_return_list_of_arrays` as the only legal branch where empty inputs bypass wcslib callbacks.
- Preserve peer symmetry by ensuring all four public transform entrypoints remain on identical branch-selection infrastructure.

## Structural completion check
- All three WCSXFORM-006 obligations are mapped to at least one owning locus in implementation and one verification locus.
- No new modules or public contracts were introduced.
- This is a concrete architecture artifact that explicitly defines ownership, boundaries, dependency direction, and seam constraints for stable repeated empty-input behavior.
