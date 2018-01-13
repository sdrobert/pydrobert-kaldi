#! /usr/bin/env bash
# Travis CI OSX build (PyPI)

set -e -x

[ $# = 1 ] || exit 1

py_ver=$1

pyenv global $py_ver
PY_BIN=$(pyenv which python${py_ver:0:1})
[ ! -f "${PY_BIN}" ] && exit 1
virtualenv "--python=${PY_BIN}" venv_build
source venv_build/bin/activate

pip install -U pip wheel setuptools
pip install numpy==1.11.3
pip install -r requirements.txt

# PyPI Numpy standard for OSX is Accelerate, I think. Makes my job easy
ACCELERATE=1 python setup.py bdist_wheel

deactivate
