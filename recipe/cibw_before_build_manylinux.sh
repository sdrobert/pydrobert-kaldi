#! /usr/bin/env bash

set -e -x

if [ `uname -m` = 'x86_64' ]; then
  MARCH_SUFFIX=.x86_64
else
  MARCH_SUFFIX=.i686
fi

yum install -y curl || true

# build swig 3.0.8
# tmpdir=$(mktemp -d)
# pushd $tmpdir
# curl -L https://github.com/swig/swig/archive/rel-3.0.8.tar.gz > rel-3.0.8
# [ "$(md5sum rel-3.0.8 | cut -d' ' -f 1)" = "9b5862b1d782b111d87fce9216a2d465" ]
# tar -xf rel-3.0.8
# cd swig-rel-3.0.8
# ./autogen.sh --without-alllang --with-python
# ./configure --without-pcre
# make
# make install
# popd

yum install -y swig-4.0.2 openblas-devel${MARCH_SUFFIX}

pip install -r recipe/cibw_before_requirements.txt