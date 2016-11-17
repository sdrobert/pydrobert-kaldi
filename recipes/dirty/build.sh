#! /usr/bin/env bash

# check if KALDI_ROOT is set.
if [ -z "${KALDI_ROOT}" ]; then
  >&2 echo "Environment variable KALDI_ROOT not set"
  exit 1
fi
if [ ! -d "${KALDI_ROOT}/src" ]; then
  >&2 echo "KALDI_ROOT (${KALDI_ROOT}) does not have src directory."\
" Is it correct?"
  exit 1
fi

# we "make" to get the compile flags that kaldi used and put them into files
make -f $RECIPE_DIR/Makefile || exit 1

$PYTHON $RECIPE_DIR/setup.py install || exit 1

make -f $RECIPE_DIR/Makefile clean || exit 1
