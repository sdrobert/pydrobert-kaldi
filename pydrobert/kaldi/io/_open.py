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

'''Contains the 'open' function

This submodule is imported directly by `pydrobert.kaldi.io` and thus
should not be directly imported
'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pydrobert.kaldi.io.basic import open_basic
from pydrobert.kaldi.io.enums import TableType
from pydrobert.kaldi.io.tables import open_table
from pydrobert.kaldi.io.util import parse_kaldi_input_path
from pydrobert.kaldi.io.util import parse_kaldi_output_path

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2017 Sean Robertson"

__all__ = ['open']

def open(
        path, kaldi_dtype=None, mode='r', error_on_str=True,
        utt2spk='', value_style='b', header=True):
    """Factory function for initializing and opening kaldi streams

    This function provides a general interface for opening kaldi
    streams. Kaldi streams are either simple input/output of kaldi
    objects (the basic stream) or key-value readers and writers
    (tables).

    When `path` starts with ``ark:`` or ``scp:`` (possibly with
    modifiers before the colon), a table is opened. Otherwise, a basic
    stream is opened.

    See also
    --------
    pydrobert.kaldi.io.tables.open_table
        For information on opening tables
    pydrobert.kaldi.io.basic.open_basic
        For information on opening basic streams
    """
    if 'r' in mode:
        table_type = parse_kaldi_input_path(path)[0]
    else:
        table_type = parse_kaldi_output_path(path)[0]
    if table_type == TableType.NotATable:
        return open_basic(path, mode=mode, header=header)
    else:
        return open_table(
            path, kaldi_dtype, mode=mode, error_on_str=error_on_str,
            utt2spk=utt2spk, value_style=value_style)
