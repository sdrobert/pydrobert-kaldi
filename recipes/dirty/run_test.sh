#! /usr/bin/env bash

export LC_ALL=C
nosetests tests || exit 1

# memory checks... not necessary, so only in dirty build
python table_profiler.py