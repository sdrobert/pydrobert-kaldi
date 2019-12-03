#! /usr/bin/env bash
# Travis CI OSX build (PyPI)

set -e -x

dir=$1

pip install -U pip wheel setuptools
pip install numpy
pip install -r requirements.txt

# PyPI Numpy standard for OSX is Accelerate, I think. Makes my job easy
ACCELERATE=1 python setup.py bdist_wheel -d $dir
