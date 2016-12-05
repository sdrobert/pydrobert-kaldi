#! /usr/bin/env bash

export LC_ALL=C
nosetests tests || exit 1

# memory checks... not necessary, so only in dirty build
if which valgrind > /dev/null && [ "`uname`" != "Darwin" ]; then
  valgrind \
    --tool=memcheck \
    --leak-check=full \
    --suppressions=valgrind-python.supp \
    python table_profiler.py
else
  python table_profiler.py
fi