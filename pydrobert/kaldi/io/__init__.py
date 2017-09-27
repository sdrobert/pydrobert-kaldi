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

"""Interfaces for Kaldi's readers and writers

This subpackage contains a factory function, `open`, which is intended
to behave similarly to python's built-in `open` factory. `open` gives
the specifics behind Kaldi's different read/write styles. Here, they
are described in a general way.

Kaldi's streams can be very exotic, including regular files, file
offsets, stdin/out, and pipes.

Data can be read/written from a binary or text stream in the usual way:
specific data types have specific encodings, and data are
packed/unpacked in that fashion. While an appropriate style for a
fixed sequence of data, variables sequences of data are encoded using
the table analogy.

Kaldi uses the table analogy to store and retrieve indexed data. In a
nutshell, Kaldi uses archive ("ark") files to store binary or text data,
and script files ("scp") to point *into* archives. Both use
whitespace-free strings as keys. Scripts and archives do not have any
built-in type checking, so it is necessary to specify the input/output
type when the files are opened.

A full account of Kaldi IO can be found on Kaldi's website under `Kaldi
I/O Mechanisms`_.

For a description of the table types which can be read/written by Kaldi,
please consult `dtypes.KaldiDataTypes`.

.. _Kaldi I/O Mechanisms: http://kaldi-asr.org/doc2/io.html
"""

from __future__ import absolute_import

# We expose the functionality of 'open' directly in the io package, but
# everything else sticks in its own submodule
from pydrobert.kaldi.io import _open
from pydrobert.kaldi.io._open import *

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2017 Sean Robertson"

__all__ = [
    'tables',
    'enums',
    'util',
] + _open.__all__
