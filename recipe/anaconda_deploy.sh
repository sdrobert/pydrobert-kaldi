#! /bin/bash

source deactivate || true

# if [[ "$TRAVIS_PYTHON_VERSION" == "2.7" ]]; then
#   conda build recipe -m recipe/travis_py2_conda_build_config.yaml
# else
#   conda build recipe -m recipe/travis_py3_conda_build_config.yaml
# fi
anaconda -t ${ANACONDA_TOKEN} upload -u sdrobert --register ${HOME}/miniconda/conda-bld/pydrobert-kaldi-*.tar.bz2
