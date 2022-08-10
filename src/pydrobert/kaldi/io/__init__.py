# Copyright 2021 Sean Robertson

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

This subpackage contains a factory function, :func:`open`, which is intended to behave
similarly to python's built-in :func:`open` factory. :func:`open` gives the specifics
behind Kaldi's different read/write styles. Here, they are described in a general way.

Kaldi's streams can be very exotic, including regular files, file offsets, stdin/out,
and pipes.

Data can be read/written from a binary or text stream in the usual way: specific data
types have specific encodings, and data are packed/unpacked in that fashion. While an
appropriate style for a fixed sequence of data, variables sequences of data are encoded
using the table analogy.

Kaldi uses the table analogy to store and retrieve indexed data. In a nutshell, Kaldi
uses archive ("ark") files to store binary or text data, and script files ("scp") to
point *into* archives. Both use whitespace- free strings as keys. Scripts and archives
do not have any built-in type checking, so it is necessary to specify the input/output
type when the files are opened.

A full account of Kaldi IO can be found on Kaldi's website under `Kaldi I/O Mechanisms
<http://kaldi-asr.org/doc/io.html>`_.

See Also
--------
pydrobert.kaldi.io.enums.KaldiDataType
    For more information on the types of streams that can be read or
    written
"""


import abc

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pydrobert.kaldi.io.enums import KaldiDataType

__all__ = [
    "KaldiIOBase",
    "open",
    "argparse",
    "corpus",
    "duck_streams",
    "enums",
    "table_streams",
    "util",
]


class KaldiIOBase(object, metaclass=abc.ABCMeta):
    """IOBase for kaldi readers and writers

    Similar to :class:`io.IOBase`, but without a lot of the assumed functionality.

    Arguments
    ---------
    path
        The path passed to "func:`pydrobert.kaldi.io.open`. One of an rspecifier,
        wspecifier, rxfilename, or wxfilename

    Attributes
    ----------
    path
        The opened path
    table_type
        The type of table that's being read/written (or ``NotATable``)
    xfilenames
        The extended file names being read/written. For tables, this
        excludes the ``'ark:'`` and ``'scp:'`` prefixes from path.
        Usually there will be only one extended file name, unless the
        path uses the special ``'ark,scp:'`` format to write both an
        archive and script at the same time
    xtypes
        The type of extended file name opened. Usually there will be
        only one extended file name, unless the path uses the special
        ``'ark,scp:'`` format to write both an archive and script at
        the same time
    binary
        Whether this stream encodes binary data (or text)
    closed
        Whether this stream is closed
    permissive
        Whether invalid values will be treated as non-existent (tables only)
    once
        Whether each entry will only be read once (readable tables only)
    sorted
        Whether keys are sorted (readable tables only)
    called_sorted
        Whether entries will be read in sorted order (readable tables only)
    background
        Whether reading is not being performed on the main thread (readable tables only)
    flush
        Whether the stream is flushed after each write operation (writable tables only)
    """

    def __init__(self, path: str):
        from pydrobert.kaldi.io.util import parse_kaldi_input_path
        from pydrobert.kaldi.io.util import parse_kaldi_output_path

        self.path = path
        self.closed = False
        if self.readable():
            (
                self._table_type,
                self._xfilenames,
                self._xtypes,
                options,
            ) = parse_kaldi_input_path(path)
        else:
            (
                self._table_type,
                self._xfilenames,
                self._xtypes,
                options,
            ) = parse_kaldi_output_path(path)
        self.binary = True
        for key, value in list(options.items()):
            setattr(self, key, value)
        super(KaldiIOBase, self).__init__()

    @abc.abstractmethod
    def close(self):
        """Close and flush the underlying IO object

        This method has no effect if the file is already closed
        """
        pass

    @abc.abstractmethod
    def readable(self) -> bool:
        """Return whether this object was opened for reading"""
        pass

    @abc.abstractmethod
    def writable(self) -> bool:
        """Return whether this object was opened for writing"""
        pass

    def __enter__(self) -> "KaldiIOBase":
        return self

    def __exit__(self, exception_type, exception_val, trace) -> None:
        self.close()


def open(
    path: str,
    kaldi_dtype: "KaldiDataType" = None,
    mode: str = "r",
    error_on_str: bool = True,
    utt2spk: str = "",
    value_style: str = "b",
    header: bool = True,
    cache: str = False,
) -> KaldiIOBase:
    """Factory function for initializing and opening kaldi streams

    This function provides a general interface for opening kaldi streams. Kaldi streams
    are either simple input/output of kaldi objects (the basic/duck stream) or key-value
    readers and writers (tables).

    When `path` starts with ``'ark:'`` or ``'scp:'`` (possibly with modifiers before the
    colon), a table is opened. Otherwise, a basic stream is opened.

    See also
    --------
    pydrobert.kaldi.io.table_streams.open_table_stream
        For information on opening tables
    pydrobert.kaldi.io.duck_streams.open_duck_stream
        For information on opening basic streams
    """
    from pydrobert.kaldi.io.enums import TableType
    from pydrobert.kaldi.io.util import parse_kaldi_input_path
    from pydrobert.kaldi.io.util import parse_kaldi_output_path
    from pydrobert.kaldi.io.duck_streams import open_duck_stream
    from pydrobert.kaldi.io.table_streams import open_table_stream

    if "r" in mode:
        table_type = parse_kaldi_input_path(path)[0]
    else:
        table_type = parse_kaldi_output_path(path)[0]
    if table_type == TableType.NotATable:
        return open_duck_stream(path, mode=mode, header=header)
    else:
        return open_table_stream(
            path,
            kaldi_dtype,
            mode=mode,
            error_on_str=error_on_str,
            utt2spk=utt2spk,
            value_style=value_style,
            cache=cache,
        )
