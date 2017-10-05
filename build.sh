# Copyright 2016 Sean Robertson

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# readonly BLAS_VARIANT=$(echo "$PKG_NAME" | cut -d '-' -f 3)
# case $BLAS_VARIANT in
#   openblas)
#     export OPENBLASROOT="${CONDA_PREFIX}"
#     ;;
#   atlas)
#     echo -e "\
# As of writing, conda's ATLAS build does not have the requisite headers for an
# ATLAS build. This build will likely fail."
#     export ATLASROOT="${CONDA_PREFIX}"
#     ;;
#   mkl)
#     echo -e "\
# As of writing, conda's MKL build does not have the requisite headers for an
# MKL build. This build will likely fail."
#     export MKLROOT="${CONDA_PREFIX}"
#     ;;
#   *)
#     echo -e "Invalid blas variant: $BLAS_VARIANT"
#     exit 1
# esac

which gcc

OPENBLASROOT="${CONDA_PREFIX}" ${PYTHON} "${RECIPE_DIR}/setup.py" install \
  --single-version-externally-managed \
  --record=record.txt || exit 1
