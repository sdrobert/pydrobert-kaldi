#ifndef _PYDROBERT_KALDI_MATRIX_H_
#define _PYDROBERT_KALDI_MATRIX_H_

#include "matrix/kaldi-matrix.h"

template <typename Real>
class NumpyMatrix : public kaldi::Matrix<Real> {
public:
  void SetData(const Real* matrix_in, const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col);
  bool ReadDataInto(const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col,
                    Real* matrix_inout) const;
};

template class NumpyMatrix<float>;
template class NumpyMatrix<double>;

#endif  // _PYDROBERT_KALDI_MATRIX_H_