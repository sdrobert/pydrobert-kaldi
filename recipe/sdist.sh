#! /usr/bin/env bash

set -e

python -m pip install build twine

cdir="$PWD"

[ -f "$cdir/install/bin/swig" ] && exit 0

# build swig 4.0.2
tmpdir=$(mktemp -d)
pushd $tmpdir
curl -L https://github.com/swig/swig/archive/rel-4.0.2.tar.gz > rel-4.0.2
[ "$(md5sum rel-4.0.2 | cut -d' ' -f 1)" = "19a61126f0f89c56b2c2e9e39cc33efe" ]
tar -xf rel-4.0.2
cd swig-rel-4.0.2
./autogen.sh
./configure --without-alllang --with-python --without-pcre --prefix="$cdir/install"
make
make install
popd

