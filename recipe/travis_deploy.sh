#! /bin/bash

set -e

echo "From travis deploy: ${PY_VER} $1"

if [[ "${PY_VER}" == "2.7" ]]; then
  echo "In py2 block"
  conda build recipe --skip-existing -m recipe/ci_py2_deploy.yaml
else
  echo "In py3 block"
  conda build recipe --skip-existing -m recipe/ci_py3_deploy.yaml
fi

anaconda -t ${ANACONDA_TOKEN} upload \
  -u sdrobert \
  --register \
  ${HOME}/miniconda/conda-bld/*/pydrobert-kaldi-*.tar.bz2
