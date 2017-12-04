#! /bin/bash

if [[ "$TRAVIS_PYTHON_VERSION" == "2.7" ]]; then
  mv recipe/travis_py2_conda_build_config.yaml recipe/conda_build_config.yaml
else
  mv recipe/travis_py3_conda_build_config.yaml recipe/conda_build_config.yaml
fi
rm recipe/travis_*.yaml
conda build recipe --skip-existing

anaconda -t ${ANACONDA_TOKEN} upload \
  -u sdrobert \
  --register \
  ${HOME}/miniconda/conda-bld/*/pydrobert-kaldi-*.tar.bz2
