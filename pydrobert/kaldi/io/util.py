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

'''Kaldi I/O utilities'''

from __future__ import absolute_import

import numpy as np

from builtins import str as text

from pydrobert.kaldi.io.enums import KaldiDataType
from pydrobert.kaldi.io.enums import RxfilenameType
from pydrobert.kaldi.io.enums import TableType
from pydrobert.kaldi.io.enums import WxfilenameType

import pydrobert.kaldi._internal as _i

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2017 Sean Robertson"

__all__ = [
    'parse_kaldi_input_path',
    'parse_kaldi_output_path',
    'infer_kaldi_data_type',
]


def parse_kaldi_input_path(path):
    '''Determine the characteristics of an input stream by its path

    Returns a 4-tuple of the following information:

    1. If path is not an rspecifier (``TableType.NotATable``):

       a. Classify path as an rxfilename
       b. return a tuple of ``(TableType, path, RxfilenameType,
          dict())``

    2. else:

       a. Put all rspecifier options (once, sorted, called_sorted,
          permissive, background) into a dictionary
       b. Extract the embedded rxfilename and classify it
       c. return a tuple of ``(TableType, rxfilename,
          RxfilenameType, options)``

    Parameters
    ----------
    path : str
        A string that would be passed to ``pydrobert.kaldi.io.open``
    '''
    cpp_ret = _i.ParseInputPath(path)
    table_type = TableType(cpp_ret[0])
    rxfilename = cpp_ret[1]
    rx_type = RxfilenameType(cpp_ret[2])
    if table_type == TableType.NotATable:
        options = dict()
    else:
        options = {
            'once': cpp_ret[3],
            'sorted': cpp_ret[4],
            'called_sorted': cpp_ret[5],
            'permissive': cpp_ret[6],
            'background': cpp_ret[7],
        }
    return (table_type, rxfilename, rx_type, options)


def parse_kaldi_output_path(path):
    '''Determine the charactersistics of an output stram by its path

    Returns a 4-tuple of the following information

    1. If path is not a wspecifier (``TableType.NotATable``)

       a. Classify path as a wxfilename
       b. return a tuple of ``(TableType, path, WxfilenameType,
          dict())``

    2. If path is an archive or script

       a. Put all wspecifier options (binary, flush, permissive)
          into a dictionary
       b. Extract the embedded wxfilename and classify it
       c. return a tuple of ``(TableType, wxfilename,
          WxfilenameType, options)``

    3. If path contains both an archive and a script
       (``TableType.BothTables``)

       a. Put all wspecifier options (binary, flush, permissive)
          into a dictionary
       b. Extract both embedded wxfilenames and classify them
       c. return a tuple of
          ``(TableType, (arch_wxfilename, script_wxfilename),
          (arch_WxfilenameType, script_WxfilenameType), options)``


    Parameters
    ----------
    path : str
        A string that would be passed to ``pydrobert.kaldi.io.open``
    '''
    cpp_ret = _i.ParseOutputPath(path)
    table_type = TableType(cpp_ret[0])
    if table_type == TableType.BothTables:
        wxfilenames = cpp_ret[1:3]
        wx_types = tuple(WxfilenameType(wx) for wx in cpp_ret[3:5])
    else:
        wxfilenames = cpp_ret[1]
        wx_types = WxfilenameType(cpp_ret[2])
    if table_type == TableType.NotATable:
        options = dict()
    else:
        options = {
            'binary': cpp_ret[-3],
            'flush': cpp_ret[-2],
            'permissive': cpp_ret[-1],
        }
    return (table_type, wxfilenames, wx_types, options)


def infer_kaldi_data_type(obj):
    '''Infer the appropriate kaldi data type for this object

    The following map is used (in order):

    +------------------------------+---------------------+
    | Object                       | KaldiDataType       |
    +==============================+=====================+
    | an int                       | Int32               |
    +------------------------------+---------------------+
    | a boolean                    | Bool                |
    +------------------------------+---------------------+
    | a float*                     | Base                |
    +------------------------------+---------------------+
    | str                          | Token               |
    +------------------------------+---------------------+
    | 2-dim numpy array float32    | FloatMatrix         |
    +------------------------------+---------------------+
    | 1-dim numpy array float32    | FloatVector         |
    +------------------------------+---------------------+
    | 2-dim numpy array float64    | DoubleMatrix        |
    +------------------------------+---------------------+
    | 1-dim numpy array float64    | DoubleVector        |
    +------------------------------+---------------------+
    | 1-dim numpy array of int32   | Int32Vector         |
    +------------------------------+---------------------+
    | 2-dim numpy array of int32\* | Int32VectorVector   |
    +------------------------------+---------------------+
    | (matrix-like, float or int)  | WaveMatrix**        |
    +------------------------------+---------------------+
    | an empty container           | BaseMatrix          |
    +------------------------------+---------------------+
    | container of str             | TokenVector         |
    +------------------------------+---------------------+
    | 1-dim py container of ints   | Int32Vector         |
    +------------------------------+---------------------+
    | 2-dim py container of ints\* | Int32VectorVector   |
    +------------------------------+---------------------+
    | 2-dim py container of pairs  | BasePairVector      |
    | of floats                    |                     |
    +------------------------------+---------------------+
    | matrix-like python container | DoubleMatrix        |
    +------------------------------+---------------------+
    | vector-like python container | DoubleVector        |
    +------------------------------+---------------------+

    \*The same data types could represent a ``Double`` or an
    ``Int32PairVector``, respectively. Care should be taken in these
    cases.

    \*\*The first element is the wave data, the second its sample
    frequency. The wave data can be a 2d numpy float array of the same
    precision as ``KaldiDataType.BaseMatrix``, or a matrix-like python
    container of floats and/or ints.

    Returns
    -------
    pydrobert.kaldi.io.enums.KaldiDataType or None
    '''
    if isinstance(obj, int):
        return KaldiDataType.Int32
    elif isinstance(obj, bool):
        return KaldiDataType.Bool
    elif isinstance(obj, float):
        return KaldiDataType.Base
    elif isinstance(obj, str) or isinstance(obj, text):
        return KaldiDataType.Token
    # the remainder are expected to be containers
    if not hasattr(obj, '__len__'):
        return None
    # numpy array or wav tuple?
    try:
        if len(obj.shape) == 1:
            if obj.dtype == np.float32:
                return KaldiDataType.FloatVector
            elif obj.dtype == np.float64:
                return KaldiDataType.DoubleVector
            elif obj.dtype == np.int32:
                return KaldiDataType.Int32Vector
        elif len(obj.shape) == 2:
            if obj.dtype == np.float32:
                return KaldiDataType.FloatMatrix
            elif obj.dtype == np.float64:
                return KaldiDataType.DoubleMatrix
            elif obj.dtype == np.int32:
                return KaldiDataType.Int32Vector
        elif len(obj) == 2 and \
                len(obj[0].shape) == 2 and (
                    obj[0].dtype == np.float32 and
                    not KaldiDataType.BaseMatrix.is_double) or (
                    obj[0].dtype == np.float64 and
                    KaldiDataType.BaseMatrix.is_double) and (
                    isinstance(obj[1], int) or isinstance(obj[1], float)):
            return KaldiDataType.WaveMatrix
    except AttributeError:
        pass
    if not len(obj):
        return KaldiDataType.BaseMatrix
    elif all(isinstance(x, str) or isinstance(x, text) for x in obj):
        return KaldiDataType.TokenVector
    elif all(isinstance(x, int) for x in obj):
        return KaldiDataType.Int32Vector
    elif all(hasattr(x, '__len__') and hasattr(x, '__getitem__') for x in obj):
        if all(all(isinstance(y, int) for y in x) for x in obj):
            return KaldiDataType.Int32VectorVector
        try:
            if all(len(x) == 2 and all(np.isreal(y) for y in x) for x in obj):
                return KaldiDataType.BasePairVector
            elif len(np.array(obj).astype(np.float64).shape) == 2:
                return KaldiDataType.DoubleMatrix
        except ValueError:
            pass
    else:
        try:
            if len(np.array(obj).astype(np.float64).shape) == 1:
                return KaldiDataType.DoubleVector
        except ValueError:
            pass
    return None
