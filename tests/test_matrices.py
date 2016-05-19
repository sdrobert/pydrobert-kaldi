"""Nosetests for SWIG matrices"""

from __future__ import division
from __future__ import print_function

import numpy

import pydrobert.kaldi._internal as internal

__author__ = "sdrobert"

def test_internal_set_data_valid():
    matr = internal.NumpyDoubleMatrix()
    matr.SetData([[1, 2], [3, 4]])
    matr.SetData(numpy.empty((1000, 10), dtype=numpy.float32))
    matr = internal.NumpyFloatMatrix()
    matr.SetData(numpy.ones((1, 100), dtype=numpy.float32))
    # note that we must pass data in two dimensions or else numpy.i
    # will freak. We'll do these simple checks in the wrapper
    matr.SetData([[]])

def test_internal_set_data_invalid():
    matr = internal.NumpyFloatMatrix()
    for vals in ['ab', 'cd'], [1], numpy.empty((10,10), dtype=numpy.float64):
        try:
            matr.SetData(vals)
            raise AssertionError('Could write "{}"'.format(matr))
        except TypeError:
            pass
        except ValueError:
            pass

def test_internal_read_data_valid():
    matr = internal.NumpyFloatMatrix()
    matr.SetData(numpy.ones((100, 1000), dtype=numpy.float32))
    np = numpy.zeros((100, 1000), dtype=numpy.float32)
    assert matr.ReadDataInto(np)
    del matr
    assert numpy.allclose(np, 1)

def test_internal_read_data_invalid():
    matr = internal.NumpyDoubleMatrix()
    matr.SetData(numpy.empty((10, 10), dtype=numpy.float64))
    for vals in [['a'] * 10] * 10, [[1] * 9] * 10, [1] * 100:
        try:
            assert not matr.ReadDataInto(vals)
        except TypeError:
            pass
        except ValueError:
            pass
