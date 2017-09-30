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

    Parameters
    ----------
    path : str
        A string that would be passed to `pydrobert.kaldi.io.open`

    Returns
    -------
    A 4-tuple of the following information
    1. If path is not an rspecifier (TableType.NotATable)
       a. Classify path as an rxfilename
       b. return a tuple of (TableType, path, RxfilenameType, dict())
    2. else
       a. Put all rspecifier options (once, sorted, called_sorted,
          permissive, background) into a dictionary
       b. Extract the embedded rxfilename and classify it
       c. return a tuple of (TableType, rxfilename, RxfilenameType,
          options)
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

    Parameters
    ----------
    path : str
        A string that would be passed to `pydrobert.kaldi.io.open`

    Returns
    -------
    A 4-tuple of the following information
    1. If path is not a wspecifier (TableType.NotATable)
       a. Classify path as a wxfilename
       b. return a tuple of (TableType, path, WxfilenameType, dict())
    2. If path is an archive or script
       a. Put all wspecifier options (binary, flush, permissive) into a
          dictionary
       b. Extract the embedded wxfilename and classify it
       c. return a tuple of (TableType, wxfilename, WxfilenameType,
          options)
    3. If path contains both an archive and a script
       (TableType.BothTables)
       a. Put all wspecifier options (binary, flush, permissive) into a
          dictionary
       b. Extract both embedded wxfilenames and classify them
       c. return a tuple of
          (TableType, (arch_wxfilename, script_wxfilename),
          (arch_WxfilenameType, script_WxfilenameType), options)
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

    The following map is used:

    +------------------------------+---------------+
    | Object                       | KaldiDataType |
    +==============================+===============+
    | 2-dim numpy array float32    | FloatMatrix   |
    +------------------------------+---------------+
    | 1-dim numpy array float32    | FloatVector   |
    +------------------------------+---------------+
    | 2-dim numpy array float64    | DoubleMatrix  |
    +------------------------------+---------------+
    | 1-dim numpy array float64    | DoubleVector  |
    +------------------------------+---------------+
    | matrix-like python container | DoubleMatrix  |
    +------------------------------+---------------+
    | vector-like python container | DoubleVector  |
    +------------------------------+---------------+
    | (matrix-like, float or int)  | WaveMatrix*   |
    +------------------------------+---------------+
    | str                          | Token         |
    +------------------------------+---------------+
    | container of str             | TokenVector   |
    +------------------------------+---------------+

    *The first element is the wave data, the second its sample
    frequency. The wave data can be a 2d numpy float array of the same
    precision as ``KaldiDataType.BaseMatrix``, or a matrix-like python
    container of floats and/or ints.

    Returns
    -------
    pydrobert.kaldi.io.enums.KaldiDataType or None
    '''
    ret = _infer_numerical_type(obj)
    if ret:
        return ret
    try:
        if isinstance(obj, str) or isinstance(obj, text):
            ret = KaldiDataType.Token
        elif len(obj) and \
                all(isinstance(x, str) or isinstance(x, text) for x in obj):
            ret = KaldiDataType.TokenVector
        if ret or len(obj) != 2 or (
                not isinstance(obj[1], int) and
                not isinstance(obj[1], float)):
            return ret
        # fall-through: could be wave data
    except AttributeError:
        return ret
    first_type = _infer_numerical_type(obj[0])
    if first_type and first_type.is_matrix:
        if first_type.is_double == KaldiDataType.BaseMatrix.is_double:
            ret = KaldiDataType.WaveMatrix
        else:
            try:
                obj[0].shape
            except AttributeError:
                # wasn't a numpy array to begin with, so was upcast.
                # could be a base float
                ret = KaldiDataType.WaveMatrix
    return ret

def _infer_numerical_type(obj):
    '''Infer if an object could be a numerical (numpy) kaldi data type'''
    # first the easy stuff. Is it a floating point numpy array of shape
    # 1 or 2?
    ret = None
    try:
        if len(obj.shape) == 2 and obj.dtype == np.float32:
            ret = KaldiDataType.FloatMatrix
        elif len(obj.shape) == 1 and obj.dtype == np.float32:
            ret = KaldiDataType.FloatVector
        elif len(obj.shape) == 2 and obj.dtype == np.float64:
            ret = KaldiDataType.DoubleMatrix
        elif len(obj.shape) == 1 and obj.dtype == np.float64:
            ret = KaldiDataType.DoubleVector
        # fall-through means it's of the wrong type or shape
        return ret
    except AttributeError:
        pass
    # it's not a numpy array. Try casting it as a floating point one
    try:
        return _infer_numerical_type(np.array(obj).astype(np.float64))
    except ValueError:
        return ret
