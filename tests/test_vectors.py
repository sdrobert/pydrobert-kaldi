"""Nosetests for SWIG vectors"""

from __future__ import division
from __future__ import print_function

import numpy

import pydrobert.kaldi._internal as internal

__author__ = "sdrobert"

def test_internal_set_data_valid():
    vec = internal.NumpyDoubleVector()
    vec.SetData([1, 2])
    vec.SetData(numpy.array([1., 2.], dtype=numpy.float32)) # upcast ok
    vec = internal.NumpyFloatVector()
    vec.SetData([1, 2])
    vec.SetData(numpy.array([1., 2.], dtype=numpy.float32))

def test_internal_set_data_invalid():
    vec = internal.NumpyFloatVector()
    for vals in 'ab', [[1]], numpy.array([1., 2.], dtype=numpy.float64):
        try:
            vec.SetData(vals)
            raise AssertionError('Could write "{}"'.format(vec))
        except TypeError:
            pass
        except ValueError:
            pass

def test_internal_read_data_valid():
    vec = internal.NumpyDoubleVector()
    vec.SetData([1] * 10)
    np = numpy.zeros(10, dtype=numpy.float64)
    assert vec.ReadDataInto(np)
    del vec
    assert numpy.allclose(np, 1)

def test_internal_read_data_invalid():
    vec = internal.NumpyFloatVector()
    vec.SetData([1] * 10)
    for vals in 'a', numpy.zeros(10, dtype=numpy.float64), \
            numpy.zeros(9, dtype=numpy.float32):
        try:
            assert not vec.ReadDataInto(vals)
        except TypeError:
            pass
        except ValueError:
            pass
