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

'''Submodule for reading and writing one-by-one, like (un)packing c structs'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from builtins import str as text
from future.utils import raise_from

from pydrobert.kaldi import _internal as _i
from pydrobert.kaldi.io import KaldiIOBase
from pydrobert.kaldi.io.enums import KaldiDataType
from pydrobert.kaldi.io.util import infer_kaldi_data_type

__all__ = [
    'KaldiInput',
    'KaldiOutput',
]


def open_duck_stream(path, mode='r', header=True):
    '''Open a "duck" stream

    "Duck" streams provide an interface for reading or writing kaldi
    objects, one at a time. Essentially: remember the order things go
    in, then pull them out in the same order.

    Duck streams can read/write binary or text data. It is mostly up
    to the user how to read or write data, though the following rules
    establish the default:

    1. An input stream that does not look for a 'binary header' is
       binary
    2. An input stream that looks for and finds a binary header when
       opening is binary
    3. An input stream that looks for but does not find a binary header
       when opening is a text stream
    4. An output stream is always binary. However, the user may choose
       not to write a binary header. The resulting input stream will be
       considered a text stream when 3. is satisfied

    Parameters
    ----------
    path : str
        The extended file name to be opened. This can be quite exotic.
        More details can be found on the `Kaldi website
        <http://kaldi-asr.org/doc2/io.html>`_.
    mode : {'r', 'r+', 'w'}
        Whether to open the stream for input (``'r'``) or output
        (``'w'``). ``'r+'`` is equivalent to ``'r'``
    header : bool
        Setting this to True will either check for a 'binary header' in
        an input stream, or write a binary header for an output stream.
        If False, no check/write is performed
    '''
    if mode in ('r', 'r+'):
        return KaldiInput(path, header=header)
    elif mode == 'w':
        return KaldiOutput(path, header=header)
    else:
        raise ValueError(
            'Invalid Kaldi I/O mode "{}" (should be one of "r","r+","w")'
            ''.format(mode))


class KaldiInput(KaldiIOBase):
    '''A kaldi input stream from which objects can be read one at a time

    Parameters
    ----------
    path : str
        An extended readable file path
    header : bool
        If False, no attempt will be made to look for the "binary"
        header in the stream; it will be assumed binary
    '''

    def __init__(self, path, header=True):
        self._internal = _i.Input()
        if header:
            opened, binary = self._internal.Open(path)
        else:
            opened = self._internal.OpenWithoutHeader(path)
            binary = True
        if not opened:
            raise IOError('Unable to open {} for reading'.format(path))
        super(KaldiInput, self).__init__(path)
        self.binary = binary

    def readable(self):
        return True

    readable.__doc__ = KaldiIOBase.readable.__doc__

    def writable(self):
        return False

    writable.__doc__ = KaldiIOBase.writable.__doc__

    def read(self, kaldi_dtype, value_style='b', read_binary=None):
        '''Read in one object from the stream

        Parameters
        ----------
        kaldi_dtype : pydrobert.kaldi.enums.KaldiDataType
            The type of object to read
        value_style : str of {'b', 's', 'd'}, optional
            ``'wm'`` readers can provide not only the audio buffer
            (``'b'``) of a wave file, but its sampling rate (``'s'``),
            and/or duration (in sec, ``'d'``). Setting `value_style` to
            some combination of ``'b'``, ``'s'``, and/or ``'d'`` will
            cause the reader to return a tuple of that information. If
            `value_style` is only one character, the result will not be
            contained in a tuple
        read_binary : bool, optional
            If set, the object will be read as either binary (``True``)
            or text (``False``). The default behaviour is to read
            according to the `binary` attribute. Ignored if there's only
            one way to read the data
        '''
        if self.closed:
            raise IOError('I/O operation on closed file.')
        kaldi_dtype = KaldiDataType(kaldi_dtype)
        if read_binary is None:
            read_binary = self.binary
        try:
            if kaldi_dtype == KaldiDataType.WaveMatrix:
                if any(x not in 'bsd' for x in value_style):
                    raise ValueError(
                        'value_style must be a combination of "b", "s",'
                        ' and "d"')
                tup = self._internal.ReadWaveData()  # (data, samp_freq)
                ret = []
                for code in value_style:
                    if code == 'b':
                        ret.append(tup[0])
                    elif code == 's':
                        ret.append(tup[1])
                    else:
                        ret.append(tup[0].shape[1] / tup[1])
                if len(ret) == 1:
                    ret = ret[0]
                else:
                    ret = tuple(ret)
            elif kaldi_dtype == KaldiDataType.Token:
                ret = self._internal.ReadToken(read_binary)
            elif kaldi_dtype == KaldiDataType.TokenVector:
                ret = self._internal.ReadTokenVector()
            elif kaldi_dtype.is_basic:
                if kaldi_dtype == KaldiDataType.Int32:
                    ret = self._internal.ReadInt32()
                elif kaldi_dtype == KaldiDataType.Int32Vector:
                    ret = self._internal.ReadInt32Vector()
                elif kaldi_dtype == KaldiDataType.Int32VectorVector:
                    ret = self._internal.ReadInt32VectorVector()
                elif kaldi_dtype == KaldiDataType.Int32PairVector:
                    ret = self._internal.ReadInt32PairVector()
                elif kaldi_dtype == KaldiDataType.Double:
                    ret = self._internal.ReadDouble()
                elif kaldi_dtype == KaldiDataType.Base:
                    ret = self._internal.ReadBaseFloat()
                elif kaldi_dtype == KaldiDataType.BasePairVector:
                    ret = self._internal.ReadBaseFloatPairVector()
                else:
                    ret = self._internal.ReadBool()
            elif kaldi_dtype.is_num_vector:
                if kaldi_dtype.is_double:
                    ret = self._internal.ReadVectorDouble(read_binary)
                else:
                    ret = self._internal.ReadVectorFloat(read_binary)
            else:
                if kaldi_dtype.is_double:
                    ret = self._internal.ReadMatrixDouble(read_binary)
                else:
                    ret = self._internal.ReadMatrixFloat(read_binary)
        except RuntimeError as err:
            raise_from(IOError('Unable to read data'), err)
        return ret

    def close(self):
        if not self.closed:
            self._internal.Close()
        self.closed = True

    close.__doc__ = KaldiIOBase.close.__doc__


class KaldiOutput(KaldiIOBase):
    '''A kaldi output stream from which objects can be written one at a time

    Parameters
    ----------
    path : str
        An extended writable file path
    header : bool
        Whether to write a header when opening the binary stream (True)
        or not.
    '''

    def __init__(self, path, header=True):
        self._internal = _i.Output()
        super(KaldiOutput, self).__init__(path)
        if not self._internal.Open(path, self.binary, header):
            raise IOError('Unable to open {} for writing'.format(path))

    def readable(self):
        return False

    readable.__doc__ = KaldiIOBase.readable.__doc__

    def writable(self):
        return True

    writable.__doc__ = KaldiIOBase.writable.__doc__

    def write(self, obj, kaldi_dtype, error_on_str=True, write_binary=True):
        '''Write one object to the stream

        Parameters
        ----------
        obj
            The object to write
        kaldi_dtype : pydrobert.kaldi.enums.KaldiDataType
            The type of object to write. The default is to infer this
        error_on_str : bool, optional
            Token vectors (``'tv'``) accept sequences of whitespace-free
            ASCII/UTF strings. A ``str`` is also a sequence of
            characters, which may satisfy the token requirements. If
            `error_on_str` is ``True``, a ``ValueError`` is raised when
            writing a ``str`` as a token vector. Otherwise a ``str``
            can be written
        write_binary : bool, optional
            The object will be written as binary (``True``) or text
            (``False``)

        Raises
        ------
        ValueError
            If unable to determine a proper data type

        See Also
        --------
        pydrobert.kaldi.io.util.infer_kaldi_data_type
            Illustrates how different inputs are mapped to data types
        '''
        if self.closed:
            raise IOError('I/O operation on closed file.')
        if kaldi_dtype is None:
            kaldi_dtype = infer_kaldi_data_type(obj)
            if kaldi_dtype is None:
                raise ValueError(
                    'Unable to find kaldi data type for {}'.format(obj))
        else:
            kaldi_dtype = KaldiDataType(kaldi_dtype)
        try:
            if kaldi_dtype == KaldiDataType.WaveMatrix:
                self._internal.WriteWaveData(obj[0], float(obj[1]))
            elif kaldi_dtype == KaldiDataType.Token:
                try:
                    obj = obj.tolist()
                except AttributeError:
                    pass
                self._internal.WriteToken(write_binary, obj)
            elif kaldi_dtype == KaldiDataType.TokenVector:
                try:
                    obj = obj.tolist()
                except AttributeError:
                    pass
                if error_on_str and (
                        isinstance(obj, str) or isinstance(obj, text)):
                    raise ValueError(
                        'Expected list of tokens, got string. If you want '
                        'to treat strings as lists of character-wide tokens, '
                        'set error_on_str to False when opening')
                self._internal.WriteTokenVector(obj)
            elif kaldi_dtype.is_basic:
                if kaldi_dtype == KaldiDataType.Int32:
                    self._internal.WriteInt32(write_binary, obj)
                elif kaldi_dtype == KaldiDataType.Int32Vector:
                    self._internal.WriteInt32Vector(write_binary, obj)
                elif kaldi_dtype == KaldiDataType.Int32VectorVector:
                    self._internal.WriteInt32VectorVector(write_binary, obj)
                elif kaldi_dtype == KaldiDataType.Int32PairVector:
                    self._internal.WriteInt32PairVector(write_binary, obj)
                elif kaldi_dtype == KaldiDataType.Double:
                    self._internal.WriteDouble(write_binary, obj)
                elif kaldi_dtype == KaldiDataType.Base:
                    self._internal.WriteBaseFloat(write_binary, obj)
                elif kaldi_dtype == KaldiDataType.BasePairVector:
                    self._internal.WriteBaseFloatPairVector(write_binary, obj)
                else:
                    self._internal.WriteBool(write_binary, obj)
            elif kaldi_dtype.is_num_vector:
                if kaldi_dtype.is_double:
                    self._internal.WriteVectorDouble(write_binary, obj)
                else:
                    self._internal.WriteVectorFloat(write_binary, obj)
            else:
                if kaldi_dtype.is_double:
                    self._internal.WriteMatrixDouble(write_binary, obj)
                else:
                    self._internal.WriteMatrixFloat(write_binary, obj)
        except RuntimeError as err:
            raise_from(IOError('Unable to write data'), err)

    def close(self):
        if not self.closed:
            self._internal.Close()
        self.closed = True
