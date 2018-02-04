#! /usr/bin/env bash
# Used to pass arguments to build_conda when building via docker

/io/recipe/build_conda.sh /io/dist-linux-py${PY_VER} || exit 1
