#include "pydrobert/kaldi/matrix.hpp"

template<typename Real>
void NumpyMatrix<Real>::SetData(const Real* matrix_in,
                                        const long dim_row,
                                        const long dim_col) {
  if ((dim_row || dim_col) && !(dim_row * dim_col)) {
    // numpy can pass (x, 0) or (0, x) into this signature, but Kaldi can't
    // handle it
    return SetData(matrix_in, 0, 0);
  }
  if (kaldi::Matrix<Real>::NumRows() != dim_row ||
      kaldi::Matrix<Real>::NumCols() != dim_col) {
    kaldi::Matrix<Real>::Resize(dim_row, dim_col, kaldi::kUndefined);
  }
  const long stride = kaldi::Matrix<Real>::Stride();
  Real* data = kaldi::Matrix<Real>::Data();
  if (stride == dim_col) {
    // copy contiguously
    std::memcpy(data, matrix_in, dim_row * dim_col * sizeof(Real));
  } else {
    // stride != cols means matrix isn't contiguous, but rows are :D
    for (long row = 0; row < dim_row; ++row) {
      std::memcpy(data + (row * stride), matrix_in + (row * dim_col),
                  dim_col * sizeof(Real));
    }
  }
}

template<typename Real>
bool NumpyMatrix<Real>::ReadDataInto(const long dim_row,
                                             const long dim_col,
                                             Real* matrix_inout) const {
  if (!(dim_row * dim_col)) {
    return (!kaldi::Matrix<Real>::NumRows() || !kaldi::Matrix<Real>::NumCols());
  }
  if (kaldi::Matrix<Real>::NumRows() != dim_row ||
      kaldi::Matrix<Real>::NumCols() != dim_col) {
    return false;
  }
  const long stride = kaldi::Matrix<Real>::Stride();
  const Real* data = kaldi::Matrix<Real>::Data();
  if (stride == dim_col) {
    std::memcpy(matrix_inout, data, dim_row * dim_col * sizeof(Real));
  } else {
    for (long row = 0; row < dim_row; ++row) {
      std::memcpy(matrix_inout + (row * dim_col), data + (row * stride),
                  dim_col * sizeof(Real));
    }
  }
  return true;
}
