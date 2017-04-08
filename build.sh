if [ "`uname`" != "Darwin" ]; then
  export CC=${PREFIX}/bin/gcc
  export CXX=${PREFIX}/bin/g++
fi

OPENBLASROOT="${CONDA_PREFIX}" ${PYTHON} setup.py install --single-version-externally-managed --record record.txt || exit 1
