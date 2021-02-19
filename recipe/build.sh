# Copyright 2017 Sean Robertson

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

if [ $blas_impl = "mkl" ]; then
  export MKLROOT="${PREFIX}"
elif [ $blas_impl = "accelerate" ]; then
  export ACCELERATE=1
elif [ $blas_impl = "openblas" ]; then
  export OPENBLASROOT="${PREFIX}"
else
  1>&2 echo Unknown blas_impl
  exit 1
fi

export SETUPTOOLS_SCM_PRETEND_VERSION="${PKG_VERSION}"

${PYTHON} setup.py install \
  --single-version-externally-managed \
  --record=record.txt || exit 1
