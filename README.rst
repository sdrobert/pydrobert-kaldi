===============
pydrobert-kaldi
===============

What is it?
-----------

Kaldi_ I/O (table) SWIG_ bindings. Easily shove your audio features into Numpy_
arrays. It builds for Python 2.7 and above. You can do stuff like

.. code:: python

   import pydrobert.kaldi.tables as tables

   # write binary BaseFloat matrices to file a.ark w/ keys+offsets in b.scp
   with tables.open('ark,scp:a.ark,b.scp', 'bm', mode='w') as f:
       f.write('foo', [[1, 2], [3, 4]])
       f.write('bar', [[1]])

   # read back in numpy arrays sequentially or with random access
   with tables.open('scp:b.scp', 'bm', mode='r') as f:
       for n_array in f:
           print(n_array)
   with tables.open('scp:b.scp', 'bm', mode='r+') as f:
       print(f['bar'])
   

Installation
------------

Installation is through Conda_. To install from the Anaconda Cloud, try the
command::

   conda install -c sdrobert pydrobert-kaldi

And everything will work automagically. If that's not working for you, you can
try::

   # if you don't have a copy of kaldi somewhere
   conda build recipes/kaldi
   conda build recipes/clean
   # if you do have a copy of kaldi somewhere
   export KALDI_ROOT=/path/to/kaldi/repo
   conda build recipes/dirty
   # finally (for both)
   conda install --use-local pydrobert-kaldi

The latter is also useful if you have Kaldi already installed somewhere. 

Possible Problems
-----------------

 - To make the Anaconda Cloud install cross-compatible, I rely on Conda's
   `gcc 4.8.5` library and implicitly its `libgcc`. This can cause issues with
   past/future installs that want another version. I highly suggest you isolate
   this package from your root environment.
 - The OSX build uses the "Accelerate Framework" and expects it to be in a
   specific absolute path. If you're getting ``symbol not found`` errors, try
   manually editing the path with ``install_name_tool`` or, better yet, build
   from source.
 - Be careful when using extended file name options such as "o" (once) or
   "s" (sorted). They are valid, but this package caches nothing and does very
   little error checking!
 - I haven't dealt with storing tokens (character strings without spaces)
   because I don't want to deal with the whole Python encoding business. If
   you're reading and writing strings, just use Python's I/O :)

License
-------

Kaldi_ is covered by the Apache 2.0 license, and so too is this.

.. _Kaldi: http://kaldi-asr.org/
.. _Swig: http://www.swig.org/
.. _Numpy: http://www.numpy.org/
.. _Conda: http://conda.pydata.org/docs/