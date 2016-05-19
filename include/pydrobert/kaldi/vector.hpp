#ifndef PYDROBERT_KALDI_VECTOR_H_
#define PYDROBERT_KALDI_VECTOR_H_

#include "matrix/kaldi-vector.h"

// subclassing vector allows us to resize with Read/Write, but does not allow
// us to use numpy memory directly.
template<typename Real>
class NumpyVector : public kaldi::Vector<Real> {
public:
  // SetData copies data from Real array into internal memory
  void SetData(const Real* vec_in, const long len);
  // ReadDataInto reads the existing data pointer into memory assumed allocated
  // len better match Dim()
  bool ReadDataInto(const long len, Real* vec_inout) const;
};

// template instantiation
template class NumpyVector<float>;
template class NumpyVector<double>;

#endif // PYDROBERT_KALDI_VECTOR_H_
