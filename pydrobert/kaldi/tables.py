# Copyright 2016 Sean Robertson

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Interfaces for Kaldi's readers and writers

Kaldi uses the table analogy to store and retrieve data.  In a nutshell,
Kaldi uses archive ("ark") files to store binary or text data, and
script files ("scp") to point *into* archives. Both use whitespace-free
strings as keys. Scripts and archives do not have any built-in type
checking, so it is necessary to specify the input/output type when the
files are opened. A full account can be found on Kaldi's website
under `Kaldi I/O Mechanisms`_.

This module contains a factory function, `open`, which is intended to
behave similarly to python's built-in `open` factory. `open` describes
what parameters are relevant to different table types.

For a description of the table types which can be read/written by Kaldi,
please consult `KaldiDataTypes`.

Examples
--------

>>> import pydrobert.kaldi.tables as tables
>>> import numpy as np
>>> # write a script/archive pair of matrices
>>> with tables.open('ark,scp:foo.ark,bar.scp', 'dm', mode='w') as t:
>>>    t.write('yo', np.random.random((100, 1000)))
>>>    t.write('dog', [[1, 2], [3, 4]])
>>> # read the archive sequentially
>>> with tables.open('ark:foo.ark', 'bv') as t:
>>>    for matrix in t:
>>>        pass # do something ...
>>> # read a script file that points to matrices with random access
>>> with tables.open('scp:bar.scp', 'dm', mode='r+') as t:
>>>    t['dog']
>>>    t['yo']

.. _Kaldi I/O Mechanisms: http://kaldi-asr.org/doc2/io.html
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc

from collections import Container
from collections import Iterator
from enum import Enum # need enum34 for python 2.7

from future.utils import implements_iterator
from six import with_metaclass

from . import _internal as _i

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2016 Sean Robertson"

class KaldiDataType(Enum):
    """Enumerates the data types stored and retrieved by Kaldi tables

    This enumerable lists the types of data written and read to various
    tables. It is used in the factory method `open` to dictate the
    subclass created.

    Notes
    -----
    The "base float" mentioned in this documentation is the same type as
    ``kaldi::BaseFloat`, which was determined when Kaldi was built. The
    easiest way to determine whether this is a double (64bit) or a float
    (32bit) is by checking the value of
    `KaldiDataType.BaseVector.is_double`.
    """

    BaseVector = 'bv'
    """Inputs/outputs are 1D numpy arrays of the base float"""

    DoubleVector = 'dv'
    """Inputs/outputs are 1D numpy arrays of 64-bit floats"""

    FloatVector = 'fv'
    """Inputs/outputs are 1D numpy arrays of 32-bit floats"""

    BaseMatrix = 'bm'
    """Inputs/outputs are 2D numpy arrays of the base float"""

    DoubleMatrix = 'dm'
    """Inputs/outputs are 2D numpy arrays of 64-bit floats"""

    FloatMatrix = 'fm'
    """Inputs/outputs are 2D numpy arrays of 32-bit floats"""

    WaveMatrix = 'wm'
    """Inputs/outputs are wave file data, cast to base float 2D arrays

    Wave matrices have the shape `(n_channels, n_samples)`. Kaldi will
    read PCM wave files, but will always convert the samples the base
    floats.

    Though Kaldi can read wave files of different types and sample
    rates, Kaldi will only write wave files as PCM16 sampled at 16k.
    """

    Token = 't'
    """Inputs/outputs are individual whitespace-free ASCII or unicode words"""

    TokenVector = 'tv'
    """Inputs/outputs are tuples of tokens"""

    @property
    def is_matrix(self):
        """bool : whether this type is a matrix type"""
        return str(self.value) in ('bm', 'dm', 'fm', 'wm')

    @property
    def is_floating_point(self):
        """bool : whether this type has a floating point representation"""
        return str(self.value) in ('bv', 'fv', 'dv', 'bm', 'fm', 'dm', 'wm')

    @property
    def is_double(self):
        '''bool: whether this data type is double precision (64-bit)'''
        if str(self.value) in ('bv', 'bm', 'wm'):
            return _i.kDoubleIsBase
        elif str(self.value) in ('dv', 'dm'):
            return True
        else:
            return False

class KaldiTable(object, with_metaclass(abc.ABCMeta)):
    """Base class for interacting with tables

    All table readers and writers are subclasses of `KaldiTable`. They
    are opened on initialization through the factory function `open`,
    and can be closed at any time with the `close` method.

    Parameters
    ----------
    xfilename : str

    Attributes
    ----------
    kaldi_dtype

    Raises
    ------
    IOError
        If unable to open table
    SystemError
        Kaldi errors are wrapped as `SystemError`s
    """

    def __init__(self, xfilename, **kwargs):
        self._open(xfilename, **kwargs)
        super(KaldiTable, self).__init__()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_val, trace):
        self.close()

    def __del__(self):
        self.close()

    @abc.abstractproperty
    def kaldi_dtype(self):
        """KaldiDataType or None: The open table's data type"""
        pass

    @abc.abstractmethod
    def close(self):
        """Close the kaldi script or archive (if open)"""
        pass

    @abc.abstractmethod
    def _open(self, xfilename, **kwargs):
        pass

@implements_iterator
class KaldiSequentialReader(KaldiTable, Iterator):
    """Abstract class for iterating over table entries

    `KaldiSequentialReader` instances are essentially iterators over
    key-value pairs. The default behaviour (i.e. that in a for-loop) is
    to iterate over the values in order of access. Similar to `dict`
    instances, `items`, `values`, and `keys` return iterators over their
    respective domains. Alternatively, the `move` method moves to the
    next pair, at which point the `key` and `value` properties can be
    queried.

    Though it is possible to mix and match access patterns, all methods
    refer to the same underlying iterator (this).

    Parameters
    ----------
    xfilename : str

    Attributes
    ----------
    kaldi_dtype
    key
    value
    done

    Raises
    ------
    IOError
    SystemError
    """

    # implementation note: subclasses are expected to implement _open,
    # which should:
    # - open an instance of a pydrobert.kaldi._internal sequential
    #   reader, raise IOError on fail
    # - set self._internal to instance
    # - set self._kaldi_dtype

    def __init__(self, xfilename, **kwargs):
        self._iterator_type = 0
        self._internal = None
        self._kaldi_dtype = None
        super(KaldiSequentialReader, self).__init__(xfilename, **kwargs)

    @property
    def kaldi_dtype(self):
        return self._kaldi_dtype

    @property
    def key(self):
        """str: return current pair's key, or `None` if done or closed"""
        if not self.done:
            return self._internal.Key()
        return None

    @property
    def value(self):
        """return current pair's value, or `None` if done or closed"""
        if not self.done:
            return self._internal.Value()
        return None

    @property
    def done(self):
        """bool: `True` when unopened or pairs are exhausted"""
        return not self._internal or self._internal.Done()

    def close(self):
        if self._internal:
            self._internal.Close()
            self._internal = None
            self._kaldi_dtype = None

    def move(self):
        """Move iterator forward

        Returns
        -------
        bool
            `True` if moved to new pair. `False` if done (pairs
            exhausted)

        Raises
        ------
        IOError
            Reader unopened
        """
        if not self._internal:
            raise IOError('I/O operation on a closed table')
        if self.done:
            return False
        self._internal.Next()

    def keys(self):
        """Returns iterator over keys"""
        self._iterator_type = 1
        return self

    def values(self):
        """Returns iterator over values"""
        self._iterator_type = 0
        return self

    def items(self):
        """Returns iterator over key, value pairs"""
        self._iterator_type = 2
        return self

    def __next__(self):
        if self.done:
            raise StopIteration
        ret = None
        if self._iterator_type == 2:
            ret = self.key, self.value
        elif self._iterator_type == 1:
            ret = self.key
        else:
            ret = self.value
        self.move()
        return ret

class KaldiRandomAccessReader(KaldiTable, Container):
    """Read-only access to values of table by key

    `KaldiRandomAccessReader` objects can access values of a table
    through either the `get` method or square bracket access (e.g.
    ``a[key]`). The presence of a key can be checked with "in" syntax
    (e.g. `key in a`). Unlike a `dict`, the extent of a
    `KaldiRandomAccessReader` is not known beforehand, so neither
    iterators nor length methods are implemented.

    Parameters
    ----------
    xfilename : str
    utt2spk : str, optional
        If set, the reader uses `utt2spk` as a map from utterance ids to
        speaker ids. The data in `xfilename`, which are assumed to be
        referenced by speaker ids, can then be refrenced by utterance.
        If `utt2spk` is unspecified, the keys in `xfilename` are used to
        query for data.

    Attributes
    ----------
    kaldi_dtype

    Raises
    ------
    IOError
    SystemError
    """

    def __init__(self, xfilename, **kwargs):
        self._internal = None
        self._kaldi_dtype = None
        super(KaldiRandomAccessReader, self).__init__(xfilename, **kwargs)

    def __contains__(self, key):
        if not self._internal:
            raise IOError('I/O operation on a closed table')
        return self._internal.HasKey(key)

    def __getitem__(self, key):
        if not self._internal:
            raise IOError('I/O operation on a closed table')
        if key not in self:
            raise KeyError(key)
        return self._internal.Value(key)

    def get(self, key, default=None):
        """D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None."""
        try:
            return self[key]
        except KeyError:
            return default

    @property
    def kaldi_dtype(self):
        return self._kaldi_dtype

    def close(self):
        if self._internal:
            self._internal.Close()
            self._internal = None
            self._kaldi_dtype = None

class KaldiWriter(KaldiTable):
    """Write key-value pairs to tables

    Parameters
    ----------
    xfilename : str

    Attributes
    ----------
    kaldi_dtype

    Raises
    ------
    IOError
    SystemError
    """

    def __init__(self, xfilename, **kwargs):
        self._internal = None
        self._kaldi_dtype = None
        super(KaldiWriter, self).__init__(xfilename, **kwargs)

    def write(self, key, value):
        """Write key value pair

        Parameters
        ----------
        key: str
        value

        Notes
        -----
        For Kaldi's table writers, pairs are written in order without
        backtracking. Uniqueness is not checked.
        """
        if not self._internal:
            raise IOError('I/O operation on a closed table')
        self._internal.Write(key, value)

    @property
    def kaldi_dtype(self):
        return self._kaldi_dtype

    def close(self):
        if self._internal:
            self._internal.Close()
            self._internal = None
            self._kaldi_dtype = None

class _KaldiSequentialSimpleReader(KaldiSequentialReader):
    __doc__ = KaldiSequentialReader.__doc__

    def __init__(self, xfilename, **kwargs):
        self._dtype_to_cls = {
            'bm' : _i.SequentialDoubleMatrixReader \
                if _i.kDoubleIsBase else _i.SequentialFloatMatrixReader,
            'bv' : _i.SequentialDoubleVectorReader \
                if _i.kDoubleIsBase else _i.SequentialFloatVectorReader,
            'dm' : _i.SequentialDoubleMatrixReader,
            'dv' : _i.SequentialDoubleVectorReader,
            'fm' : _i.SequentialDoubleMatrixReader,
            'fv' : _i.SequentialDoubleVectorReader,
            't' : _i.SequentialTokenReader,
            'tv' : _i.SequentialTokenVectorReader,
        }
        super(_KaldiSequentialSimpleReader, self).__init__(xfilename, **kwargs)

    def _open(self, xfilename, **kwargs):
        kaldi_dtype = kwargs.pop('kaldi_dtype', KaldiDataType.BaseVector)
        if len(kwargs):
            raise TypeError(
                "open() got an unexpected keyword argument '{}'"
                "".format(kwargs.popitem()[0])
            )
        try:
            instance = self._dtype_to_cls[kaldi_dtype.value]()
        except KeyError:
            raise TypeError('"{}" is not a KaldiDataType'.format(kaldi_dtype))
        if not instance.Open(xfilename):
            raise IOError('Unable to open for sequential read')
        self._internal = instance
        self._kaldi_dtype = kaldi_dtype

class _KaldiRandomAccessSimpleReader(KaldiRandomAccessReader):
    __doc__ = KaldiRandomAccessReader.__doc__

    def __init__(self, xfilename, **kwargs):
        self._dtype_to_cls = {
            'bm' : _i.RandomAccessDoubleMatrixReader \
                if _i.kDoubleIsBase else _i.RandomAccessFloatMatrixReader,
            'bv' : _i.RandomAccessDoubleVectorReader \
                if _i.kDoubleIsBase else _i.RandomAccessFloatVectorReader,
            'dm' : _i.RandomAccessDoubleMatrixReader,
            'dv' : _i.RandomAccessDoubleVectorReader,
            'fm' : _i.RandomAccessFloatMatrixReader,
            'fv' : _i.RandomAccessFloatVectorReader,
            't' : _i.RandomAccessTokenReader,
            'tv' : _i.RandomAccessTokenVectorReader,
        }
        super(_KaldiRandomAccessSimpleReader, self).__init__(
            xfilename, **kwargs)

    def _open(self, xfilename, **kwargs):
        kaldi_dtype = kwargs.pop('kaldi_dtype', KaldiDataType.BaseVector)
        utt2spk = kwargs.pop('utt2spk', '')
        if len(kwargs):
            raise TypeError(
                "open() got an unexpected keyword argument '{}'"
                "".format(kwargs.popitem()[0])
            )
        try:
            instance = self._dtype_to_cls[kaldi_dtype.value]()
        except KeyError:
            raise TypeError('"{}" is not a KaldiDataType'.format(kaldi_dtype))
        if not instance.Open(xfilename, utt2spk):
            raise IOError('Unable to open for random access read')
        self._internal = instance
        self._kaldi_dtype = kaldi_dtype

class _KaldiSimpleWriter(KaldiWriter):
    __doc__ = KaldiWriter.__doc__

    def __init__(self, xfilename, **kwargs):
        self._dtype_to_cls = {
            'bm' : _i.DoubleMatrixWriter \
                if _i.kDoubleIsBase else _i.FloatMatrixWriter,
            'bv' : _i.DoubleVectorWriter \
                if _i.kDoubleIsBase else _i.FloatVectorWriter,
            'dm' : _i.DoubleMatrixWriter,
            'dv' : _i.DoubleVectorWriter,
            'fm' : _i.FloatMatrixWriter,
            'fv' : _i.FloatVectorWriter,
            't' : _i.TokenWriter,
            'wm' : _i.WaveWriter,
        }
        super(_KaldiSimpleWriter, self).__init__(xfilename, **kwargs)

    def _open(self, xfilename, **kwargs):
        kaldi_dtype = kwargs.pop('kaldi_dtype', KaldiDataType.BaseVector)
        if len(kwargs):
            raise TypeError(
                "open() got an unexpected keyword argument '{}'"
                "".format(kwargs.popitem()[0])
            )
        try:
            instance = self._dtype_to_cls[kaldi_dtype.value]()
        except KeyError:
            raise TypeError('"{}" is not a KaldiDataType'.format(kaldi_dtype))
        if not instance.Open(xfilename):
            raise IOError('Unable to open for write')
        self._internal = instance
        self._kaldi_dtype = kaldi_dtype

class _KaldiSequentialWaveReader(KaldiSequentialReader):
    __doc__ = KaldiSequentialReader.__doc__

    def __init__(self, xfilename, **kwargs):
        self._value_style = None
        # lambdas b/c internal not yet set
        self._value_map = {
            'b' : lambda: self._internal.Value(),
            's' : lambda: self._internal.SampFreq(),
            'd' : lambda: self._internal.Duration(),
        }
        super(_KaldiSequentialWaveReader, self).__init__(xfilename, **kwargs)

    @property
    def value(self):
        if self._internal and not self._internal.Done():
            ret = tuple(self._value_map[key]() for key in self._value_style)
            if len(ret) == 1:
                return ret[0]
            else:
                return ret
        return None

    def _open(self, xfilename, **kwargs):
        value_style = kwargs.pop('value_style', 'b')
        if len(kwargs):
            raise TypeError(
                "open() got an unexpected keyword argument '{}'"
                "".format(kwargs.popitem()[0])
            )
        if not value_style:
            raise ValueError('value_style must be a non-empty string')
        for char in value_style:
            if char not in 'bsd':
                raise ValueError(
                    '"{}" in value_style must be one of "b","s","d"'
                    ''.format(char)
                )
        instance = None
        if 'b' in value_style:
            instance = _i.SequentialWaveReader()
        else:
            instance = _i.SequentialWaveInfoReader()
        if not instance.Open(xfilename):
            raise IOError('Unable to open for sequential read')
        self._kaldi_dtype = KaldiDataType.WaveMatrix
        self._internal = instance
        self._value_style = value_style

class _KaldiRandomAccessWaveReader(KaldiRandomAccessReader):
    __doc__ = KaldiRandomAccessReader.__doc__

    def __init__(self, xfilename, **kwargs):
        self._value_style = None
        self._value_map = {
            'b' : lambda: self._internal.Value(),
            's' : lambda: self._internal.SampFreq(),
            'd' : lambda: self._internal.Duration(),
        }
        super(_KaldiRandomAccessWaveReader, self).__init__(xfilename, **kwargs)

    def __getitem__(self, key):
        if not self._internal:
            raise IOError('I/O operation on a closed table')
        if key not in self:
            raise KeyError(key)
        ret = tuple(self._value_map[key]() for key in self._value_style)
        if len(ret) == 1:
            return ret[0]
        else:
            return ret

    def _open(self, xfilename, **kwargs):
        value_style = kwargs.pop('value_style', 'b')
        if len(kwargs):
            raise TypeError(
                "open() got an unexpected keyword argument '{}'"
                "".format(kwargs.popitem()[0])
            )
        if not value_style:
            raise ValueError('value_style must be a non-empty string')
        for char in str(value_style):
            if char not in 'bsd':
                raise ValueError(
                    '"{}" in value_style must be one of "b","s","d"'
                    ''.format(char)
                )
        instance = None
        if 'b' in value_style:
            instance = _i.RandomAccessWaveReader()
        else:
            instance = _i.RandomAccessWaveInfoReader()
        if not instance.Open(xfilename):
            raise IOError('Unable to open for random access read')
        self._kaldi_dtype = KaldiDataType.WaveMatrix
        self._internal = instance
        self._value_style = value_style

class _KaldiTokenVectorWriter(KaldiWriter):
    __doc__ = KaldiWriter.__doc__

    def __init__(self, xfilename, **kwargs):
        self._error_on_str = None
        super(_KaldiTokenVectorWriter, self).__init__(xfilename, **kwargs)

    def _open(self, xfilename, **kwargs):
        error_on_str = kwargs.pop('error_on_str', True)
        if len(kwargs):
            raise TypeError(
                "open() got an unexpected keyword argument '{}'"
                "".format(kwargs.popitem()[0])
            )
        instance = _i.TokenVectorWriter()
        if not instance.Open(xfilename):
            raise IOError('Unable to open for random access read')
        self._kaldi_dtype = KaldiDataType.WaveMatrix
        self._internal = instance
        self._error_on_str = error_on_str

    def write(self, key, value):
        if not self._internal:
            raise IOError('I/O operation on a closed file')
        if isinstance(value, str):
            raise ValueError(
                'Expected list of tokens, got string. If you want '
                'to treat strings as lists of character-wide tokens, '
                'set error_on_str to False when opening')
        self._internal.Write(key, value)

def open(xfilename, kaldi_dtype, mode='r', **kwargs):
    """Factory function for initializing and opening tables

    This function finds the correct `KaldiTable` according to the args
    `kaldi_dtype` and `mode`. Specific combinations allow for optional
    parameters outlined by the table below

    +------+-------------+=====================+
    | mode | kaldi_dtype | additional kwargs   |
    +======+=============+=====================+
    |`'r'` | `'wm'`      | `value_style='b'`   |
    +------+-------------+---------------------+
    |`'r+'`| *           | `utt2spk=''`        |
    +------+-------------+---------------------+
    |`'r+'`| `'wm'`      | `value_style='b'`   |
    +------+-------------+---------------------+
    |`'w'` | `'tv'`      | `error_on_str=True` |
    +------+-------------+---------------------+

    Parameters
    ----------
    xfilename : str
        The "extended file name" used by kaldi to open the script.
        Generally these will take the form `"{ark|scp}:<path_to_file>"`,
        though they can take much more interesting forms (like pipes).
        More information can be found on the `Kaldi website
        <http://kaldi-asr.org/doc2/io.html>`_.
    kaldi_dtype : KaldiDataType
        The type of data the table is expected to handle.
    mode : {'r', 'r+', 'w'}, optional
        Specifies the type of access to be performed: read sequential,
        read random, or write. They are implemented by subclasses of
        `KaldiSequentialReader`, `KaldiRandomAccessReader`, or
        `KaldiWriter`, resp. Defaults to `'r'`.
    error_on_str : bool, optional
        Token vectors (`'tv'`) accept sequences of whitespace-free
        ASCII/UTF strings. A `str` is also a sequence of characters,
        which may satisfy the token requirements. If
        `error_on_str=True`, a `ValueError` is raised when writing a
        `str` as a token vector. Otherwise a `str` can be written.
        Defaults to `True`.
    utt2spk : str, optional
        If set, the reader uses `utt2spk` as a map from utterance ids to
        speaker ids. The data in `xfilename`, which are assumed to be
        referenced by speaker ids, can then be refrenced by utterance.
        If `utt2spk` is unspecified, the keys in `xfilename` are used to
        query for data.
    value_style : str of {'b', 's', 'd'}, optional
        `wm` readers can provide not only the audio buffer (`'b'`) of a
        wave file, but its sampling rate (`'s'`), and/or duration (in
        sec, `'d'`). Setting `value_style` to some combination of `'b'`,
        `'s'`, and/or `'d'` will cause the reader to return a tuple of
        that information. If `value_style` is only one character, the
        result will not be contained in a tuple. Defaults to `'b'`

    Returns
    -------
    KaldiTable
        A table, opened.

    Raises
    ------
        IOError
            On failure to open
        SytemError
            Kaldi errors are thrown as `SystemError`s.
    """
    table = None
    kaldi_dtype = KaldiDataType(kaldi_dtype)
    if mode == 'r':
        if kaldi_dtype.value == 'wm':
            table = _KaldiSequentialWaveReader(xfilename, **kwargs)
        else:
            table = _KaldiSequentialSimpleReader(
                xfilename, kaldi_dtype=kaldi_dtype, **kwargs)
    elif mode == 'r+':
        if kaldi_dtype.value == 'wm':
            table = _KaldiRandomAccessWaveReader(xfilename, **kwargs)
        else:
            table = _KaldiRandomAccessSimpleReader(
                xfilename, kaldi_dtype=kaldi_dtype, **kwargs)
    elif mode in ('w', 'w+'):
        if kaldi_dtype.value == 'tv':
            table = _KaldiTokenVectorWriter(xfilename, **kwargs)
        else:
            table = _KaldiSimpleWriter(
                xfilename, kaldi_dtype=kaldi_dtype, **kwargs)
    else:
        raise ValueError(
            'Invalid Kaldi I/O mode "{}" (should be one of "r","r+","w")'
            ''.format(mode))
    return table
