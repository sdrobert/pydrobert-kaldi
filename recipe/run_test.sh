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

export LC_ALL=C

# c++ tests
# readonly SITE_PACKAGES_DIR=$($PYTHON -c  "import site; print(site.getsitepackages()[0])")
# if [ "`uname`" != "Darwin" ]; then
#   export CC=${PREFIX}/bin/gcc
#   export CXX=${PREFIX}/bin/g++
#   ln -s $SITE_PACKAGES_DIR/pydrobert/kaldi/_internal.* libinternal.so
# else
#   ln -s $SITE_PACKAGES_DIR/pydrobert/kaldi/_internal.* libinternal.dylib
# fi
# export CXXFLAGS="$CXXFLAGS -DKALDI_DOUBLEPRECISION=0"
# readonly BLAS_VARIANT=$(echo "$PKG_NAME" | cut -d '-' -f 3)
# case $BLAS_VARIANT in
#   atlas)
#     export CXXFLAGS="$CXXFLAGS -DHAVE_ATLAS"
#     ;;
#   openblas)
#     export CXXFLAGS="$CXXFLAGS -DHAVE_OPENBLAS"
#     ;;
#   *)
#     echo -e "Invalid blas variant: $BLAS_VARIANT"
#     exit 1
# esac

# for file_name in tests/src/*/* ; do
#   out_name=$(echo $file_name | cut -d '/' -f 4 | cut -d '.' -f 1)
#   $CXX -L. -Isrc -linternal $file_name -o $out_name
#   ./$out_name
# done

# python tests
py.test tests/python || exit 1
