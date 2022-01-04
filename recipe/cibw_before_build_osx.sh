#! /usr/bin/env bash

set -e -x

brew install swig@4.0.2

export ACCELERATE=1

python -m pip install -r recipe/cibw_before_requirements.txt