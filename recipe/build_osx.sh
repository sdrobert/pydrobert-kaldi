#! /usr/bin/env bash
# Travis CI OSX build (PyPI)

set -e -x

# see https://github.com/MacPython/wiki/wiki/Spinning-wheels

dir=$1
tdir="$(mktemp -d)"

pip install -U pip wheel setuptools
pip install numpy delocate
pip install -r requirements.txt
hash -r

# PyPI Numpy standard for OSX is Accelerate, I think. Makes my job easy
ACCELERATE=1 python setup.py bdist_wheel -d "${tdir}"

mkdir -p "${dir}"
delocate-wheel -w "${dir}" "${tdir}/"*.whl
