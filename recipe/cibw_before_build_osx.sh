#! /usr/bin/env bash

set -e -x

if ! command -v swig; then
  brew install swig@4.0
fi

python -m pip install -r recipe/cibw_before_requirements.txt