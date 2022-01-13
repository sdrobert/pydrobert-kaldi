#! /usr/bin/env bash

set -e -x

if command -v yum &> /dev/null; then
  install_command="yum install -y"
  openblas_pkg=openblas-devel
  atlas_pkg=atlas-devel
else
  install_command="apk add"
  openblas_pkg=openblas-dev
  atlas_pkg=atlas-dev
  $install_command libexecinfo-dev || true
fi

if ! command -v curl; then
  $install_command add curl 
  command -v curl
fi

if ! command -v swig; then
  if ! $install_command 'swig=4.0.2-r4' || ! command -v swig; then
    # build swig 4.0.2
    tmpdir=$(mktemp -d)
    pushd $tmpdir
    curl -L https://github.com/swig/swig/archive/rel-4.0.2.tar.gz > rel-4.0.2
    [ "$(md5sum rel-4.0.2 | cut -d' ' -f 1)" = "19a61126f0f89c56b2c2e9e39cc33efe" ]
    tar -xf rel-4.0.2
    cd swig-rel-4.0.2
    ./autogen.sh --without-alllang --with-python
    ./configure --without-pcre
    make
    make install
    popd
    command -v swig
  fi
fi

if [ ! -z "${OPENBLASROOT}" ]; then
  if [ ! -f "${OPENBLASROOT}/include/cblas.h" ] ; then
    $install_command $openblas_pkg
    find "${OPENBLASROOT}" \( -name 'cblas.h' -o -name 'lapacke.h' -o -name 'libopenblas.so' \)
  fi
fi
if [ ! -z "${ATLASROOT}" ]; then
  if [ ! -f "${ATLASROOT}/include/cblas.h" ] ; then
    $install_command $atlas_pkg
    find "${ATLASROOT}" \( -name 'cblas.h' -o -name 'clapack.h' -o -name 'libatlas.so' \)
  fi
fi