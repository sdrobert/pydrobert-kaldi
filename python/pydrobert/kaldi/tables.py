"""Interface for tables"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc

from contextlib import contextmanager
from enum import Enum # need enum34 for python 2.7

import numpy

from future.utils import implements_iterator
from six import with_metaclass

# we rename with an underscore so tab-completion isn't polluted with
# these
from ._internal import ExtNumpyDoubleMatrixWriter as _ExtNumpyDoubleMatrixWriter
from ._internal import ExtNumpyDoubleVectorWriter as _ExtNumpyDoubleVectorWriter
from ._internal import ExtNumpyFloatMatrixWriter as _ExtNumpyFloatMatrixWriter
from ._internal import ExtNumpyFloatVectorWriter as _ExtNumpyFloatVectorWriter
from ._internal import ExtRandomAccessNumpyDoubleMatrixReader as _ExtRandomAccessNumpyDoubleMatrixReader
from ._internal import ExtRandomAccessNumpyDoubleMatrixReaderMapped as _ExtRandomAccessNumpyDoubleMatrixReaderMapped
from ._internal import ExtRandomAccessNumpyDoubleVectorReader as _ExtRandomAccessNumpyDoubleVectorReader
from ._internal import ExtRandomAccessNumpyDoubleVectorReaderMapped as _ExtRandomAccessNumpyDoubleVectorReaderMapped
from ._internal import ExtRandomAccessNumpyFloatMatrixReader as _ExtRandomAccessNumpyFloatMatrixReader
from ._internal import ExtRandomAccessNumpyFloatMatrixReaderMapped as _ExtRandomAccessNumpyFloatMatrixReaderMapped
from ._internal import ExtRandomAccessNumpyFloatVectorReader as _ExtRandomAccessNumpyFloatVectorReader
from ._internal import ExtRandomAccessNumpyFloatVectorReaderMapped as _ExtRandomAccessNumpyFloatVectorReaderMapped
from ._internal import ExtSequentialNumpyDoubleMatrixReader as _ExtSequentialNumpyDoubleMatrixReader
from ._internal import ExtSequentialNumpyDoubleVectorReader as _ExtSequentialNumpyDoubleVectorReader
from ._internal import ExtSequentialNumpyFloatMatrixReader as _ExtSequentialNumpyFloatMatrixReader
from ._internal import ExtSequentialNumpyFloatVectorReader as _ExtSequentialNumpyFloatVectorReader
from ._internal import kDoubleIsBase as _kDoubleIsBase

__author__ = "sdrobert"

class KaldiDataType(Enum):
    """"""
    BaseVector = 'bv'
    DoubleVector = 'dv'
    FloatVector = 'fv'
    BaseMatrix = 'bm'
    DoubleMatrix = 'dm'
    FloatMatrix = 'fm'

    @property
    def is_matrix(self):
        """"""
        # str(.) is to keep pylint from complaining
        return 'm' in str(self.value)

    @property
    def is_double(self):
        """"""
        val = str(self.value)
        if 'b' in val:
            return _kDoubleIsBase
        else:
            return 'd' in val

class KaldiIO(with_metaclass(abc.ABCMeta)):
    """"""

    if _kDoubleIsBase:
        _BaseVector = KaldiDataType.DoubleVector
        _BaseMatrix = KaldiDataType.DoubleMatrix
    else:
        _BaseVector = KaldiDataType.FloatVector
        _BaseMatrix = KaldiDataType.FloatMatrix

    def __del__(self):
        self.close()

    def open(self, xfilename, kaldi_dtype, **kwargs):
        """"""
        kaldi_dtype = KaldiDataType(kaldi_dtype)
        if kaldi_dtype == KaldiDataType.BaseVector:
            kaldi_dtype = KaldiIO._BaseVector
        elif kaldi_dtype == KaldiDataType.BaseMatrix:
            kaldi_dtype = KaldiIO._BaseMatrix
        return self._open(xfilename, kaldi_dtype, **kwargs)

    @abc.abstractmethod
    def _open(self, xfilename, dtype, **kwargs):
        pass

    def close(self):
        """"""
        pass

@implements_iterator
class KaldiSequentialTableReader(KaldiIO):
    """"""

    def __init__(self, **kwargs):
        self._is_matrix = None
        self._numpy_dtype = None
        self._internal = None
        keys = list(kwargs)
        if 'xfilename' in keys and 'kaldi_dtype' in keys:
            self.open(kwargs['xfilename'], kwargs['kaldi_dtype'], **kwargs)

    def close(self):
        if self._internal:
            self._internal.Close()
            self._internal = None

    def _open(self, xfilename, kaldi_dtype, **kwargs):
        cls = None
        if kaldi_dtype == KaldiDataType.DoubleVector:
            cls = _ExtSequentialNumpyDoubleVectorReader
        elif kaldi_dtype == KaldiDataType.FloatVector:
            cls = _ExtSequentialNumpyFloatVectorReader
        elif kaldi_dtype == KaldiDataType.DoubleMatrix:
            cls = _ExtSequentialNumpyDoubleMatrixReader
        elif kaldi_dtype == KaldiDataType.FloatMatrix:
            cls = _ExtSequentialNumpyFloatMatrixReader
        assert cls
        instance = cls()
        if not instance.Open(xfilename):
            raise IOError(
                'Unable to open file "{}" for sequential '
                'read.'.format(xfilename))
        self._internal = instance
        self._is_matrix = kaldi_dtype.is_matrix
        if kaldi_dtype.is_double:
            self._numpy_dtype = numpy.dtype(numpy.float64)
        else:
            self._numpy_dtype = numpy.dtype(numpy.float32)

    def __iter__(self):
        if not self._internal:
            raise ValueError('I/O operation on a closed file')
        return self

    def __next__(self):
        if not self._internal:
            raise ValueError('I/O operation on a closed file')
        if self._internal.Done():
            raise StopIteration
        data_obj = self._internal.Value()
        ret = None
        if self._is_matrix:
            ret = numpy.empty(
                (data_obj.NumRows(), data_obj.NumCols()),
                dtype=self._numpy_dtype)
            data_obj.ReadDataInto(ret)
        else:
            ret = numpy.empty(data_obj.Dim(), dtype=self._numpy_dtype)
            data_obj.ReadDataInto(ret)
        self._internal.Next()
        return ret

class KaldiRandomAccessTableReader(KaldiIO):
    """"""

    def __init__(self, **kwargs):
        self._is_matrix = None
        self._numpy_dtype = None
        self._internal = None
        keys = list(kwargs)
        if 'xfilename' in keys and 'kaldi_dtype' in keys:
            self.open(kwargs['xfilename'], kwargs['kaldi_dtype'], **kwargs)

    def close(self):
        if self._internal:
            self._internal.Close()
            self._internal = None

    def _open(self, xfilename, kaldi_dtype, **kwargs):
        utt2spk = kwargs.get('utt2spk')
        cls = None
        if kaldi_dtype == KaldiDataType.DoubleVector:
            if utt2spk:
                cls = _ExtRandomAccessNumpyDoubleVectorReaderMapped
            else:
                cls = _ExtRandomAccessNumpyDoubleVectorReader
        elif kaldi_dtype == KaldiDataType.FloatVector:
            if utt2spk:
                cls = _ExtRandomAccessNumpyFloatVectorReaderMapped
            else:
                cls = _ExtRandomAccessNumpyFloatVectorReader
        elif kaldi_dtype == KaldiDataType.DoubleMatrix:
            if utt2spk:
                cls = _ExtRandomAccessNumpyDoubleMatrixReaderMapped
            else:
                cls = _ExtRandomAccessNumpyDoubleMatrixReader
        elif kaldi_dtype == KaldiDataType.FloatMatrix:
            if utt2spk:
                cls = _ExtRandomAccessNumpyFloatMatrixReaderMapped
            else:
                cls = _ExtRandomAccessNumpyFloatMatrixReader
        assert cls
        instance = cls()
        res = None
        if utt2spk:
            res = instance.Open(xfilename, utt2spk)
        else:
            res = instance.Open(xfilename)
        if not res:
            raise IOError(
                'Unable to open file "{}" for writing.'.format(xfilename))
        self._internal = instance
        self._is_matrix = kaldi_dtype.is_matrix
        if kaldi_dtype.is_double:
            self._numpy_dtype = numpy.dtype(numpy.float64)
        else:
            self._numpy_dtype = numpy.dtype(numpy.float32)

    def get(self, key, will_raise=False):
        """"""
        if not self._internal:
            raise ValueError('I/O operation on a closed file')
        if not self._internal.HasKey(key):
            if will_raise:
                raise KeyError(key)
            return None
        data_obj = self._internal.Value(key)
        ret = None
        if self._is_matrix:
            ret = numpy.empty(
                (data_obj.NumRows(), data_obj.NumCols()),
                dtype=self._numpy_dtype)
            data_obj.ReadDataInto(ret)
        else:
            ret = numpy.empty(data_obj.Dim(), dtype=self._numpy_dtype)
            data_obj.ReadDataInto(ret)
        return ret

    def __getitem__(self, key):
        return self.get(key, will_raise=True)

class KaldiTableWriter(KaldiIO):
    """"""

    def __init__(self, **kwargs):
        self._is_matrix = None
        self._numpy_dtype = None
        self._internal = None
        keys = list(kwargs)
        if 'xfilename' in keys and 'kaldi_dtype' in keys:
            self.open(kwargs['xfilename'], kwargs['kaldi_dtype'], **kwargs)

    def close(self):
        if self._internal:
            self._internal.Close()
            self._internal = None

    def _open(self, xfilename, kaldi_dtype, **kwargs):
        # no keyword arguments for table writer
        cls = None
        if kaldi_dtype == KaldiDataType.DoubleVector:
            cls = _ExtNumpyDoubleVectorWriter
        elif kaldi_dtype == KaldiDataType.FloatVector:
            cls = _ExtNumpyFloatVectorWriter
        elif kaldi_dtype == KaldiDataType.DoubleMatrix:
            cls = _ExtNumpyDoubleMatrixWriter
        elif kaldi_dtype == KaldiDataType.FloatMatrix:
            cls = _ExtNumpyFloatMatrixWriter
        assert cls
        instance = cls()
        if not instance.Open(xfilename):
            raise IOError(
                'Unable to open file "{}" for writing.'.format(xfilename))
        self._internal = instance
        self._is_matrix = kaldi_dtype.is_matrix
        if kaldi_dtype.is_double:
            self._numpy_dtype = numpy.dtype(numpy.float64)
        else:
            self._numpy_dtype = numpy.dtype(numpy.float32)

    def write(self, key, value):
        """"""
        if not self._internal:
            raise ValueError('I/O operation on a closed file')
        if self._is_matrix:
            # Kaldi only accepts 2D arrays which, if empty, must have
            # dimensions (0,0). Therefore we need to check for cases
            # like
            # - numpy.ones((0,1))
            # - [[]]
            # - []
            # while still avoiding
            # - [[[]]]
            # - numpy.ones((0,1,0))
            if isinstance(value, numpy.ndarray):
                if len(value.shape) <= 2 and not numpy.all(value.shape):
                    value = numpy.empty((0, 0), dtype=value.dtype)
            else:
                try:
                    if value is None or not len(value) or \
                            (len(value[0]) == 1 and not len(value[0])):
                        value = numpy.empty((0, 0), dtype=self._numpy_dtype)
                except TypeError:
                    raise ValueError('Expected 2D array-like')
        self._internal.WriteData(key, value)

@contextmanager
def open(xfilename, kaldi_dtype, **kwargs):
    """"""
    mode = kwargs.get('mode')
    if mode is None:
        mode = 'r'
    io_obj = None
    if mode == 'r':
        io_obj = KaldiSequentialTableReader()
    elif mode == 'r+':
        io_obj = KaldiRandomAccessTableReader()
    elif mode in ('w', 'w+'):
        io_obj = KaldiTableWriter()
    else:
        raise ValueError(
            'Invalid Kaldi I/O mode "{}" (should be one of "r","r+","w")'
            ''.format(mode))
    io_obj.open(xfilename, kaldi_dtype, **kwargs)
    yield io_obj
    io_obj.close()
