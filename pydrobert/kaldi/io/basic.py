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

'''Submodule for 'basic' reading and writing, like (un)packing c structs'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc

from six import with_metaclass

from pydrobert.kaldi.io.util import parse_kaldi_input_path
from pydrobert.kaldi.io.util import parse_kaldi_output_path

__all__ = [
    'KaldiIOBase',
    'KaldiInput',
    'KaldiOutput',
]

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
    permissive : bool
        True if invalid data will be treated as non-existent

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

    binary : bool
        True if writing in binary (False is text)
    flush : bool
        True if the stream is flushed after each write operation
    '''

    def __init__(self, path):
        self._path = path
        self._closed = False
        if self.readable():
            self._table_type, self._xfilenames, self._xtypes, options = \
                parse_kaldi_input_path(path)
        else:
            self._table_type, self._xfilenames, self._xtypes, options = \
                parse_kaldi_output_path(path)
        for key, value in options.items():
            setattr(self, key, value)
        super(KaldiIOBase, self).__init__()

    @property
    def closed(self):
        '''Whether the object is closed'''
        return self._closed

    def close(self):
        '''Close and flush the underlying IO object

        This method has no effect if the file is already closed
        '''
        self._closed = True

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

class KaldiInput(KaldiIOBase):
    pass

class KaldiOutput(KaldiIOBase):
    pass
