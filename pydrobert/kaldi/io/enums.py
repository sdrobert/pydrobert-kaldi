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

'''Kaldi enumerations, including data types and xspecifier types'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from enum import Enum  # need enum34 for python 2.7

from pydrobert.kaldi._internal import kDoubleIsBase as _DOUBLE_IS_BASE

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2017 Sean Robertson"

__all__ = [
    'KaldiDataType',
    'RxfilenameType',
    'WxfilenameType',
    'TableType',
]


class KaldiDataType(Enum):
    """Enumerates the data types stored and retrieved by Kaldi I/O

    This enumerable lists the types of data written and read to various
    readers and writers. It is used in the factory method
    ``pydrobert.kaldi.io.open()`` to dictate the subclass created.

    Notes
    -----
    The "base float" mentioned in this documentation is the same type as
    ``kaldi::BaseFloat``, which was determined when Kaldi was built. The
    easiest way to determine whether this is a double (64-bit) or a
    float (32-bit) is by checking the value of
    ``KaldiDataType.BaseVector.is_double()``.
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

    Wave matrices have the shape ``(n_channels, n_samples)``. Kaldi will
    read PCM wave files, but will always convert the samples the base
    floats.

    Though Kaldi can read wave files of different types and sample
    rates, Kaldi will only write wave files as PCM16 sampled at 16k.
    """

    Token = 't'
    """Inputs/outputs are individual whitespace-free ASCII or unicode words"""

    TokenVector = 'tv'
    """Inputs/outputs are tuples of tokens"""

    Int32 = 'i'
    """Inputs/outputs are single 32-bit ints"""

    Int32Vector = 'iv'
    """Inputs/outputs are tuples of 32-bit ints"""

    Int32VectorVector = 'ivv'
    """Inputs/outputs are tuples of tuples of 32-bit ints"""

    Int32PairVector = 'ipv'
    """Inputs/outputs are tuples of pairs of 32-bit ints"""

    Double = 'd'
    """Inputs/outputs are single 64-bit floats"""

    Base = 'b'
    """Inputs/outputs are single base floats"""

    BasePairVector = 'bpv'
    """Inputs/outputs are tuples of pairs of the base float"""

    Bool = 'B'
    """Inputs/outputs are single booleans"""

    @property
    def is_matrix(self):
        """bool : whether this type is a numpy matrix type"""
        return str(self.value) in ('bm', 'dm', 'fm', 'wm')

    @property
    def is_num_vector(self):
        """bool : whether this is a numpy vector"""
        return str(self.value) in ('bv', 'fv', 'dv')

    @property
    def is_basic(self):
        """bool : whether data are stored in kaldi with Read/WriteBasicType"""
        return str(self.value) in (
            'i', 'iv', 'ivv', 'ipv', 'b', 'd', 'bpv', 'B')

    @property
    def is_floating_point(self):
        """bool : whether this type has a floating point representation"""
        return str(self.value) in ('bv', 'fv', 'dv', 'bm', 'fm', 'dm', 'wm')

    @property
    def is_double(self):
        '''bool: whether this data type is double precision (64-bit)'''
        if str(self.value) in ('bv', 'bm', 'wm', 'b', 'bpv'):
            return _DOUBLE_IS_BASE
        elif str(self.value) in ('dv', 'dm', 'd'):
            return True
        else:
            return False


class RxfilenameType(Enum):
    '''The type of stream to read, based on an extended filename'''

    InvalidInput = 0
    '''An invalid stream'''

    FileInput = 1
    '''Input is from a file on disk with no offset'''

    StandardInput = 2
    '''Input is being piped from stdin'''

    PipedInput = 3
    '''Input is being piped from a command'''

    OffsetFileInput = 4
    '''Input is from a file on disk, read from a specific offset'''


class WxfilenameType(Enum):
    '''The type of stream to write, based on an extended filename'''

    InvalidOutput = 0
    '''An invalid stream'''

    FileOutput = 1
    '''Output to a file on disk'''

    StandardOutput = 2
    '''Output is being piped to stdout'''

    PipedOutput = 3
    '''Output is being piped to some command'''


class TableType(Enum):
    '''The type of table a stream points to'''

    NotATable = 0
    '''The stream is not a table'''

    ArchiveTable = 1
    '''The stream points to an archive (keys and values)'''

    ScriptTable = 2
    '''The stream points to a script (keys and extended file names)'''

    BothTables = 3
    '''The stream points simultaneously to a script and archive

    This is a special pattern for writing. The archive stores
    keys and values; the script stores keys and points to the locations
    in the archive
    '''
