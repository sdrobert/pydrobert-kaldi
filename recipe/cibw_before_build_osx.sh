#! /usr/bin/env bash

set -e -x

brew install swig@4.0

python -m pip install -r recipe/cibw_before_requirements.txt