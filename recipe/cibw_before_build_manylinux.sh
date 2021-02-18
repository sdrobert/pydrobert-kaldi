#! /usr/bin/env bash

set -e -x

if [ `uname -m` = 'x86_64' ]; then
  MARCH_SUFFIX=.x86_64
else
  MARCH_SUFFIX=.i386
fi

yum install -y openblas-devel${MARCH_SUFFIX} swig

pip install oldest-supported-numpy