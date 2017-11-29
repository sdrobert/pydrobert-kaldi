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

if [ ! -z "${NOMKL}" ] && [ ${NOMKL} = 1 ]; then
  if [ `uname` = "Darwin" ]; then
    export ACCELERATE=1
  else
    export OPENBLASROOT="${CONDA_PREFIX}"
  fi
else
  export MKLROOT="${CONDA_PREFIX}"
fi

${PYTHON} setup.py install \
  --single-version-externally-managed \
  --record=record.txt || exit 1
