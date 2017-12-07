#! /bin/bash

set -e

if [[ "$TRAVIS_PYTHON_VERSION" == "2.7" ]]; then
  conda build recipe --skip-existing -m recipe/ci_py2_deploy.yaml
else
  conda build recipe --skip-existing -m recipe/ci_py3_deploy.yaml
fi

anaconda -t ${ANACONDA_TOKEN} upload \
  -u sdrobert \
  --register \
  ${HOME}/miniconda/conda-bld/*/pydrobert-kaldi-*.tar.bz2
