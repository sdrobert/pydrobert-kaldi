# !/usr/bin/env bash
# Travis CI OSX test (PyPI)

set -e -x

[ $# = 1 ] || exit 1

py_ver=$1

pyenv global $py_ver
PY_BIN=$(pyenv which python${py_ver:0:1})
[ ! -f "${PY_BIN}" ] && exit 1
pyenv virtualenv venv_test
pyenv global venv_test

pip install pytest
pip install pydrobert-kaldi -f dist-osx-py${PY_VER}
pytest tests/python
