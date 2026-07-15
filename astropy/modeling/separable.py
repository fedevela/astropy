# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
Functions to determine if a model is separable, i.e.
if the model outputs are independent.

It analyzes ``n_inputs``, ``n_outputs`` and the operators
in a compound model by stepping through the transforms
and creating a ``coord_matrix`` of shape (``n_outputs``, ``n_inputs``).


Each modeling operator is represented by a function which
takes two simple models (or two ``coord_matrix`` arrays) and
returns an array of shape (``n_outputs``, ``n_inputs``).

"""

import numpy as np

from .core import Model, ModelDefinitionError, CompoundModel
from .mappings import Mapping


__all__ = ["is_separable", "separability_matrix"]

# AST12907-005 requirement-to-logic locus:
# - AST12907-005.S1: nested compound input must always produce a 2D boolean matrix.
# - AST12907-005.S2: returned matrix must be shaped exactly (n_outputs, n_inputs).
# - AST12907-005.S3: output/input index ordering must remain stable across
#   equivalent nested vs flattened compound model forms.
# Traceability:
# - test_AST12907_005_nested_compound_matrix_is_2d_boolean
# - test_AST12907_005_nested_compound_matrix_shape_matches_output_input_counts
# - test_AST12907_005_nested_vs_flattened_ordering_stable_by_output_input_indices

# AST12907-004 requirement traceability (pseudocode obligation locus)
# - Preserve non-nested behavior for: test_coord_matrix, test_cdot, test_cstack,
#   test_arith_oper, test_custom_model_separable, and compound_model0-result0,
#   compound_model1-result1, compound_model2-result2, compound_model3-result3,
#   compound_model4-result4, compound_model5-result5, compound_model7-result7,
#   compound_model8-result8.
# - AST12907-004 explicitly excludes compound_model6-result6 and
#   compound_model9-result9 exceptions handled in AST12907-003.


def is_separable(transform):
    """
    A separability test for the outputs of a transform.

    Parameters
    ----------
    transform : `~astropy.modeling.core.Model`
        A (compound) model.

    Returns
    -------
    is_separable : ndarray
        A boolean array with size ``transform.n_outputs`` where
        each element indicates whether the output is independent
        and the result of a separable transform.

    Examples
    --------
    >>> from astropy.modeling.models import Shift, Scale, Rotation2D, Polynomial2D
    >>> is_separable(Shift(1) & Shift(2) | Scale(1) & Scale(2))
        array([ True,  True]...)
    >>> is_separable(Shift(1) & Shift(2) | Rotation2D(2))
        array([False, False]...)
    >>> is_separable(Shift(1) & Shift(2) | Mapping([0, 1, 0, 1]) | \
        Polynomial2D(1) & Polynomial2D(2))
        array([False, False]...)
    >>> is_separable(Shift(1) & Shift(2) | Mapping([0, 1, 0, 1]))
        array([ True,  True,  True,  True]...)

    """
    # AST12907-004.S1: preserve legacy one-to-many short-circuit contract.
    # INPUTS:
    # - transform.n_inputs, transform.n_outputs
    # DECISION:
    # - IF n_inputs == 1 and n_outputs > 1:
    #   - return array(False, repeat=n_outputs)
    # - ELSE:
    #   - separable_matrix <- _separable(transform)
    #   - is_separable <- separable_matrix.sum(1)
    #   - is_separable <- True iff row sum == 1
    # FAILURE/EXCEPTIONS:
    # - delegates to _separable and operator-level failures unchanged
    if transform.n_inputs == 1 and transform.n_outputs > 1:
        is_separable = np.array([False] * transform.n_outputs).T
        return is_separable
    separable_matrix = _separable(transform)
    is_separable = separable_matrix.sum(1)
    is_separable = np.where(is_separable != 1, False, True)
    return is_separable


def separability_matrix(transform):
    """
    Compute the correlation between outputs and inputs.

    Parameters
    ----------
    transform : `~astropy.modeling.core.Model`
        A (compound) model.

    Returns
    -------
    separable_matrix : ndarray
        A boolean correlation matrix of shape (n_outputs, n_inputs).
        Indicates the dependence of outputs on inputs. For completely
        independent outputs, the diagonal elements are True and
        off-diagonal elements are False.

    Examples
    --------
    >>> from astropy.modeling.models import Shift, Scale, Rotation2D, Polynomial2D
    >>> separability_matrix(Shift(1) & Shift(2) | Scale(1) & Scale(2))
        array([[ True, False], [False,  True]]...)
    >>> separability_matrix(Shift(1) & Shift(2) | Rotation2D(2))
        array([[ True,  True], [ True,  True]]...)
    >>> separability_matrix(Shift(1) & Shift(2) | Mapping([0, 1, 0, 1]) | \
        Polynomial2D(1) & Polynomial2D(2))
        array([[ True,  True], [ True,  True]]...)
    >>> separability_matrix(Shift(1) & Shift(2) | Mapping([0, 1, 0, 1]))
        array([[ True, False], [False,  True], [ True, False], [False,  True]]...)

    """
    # AST12907-005.S1/S2 (contract enforcement locus):
    # INPUTS:
    # - transform: Model/CompoundModel under inspection
    # - expected contract envelope = (transform.n_outputs, transform.n_inputs)
    # DECISION:
    # - IF transform.n_inputs == 1 and transform.n_outputs > 1:
    #   - raw_matrix <- ones((n_outputs, n_inputs), dtype=bool)
    # - ELSE:
    #   - raw_matrix <- _separable(transform)
    #   - normalize each cell to boolean via (raw_matrix != 0)
    # POST-CONDITIONS:
    # - output_matrix.ndim == 2
    # - output_matrix.shape == (transform.n_outputs, transform.n_inputs)
    # - output_matrix.dtype == bool
    # - all truth values are stable with respect to transform.n_outputs/n_inputs axes.
    # FAILURE/EXCEPTIONS:
    # - preserve current behavior; no local conversion exceptions or recovery.
    if transform.n_inputs == 1 and transform.n_outputs > 1:
        return np.ones((transform.n_outputs, transform.n_inputs),
                       dtype=np.bool_)
    separable_matrix = _separable(transform)
    separable_matrix = np.where(separable_matrix != 0, True, False)
    return separable_matrix


def _compute_n_outputs(left, right):
    """
    Compute the number of outputs of two models.

    The two models are the left and right model to an operation in
    the expression tree of a compound model.

    Parameters
    ----------
    left, right : `astropy.modeling.Model` or ndarray
        If input is of an array, it is the output of `coord_matrix`.

    """
    if isinstance(left, Model):
        lnout = left.n_outputs
    else:
        lnout = left.shape[0]
    if isinstance(right, Model):
        rnout = right.n_outputs
    else:
        rnout = right.shape[0]
    noutp = lnout + rnout
    return noutp


def _flatten_ampersand_chain(transform):
    """
    Return a left-to-right list of operands from an '&' chain.

    Parameters
    ----------
    transform : `astropy.modeling.Model`
        A model or compound model.
    """
    # AST12907-002 / AST12907-005.S3:
    # Inputs:
    # - transform: a model tree possibly containing '&' compounds.
    # Output:
    # - operands: leaf nodes visited in left-to-right, depth-first order.
    # Branching and transitions:
    # - start with stack = [transform].
    # - while stack not empty:
    #   - pop(node); if node is '&', push right then left (preserves left-to-right append).
    #   - otherwise append node as a leaf operand.
    # Invariant:
    # - flattening captures associativity-only rewrites without creating new coupling.
    # AST12907-003:
    # - this sequence is the required determinism point for nested cases behind
    #   test_separable[compound_model6-result6] and
    #   test_separable[compound_model9-result9]:
    #   input tree shape must only affect traversal ordering, not matrix semantics.
    # - no local transformation failure handling is introduced; non-ampersand
    #   branches remain terminal operands and are delegated to downstream logic.
    if isinstance(transform, CompoundModel) and transform.op == '&':
        operands = _flatten_ampersand_chain(transform.left)
        operands.extend(_flatten_ampersand_chain(transform.right))
        return operands

    return [transform]


def _to_coord_operand(operand, pos, noutp):
    """
    Normalize an '&' operand into a coord-matrix block.

    Parameters
    ----------
    operand : `astropy.modeling.Model` or ndarray
        Leaf model or intermediate coord-matrix.
    pos : {'left', 'right'}
        Operand placement in composed outputs.
    noutp : int
        Total outputs of the composed '&' block.
    """
    # AST12907-005.S3:
    # - For leaf Model: delegate to _coord_matrix so per-operand output/input
    #   axes remain canonical.
    # - For ndarray block:
    #   - IF pos == 'left': place block in leading rows/cols.
    #   - IF pos == 'right': place block in trailing rows/cols.
    # This preserves stable column and row indices in '&' composition regardless
    # of nested tree shape.
    if isinstance(operand, Model):
        return _coord_matrix(operand, pos, noutp)

    mat = np.zeros((noutp, operand.shape[1]))
    if pos == 'left':
        mat[:operand.shape[0], :operand.shape[1]] = operand
    else:
        mat[-operand.shape[0]:, -operand.shape[1]:] = operand
    return mat


def _arith_oper(left, right):
    """
    Function corresponding to one of the arithmetic operators
    ['+', '-'. '*', '/', '**'].

    This always returns a nonseparable output.


    Parameters
    ----------
    left, right : `astropy.modeling.Model` or ndarray
        If input is of an array, it is the output of `coord_matrix`.

    Returns
    -------
    result : ndarray
        Result from this operation.
    """
    # AST12907-004.S5: preserve non-nested arithmetic operator contract.
    # DECISION:
    # - derive n_inputs/n_outputs for both operands.
    # - IF arities differ -> raise ModelDefinitionError.
    # - ELSE -> return ones((n_outputs, n_inputs)).
    # This keeps existing non-nested error and matrix-shape behavior.

    # models have the same number of inputs and outputs
    def _n_inputs_outputs(input):
        if isinstance(input, Model):
            n_outputs, n_inputs = input.n_outputs, input.n_inputs
        else:
            n_outputs, n_inputs = input.shape
        return n_inputs, n_outputs

    left_inputs, left_outputs = _n_inputs_outputs(left)
    right_inputs, right_outputs = _n_inputs_outputs(right)

    if left_inputs != right_inputs or left_outputs != right_outputs:
        raise ModelDefinitionError(
            "Unsupported operands for arithmetic operator: left (n_inputs={}, "
            "n_outputs={}) and right (n_inputs={}, n_outputs={}); "
            "models must have the same n_inputs and the same "
            "n_outputs for this operator.".format(
                left_inputs, left_outputs, right_inputs, right_outputs))

    result = np.ones((left_outputs, left_inputs))
    return result


def _coord_matrix(model, pos, noutp):
    """
    Create an array representing inputs and outputs of a simple model.

    The array has a shape (noutp, model.n_inputs).

    Parameters
    ----------
    model : `astropy.modeling.Model`
        model
    pos : str
        Position of this model in the expression tree.
        One of ['left', 'right'].
    noutp : int
        Number of outputs of the compound model of which the input model
        is a left or right child.

    """
    # AST12907-004.S2: preserve non-nested simple-model matrix behavior.
    # BRANCHING:
    # - IF model is Mapping:
    #     - derive rows from mapping indices.
    #     - place block in left span when pos='left', right span when pos='right'.
    # - ELSE IF model.separable is False:
    #     - emit dense ones over the model output/input region.
    # - ELSE (model.separable is True):
    #     - emit diagonal-like local dependency rows, then roll right-position rows if needed.
    # OUTPUT:
    # - matrix dimensions and placement are unchanged from prior logic.
    # AST12907-005.S2/S3:
    # - Contract requires matrix dimensions always align to (noutp, model.n_inputs).
    # - For non-right positions, write block into the leading input/output span;
    #   for right positions, shift rows to trailing output span.
    if isinstance(model, Mapping):
        axes = []
        for i in model.mapping:
            axis = np.zeros((model.n_inputs,))
            axis[i] = 1
            axes.append(axis)
        m = np.vstack(axes)
        mat = np.zeros((noutp, model.n_inputs))
        if pos == 'left':
            mat[: model.n_outputs, :model.n_inputs] = m
        else:
            mat[-model.n_outputs:, -model.n_inputs:] = m
        return mat
    # AST12907-004.S2: custom Model.separable attribute is the single source of truth.
    if not model.separable:
        # this does not work for more than 2 coordinates
        mat = np.zeros((noutp, model.n_inputs))
        if pos == 'left':
            mat[:model.n_outputs, : model.n_inputs] = 1
        else:
            mat[-model.n_outputs:, -model.n_inputs:] = 1
    else:
        mat = np.zeros((noutp, model.n_inputs))

        for i in range(model.n_inputs):
            mat[i, i] = 1
        if pos == 'right':
            mat = np.roll(mat, (noutp - model.n_outputs))
    return mat


def _cstack(left, right):
    """
    Function corresponding to '&' operation.

    Parameters
    ----------
    left, right : `astropy.modeling.Model` or ndarray
        If input is of an array, it is the output of `coord_matrix`.

    Returns
    -------
    result : ndarray
        Result from this operation.

    """
    # AST12907-004.S4 / AST12907-005.S2/S3:
    # DECISION:
    # - noutp <- _compute_n_outputs(left, right)
    # - cleft <- _to_coord_operand(left, 'left', noutp)
    # - cright <- _to_coord_operand(right, 'right', noutp)
    # - return np.hstack([cleft, cright])
    # PROPERTY:
    # - preserve disjoint input-column blocks with no new cross-block coupling.

    # AST12907-002: '&' transition must append independent coordinate block.
    # Step:
    # 1) noutp <- left.n_outputs + right.n_outputs
    # 2) cleft <- normalize left operand into rows [0:nleft) and its own input span.
    # 3) cright <- normalize right operand into rows [-nright:] and trailing input span.
    # 4) return np.hstack([cleft, cright]).
    # Property:
    # - existing left-block dependencies never write into right-block columns and
    #   right-block independence is not coupled into left columns.
    noutp = _compute_n_outputs(left, right)
    cleft = _to_coord_operand(left, 'left', noutp)
    cright = _to_coord_operand(right, 'right', noutp)
    return np.hstack([cleft, cright])

def _cdot(left, right):
    """
    Function corresponding to "|" operation.

    Parameters
    ----------
    left, right : `astropy.modeling.Model` or ndarray
        If input is of an array, it is the output of `coord_matrix`.

    Returns
    -------
    result : ndarray
        Result from this operation.
    """

    # AST12907-004.S3 / AST12907-005.S2/S3:
    # DECISION:
    # - swap(left, right) assignment is canonical for this operator.
    # - convert each operand into coord-matrix form if needed.
    # - try matrix-matrix dot product.
    # EXCEPTION:
    # - on ValueError, raise ModelDefinitionError with operator diagnostics.
    # - preserve same exception shape/propagation behavior as before.

    left, right = right, left

    def _n_inputs_outputs(input, position):
        """
        Return ``n_inputs``, ``n_outputs`` for a model or coord_matrix.
        """
        if isinstance(input, Model):
            coords = _coord_matrix(input, position, input.n_outputs)
        else:
            coords = input
        return coords

    cleft = _n_inputs_outputs(left, 'left')
    cright = _n_inputs_outputs(right, 'right')

    try:
        result = np.dot(cleft, cright)
    except ValueError:
        raise ModelDefinitionError(
            'Models cannot be combined with the "|" operator; '
            'left coord_matrix is {}, right coord_matrix is {}'.format(
                cright, cleft))
    return result


def _separable(transform):
    """
    Calculate the separability of outputs.

    Parameters
    ----------
    transform : `astropy.modeling.Model`
        A transform (usually a compound model).

    Returns :
    is_separable : ndarray of dtype np.bool
        An array of shape (transform.n_outputs,) of boolean type
        Each element represents the separablity of the corresponding output.
    """
    # AST12907-004.S6/S7 / AST12907-005.S2/S3:
    # - non-regressed fixtures keep existing branching for operator-specific composition.
    # - only '&' nested-chain normalization is allowed to alter traversal form.
    # - nested '&' behavior changed only for AST12907-003-covered cases.
    # AST12907-005-specific mapping:
    # - S2 exact shape contract:
    #   - If custom hook returns a matrix, it is treated as full matrix for this
    #     transform and must already represent (n_outputs, n_inputs).
    #   - All operator combinators consume and emit matrix-shaped by rows=outputs,
    #     cols=inputs, so the same dimensional contract is preserved.
    # - S3 ordering stability:
    #   - Nested '&' is flattened to an operand list in deterministic order.
    #   - matrix accumulation folds operands left-to-right with _operators['&'].
    #   - no branch reorders operands, so resulting row/column labels stay
    #     aligned to output/input order semantics of the equivalent flattened form.
    if (transform_matrix := transform._calculate_separability_matrix()) is not NotImplemented:
        return transform_matrix
    elif isinstance(transform, CompoundModel):
        if transform.op == '&':
            # AST12907-002.S1/S2: nested '&' must preserve independent right-hand linear block.
            # AST12907-003.S1/S2: baseline regression stability for compound_model6-result6 / result9.
            # Inputs:
            # - transform: CompoundModel with op '&'.
            # State model:
            # - state_matrix := _separable(operands[0]) after flatten.
            # - loop_idx from 1..(len(operands)-1).
            # Deterministic transition:
            # - IF operands length <= 1:
            #     return _separable(transform) via direct recursion/leaf handling.
            # - ELSE:
            #     operands <- _flatten_ampersand_chain(transform)
            #     state_matrix <- _separable(operands[0])
            #     FOR each operand in operands[1:]:
            #         next_matrix <- _separable(operand)
            #         state_matrix <- _operators['&'](state_matrix, next_matrix)
            #     RETURN state_matrix.
            # Required post-conditions (traceable to AST12907-003 cases):
            # - nested form and flattened form produce identical matrix.
            # - no new cross-block coupling may be introduced for baseline fixtures.
            # Failure path:
            # - propagate ModelDefinitionError or similar exceptions unchanged.
            operands = _flatten_ampersand_chain(transform)
            if len(operands) == 1:
                return _separable(operands[0])

            separable_matrix = _separable(operands[0])
            for operand in operands[1:]:
                separable_matrix = _operators['&'](separable_matrix,
                                                   _separable(operand))
            return separable_matrix

        # AST12907-004.S7: legacy non-nested compound path for operators
        # other than '&' must remain unchanged in output semantics.
        # - compute left/right recursively.
        # - dispatch exact operator matrix function via _operators.
        # - propagate ModelDefinitionError from operator nodes.
        sepleft = _separable(transform.left)
        sepright = _separable(transform.right)
        return _operators[transform.op](sepleft, sepright)
    elif isinstance(transform, Model):
        return _coord_matrix(transform, 'left', transform.n_outputs)


# Maps modeling operators to a function computing and represents the
# relationship of axes as an array of 0-es and 1-s
_operators = {'&': _cstack, '|': _cdot, '+': _arith_oper, '-': _arith_oper,
              '*': _arith_oper, '/': _arith_oper, '**': _arith_oper}
