#! /usr/bin/env bash

$PYTHON $RECIPE_DIR/setup.py install || exit 1

$PYTHON -c 'import pydrobert.kaldi._internal'
