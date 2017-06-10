===============
pydrobert-kaldi
===============

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

This functionality exists in the `tables` submodule. Kaldi logging is
automatically tethered to a logger named ``'pydrobert.kaldi'`` from Python's
`logging` module.

Eventually, I plan on adding hooks for Kaldi audio features and
pre-/post-processing. However, I have no plans on porting any code involving
modelling or decoding.

Installation
------------

Kaldi requires BLAS libraries to operate. The least-hassle method of installing
this package is through Conda_. Simply::

   conda install -c sdrobert pydrobert-kaldi-openblas

Which installs `pydrobert.kaldi` binaries with OpenBLAS.

Alternatively, to build through pip::

   # for OpenBLAS
   OPENBLASROOT=/path/to/openblas/install pip install \
     git+https://github.com/sdrobert/pydrobert-kaldi.git
   # for MKL
   MKLROOT=/path/to/mkl/install pip install \
     git+https://github.com/sdrobert/pydrobert-kaldi.git

Though this takes considerably longer, given the binaries must be compiled for
your specific BLAS library.

Possible Problems
-----------------

- To make the Anaconda Cloud install cross-compatible, I rely on Conda's
  `libgcc` package. This can cause issues with past/future installs that want
  another version. I highly suggest you isolate this package from your root
  environment.
- The OSX build uses the "Accelerate Framework" and expects it to be in a
  specific absolute path. If you're getting ``symbol not found`` errors, try
  manually editing the path with ``install_name_tool`` or, better yet, build
  from source.
- Be careful when using extended file name options such as "o" (once) or
  "s" (sorted). They are valid, but this package caches nothing and does very
  little error checking!

License
-------

This code is licensed under Apache 2.0.

Code found under the `src/` directory has been primarily copied from Kaldi_
version 5.1.46. `setup.py` is also strongly influenced by Kaldi's build
configuration. Kaldi is also covered by the Apache 2.0 license; its specific
license file was copied into `src/COPYING_Kaldi_Project` to live among its
fellows. The Kaldi team uses a minim

.. _Kaldi: http://kaldi-asr.org/
.. _Swig: http://www.swig.org/
.. _Numpy: http://www.numpy.org/
.. _Conda: http://conda.pydata.org/docs/
