#! /bin/bash

set -e

echo "From travis deploy: ${PY_VER} $1"

if [[ "${PY_VER}" == "2.7" ]]; then
  conda build recipe --skip-existing -m recipe/ci_py2_deploy.yaml
else
  conda build recipe --skip-existing -m recipe/ci_py3_deploy.yaml
fi

sleep 1
exit 1

anaconda -t ${ANACONDA_TOKEN} upload \
  -u sdrobert \
  --register \
  ${HOME}/miniconda/conda-bld/*/pydrobert-kaldi-*.tar.bz2
