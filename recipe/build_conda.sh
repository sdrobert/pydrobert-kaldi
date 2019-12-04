# !/usr/bin/env bash
# Travis CI Conda building

set -e -x

[ ! -z "$PY_VER" ] || exit 1

recipe_dir=$(dirname "$0")
dist_dir="$1"
shift

conda config --set always_yes yes --set changeps1 no
conda update -q conda
conda install conda-build conda-verify

# this doesn't seem to work when using a 64-bit conda to build a 32-bit package
_old="${CONDA_SUBDIR}"
export CONDA_SUBDIR="${CONDA_SUBDIR:-$(basename "${dist_dir}")}"
conda build "${recipe_dir}" \
  --python "${PY_VER}" \
  -m "${recipe_dir}/ci_build.yaml" "$@"
export CONDA_SUBDIR="${_old}"

"$(conda info --base)/bin/python" \
  "${recipe_dir}/copy_conda_build_packages.py" \
  pydrobert-kaldi "${dist_dir}"

conda build purge
