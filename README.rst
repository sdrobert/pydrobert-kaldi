===============
pydrobert-kaldi
===============

What is it?
-----------

Kaldi_ I/O (table) SWIG_ bindings. Easily shove your audio features into Numpy_
arrays. You can do stuff like::

   import pydrobert.kaldi.tables as tables

   # write binary BaseFloat matrices to file a.ark w/ keys+offsets in b.scp
   with tables.open('ark,scp:a.ark,b.scp', 'bm', mode='w') as f:
       f.write('foo', [[1, 2], [3, 4]])
       f.write('bar', [[1]])

   # read back in numpy arrays sequentially or with random access
   with tables.open('scp:b.scp', 'bm', mode='s') as f:
      for n_array in f:
         print(n_array)
   with tables.open('scp:b.scp', 'bm', mode='r') as f:
      print(f['bar'])

.. note::
   
   This is in *very* early alpha stages. I haven't documented most of it. Also,
   I'm having issues getting the installation to work on OSX.

Installation
------------

Installation is through Conda_. If you're lucky, you can just call::

   conda install -c sdrobert pydrobert-kaldi

And everything will work automagically. Unfortunately, as of now I only have
Linux 64-bit binaries working. If you want to have a crack at installing from
source, try from the repo directory::

   # if you don't have a copy of kaldi somewhere
   conda build recipes/kaldi
   conda build recipes/clean
   # if you do have a copy of kaldi somewhere
   export KALDI_ROOT=/path/to/kaldi/repo
   conda build recipes/dirty
   # finally (for both)
   conda install --use-local pydrobert-kaldi

.. _Kaldi: http://kaldi-asr.org/
.. _Swig: http://www.swig.org/
.. _Numpy: http://www.numpy.org/
.. _Conda: http://conda.pydata.org/docs/