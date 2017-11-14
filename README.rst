===============
pydrobert-kaldi
===============

.. image:: https://travis-ci.org/sdrobert/pydrobert-kaldi.svg?branch=master

What is it?
-----------

Some Kaldi_ SWIG_ bindings for Python. I started this project because I wanted
to seamlessly incorporate Kaldi's I/O mechanism into the gamut of Python-based
data science packages (e.g. Theano, Tensorflow, CNTK, PyTorch, etc.). The
code base is expanding to wrap more of Kaldi's feature processing and
mathematical functions, but is unlikely to include modelling or decoding.

Eventually, I plan on adding hooks for Kaldi audio features and
pre-/post-processing. However, I have no plans on porting any code involving
modelling or decoding.

Input/Output
------------

Most I/O can be performed with the ``pydrobert.kaldi.io.open`` function:

>>> from pydrobert.kaldi import io
>>> with io.open('scp:foo.scp', 'bm') as f:
>>>     for matrix in f:
>>>         pass # do something

``open`` is a factory function that determines the appropriate underlying stream
to open, much like Python's built-in ``open``. The data types we can read (here,
a BaseMatrix) are listed in ``pydrobert.kaldi.io.enums.KaldiDataType``. Big
data types, like matrices and vectors, are piped into Numpy_ arrays. Passing
an extended filename  (e.g. paths to files on discs, '-' for stdin/stdout,
'gzip -c a.ark.gz |', etc.) opens a stream from which data types can be read
one-by-one and in the order they were written. Alternatively, prepending the
extended filename with "ark[,[option_a[,option_b...]]:" or "scp[,...]:" and
specifying a data type allows one to open a Kaldi table for iterator-like
sequential reading (``mode='r'``), dict-like random access reading
(``mode='r+'``), or writing (``mode='w'``). For more information on the open
function, consult the docstring. Information on `Kaldi I/O`_ can be found on
their website.

Logging and CLI
---------------

By default, Kaldi error, warning, and critical messages are piped to standard
error. The ``pydrobert.kaldi.logging`` submodule provides hooks into python's
native logging interface: the ``logging`` module. The ``KaldiLogger`` can handle
stack traces from Kaldi C++ code, and there are a variety of decorators to
finagle the kaldi logging patterns to python logging patterns, or vice versa.

You'd likely want to explicitly handle logging when creating new kaldi-style
commands for command line. ``pydrobert.kaldi.command_line`` provides
``KaldiParser``, an ``ArgumentParser`` tailored to Kaldi inputs/outputs. It is
used by a few command-line entry points added by this package. They are:

write-table-to-pickle
  Write the contents of a kaldi table to a pickle file(s). Good for late night
  attempts at reaching a paper deadline.
write-pickle-to-table
  Write the contents of of a pickle file(s) to a kaldi table.

Installation
------------

If you're on a Linux or OSX machine and you've got Conda_ installed, your life
is easy.

Simply::

   conda install -c sdrobert pydrobert-kaldi

Which installs binaries with MKL BLAS. If ``nomkl`` is installed into the
environment, either an OpenBLAS version (Linux) or Accelerate (OSX) version is
installed.

Alternatively, to build through PyPI, you'll need to point the install to a BLAS
library::

   # for OpenBLAS
   OPENBLASROOT=/path/to/openblas/install pip install \
     git+https://github.com/sdrobert/pydrobert-kaldi.git
   # for MKL
   MKLROOT=/path/to/mkl/install pip install \
     git+https://github.com/sdrobert/pydrobert-kaldi.git
   # see setup.py for more options

You'll need either GCC or Clang plus Swig >= 3.0.8 for this.

I plan on getting Windows working some time in the future.

License
-------

This code is licensed under Apache 2.0.

Code found under the ``src/`` directory has been primarily copied from Kaldi
version 5.1.46. ``setup.py`` is also strongly influenced by Kaldi's build
configuration. Kaldi is also covered by the Apache 2.0 license; its specific
license file was copied into ``src/COPYING_Kaldi_Project`` to live among its
fellows.

.. _Kaldi: http://kaldi-asr.org/
.. _`Kaldi I/O`: http://kaldi-asr.org/doc/io.html
.. _Swig: http://www.swig.org/
.. _Numpy: http://www.numpy.org/
.. _Conda: http://conda.pydata.org/docs/
