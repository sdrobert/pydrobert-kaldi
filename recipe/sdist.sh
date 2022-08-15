#! /usr/bin/env bash

set -e

cdir="$PWD"

# build swig 4.0.2
tmpdir=$(mktemp -d)
pushd $tmpdir
curl -L https://github.com/swig/swig/archive/rel-4.0.2.tar.gz > rel-4.0.2
[ "$(md5sum rel-4.0.2 | cut -d' ' -f 1)" = "19a61126f0f89c56b2c2e9e39cc33efe" ]
tar -xf rel-4.0.2
cd swig-rel-4.0.2
./autogen.sh --without-alllang --with-python
./configure --without-pcre --prefix="$PWD/install"
make
make install
popd

python -m pip install build
