v0.7.0
------

- Removed `KaldiLocaleWarning` and added a documentation page addressing
  locales.
- Updated documentation, including a special page for the CLI.
- Updated CI to only use
  `cibuildwheel <https://github.com/pypa/cibuildwheel/>`__. Able to compile
  Win-64 builds.
- Updated Kaldi source.
- Fixed ``setup.py``.
- Got rid of Conda recipe. Will switch to
  `conda-forge <https://conda-forge.org/>`__.

v0.6.0
------

A considerable amount of refactoring occurred for this build, chiefly to get
rid of Python 2.7 support. While the functionality did not change much for this
version, we have switched from a ``pkgutil``-style ``pydrobert`` namespace to
PEP-420-style namespaces. As a result, *this package is not
backwards-compatible with previous ``pydrobert`` packages!* Make sure that if
any of the following are installed, they exceed the following version
thresholds:

- ``pydrobert-param >0.2.0``
- ``pydrobert-pytorch >0.2.1``
- ``pydrobert-speech >0.1.0``

Miscellaneous other changes include:

- Type hints everywhere
- Shifted python source to ``src/``, alongside Kaldi source
- Updated numpy swig bindings for numpy 1.11.3
- Black-formatted remaining source
- Removed ``future`` and `six`, `configparser`
- Shifted a lot of the configuration to `setup.cfg`. There is still
  considerable work in ``setup.py`` due to the C extension
- Shifted documentation source from ``doc/`` to ``docs/``
- Shuffled around the indexing of documentation
- Added changelog :D

