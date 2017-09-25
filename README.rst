===============
pydrobert-kaldi
===============

.. image:: https://travis-ci.org/sdrobert/pydrobert-kaldi.svg?branch=master

What is it?
-----------

Some Kaldi_ SWIG_ bindings for Python. The primary purpose is to read and write
Kaldi-style features efficiently and python-ically for use outside the Kaldi
ecosystem. For example:

>>> from pydrobert.kaldi import tables
>>> with tables.open('scp:foo.scp', 'bm') as f:
>>>     for matrix in f:
>>>         # do something
>>>

This functionality exists in the `tables` submodule.

By default, Kaldi error, warning, and critical messages are piped to standard
error. The `logging` submodule provides hooks into python's native logging
interface: the `logging` module.

Eventually, I plan on adding hooks for Kaldi audio features and
pre-/post-processing. However, I have no plans on porting any code involving
modelling or decoding.

Installation
------------

If you're on a Linux machine and you've got Conda_ installed, your life is easy.
Simply::

   conda install -c sdrobert pydrobert-kaldi-openblas

Which installs `pydrobert.kaldi` binaries with OpenBLAS. Alternatively, to build
through pip on Linux, you'll need to point the install to a BLAS library::

   # for OpenBLAS
   OPENBLASROOT=/path/to/openblas/install pip install \
     git+https://github.com/sdrobert/pydrobert-kaldi.git
   # for MKL
   MKLROOT=/path/to/mkl/install pip install \
     git+https://github.com/sdrobert/pydrobert-kaldi.git

This takes considerably longer, given the binaries must be compiled for
your specific BLAS library.

The OSX build links to Apple's Accelerate framework, which lives outside the
Conda environment and thus has to be built locally::

   pip install git+https://github.com/sdrobert/pydrobert-kaldi.git

I plan on getting Windows working some time in the future.

License
-------

This code is licensed under Apache 2.0.

Code found under the `src/` directory has been primarily copied from Kaldi_
version 5.1.46. `setup.py` is also strongly influenced by Kaldi's build
configuration. Kaldi is also covered by the Apache 2.0 license; its specific
license file was copied into `src/COPYING_Kaldi_Project` to live among its
fellows.

.. _Kaldi: http://kaldi-asr.org/
.. _Swig: http://www.swig.org/
.. _Numpy: http://www.numpy.org/
.. _Conda: http://conda.pydata.org/docs/
