if [ "`uname`" != "Darwin" ]; then
  export CC=${PREFIX}/bin/gcc
  export CXX=${PREFIX}/bin/g++
fi

readonly BLAS_VARIANT=$(echo "$PKG_NAME" | cut -d '-' -f 3)
case $BLAS_VARIANT in
  atlas)
    export ATLASROOT="${CONDA_PREFIX}"
    ;;
  openblas)
    export OPENBLASROOT="${CONDA_PREFIX}"
    ;;
  *)
    echo -e "Invalid blas variant: $BLAS_VARIANT"
    exit 1
esac

${PYTHON} "${RECIPE_DIR}/setup.py" install --single-version-externally-managed --record=record.txt || exit 1
