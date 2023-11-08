Kaldi I/O - Pythonized
======================

Basics
------

The submodule :mod:`pydrobert.kaldi.io` wraps Kaldi's I/O mechanism. If you
don't know about scripts, archives, binary *vs.* text mode, and so forth, you
should read up on them `here <https://kaldi-asr.org/doc/io.html>`_.

Similar to Python's :func:`open` opening and returning a specific
implementation of :class:`io.IOBase`, the :func:`pydrobert.kaldi.io.open`
function opens an implementation of :class:`KaldiIOBase`. Streams opened in
either :obj:`"r"` or :obj:`"r+"` mode are readers and those opened in
:obj:`"w"` mode are writers, implementing :func:`read` and :func:`write`
methods, respectively.

Opening a stream for reading or writing an unstructured sequence of values
requires an (extended) file name. If opened with ``mode='w'``, a
:class:`pydrobert.kaldi.io.duck_streams.KaldiOutput` stream is opened. Writing
values usually doesn't require passing more than the value itself to the
stream's write method:

>>> from pydrobert.kaldi.io import open as kaldi_open
>>> import numpy as np
>>> with kaldi_open('foo.dump', mode='w') as writer:
...     writer.write(np.random.rand(10))

Doing so implicitly calls :func:`pydrobert.kaldi.io.util.infer_kaldi_data_type`
to infer what :class:`pydrobert.kaldi.io.enums.KaldiDataType` the value should
be written as. In this case, the value written will be inferred to be of type
`BaseVector`, or :obj:`"bv"` for short. We could have specified the type as
we wrote it to avoid any unforeseen consequences. For example, the value
:obj:`1.0` would be mapped to the `Base` floating-point type :obj:`"b"`,
which is usually 32-bit. To ensure it's double precision:

>>> with kaldi_open('foo.dump', mode='w') as writer:
...     writer.write(1.0, "d")

You can also write multiple values to a single stream, mixing and matching
types:

>>> with kaldi_open('foo.dump', mode='w') as writer:
...     writer.write(1)
...     writer.write(1.0)
...     writer.write(2.0, "d")

A :class:`pydrobert.kaldi.io.duck_streams.KaldiInput` stream is opened when
``mode='r'`` (``'r+'`` is the same here). To read values, call :func:`read`
with the types of the written values in the order they were written. Because
Kaldi's read routine changes depending on the type it is reading, the type
cannot be inferred after-the-fact.

>>> with kaldi_open('foo.dump') as reader:
...     assert reader.read("i") == 1
...     assert reader.read("b") == 1.0
...     assert reader.read("d") == 2.0

Opening a table requires an rspecifier/wspecifier and a
:class:`pydrobert.kaldi.io.enums.KaldiDataType` to specify the type of all
entries. A :class:`pydrobert.kaldi.io.table_streams.KaldiWriter` is opened when
``mode='w'``. It writes pairs of keys and values (of that type) to stream in
that order.

>>> with kaldi_open('ark:foo.ark', 'i', 'w') as writer:
...     writer.write('bar', 1)
...     writer.write('baz', 2)

The table reader, :class:`pydrobert.kaldi.io.table_streams.KaldiReader`, comes
in two flavours, depending on whether ``mode='r'`` or ``'r+'``. The former,
:class:`pydrobert.kaldi.io.table_streams.KaldiSequentialTableReader` opens the
stream for sequential reading of keys and/or values. By default, only values
are iterated over:

>>> with kaldi_open('ark:foo.ark', 'i') as reader:
...     assert list(reader) == [1, 2]

Alternatively, one can iterate over just the keys or key/value pairs:

>>> with kaldi_open('ark:foo.ark', 'i') as reader:
...     assert list(reader.keys()) == ['bar', 'baz']
>>> with kaldi_open('ark:foo.ark', 'i') as reader:
...     assert list(reader.items()) == [('bar', 1), ('baz', 2)]

When ``mode='r+'``, a
:class:`pydrobert.kaldi.io.table_streams.KaldiRandomAccessTableReader` is
opened instead. It resembles a :class:`collections.abc.Mapping` in that values
are retrieved by key:

>>> with kaldi_open('ark:foo.ark', 'i', 'r+') as reader:
...     assert reader['baz'] == 2.0
...     assert 'bar' in reader

However, unlike the sequential readers and a :class:`Mapping`, random access
readers cannot be iterated over.

Because the only way to determine the length of a table is to read to its end,
neither the sequential nor random access reader implement :func:`__len__`.

Wav files
---------



Text mode
---------

Kaldi allows many data types 