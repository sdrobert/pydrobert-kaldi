#! /usr/bin/env bash
# Travis CI manylinux test

set -e -x

PY_VER_CONTR=${PY_VER:0:1}${PY_VER:2:3}

if [ "${PY_VER}" = "2.7" ]; then
  PYBINS=( "/opt/python/cp27-cp27mu/bin" "/opt/python/cp27-cp27m/bin" )
else
  PYBINS=( "/opt/python/cp${PY_VER_CONTR}-cp${PY_VER_CONTR}m/bin" )
fi

cd /io

for PYBIN in "${PYBINS[@]}"; do
  "${PYBIN}/pip" install pytest
  "${PYBIN}/pip" install pydrobert-kaldi -f dist-linux-py${PY_VER}
  "${PYBIN}/pytest" tests/python -m "not pytorch"
done
