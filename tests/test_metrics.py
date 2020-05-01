# License: BSD 3 clause
"""
Module for running a bunch of simple unit tests. Should be expanded more in
the future.

:author: Michael Heilman (mheilman@ets.org)
:author: Nitin Madnani (nmadnani@ets.org)
:author: Dan Blanchard (dblanchard@ets.org)
:author: Aoife Cahill (acahill@ets.org)
"""

import os

from os.path import abspath, dirname, exists, join

from nose.tools import raises
from numpy.testing import assert_almost_equal

from skll.utils.constants import KNOWN_DEFAULT_PARAM_GRIDS
from skll.metrics import kappa

_ALL_MODELS = list(KNOWN_DEFAULT_PARAM_GRIDS.keys())

# Inputs derived from Ben Hamner's unit tests for his
# kappa implementation as part of the ASAP competition
_KAPPA_INPUTS = [([1, 2, 3], [1, 2, 3]),
                 ([1, 2, 1], [1, 2, 2]),
                 ([1, 2, 3, 1, 2, 2, 3], [1, 2, 3, 1, 2, 3, 2]),
                 ([1, 2, 3, 3, 2, 1], [1, 1, 1, 2, 2, 2]),
                 ([-1, 0, 1, 2], [-1, 0, 0, 2]),
                 ([5, 6, 7, 8], [5, 6, 6, 8]),
                 ([1, 1, 2, 2], [3, 3, 4, 4]),
                 ([1, 1, 3, 3], [2, 2, 4, 4]),
                 ([1, 1, 4, 4], [2, 2, 3, 3]),
                 ([1, 2, 4], [1, 2, 4]),
                 ([1, 2, 4], [1, 2, 2])]

_my_dir = abspath(dirname(__file__))


def setup():
    """
    Create necessary directories for testing.
    """
    train_dir = join(_my_dir, 'train')
    if not exists(train_dir):
        os.makedirs(train_dir)
    test_dir = join(_my_dir, 'test')
    if not exists(test_dir):
        os.makedirs(test_dir)
    output_dir = join(_my_dir, 'output')
    if not exists(output_dir):
        os.makedirs(output_dir)


def check_kappa(y_true, y_pred, weights, allow_off_by_one, expected):
    assert_almost_equal(kappa(y_true, y_pred, weights=weights,
                              allow_off_by_one=allow_off_by_one), expected)


def test_quadratic_weighted_kappa():
    outputs = [1.0, 0.4, 0.75, 0.0, 0.9, 0.9, 0.11111111, 0.6666666666667, 0.6,
               1.0, 0.4]

    for (y_true, y_pred), expected in zip(_KAPPA_INPUTS, outputs):
        yield check_kappa, y_true, y_pred, 'quadratic', False, expected

    # Swap y_true and y_pred and test again
    for (y_pred, y_true), expected in zip(_KAPPA_INPUTS, outputs):
        yield check_kappa, y_true, y_pred, 'quadratic', False, expected


def test_allow_off_by_one_qwk():
    outputs = [1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.3333333333333333, 1.0, 1.0,
               1.0, 0.5]

    for (y_true, y_pred), expected in zip(_KAPPA_INPUTS, outputs):
        yield check_kappa, y_true, y_pred, 'quadratic', True, expected

    # Swap y_true and y_pred and test again
    for (y_pred, y_true), expected in zip(_KAPPA_INPUTS, outputs):
        yield check_kappa, y_true, y_pred, 'quadratic', True, expected


def test_linear_weighted_kappa():
    outputs = [1.0, 0.4, 0.65, 0.0, 0.8, 0.8, 0.0, 0.3333333, 0.3333333, 1.0,
               0.4]

    for (y_true, y_pred), expected in zip(_KAPPA_INPUTS, outputs):
        yield check_kappa, y_true, y_pred, 'linear', False, expected

    # Swap y_true and y_pred and test again
    for (y_pred, y_true), expected in zip(_KAPPA_INPUTS, outputs):
        yield check_kappa, y_true, y_pred, 'linear', False, expected


def test_unweighted_kappa():
    outputs = [1.0, 0.4, 0.5625, 0.0, 0.6666666666667, 0.6666666666667,
               0.0, 0.0, 0.0, 1.0, 0.5]

    for (y_true, y_pred), expected in zip(_KAPPA_INPUTS, outputs):
        yield check_kappa, y_true, y_pred, None, False, expected

    # Swap y_true and y_pred and test again
    for (y_pred, y_true), expected in zip(_KAPPA_INPUTS, outputs):
        yield check_kappa, y_true, y_pred, None, False, expected


@raises(ValueError)
def test_invalid_weighted_kappa():
    kappa([1, 2, 1], [1, 2, 1], weights='invalid', allow_off_by_one=False)
    kappa([1, 2, 1], [1, 2, 1], weights='invalid', allow_off_by_one=True)


@raises(ValueError)
def test_invalid_lists_kappa():
    kappa(['a', 'b', 'c'], ['a', 'b', 'c'])
