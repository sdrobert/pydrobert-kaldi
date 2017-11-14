#! /usr/bin/env bash

source deactivate || true

conda build purge

if [[ "$TRAVIS_PYTHON_VERSION" == "2.7" ]]; then
  conda build recipe -m recipe/travis_py2_conda_build_config.yaml
else
  conda build recipe -m recipe/travis_py3_conda_build_config.yaml
fi
anaconda -t ${ANACONDA_TOKEN} upload ${HOME}/miniconda/conda-bld/pydrobert-kaldi-*.tar.bz2
