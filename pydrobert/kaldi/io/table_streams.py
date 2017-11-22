# Copyright 2017 Sean Robertson

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''Submodule containing table readers and writers'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc

from collections import Container
from collections import Iterator

from builtins import str as text
from future.utils import implements_iterator

from pydrobert.kaldi import _internal as _i
from pydrobert.kaldi.io import KaldiIOBase
from pydrobert.kaldi.io.enums import KaldiDataType

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2017 Sean Robertson"

__all__ = [
    'KaldiTable',
    'KaldiSequentialReader',
    'KaldiRandomAccessReader',
    'KaldiWriter',
]


def open_table_stream(
        path, kaldi_dtype, mode='r', error_on_str=True,
        utt2spk='', value_style='b'):
    '''Factory function to open a kaldi table

    This function finds the correct `KaldiTable` according to the args
    `kaldi_dtype` and `mode`. Specific combinations allow for optional
    parameters outlined by the table below

    +------+-------------+---------------------+
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
    path : str
        The specifier used by kaldi to open the script.
        Generally these will take the form
        ``"{ark|scp}:<path_to_file>"``,
        though they can take much more interesting forms (like pipes).
        More information can be found on the `Kaldi website
        <http://kaldi-asr.org/doc2/io.html>`_.
    kaldi_dtype : KaldiDataType
        The type of data the table is expected to handle.
    mode : {'r', 'r+', 'w'}, optional
        Specifies the type of access to be performed: read sequential,
        read random, or write. They are implemented by subclasses of
        `KaldiSequentialReader`, `KaldiRandomAccessReader`, or
        `KaldiWriter`, resp.
    error_on_str : bool, optional
        Token vectors (`'tv'`) accept sequences of whitespace-free
        ASCII/UTF strings. A `str` is also a sequence of characters,
        which may satisfy the token requirements. If
        `error_on_str=True`, a `ValueError` is raised when writing a
        `str` as a token vector. Otherwise a `str` can be written.
    utt2spk : str, optional
        If set, the reader uses `utt2spk` as a map from utterance ids to
        speaker ids. The data in `path`, which are assumed to be
        referenced by speaker ids, can then be refrenced by utterance.
        If `utt2spk` is unspecified, the keys in `path` are used to
        query for data.
    value_style : str of {'b', 's', 'd'}, optional
        `wm` readers can provide not only the audio buffer (`'b'`) of a
        wave file, but its sampling rate (`'s'`), and/or duration (in
        sec, `'d'`). Setting `value_style` to some combination of `'b'`,
        `'s'`, and/or `'d'` will cause the reader to return a tuple of
        that information. If `value_style` is only one character, the
        result will not be contained in a tuple.

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
    '''
    kaldi_dtype = KaldiDataType(kaldi_dtype)
    if mode == 'r':
        if kaldi_dtype.value == 'wm':
            table = _KaldiSequentialWaveReader(
                path, kaldi_dtype, value_style=value_style)
        else:
            table = _KaldiSequentialSimpleReader(path, kaldi_dtype)
    elif mode == 'r+':
        if kaldi_dtype.value == 'wm':
            table = _KaldiRandomAccessWaveReader(
                path, kaldi_dtype, utt2spk=utt2spk,
                value_style=value_style
            )
        else:
            table = _KaldiRandomAccessSimpleReader(
                path, kaldi_dtype, utt2spk=utt2spk)
    elif mode in ('w', 'w+'):
        if kaldi_dtype.value == 't':
            table = _KaldiTokenWriter(path, kaldi_dtype)
        elif kaldi_dtype.value == 'tv':
            table = _KaldiTokenVectorWriter(
                path, kaldi_dtype, error_on_str=error_on_str)
        else:
            table = _KaldiSimpleWriter(path, kaldi_dtype)
    else:
        raise ValueError(
            'Invalid Kaldi I/O mode "{}" (should be one of "r","r+","w")'
            ''.format(mode))
    return table


class KaldiTable(KaldiIOBase):
    """Base class for interacting with tables

    All table readers and writers are subclasses of `KaldiTable`. Tables
    must specify the type of data being read ahead of time

    Parameters
    ----------
    path : str
    kaldi_dtype : pydrobert.kaldi.io.enums.KaldiDataType
        The type of data type this table contains

    Attributes
    ----------
    kaldi_dtype : KaldiDataType
        The table's data type

    Raises
    ------
    IOError
        If unable to open table
    SystemError
        Kaldi errors are wrapped as `SystemError`s
    """

    def __init__(self, path, kaldi_dtype):
        self.kaldi_dtype = KaldiDataType(kaldi_dtype)
        super(KaldiTable, self).__init__(path)


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
    path : str
    kaldi_dtype : pydrobert.kaldi.io.enums.KaldiDataType

    Raises
    ------
    IOError
    SystemError
    """

    def __init__(self, path, kaldi_dtype):
        self._iterator_type = 0
        super(KaldiSequentialReader, self).__init__(path, kaldi_dtype)

    @abc.abstractmethod
    def key(self):
        """return current pair's key, or `None` if done

        Raises
        ------
        IOError
            If closed
        """
        pass

    @abc.abstractmethod
    def value(self):
        """return current pair's value, or `None` if done

        Raises
        ------
        IOError
            If closed
        """
        pass

    @abc.abstractmethod
    def done(self):
        """bool: `True` when closed or pairs are exhausted"""
        pass

    @abc.abstractmethod
    def move(self):
        """Move iterator forward

        Returns
        -------
        bool
            `True` if moved to new pair. `False` if done

        Raises
        ------
        IOError
            If closed
        """
        pass

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

    def readable(self):
        return True

    def writable(self):
        return False

    def __next__(self):
        if self.closed:
            raise IOError('I/O operation on a closed file')
        if self.done():
            raise StopIteration
        ret = None
        if self._iterator_type == 2:
            ret = self.key(), self.value()
        elif self._iterator_type == 1:
            ret = self.key()
        else:
            ret = self.value()
        self.move()
        return ret

    def __iter__(self):
        return self

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
    path : str
    kaldi_dtype : pydrobert.kaldi.io.enums.KaldiDataType
    utt2spk : str, optional
        If set, the reader uses `utt2spk` as a map from utterance ids to
        speaker ids. The data in `path`, which are assumed to be
        referenced by speaker ids, can then be refrenced by utterance.
        If `utt2spk` is unspecified, the keys in `path` are used to
        query for data.

    Attributes
    ----------
    utt2spk : str or None

    Raises
    ------
    IOError
    SystemError
    """

    def __init__(self, path, kaldi_dtype, utt2spk=''):
        self._utt2spk = utt2spk
        super(KaldiRandomAccessReader, self).__init__(path, kaldi_dtype)

    @abc.abstractmethod
    def __contains__(self, key):
        pass

    @abc.abstractmethod
    def __getitem__(self, key):
        pass

    def get(self, key, default=None):
        """D.get(k[,d]) -> D[k] if k in D, else d. d defaults to None.

        Raises
        ------
        IOError
            If closed
        """
        try:
            return self[key]
        except KeyError:
            return default

    def readable(self):
        return True

    def writable(self):
        return False


class KaldiWriter(KaldiTable):
    """Write key-value pairs to tables

    Parameters
    ----------
    path : str
    kaldi_dtype : pydrobert.kaldi.io.enums.KaldiDataType

    Raises
    ------
    IOError
    SystemError
    """

    def __init__(self, path, kaldi_dtype):
        super(KaldiWriter, self).__init__(path, kaldi_dtype)

    @abc.abstractmethod
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
        pass

    def readable(self):
        return False

    def writable(self):
        return True


class _KaldiSequentialSimpleReader(KaldiSequentialReader):
    __doc__ = KaldiSequentialReader.__doc__

    _dtype_to_cls = {
        'bm': (
            _i.SequentialDoubleMatrixReader
            if _i.kDoubleIsBase else _i.SequentialFloatMatrixReader
        ),
        'bv': (
            _i.SequentialDoubleVectorReader
            if _i.kDoubleIsBase else _i.SequentialFloatVectorReader
        ),
        'dm': _i.SequentialDoubleMatrixReader,
        'dv': _i.SequentialDoubleVectorReader,
        'fm': _i.SequentialDoubleMatrixReader,
        'fv': _i.SequentialDoubleVectorReader,
        't': _i.SequentialTokenReader,
        'tv': _i.SequentialTokenVectorReader,
        'i': _i.SequentialInt32Reader,
        'iv': _i.SequentialInt32VectorReader,
        'ivv': _i.SequentialInt32VectorVectorReader,
        'ipv': _i.SequentialInt32PairVectorReader,
        'd': _i.SequentialDoubleReader,
        'b': _i.SequentialBaseFloatReader,
        'bpv': _i.SequentialBaseFloatPairVectorReader,
        'B': _i.SequentialBoolReader,
    }

    def __init__(self, path, kaldi_dtype):
        kaldi_dtype = KaldiDataType(kaldi_dtype)
        instance = self._dtype_to_cls[kaldi_dtype.value]()
        if not instance.Open(path):
            raise IOError('Unable to open for sequential read')
        self._internal = instance
        super(_KaldiSequentialSimpleReader, self).__init__(path, kaldi_dtype)
        self.binary &= self._internal.IsBinary()

    def done(self):
        return self.closed or self._internal.Done()

    def key(self):
        if self.closed:
            raise IOError('I/O operation on closed file.')
        elif self.done():
            return None
        else:
            return self._internal.Key()

    def value(self):
        if self.closed:
            raise IOError('I/O operation on closed file.')
        elif self.done():
            return None
        else:
            return self._internal.Value()

    def move(self):
        if self.closed:
            raise IOError('I/O operation on closed file.')
        elif self.done():
            return False
        else:
            self._internal.Next()
            return True

    def close(self):
        if not self.closed:
            self._internal.Close()
        self.closed = True


class _KaldiRandomAccessSimpleReader(KaldiRandomAccessReader):
    __doc__ = KaldiRandomAccessReader.__doc__

    _dtype_to_cls = {
        'bm': (
            _i.RandomAccessDoubleMatrixReader
            if _i.kDoubleIsBase else _i.RandomAccessFloatMatrixReader
        ),
        'bv': (
            _i.RandomAccessDoubleVectorReader
            if _i.kDoubleIsBase else _i.RandomAccessFloatVectorReader
        ),
        'dm': _i.RandomAccessDoubleMatrixReader,
        'dv': _i.RandomAccessDoubleVectorReader,
        'fm': _i.RandomAccessFloatMatrixReader,
        'fv': _i.RandomAccessFloatVectorReader,
        't': _i.RandomAccessTokenReader,
        'tv': _i.RandomAccessTokenVectorReader,
        'i': _i.RandomAccessInt32Reader,
        'iv': _i.RandomAccessInt32VectorReader,
        'ivv': _i.RandomAccessInt32VectorVectorReader,
        'ipv': _i.RandomAccessInt32PairVectorReader,
        'd': _i.RandomAccessDoubleReader,
        'b': _i.RandomAccessBaseFloatReader,
        'bpv': _i.RandomAccessBaseFloatPairVectorReader,
        'B': _i.RandomAccessBoolReader,
    }

    def __init__(self, path, kaldi_dtype, utt2spk=''):
        kaldi_dtype = KaldiDataType(kaldi_dtype)
        instance = self._dtype_to_cls[kaldi_dtype.value]()
        if not instance.Open(path, utt2spk):
            raise IOError('Unable to open for random access read')
        self._internal = instance
        super(_KaldiRandomAccessSimpleReader, self).__init__(
            path, kaldi_dtype, utt2spk=utt2spk)
        self.binary &= self._internal.IsBinary()

    def __contains__(self, key):
        if self.closed:
            raise IOError('I/O operation on closed file.')
        return self._internal.HasKey(key)

    def __getitem__(self, key):
        if self.closed:
            raise IOError('I/O operation on a closed file')
        if key not in self:
            raise KeyError(key)
        return self._internal.Value(key)

    def close(self):
        if not self.closed:
            self._internal.Close()
        self.closed = True


class _KaldiSimpleWriter(KaldiWriter):
    __doc__ = KaldiWriter.__doc__

    _dtype_to_cls = {
        'bm': (
            _i.DoubleMatrixWriter
            if _i.kDoubleIsBase else _i.FloatMatrixWriter
        ),
        'bv': (
            _i.DoubleVectorWriter
            if _i.kDoubleIsBase else _i.FloatVectorWriter
        ),
        'dm': _i.DoubleMatrixWriter,
        'dv': _i.DoubleVectorWriter,
        'fm': _i.FloatMatrixWriter,
        'fv': _i.FloatVectorWriter,
        'wm': _i.WaveWriter,
        'i': _i.Int32Writer,
        'iv': _i.Int32VectorWriter,
        'ivv': _i.Int32VectorVectorWriter,
        'ipv': _i.Int32PairVectorWriter,
        'd': _i.DoubleWriter,
        'b': _i.BaseFloatWriter,
        'bpv': _i.BaseFloatPairVectorWriter,
        'B': _i.BoolWriter,
    }

    def __init__(self, path, kaldi_dtype):
        kaldi_dtype = KaldiDataType(kaldi_dtype)
        instance = self._dtype_to_cls[kaldi_dtype.value]()
        if not instance.Open(path):
            raise IOError('Unable to open for write')
        self._internal = instance
        super(_KaldiSimpleWriter, self).__init__(path, kaldi_dtype)
        self.binary &= self._internal.IsBinary()

    def write(self, key, value):
        if self.closed:
            raise IOError('I/O operation on a closed file')
        self._internal.Write(key, value)

    def close(self):
        if not self.closed:
            self._internal.Close()
        self.closed = True


class _KaldiSequentialWaveReader(KaldiSequentialReader):
    __doc__ = KaldiSequentialReader.__doc__

    def __init__(self, path, kaldi_dtype, value_style='b'):
        self._value_calls = []
        if any(char not in 'bsd' for char in value_style):
            raise ValueError(
                'value_style must be a combination of "b", "s", and "d"')
        if 'b' in value_style:
            instance = _i.SequentialWaveReader()
        else:
            instance = _i.SequentialWaveInfoReader()
        if not instance.Open(path):
            raise IOError('Unable to open for sequential read')
        self._internal = instance
        for char in value_style:
            if char == 'b':
                self._value_calls.append(self._internal.Value)
            elif char == 's':
                self._value_calls.append(self._internal.SampFreq)
            else:
                self._value_calls.append(self._internal.Duration)
        super(_KaldiSequentialWaveReader, self).__init__(path, kaldi_dtype)
        self.binary = True

    def value(self):
        if self.closed:
            raise IOError('I/O operation on a closed file')
        elif self.done():
            return None
        else:
            ret = tuple(func() for func in self._value_calls)
            if len(ret) == 1:
                return ret[0]
            else:
                return ret

    def done(self):
        return self.closed or self._internal.Done()

    def key(self):
        if self.closed:
            raise IOError('I/O operation on closed file.')
        elif self.done():
            return None
        else:
            return self._internal.Key()

    def move(self):
        if self.closed:
            raise IOError('I/O operation on closed file.')
        elif self.done():
            return False
        else:
            self._internal.Next()
            return True

    def close(self):
        if not self.closed:
            self._internal.Close()
        self.closed = True


class _KaldiRandomAccessWaveReader(KaldiRandomAccessReader):
    __doc__ = KaldiRandomAccessReader.__doc__

    def __init__(self, path, kaldi_dtype, utt2spk='', value_style='b'):
        self._value_calls = []
        if any(char not in 'bsd' for char in value_style):
            raise ValueError(
                'value_style must be a combination of "b", "s", and "d"')
        if 'b' in value_style:
            instance = _i.RandomAccessWaveReader()
        else:
            instance = _i.RandomAccessWaveInfoReader()
        if not instance.Open(path, utt2spk):
            raise IOError('Unable to open for sequential read')
        self._internal = instance
        for char in value_style:
            if char == 'b':
                self._value_calls.append(self._internal.Value)
            elif char == 's':
                self._value_calls.append(self._internal.SampFreq)
            else:
                self._value_calls.append(self._internal.Duration)
        super(_KaldiRandomAccessWaveReader, self).__init__(
            path, kaldi_dtype, utt2spk=utt2spk)
        self.binary = True

    def __contains__(self, key):
        if self.closed:
            raise IOError('I/O operation on closed file.')
        return self._internal.HasKey(key)

    def __getitem__(self, key):
        if self.closed:
            raise IOError('I/O operation on a closed file')
        if key not in self:
            raise KeyError(key)
        ret = tuple(func(key) for func in self._value_calls)
        if len(ret) == 1:
            return ret[0]
        else:
            return ret

    def close(self):
        if not self.closed:
            self._internal.Close()
        self.closed = True


class _KaldiTokenWriter(KaldiWriter):
    __doc__ = KaldiWriter.__doc__

    def __init__(self, path, kaldi_dtype):
        instance = _i.TokenWriter()
        if not instance.Open(path):
            raise IOError('Unable to open for write')
        self._internal = instance
        super(_KaldiTokenWriter, self).__init__(path, kaldi_dtype)
        self.binary = False

    def write(self, key, value):
        # swig bindings have difficulty when this value is a scalar
        # numpy array. Easy fix is to use 'tolist', which actually
        # returns str or unicode.
        if self.closed:
            raise IOError('I/O operation on a closed file')
        try:
            value = value.tolist()
        except AttributeError:
            pass
        self._internal.Write(key, value)

    def close(self):
        if not self.closed:
            self._internal.Close()
        self.closed = True


class _KaldiTokenVectorWriter(KaldiWriter):
    __doc__ = KaldiWriter.__doc__

    def __init__(self, path, kaldi_dtype, error_on_str=True):
        self._error_on_str = error_on_str
        instance = _i.TokenVectorWriter()
        if not instance.Open(path):
            raise IOError('Unable to open for write')
        self._internal = instance
        super(_KaldiTokenVectorWriter, self).__init__(path, kaldi_dtype)
        self.binary = False

    def write(self, key, value):
        if self.closed:
            raise IOError('I/O operation on a closed file')
        try:
            value = value.tolist()
        except AttributeError:
            pass
        if self._error_on_str and (
                isinstance(value, str) or isinstance(value, text)):
            raise ValueError(
                'Expected list of tokens, got string. If you want '
                'to treat strings as lists of character-wide tokens, '
                'set error_on_str to False when opening')
        self._internal.Write(key, value)

    def close(self):
        if not self.closed:
            self._internal.Close()
        self.closed = True
