"""Interface for Kaldi's readers and writers

The README file has a good example of standard usage; using the `open`
generator should be enough for most. However, :class:`KaldiIO`
subclasses can be initialized directly for greater granularity.
"""

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
from ._internal import DoubleMatrixWriter as _DoubleMatrixWriter
from ._internal import DoubleVectorWriter as _DoubleVectorWriter
from ._internal import FloatMatrixWriter as _FloatMatrixWriter
from ._internal import FloatVectorWriter as _FloatVectorWriter
from ._internal import RandomAccessDoubleMatrixReader as _RandomAccessDoubleMatrixReader
from ._internal import RandomAccessDoubleMatrixReaderMapped as _RandomAccessDoubleMatrixReaderMapped
from ._internal import RandomAccessDoubleVectorReader as _RandomAccessDoubleVectorReader
from ._internal import RandomAccessDoubleVectorReaderMapped as _RandomAccessDoubleVectorReaderMapped
from ._internal import RandomAccessFloatMatrixReader as _RandomAccessFloatMatrixReader
from ._internal import RandomAccessFloatMatrixReaderMapped as _RandomAccessFloatMatrixReaderMapped
from ._internal import RandomAccessFloatVectorReader as _RandomAccessFloatVectorReader
from ._internal import RandomAccessFloatVectorReaderMapped as _RandomAccessFloatVectorReaderMapped
from ._internal import SequentialDoubleMatrixReader as _SequentialDoubleMatrixReader
from ._internal import SequentialDoubleVectorReader as _SequentialDoubleVectorReader
from ._internal import SequentialFloatMatrixReader as _SequentialFloatMatrixReader
from ._internal import SequentialFloatVectorReader as _SequentialFloatVectorReader
from ._internal import kDoubleIsBase as _kDoubleIsBase

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2016 Sean Robertson"

class KaldiDataType(Enum):
    """Indicates the data type an archive stores. Values for `kaldi_dtype`

    Whenever `kaldi_dtype` is an argument to a method or function in
    `tables`, one of these attributes can be passed directly via
    ``KaldiDataType.XXX`, or by its :class:`str` form, e.g. ``'bv'``.

    Attributes:
        +----------------+------------+-------------+-----------------+
        | Attribute Name | String Rep | Numpy shape | Float precision |
        +================+============+=============+=================+
        | `BaseVector`   | ``'bv'``   | (X,)        | Kaldi default   |
        +----------------+------------+-------------+-----------------+
        | `DoubleVector` | ``'dv'``   | (X,)        | 64-bit          |
        +----------------+------------+-------------+-----------------+
        | `FloatVector`  | ``'fv'``   | (X,)        | 32-bit          |
        +----------------+------------+-------------+-----------------+
        | `BaseMatrix`   | ``'bm'``   | (X,X)       | Kaldi default   |
        +----------------+------------+-------------+-----------------+
        | `DoubleMatrix` | ``'dm'``   | (X,X)       | 64-bit          |
        +----------------+------------+-------------+-----------------+
        | `FloatMatrix`  | ``'fm'``   | (X,X)       | 32-bit          |
        +----------------+------------+-------------+-----------------+
    """
    BaseVector = 'bv'
    DoubleVector = 'dv'
    FloatVector = 'fv'
    BaseMatrix = 'bm'
    DoubleMatrix = 'dm'
    FloatMatrix = 'fm'

    @property
    def is_matrix(self):
        # str(.) is to keep pylint from complaining
        return 'm' in str(self.value)

    @property
    def is_double(self):
        """bool: Returns ``True`` if 64-bit floating point"""
        val = str(self.value)
        if 'b' in val:
            return _kDoubleIsBase
        else:
            return 'd' in val

class KaldiIO(with_metaclass(abc.ABCMeta)):
    """Base class for interacting with Kaldi scripts/archives

    :class:`KaldiIO` subclasses all contain `open` and `close` methods.
    Additional methods depend on the subclass, but in general have
    either read- or write-like methods, depending on whether they are
    reading or writing the archives. These methods accept or return
    :class:`numpy.ndarray` objects with floating-point entries.
    `Kaldi I/O Mechanisms`_ describes how Kaldi uses extended file names
    and tables and such.

    Note:
        Subclasses can be initialized without arguments or with the same
        arguments as `open` to open a file immediately.

    Warning:
        It is possible to raise one of Kaldi's runtime errors when using
        these subclasses. You should consult Kaldi's output to stderr to
        figure out what went wrong. Hopefully the error will be wrapped
        in Python's :class:`RuntimeError` rather than causing a
        segfault.

    .. _Kaldi I/O Mechanisms:
        http://kaldi-asr.org/doc2/io.html
    """

    if _kDoubleIsBase:
        _BaseVector = KaldiDataType.DoubleVector
        _BaseMatrix = KaldiDataType.DoubleMatrix
    else:
        _BaseVector = KaldiDataType.FloatVector
        _BaseMatrix = KaldiDataType.FloatMatrix

    def __del__(self):
        self.close()

    def open(self, xfilename, kaldi_dtype, **kwargs):
        """Open a Kaldi script or archive

        Args:
            xfilename(str): An extended file name to open. Whether this
                is a `wxfilename` or `rxfilename` depends on the
                subclass. This can be an archive or script file.
            kaldi_dtype(KaldiDataType): What kaldi data type is/will be
                stored. All array-likes written or read are expected to
                be of this type.
            utt2spk(Optional[str]): Applicable to
                :class:`KaldiRandomAccessTableReader`, setting this
                opens a `RandomAccessTableReaderMapped`_ and with
                `utt2spk_rxfilename` set to this.

        Raises:
            IOError: If the arhive or script cannot be opened, but does
                not cause a :class:`RuntimeError`.

        ..seealso:: :class:`KaldiDataType`
        .. _mapped form:
            http://kaldi-asr.org/doc2/classkaldi_1_1RandomAccessTableReaderMapped.html
        """
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
        """Closes the `KaldiIO` object, or does nothing if not opened

        This happens automatically when this object is destroyed.
        """
        pass

@implements_iterator
class KaldiSequentialTableReader(KaldiIO):
    """Read a Kaldi script/archive as an iterable"""

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
            cls = _SequentialDoubleVectorReader
        elif kaldi_dtype == KaldiDataType.FloatVector:
            cls = _SequentialFloatVectorReader
        elif kaldi_dtype == KaldiDataType.DoubleMatrix:
            cls = _SequentialDoubleMatrixReader
        elif kaldi_dtype == KaldiDataType.FloatMatrix:
            cls = _SequentialFloatMatrixReader
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
    """Read a Kaldi archive/script like a dictionary with string keys"""

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
                cls = _RandomAccessDoubleVectorReaderMapped
            else:
                cls = _RandomAccessDoubleVectorReader
        elif kaldi_dtype == KaldiDataType.FloatVector:
            if utt2spk:
                cls = _RandomAccessFloatVectorReaderMapped
            else:
                cls = _RandomAccessFloatVectorReader
        elif kaldi_dtype == KaldiDataType.DoubleMatrix:
            if utt2spk:
                cls = _RandomAccessDoubleMatrixReaderMapped
            else:
                cls = _RandomAccessDoubleMatrixReader
        elif kaldi_dtype == KaldiDataType.FloatMatrix:
            if utt2spk:
                cls = _RandomAccessFloatMatrixReaderMapped
            else:
                cls = _RandomAccessFloatMatrixReader
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
        """Get data indexed by key

        Args:
            key(str): Key which data is mapped to in archive
            will_raise(Optional[bool]): Whether to raise a
                :class:`KeyError`. If the key is not found. Defaults to
                ``False``.

        Returns:
            :class:`numpy.ndarray` associated with key if present,
            ``None`` if the key is absent and `will_raise` is set to
            ``False``

        Raises:
            ValueError: If object is closed
            KeyError: If `key` is not present in script/archive and
                `will_raise` is set to ``True``.

        Examples:
            >>> reader.get('foo') # (1)
            >>> reader.get('foo', will_raise=True) # (2)
            >>> reader['foo'] # equivalent to (2)
        """
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
    """Write to key/data combinations sequentially to a Kaldi script/archive"""

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
            cls = _DoubleVectorWriter
        elif kaldi_dtype == KaldiDataType.FloatVector:
            cls = _FloatVectorWriter
        elif kaldi_dtype == KaldiDataType.DoubleMatrix:
            cls = _DoubleMatrixWriter
        elif kaldi_dtype == KaldiDataType.FloatMatrix:
            cls = _FloatMatrixWriter
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
        """Write key/value pair to script/archive

        Args:
            key(str):
            value(array-like):

        Raises:
            ValueError: Operating on closed file, or `value` cannot be
                cast to the `kaldi_dtype` specified when this object
                was opened
            TypeError: If casting the 1value`, already a
                :class:`numpy.ndarray` to the `kaldi_dtype`

        Warning:
            There are two situations where the array-like written may
            not match whatever will be read from the script/archive in
            the future. First, in the case of a matrix `kaldi_dtype`,
            Kaldi does not accept arrays of shape (0,X) or (X,0), where
            X > 0, nor does it accept the shape (0,). This method
            automatically converts all such input to a matrix of shape
            (0,0). Second, any array-like which is not a
            :class:`numpy.ndarray` will be cast to one in the numpy
            style. This does not guard against overflow, underflow, or
            loss of precision.
        """
        if not self._internal:
            raise ValueError('I/O operation on a closed file')
        if self._is_matrix:
            # check for perverse shapes of empty arrays
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
    """:class:`KaldiIO` subclass generator for use with ``with`` statements

    Args:
        xfilename(str):
        kaldi_dtype(KaldiDataType):
        utt2spk(Optional[str]):
        mode(Optional[str]): One of "r", "r+", and "w", which generate
            a :class:`KaldiSequentialTableReader`,
            a :class:`KaldiRandomAccessTableReader`, and a
            :class:`KaldiTableWriter` respectively.

    Yields:
        A :class:`KaldiIO` subclass

    Raises:
        IOError:

    ..seealso:: :class:`KaldiIO`
    """
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
    try:
        yield io_obj
    finally:
        io_obj.close()
