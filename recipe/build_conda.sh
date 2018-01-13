# !/usr/bin/env bash
# Travis CI Conda building

set -e -x

[ $# = 1 ] || exit 1
[ ! -z "$PY_VER" ] || exit 1

recipe_dir=$(dirname "$0")
dist_dir="$1"

conda config --set always_yes yes --set changeps1 no
conda update -q --all
conda install conda-build
conda build "${recipe_dir}" \
  --python "${PY_VER}" \
  -m "${recipe_dir}/ci_build.yaml" \
  --output-folder "${dist_dir}"
