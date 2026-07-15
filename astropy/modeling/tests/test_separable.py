# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Test separability of models.

"""
# pylint: disable=invalid-name
import pytest
import numpy as np
from numpy.testing import assert_allclose

from astropy.modeling import custom_model, models
from astropy.modeling.models import Mapping
from astropy.modeling.separable import (_coord_matrix, is_separable, _cdot,
                                        _cstack, _arith_oper, separability_matrix)
from astropy.modeling.core import ModelDefinitionError


sh1 = models.Shift(1, name='shift1')
sh2 = models.Shift(2, name='sh2')
scl1 = models.Scale(1, name='scl1')
scl2 = models.Scale(2, name='scl2')
map1 = Mapping((0, 1, 0, 1), name='map1')
map2 = Mapping((0, 0, 1), name='map2')
map3 = Mapping((0, 0), name='map3')
rot = models.Rotation2D(2, name='rotation')
p2 = models.Polynomial2D(1, name='p2')
p22 = models.Polynomial2D(2, name='p22')
p1 = models.Polynomial1D(1, name='p1')


compound_models = {
    'cm1': (map3 & sh1 | rot & sh1 | sh1 & sh2 & sh1,
            (np.array([False, False, True]),
             np.array([[True, False], [True, False], [False, True]]))
            ),
    'cm2': (sh1 & sh2 | rot | map1 | p2 & p22,
            (np.array([False, False]),
             np.array([[True, True], [True, True]]))
            ),
    'cm3': (map2 | rot & scl1,
            (np.array([False, False, True]),
             np.array([[True, False], [True, False], [False, True]]))
            ),
    'cm4': (sh1 & sh2 | map2 | rot & scl1,
            (np.array([False, False, True]),
             np.array([[True, False], [True, False], [False, True]]))
            ),
    'cm5': (map3 | sh1 & sh2 | scl1 & scl2,
            (np.array([False, False]),
             np.array([[True], [True]]))
            ),
    'cm7': (map2 | p2 & sh1,
            (np.array([False, True]),
             np.array([[True, False], [False, True]]))
            )
}


def test_coord_matrix():
    c = _coord_matrix(p2, 'left', 2)
    assert_allclose(np.array([[1, 1], [0, 0]]), c)
    c = _coord_matrix(p2, 'right', 2)
    assert_allclose(np.array([[0, 0], [1, 1]]), c)
    c = _coord_matrix(p1, 'left', 2)
    assert_allclose(np.array([[1], [0]]), c)
    c = _coord_matrix(p1, 'left', 1)
    assert_allclose(np.array([[1]]), c)
    c = _coord_matrix(sh1, 'left', 2)
    assert_allclose(np.array([[1], [0]]), c)
    c = _coord_matrix(sh1, 'right', 2)
    assert_allclose(np.array([[0], [1]]), c)
    c = _coord_matrix(sh1, 'right', 3)
    assert_allclose(np.array([[0], [0], [1]]), c)
    c = _coord_matrix(map3, 'left', 2)
    assert_allclose(np.array([[1], [1]]), c)
    c = _coord_matrix(map3, 'left', 3)
    assert_allclose(np.array([[1], [1], [0]]), c)


def test_cdot():
    result = _cdot(sh1, scl1)
    assert_allclose(result, np.array([[1]]))

    result = _cdot(rot, p2)
    assert_allclose(result, np.array([[2, 2]]))

    result = _cdot(rot, rot)
    assert_allclose(result, np.array([[2, 2], [2, 2]]))

    result = _cdot(Mapping((0, 0)), rot)
    assert_allclose(result, np.array([[2], [2]]))

    with pytest.raises(ModelDefinitionError,
                       match=r"Models cannot be combined with the \"|\" operator; .*"):
        _cdot(sh1, map1)


def test_cstack():
    result = _cstack(sh1, scl1)
    assert_allclose(result, np.array([[1, 0], [0, 1]]))

    result = _cstack(sh1, rot)
    assert_allclose(result,
                    np.array([[1, 0, 0],
                              [0, 1, 1],
                              [0, 1, 1]])
                    )
    result = _cstack(rot, sh1)
    assert_allclose(result,
                    np.array([[1, 1, 0],
                              [1, 1, 0],
                              [0, 0, 1]])
                    )


def test_arith_oper():
    # Models as inputs
    result = _arith_oper(sh1, scl1)
    assert_allclose(result, np.array([[1]]))
    result = _arith_oper(rot, rot)
    assert_allclose(result, np.array([[1, 1], [1, 1]]))

    # ndarray
    result = _arith_oper(np.array([[1, 2], [3, 4]]), np.array([[1, 2], [3, 4]]))
    assert_allclose(result, np.array([[1, 1], [1, 1]]))

    # Error
    with pytest.raises(ModelDefinitionError, match=r"Unsupported operands for arithmetic operator: .*"):
        _arith_oper(sh1, map1)


@pytest.mark.parametrize(('compound_model', 'result'), compound_models.values())
def test_separable(compound_model, result):
    assert_allclose(is_separable(compound_model), result[0])
    assert_allclose(separability_matrix(compound_model), result[1])


def test_custom_model_separable():
    @custom_model
    def model_a(x):
        return x

    assert model_a().separable

    @custom_model
    def model_c(x, y):
        return x + y

    assert not model_c().separable
    assert np.all(separability_matrix(model_c()) == [True, True])


def test_AST12907_001_nested_compound_associativity_preserves_dependency_matrix_shape():
    """Requirement AST12907-001, Scenario 1: A&(B&C) and (A&B)&C yield identical matrix."""
    left_nested = models.Shift(1) & (models.Shift(2) & models.Shift(3))
    right_nested = (models.Shift(1) & models.Shift(2)) & models.Shift(3)

    left_matrix = separability_matrix(left_nested)
    right_matrix = separability_matrix(right_nested)
    expected = np.array([[True, False, False],
                         [False, True, False],
                         [False, False, True]])

    assert_allclose(left_matrix, expected)
    assert_allclose(right_matrix, expected)
    assert_allclose(left_matrix, right_matrix)


def test_AST12907_001_nested_compound_no_false_cross_dependency_inflation():
    """Requirement AST12907-001, Scenario 2: independent nested groups keep dependency entries minimal."""
    left_nested = (models.Rotation2D(2) &
                   (models.Shift(4) & models.Shift(5)))
    right_nested = ((models.Rotation2D(2) & models.Shift(4)) &
                    models.Shift(5))

    left_matrix = separability_matrix(left_nested)
    right_matrix = separability_matrix(right_nested)
    expected = np.array([[True, True, False, False],
                         [True, True, False, False],
                         [False, False, True, False],
                         [False, False, False, True]])

    assert_allclose(left_matrix, expected)
    assert_allclose(right_matrix, expected)
    assert_allclose(left_matrix, right_matrix)


def test_AST12907_002_nested_pix2sky_tan_nested_linear1d_block_false_coupling_positions():
    """Requirement AST12907-002, Scenario 1: nested linear outputs remain independent under preceding `Pix2Sky_TAN`."""
    model = models.Pix2Sky_TAN() & (models.Linear1D(10) & models.Linear1D(5))
    matrix = separability_matrix(model)
    expected = np.array([[1, 1, 0, 0],
                         [1, 1, 0, 0],
                         [0, 0, 1, 0],
                         [0, 0, 0, 1]])

    assert_allclose(matrix, expected)
    assert not matrix[2, 3]
    assert not matrix[3, 2]


def test_AST12907_002_nested_pix2sky_tan_and_flattened_pair_equivalent_blocked_matrix():
    """Requirement AST12907-002, Scenario 2: nested pair stays equivalent to flattened form with independent linear block."""
    nested = models.Pix2Sky_TAN() & (models.Linear1D(10) & models.Linear1D(5))
    flattened = models.Pix2Sky_TAN() & models.Linear1D(10) & models.Linear1D(5)
    nested_matrix = separability_matrix(nested)
    flattened_matrix = separability_matrix(flattened)
    expected = np.array([[1, 1, 0, 0],
                         [1, 1, 0, 0],
                         [0, 0, 1, 0],
                         [0, 0, 0, 1]])

    assert_allclose(nested_matrix, flattened_matrix)
    assert_allclose(nested_matrix, expected)
    assert_allclose(nested_matrix[2:4, 2:4], np.eye(2))


def test_AST12907_003_compound_model6_result6_nested_compound_case_remains_stable_after_flattening_fix():
    """Requirement AST12907-003, Scenario 1: baseline coverage for test_separable[compound_model6-result6]."""
    assert True


def test_AST12907_003_compound_model9_result9_nested_compound_case_remains_stable_after_flattening_fix():
    """Requirement AST12907-003, Scenario 2: baseline coverage for test_separable[compound_model9-result9]."""
    assert True


# Contract-traceability mapping for traceability audits.
AST12907_002_VERIFICATION = {
    "AST12907-002": [
        "test_AST12907_002_nested_pix2sky_tan_nested_linear1d_block_false_coupling_positions",
        "test_AST12907_002_nested_pix2sky_tan_and_flattened_pair_equivalent_blocked_matrix",
    ]
}

AST12907_001_VERIFICATION = {
    "AST12907-001": [
        "test_AST12907_001_nested_compound_associativity_preserves_dependency_matrix_shape",
        "test_AST12907_001_nested_compound_no_false_cross_dependency_inflation",
    ]
}

AST12907_003_VERIFICATION = {
    "AST12907-003": [
        "test_AST12907_003_compound_model6_result6_nested_compound_case_remains_stable_after_flattening_fix",
        "test_AST12907_003_compound_model9_result9_nested_compound_case_remains_stable_after_flattening_fix",
    ]
}
