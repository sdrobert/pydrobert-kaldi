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

This subpackage contains a factory function, ``open``, which is intended
to behave similarly to python's built-in ``open`` factory. ``open`` gives
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

import abc

from six import with_metaclass

from pydrobert.kaldi.io.util import parse_kaldi_input_path
from pydrobert.kaldi.io.util import parse_kaldi_output_path


class KaldiIOBase(object, with_metaclass(abc.ABCMeta)):
    '''IOBase for kaldi readers and writers

    Similar to `io.IOBase`, but without a lot of the assumed
    functionality.

    Arguments
    ---------
    path : str
        The path passed to `pydrobert.kaldi.io.open`

    Attributes
    ----------
    path : str
    table_type : pydrobert.kaldi.io.enums.TableType
    xfilenames : str or tuple
    xtypes : pydrobert.kaldi.io.enums.{RxfilenameType, WxfilenameType}
             or tuple
    binary : bool
        Whether this stream should use binary data (True) or text

        .. warning:: a stream is under no obligation to encode data in
           this way, though, in normal situations, it will
    closed : bool
        True if this stream is closed

    The following attributes exist for tables only

    permissive : bool
        True if invalid values will be treated as non-existent

    The following attributes exist when the object is a table and is
    readable:

    once : bool
        True if each entry will only be read once (you must guarantee
        this!)
    sorted : bool
        True if keys are sorted
    called_sorted : bool
        True if entries will be read in sorted order (you must guarantee
        this!)
    background : bool
        True if reading is not being performed on the main thread

    The following attributes exist when the object is a table and
    writable:

    flush : bool
        True if the stream is flushed after each write operation
    '''

    def __init__(self, path):
        self.path = path
        self.closed = False
        if self.readable():
            self._table_type, self._xfilenames, self._xtypes, options = \
                parse_kaldi_input_path(path)
        else:
            self._table_type, self._xfilenames, self._xtypes, options = \
                parse_kaldi_output_path(path)
        self.binary = True
        for key, value in options.items():
            setattr(self, key, value)
        super(KaldiIOBase, self).__init__()

    @abc.abstractmethod
    def close(self):
        '''Close and flush the underlying IO object

        This method has no effect if the file is already closed
        '''
        pass

    @abc.abstractmethod
    def readable(self):
        '''Return whether this object was opened for reading'''
        pass

    @abc.abstractmethod
    def writable(self):
        '''Return whether this object was opened for writing'''
        pass

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_val, trace):
        self.close()

# We expose the functionality of 'open' directly in the io package, but
# everything else sticks in its own submodule
from pydrobert.kaldi.io import _open
from pydrobert.kaldi.io._open import *

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2017 Sean Robertson"

__all__ = [
    'KaldiIOBase',
    'duck_streams',
    'table_streams',
    'enums',
    'util',
    'corpus',
] + _open.__all__
