#! /usr/bin/env bash

if [ "`uname`" != "Darwin" ]; then
  export CC=${PREFIX}/bin/gcc
  export CXX=${PREFIX}/bin/g++
fi

$PYTHON $RECIPE_DIR/setup.py install || exit 1
