if [ "`uname`" != "Darwin" ]; then
  export CC=${PREFIX}/bin/gcc
  export CXX=${PREFIX}/bin/g++
fi

readonly BLAS_VARIANT=$(echo "$PKG_NAME" | cut -d '-' -f 3)
case $BLAS_VARIANT in
  openblas)
    export OPENBLASROOT="${CONDA_PREFIX}"
    ;;
  atlas)
    echo -e "\
As of writing, conda's ATLAS build does not have the requisite headers for an
ATLAS build. This build will likely fail."
    export ATLASROOT="${CONDA_PREFIX}"
    ;;
  mkl)
    echo -e "\
As of writing, conda's MKL build does not have the requisite headers for an
MKL build. This build will likely fail."
    export MKLROOT="${CONDA_PREFIX}"
    ;;
  *)
    echo -e "Invalid blas variant: $BLAS_VARIANT"
    exit 1
esac

${PYTHON} "${RECIPE_DIR}/setup.py" install \
  --single-version-externally-managed \
  --record=record.txt || exit 1
