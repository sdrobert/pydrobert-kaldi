# !/usr/bin/env bash
# Travis CI OSX test (PyPI)

set -e -x

dir=$1

pip install pytest
pip install pydrobert-kaldi -f $1
pytest tests/python -m "not pytorch"
