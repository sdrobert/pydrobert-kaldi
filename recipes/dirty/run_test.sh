#! /usr/bin/env bash

export LC_ALL=C
nosetests . || exit 1
