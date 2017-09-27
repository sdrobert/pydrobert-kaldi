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
        path, kaldi_dtype, mode='r', error_on_str=True,
        utt2spk='', value_style='b'):
    """Factory function for initializing and opening readers and writers

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
    if 'r' in mode:
        table_type = parse_kaldi_input_path(path)[0]
    else:
        table_type = parse_kaldi_output_path(path)[0]
    if table_type == TableType.NotATable:
        raise NotImplementedError('TODO')
    else:
        return open_table(
            path, kaldi_dtype, mode=mode, error_on_str=error_on_str,
            utt2spk=utt2spk, value_style=value_style)
