#! /usr/bin/env bash
# Travis CI manylinux build (PyPI)

set -e -x

if [ `uname -m` = 'x86_64' ]; then
  MARCH_SUFFIX=.x86_64
else
  MARCH_SUFFIX=.i386
fi

ls

# PY_VER is in form x.y... want xy
PY_VER_CONTR=${PY_VER:0:1}${PY_VER:2:3}

if [ "${PY_VER}" = "2.7" ]; then
  PYBINS=( "/opt/python/cp27-cp27mu/bin" "/opt/python/cp27-cp27m/bin" )
else
  PYBINS=( "/opt/python/cp${PY_VER_CONTR}-cp${PY_VER_CONTR}m/bin" )
fi

# yum install -y wget
yum install -y curl || true

# build swig 3.0.8
tmpdir=$(mktemp -d)
pushd $tmpdir
curl -L https://github.com/swig/swig/archive/rel-3.0.8.tar.gz > rel-3.0.8
[ "$(md5sum rel-3.0.8 | cut -d' ' -f 1)" = "9b5862b1d782b111d87fce9216a2d465" ]
tar -xf rel-3.0.8
cd swig-rel-3.0.8
./autogen.sh --without-alllang --with-python
./configure --without-pcre
make
make install
popd

# install openblas
yum install -y openblas-devel${MARCH_SUFFIX}

for PYBIN in "${PYBINS[@]}"; do
  # FIXME(sdrobert): wheel version based on https://github.com/pypa/auditwheel/issues/102
  "${PYBIN}/pip" install -U pip setuptools numpy wheel==0.31.1
  "${PYBIN}/pip" install -r /io/requirements.txt
  "${PYBIN}/pip" wheel /io/ -w dist --no-deps
done

for whl in dist/pydrobert*.whl; do
    auditwheel repair "$whl" -w /io/dist-linux-py${PY_VER}
done
