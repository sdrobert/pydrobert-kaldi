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
]

def parse_kaldi_input_path(path):
    '''Determine the characteristics of an input stream by its path

    Arguments
    ---------
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

    Arguments
    ---------
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
