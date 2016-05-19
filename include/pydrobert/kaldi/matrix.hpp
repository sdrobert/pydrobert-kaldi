#ifndef _PYDROBERT_KALDI_MATRIX_H_
#define _PYDROBERT_KALDI_MATRIX_H_

#include "matrix/kaldi-matrix.h"

template <typename Real>
class NumpyMatrix : public kaldi::Matrix<Real> {
public:
  void SetData(const Real* matrix_in, const long dim_row, const long dim_col);
  bool ReadDataInto(const long dim_row, const long dim_col,
                    Real* matrix_inout) const;
};

template class NumpyMatrix<float>;
template class NumpyMatrix<double>;

#endif  // _PYDROBERT_KALDI_MATRIX_H_