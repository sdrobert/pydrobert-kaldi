#! /bin/bash

# for dev branch, only build 2.7 and 3.6. Otherwise, build the lot of em

if [ "$1" = "dev" ]; then
  label=dev
elif [ "$1" = "main" ]; then
  label=main;
  if [[ "$TRAVIS_PYTHON_VERSION" == "2.7" ]]; then
    conda build recipe -m recipe/travis_py2_conda_build_config.yaml
  else
    conda build recipe -m recipe/travis_py3_conda_build_config.yaml
  fi
fi

anaconda -t ${ANACONDA_TOKEN} upload \
  -u sdrobert \
  --register \
  ${HOME}/miniconda/conda-bld/*/pydrobert-kaldi-*.tar.bz2 \
  -l $label
