===============
pydrobert-kaldi
===============

|appveyor| |readthedocs|

`Read the latest docs <http://pydrobert-kaldi.readthedocs.io/en/latest>`_

**This is student-driven code, so don't expect a stable API. I'll try to use
semantic versioning, but the best way to keep functionality stable is by
forking.**

What is it?
-----------

Some Kaldi_ SWIG_ bindings for Python. I started this project because I wanted
to seamlessly incorporate Kaldi's I/O mechanism into the gamut of Python-based
data science packages (e.g. Theano, Tensorflow, CNTK, PyTorch, etc.). The code
base is expanding to wrap more of Kaldi's feature processing and mathematical
functions, but is unlikely to include modelling or decoding.

Eventually, I plan on adding hooks for Kaldi audio features and pre-/post-
processing. However, I have no plans on porting any code involving modelling or
decoding.

Input/Output
------------

Most I/O can be performed with the ``pydrobert.kaldi.io.open`` function:

>>> from pydrobert.kaldi import io
>>> with io.open('scp:foo.scp', 'bm') as f:
>>>     for matrix in f:
>>>         pass # do something

``open`` is a factory function that determines the appropriate underlying
stream to open, much like Python's built-in ``open``. The data types we can
read (here, a ``BaseMatrix``) are listed in
``pydrobert.kaldi.io.enums.KaldiDataType``. Big data types, like matrices and
vectors, are piped into Numpy_ arrays. Passing an extended filename  (e.g.
paths to files on discs, ``'-'`` for stdin/stdout, ``'gzip -c a.ark.gz |'``,
etc.) opens a stream from which data types can be read one-by-one and in the
order they were written. Alternatively, prepending the extended filename with
``'ark[,[option_a[,option_b...]]:'`` or ``'scp[,...]:'`` and specifying a data
type allows one to open a Kaldi table for iterator-like sequential reading
(``mode='r'``), dict-like random access reading (``mode='r+'``), or writing
(``mode='w'``). For more information on the open function, consult the
docstring. Information on `Kaldi I/O`_ can be found on their website.

The submodule ``pydrobert.kaldi.io.corpus`` contains useful wrappers around
Kaldi I/O to serve up batches of data to, say, a neural network:

>>> train = ShuffledData('scp:feats.scp', 'scp:labels.scp', batch_size=10)
>>> for feat_batch, label_batch in train:
>>>     pass  # do something

Logging and CLI
---------------

By default, Kaldi error, warning, and critical messages are piped to standard
error. The ``pydrobert.kaldi.logging`` submodule provides hooks into python's
native logging interface: the ``logging`` module. The ``KaldiLogger`` can
handle stack traces from Kaldi C++ code, and there are a variety of decorators
to finagle the kaldi logging patterns to python logging patterns, or vice
versa.

You'd likely want to explicitly handle logging when creating new kaldi-style
commands for command line. ``pydrobert.kaldi.io.argparse`` provides
``KaldiParser``, an ``ArgumentParser`` tailored to Kaldi inputs/outputs. It is
used by a few command-line entry points added by this package. They are:

write-table-to-pickle
  Write the contents of a kaldi table to a pickle file(s). Good for late night
  attempts at reaching a paper deadline.
write-pickle-to-table
  Write the contents of of a pickle file(s) to a kaldi table.
write-table-to-torch-dir
  Write the contents of a kaldi table into a directory as a series of PyTorch
  tensor files. Suitable for PyTorch data loaders with multiprocessing.
  Requires PyTorch_.
write-torch-dir-to-table
  Write the contents of a directory of tensor files back to a Kaldi table.
  Requires PyTorch_.
normalize-feat-lens
  Ensure that features have the same length as some reference by truncating
  or appending frames.
compute-error-rate
  Compute an error rate between reference and hypothesis texts, such as a WER
  or PER.
normalize-feat-lens
  Ensure features match some reference length, either by padding or clipping
  the end.

Installation
------------

Check the following compatibility table to see if you can get a PyPI_ or Conda_
install going:

+----------+------+--------+--------+-------+
| Platform | Arch | Python | Conda? | PyPI? |
+==========+======+========+========+=======+
| Windows  | 32   | -      | No     | No    |
+----------+------+--------+--------+-------+
| Windows  | 64   | 2.7    | No     | No    |
+----------+------+--------+--------+-------+
| Windows  | 64   | 3.5    | Yes    | No    |
+----------+------+--------+--------+-------+
| Windows  | 64   | 3.6    | Yes    | No    |
+----------+------+--------+--------+-------+
| Windows  | 64   | 3.7    | Yes    | No    |
+----------+------+--------+--------+-------+
| Windows  | 64   | 3.8    | Yes    | No    |
+----------+------+--------+--------+-------+
| Windows  | 64   | 3.9    | Yes    | No    |
+----------+------+--------+--------+-------+
| OSX      | 32   | -      | No     | No    |
+----------+------+--------+--------+-------+
| OSX      | 64   | 2.7    | Yes    | Yes   |
+----------+------+--------+--------+-------+
| OSX      | 64   | 3.5    | Yes    | Yes   |
+----------+------+--------+--------+-------+
| OSX      | 64   | 3.6    | Yes    | Yes   |
+----------+------+--------+--------+-------+
| OSX      | 64   | 3.7    | Yes    | Yes   |
+----------+------+--------+--------+-------+
| OSX      | 64   | 3.8    | Yes    | Yes   |
+----------+------+--------+--------+-------+
| OSX      | 64   | 3.9    | Yes    | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 32   | 2.7    | No     | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 32   | 3.5    | No     | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 32   | 3.6    | No     | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 32   | 3.7    | No     | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 32   | 3.8    | No     | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 32   | 3.9    | No     | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 64   | 2.7    | Yes    | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 64   | 3.5    | Yes    | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 64   | 3.6    | Yes    | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 64   | 3.7    | Yes    | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 64   | 3.8    | Yes    | Yes   |
+----------+------+--------+--------+-------+
| Linux    | 64   | 3.9    | Yes    | Yes   |
+----------+------+--------+--------+-------+


To install via ``conda``::

   conda install -c sdrobert pydrobert-kaldi

To install via ``pip``::

   pip install pydrobert-kaldi

You can also try building from source, but you'll have to specify where your
BLAS install is somehow::

   # for OpenBLAS
   OPENBLASROOT=/path/to/openblas/install pip install \
     git+https://github.com/sdrobert/pydrobert-kaldi.git
   # for MKL
   MKLROOT=/path/to/mkl/install pip install \
     git+https://github.com/sdrobert/pydrobert-kaldi.git
   # for Accelerate (OSX only)
   ACCELLERATE=1 pip install \
     git+https://github.com/sdrobert/pydrobert-kaldi.git
   # see setup.py for more options

License
-------

This code is licensed under Apache 2.0.

Code found under the ``src/`` directory has been primarily copied from Kaldi.
``setup.py`` is also strongly influenced by Kaldi's build
configuration. Kaldi is also covered by the Apache 2.0 license; its specific
license file was copied into ``src/COPYING_Kaldi_Project`` to live among its
fellows.

How to Cite
-----------

Please see the `pydrobert page <https://github.com/sdrobert/pydrobert>`__ for
more details.

.. _Kaldi: http://kaldi-asr.org/
.. _`Kaldi I/O`: http://kaldi-asr.org/doc/io.html
.. _Swig: http://www.swig.org/
.. _Numpy: http://www.numpy.org/
.. _Conda: http://conda.pydata.org/docs/
.. _PyPI: https://pypi.org/
.. _PyTorch: https://pytorch.org/
.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/lvjhj9pgju90wn8j/branch/master?svg=true
              :target: https://ci.appveyor.com/project/sdrobert/pydrobert-kaldi
              :alt: AppVeyor Build Status
.. |readthedocs| image:: https://readthedocs.org/projects/pydrobert-kaldi/badge/?version=stable
                 :target: https://pydrobert-kaldi.readthedocs.io/en/stable/
                 :alt: Documentation Status
