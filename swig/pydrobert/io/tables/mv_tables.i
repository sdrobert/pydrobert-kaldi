/* -*- C++ -*-

 Copyright 2016 Sean Robertson

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 
*/

%{
  #include "matrix/kaldi-matrix.h"
  #include "matrix/kaldi-vector.h"
%}

namespace kaldi {
  template <typename Real> class Vector {};
  template <typename Real> class Matrix {};
}

%define EXTEND_MV_WITH_REAL(Real, RealName)

// stores matrix/vector read-only in first argument, dim in second. C-contiguous
// Kaldi always keeps rows contiguous, but not necessarily columns
%apply(Real* IN_ARRAY1, kaldi::MatrixIndexT DIM1) {(const Real *vec_in, const kaldi::MatrixIndexT len)}
%apply(Real* IN_ARRAY2, kaldi::MatrixIndexT DIM1, kaldi::MatrixIndexT DIM2) {(const Real* matrix_in, const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col)}
// will allocate into first, storing dimensions into later
%apply(Real** ARGOUTVIEWM_ARRAY1, kaldi::MatrixIndexT* DIM1) {(Real** vec_out, kaldi::MatrixIndexT* len)}
%apply(Real** ARGOUTVIEWM_ARRAY2, kaldi::MatrixIndexT* DIM1, kaldi::MatrixIndexT* DIM2) {(Real** matrix_out, kaldi::MatrixIndexT* dim_row, kaldi::MatrixIndexT* dim_col)}

%extend kaldi::TableWriter<kaldi::KaldiObjectHolder<kaldi::Vector<Real > > > {
  void Write(const std::string &key,
             const Real *vec_in, const kaldi::MatrixIndexT len) const {
    kaldi::Vector<Real> vector(len, kaldi::kUndefined);
    if (len) std::memcpy(vector.Data(), vec_in, len * sizeof(Real));
    $self->Write(key, vector);
  };
}
%extend kaldi::TableWriter<kaldi::KaldiObjectHolder<kaldi::Matrix<Real> > > {
  void Write(const std::string &key,
                 const Real *matrix_in,
                 const kaldi::MatrixIndexT dim_row,
                 const kaldi::MatrixIndexT dim_col) const {
    kaldi::MatrixIndexT effective_dim_row = dim_row;
    kaldi::MatrixIndexT effective_dim_col = dim_col;
    if (!(dim_row && dim_col)) {
      // numpy can pass matrices with only one zero-dimension axis, but
      // kaldi can't handle that
      effective_dim_col = 0;
      effective_dim_row = 0;
    }
    kaldi::Matrix<Real> matrix(effective_dim_row, effective_dim_col,
                               kaldi::kUndefined, kaldi::kStrideEqualNumCols);
    if (effective_dim_row) {
      std::memcpy(matrix.Data(), matrix_in, dim_row * dim_col * sizeof(Real));
    }
    $self->Write(key, matrix);
  };
}
%extend kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<kaldi::Vector<Real > > > {
  void Value(Real **vec_out, kaldi::MatrixIndexT *len) {
    const kaldi::Vector<Real > &vec = $self->Value();
    const kaldi::MatrixIndexT dim = vec.Dim();
    *vec_out = (Real*) std::malloc(dim * sizeof(Real));
    std::memcpy(*vec_out, vec.Data(), dim * sizeof(Real));
    *len = dim;
  };
}
%extend kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<kaldi::Matrix<Real > > > {
  void Value(Real **matrix_out,
             kaldi::MatrixIndexT *dim_row,
             kaldi::MatrixIndexT *dim_col) {
    const kaldi::Matrix<Real > &matr = $self->Value();
    const kaldi::MatrixIndexT num_rows = matr.NumRows();
    const kaldi::MatrixIndexT num_cols = matr.NumCols();
    const kaldi::MatrixIndexT stride = matr.Stride();
    *matrix_out = (Real*) std::malloc(sizeof(Real) * num_rows * num_cols);
    if (stride == num_cols) {
      // contiguous
      std::memcpy(*matrix_out, matr.Data(), sizeof(Real) * num_rows * num_cols);
    } else {
      // rows are contiguous, but distance between them is not necessarily
      for (kaldi::MatrixIndexT row = 0; row < num_rows; ++row) {
        std::memcpy((*matrix_out) + (row * num_cols), matr.Data() + (row * stride),
                    num_cols * sizeof(Real));
      }
    }
    *dim_row = num_rows;
    *dim_col = num_cols;
  };
}
%extend kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<kaldi::Vector<Real > > > {
  void Value(const std::string &key, Real **vec_out, kaldi::MatrixIndexT *len) {
    const kaldi::Vector<Real > &vec = $self->Value(key);
    const kaldi::MatrixIndexT dim = vec.Dim();
    *vec_out = (Real*) std::malloc(dim * sizeof(Real));
    std::memcpy(*vec_out, vec.Data(), dim * sizeof(Real));
    *len = dim;
  };
}
%extend kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<kaldi::Matrix<Real > > > {
  void Value(const std::string &key, Real **matrix_out,
             kaldi::MatrixIndexT *dim_row,
             kaldi::MatrixIndexT *dim_col) {
    const kaldi::Matrix<Real > &matr = $self->Value(key);
    const kaldi::MatrixIndexT num_rows = matr.NumRows();
    const kaldi::MatrixIndexT num_cols = matr.NumCols();
    const kaldi::MatrixIndexT stride = matr.Stride();
    *matrix_out = (Real*) std::malloc(sizeof(Real) * num_rows * num_cols);
    if (stride == num_cols) {
      std::memcpy(*matrix_out, matr.Data(), sizeof(Real) * num_rows * num_cols);
    } else {
      for (kaldi::MatrixIndexT row = 0; row < num_rows; ++row) {
        std::memcpy((*matrix_out) + (row * num_cols), matr.Data() + (row * stride),
                    num_cols * sizeof(Real));
      }
    }
    *dim_row = num_rows;
    *dim_col = num_cols;
  };
}

// %clear (const Real *vec_in, const kaldi::MatrixIndexT len);
// %clear (const Real* matrix_in, const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col);
// %clear (Real** vec_out, kaldi::MatrixIndexT* len);
// %clear (Real** matrix_out, kaldi::MatrixIndexT* dim_row, kaldi::MatrixIndexT* dim_col);

TEMPLATE_WITH_KOBJECT_NAME_AND_TYPE(RealName ## Vector, kaldi::Vector<Real>)
TEMPLATE_WITH_KOBJECT_NAME_AND_TYPE(RealName ## Matrix, kaldi::Matrix<Real>)

%enddef
EXTEND_MV_WITH_REAL(double, Double)
EXTEND_MV_WITH_REAL(float, Float)

