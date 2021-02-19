#! /usr/bin/env bash

set -e -x

if [ `uname -m` = 'x86_64' ]; then
  MARCH_SUFFIX=.x86_64
else
  MARCH_SUFFIX=.i686
fi

yum install -y curl || true

# build swig 4.0.2
tmpdir=$(mktemp -d)
pushd $tmpdir
curl -L https://github.com/swig/swig/archive/rel-4.0.2.tar.gz > rel-4.0.2
[ "$(md5sum rel-4.0.2 | cut -d' ' -f 1)" = "77026bde998521cf1244fb43950203b9" ]
tar -xf rel-4.0.2
cd swig-rel-4.0.2
./autogen.sh --without-alllang --with-python
./configure --without-pcre
make
make install
popd

yum install -y openblas-devel${MARCH_SUFFIX}

pip install -r recipe/cibw_before_requirements.txt