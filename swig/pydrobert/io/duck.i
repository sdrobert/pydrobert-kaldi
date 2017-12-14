/* -*- C++ -*-

 Copyright 2017 Sean Robertson

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
#include <string>
#include <istream>
#include <ostream>
#include "base/io-funcs.h"
#include "feat/wave-reader.h"
#include "matrix/kaldi-matrix.h"
#include "matrix/kaldi-vector.h"
#include "util/kaldi-io.h"
#include "util/text-utils.h"
#include "util/kaldi-holder.h"
%}

namespace kaldi {
  class Input {
    public:
      bool Open(const std::string &rxfilename, bool *OUTPUT);
      long Close();
  };
  class Output {
    public:
      bool Open(const std::string &wxfilename, bool binary, bool write_header);
      long Close();
  };
}

%define EXTEND_IO_WITH_REAL(Real, RealName)

// stores matrix/vector read-only in first argument, dim in second. C-contiguous
// Kaldi always keeps rows contiguous, but not necessarily columns
%apply (Real* IN_ARRAY1, kaldi::MatrixIndexT DIM1)
       {(const Real *vec_in, const kaldi::MatrixIndexT len)};
%apply (Real* IN_ARRAY2, kaldi::MatrixIndexT DIM1, kaldi::MatrixIndexT DIM2)
       {(const Real* matrix_in, const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col)};
// will allocate into first, storing dimensions into later
%apply (Real** ARGOUTVIEWM_ARRAY1, kaldi::MatrixIndexT* DIM1)
       {(Real** vec_out, kaldi::MatrixIndexT* len)};
%apply (Real** ARGOUTVIEWM_ARRAY2, kaldi::MatrixIndexT* DIM1, kaldi::MatrixIndexT* DIM2)
       {(Real** matrix_out, kaldi::MatrixIndexT* dim_row, kaldi::MatrixIndexT* dim_col)};

%extend kaldi::Input {
  void ReadVector ## RealName (bool binary,
                               Real** vec_out, kaldi::MatrixIndexT* len) {
    kaldi::Vector<Real > vec;
    vec.Read($self->Stream(), binary);
    const kaldi::MatrixIndexT dim = vec.Dim();
    *vec_out = (Real*) std::malloc(dim * sizeof(Real));
    std::memcpy(*vec_out, vec.Data(), dim * sizeof(Real));
    *len = dim;
  };

  void ReadMatrix ## RealName(bool binary,
                              Real **matrix_out,
                              kaldi::MatrixIndexT *dim_row,
                              kaldi::MatrixIndexT *dim_col) {
    kaldi::Matrix<Real > matr;
    matr.Read($self->Stream(), binary);
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

%extend kaldi::Output {
  void WriteVector ## RealName (bool binary,
                                const Real *vec_in,
                                const kaldi::MatrixIndexT len) {
    kaldi::Vector<Real> vec(len, kaldi::kUndefined);
    if (len) std::memcpy(vec.Data(), vec_in, len * sizeof(Real));
    vec.Write($self->Stream(), binary);
  };

  void WriteMatrix ## RealName (bool binary,
                                const Real *matrix_in,
                                const kaldi::MatrixIndexT dim_row,
                                const kaldi::MatrixIndexT dim_col) {
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
    matrix.Write($self->Stream(), binary);
  };
}

// %clear (const Real* matrix_in, const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col);
// %clear (const Real *vec_in, const kaldi::MatrixIndexT len);
// %clear (Real** vec_out, kaldi::MatrixIndexT* len);
// %clear (Real** matrix_out, kaldi::MatrixIndexT* dim_row, kaldi::MatrixIndexT* dim_col);

%enddef

EXTEND_IO_WITH_REAL(float, Float)
EXTEND_IO_WITH_REAL(double, Double)

%apply (kaldi::BaseFloat* IN_ARRAY2, kaldi::MatrixIndexT DIM1, kaldi::MatrixIndexT DIM2)
      {(const kaldi::BaseFloat* matrix_in, const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col)};
%apply (kaldi::BaseFloat** ARGOUTVIEWM_ARRAY2, kaldi::MatrixIndexT* DIM1, kaldi::MatrixIndexT* DIM2)
      {(kaldi::BaseFloat** matrix_out, kaldi::MatrixIndexT* dim_row, kaldi::MatrixIndexT* dim_col)};

%extend kaldi::Input {

  bool OpenWithoutHeader(const std::string &rxfilename) {
    return $self->Open(rxfilename);
  }

  // TODO(sdrobert): add ReadWaveInfo to avoid unnecessary copies

  void ReadWaveData(kaldi::BaseFloat **matrix_out,
                  kaldi::MatrixIndexT *dim_row,
                  kaldi::MatrixIndexT *dim_col,
                  double *OUTPUT) // samp_freq
  {
    kaldi::WaveData wave_data;
    wave_data.Read($self->Stream());
    const kaldi::Matrix<kaldi::BaseFloat > &matr = wave_data.Data();
    const kaldi::MatrixIndexT num_rows = matr.NumRows();
    const kaldi::MatrixIndexT num_cols = matr.NumCols();
    const kaldi::MatrixIndexT stride = matr.Stride();
    *matrix_out = (kaldi::BaseFloat*) std::malloc(sizeof(kaldi::BaseFloat) * num_rows * num_cols);
    if (stride == num_cols) {
      // contiguous
      std::memcpy(*matrix_out, matr.Data(), sizeof(kaldi::BaseFloat) * num_rows * num_cols);
    } else {
      // rows are contiguous, but distance between them is not necessarily
      for (kaldi::MatrixIndexT row = 0; row < num_rows; ++row) {
        std::memcpy((*matrix_out) + (row * num_cols), matr.Data() + (row * stride),
                    num_cols * sizeof(kaldi::BaseFloat));
      }
    }
    *dim_row = num_rows;
    *dim_col = num_cols;
    *OUTPUT = static_cast<double >(wave_data.SampFreq());
  };

  std::string ReadToken(bool binary) {
    std::string out_token;
    kaldi::ReadToken($self->Stream(), binary, &out_token);
    return out_token;
  };

  std::vector<std::string > ReadTokenVector() {
    // this is not defined in kaldi, so we'll base it off the
    // TokenVectorHolder's construction.
    std::istream &is = $self->Stream();
    std::string line;
    getline(is, line);
    if (is.fail()) {
      KALDI_ERR << "ReadTokenVector, failed to read at file position "
                << is.tellg();
    }
    const char *white_chars = " \t\n\r\f\v";
    std::vector<std::string > out_tvec;
    kaldi::SplitStringToVector(line, white_chars, true, &out_tvec);
    return out_tvec;
  };
}

%extend kaldi::Output {

  void WriteWaveData(const kaldi::BaseFloat *matrix_in,
                     const kaldi::MatrixIndexT dim_row,
                     const kaldi::MatrixIndexT dim_col,
                     kaldi::BaseFloat samp_freq) {
    if (!(dim_row * dim_col)) {
      PyErr_SetString(PyExc_ValueError, "Cannot write an empty wave file");
      return;
    }
    kaldi::Matrix<kaldi::BaseFloat> matrix(dim_row, dim_col,
                               kaldi::kUndefined, kaldi::kStrideEqualNumCols);
    std::memcpy(matrix.Data(), matrix_in,
                dim_row * dim_col * sizeof(kaldi::BaseFloat));
    // I'm not sure if this copy gets optimized into a swap...
    const kaldi::WaveData wave_data(samp_freq, matrix);
    wave_data.Write($self->Stream());
  };

  void WriteToken(bool binary, const std::string& token) {
    if (!kaldi::IsToken(token)) {
      PyErr_SetString(PyExc_ValueError, "Value is not a token");
      return;
    }
    kaldi::WriteToken($self->Stream(), binary, token);
  }

  void WriteTokenVector(const std::vector<std::string >& token_vec) {
    for (std::vector<std::string >::const_iterator iter = token_vec.begin();
         iter != token_vec.end(); ++iter) {
      if (!kaldi::IsToken(*iter)) {
        PyErr_SetString(PyExc_ValueError, "At least one element is not a token");
        return;
      }
    }
    std::ostream &os = $self->Stream();
    // now do it again, with writing
    for (std::vector<std::string >::const_iterator iter = token_vec.begin();
         iter != token_vec.end(); ++iter) {
      os << *iter << ' ';
      if (os.fail()) {
        throw std::runtime_error("Write failure in WriteTokenVector.");
      }
    }
    os << '\n';
    if (os.fail()) {
        throw std::runtime_error("Write failure in WriteTokenVector.");
    }
  };

}

// %clear (const kaldi::BaseFloat* matrix_in, const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col);
// %clear (kaldi::BaseFloat** matrix_out, kaldi::MatrixIndexT* dim_row, kaldi::MatrixIndexT* dim_col);

%define EXTEND_IO_WITH_BASIC_NAME_AND_TYPE(Suffix, HolderName, ValType...)
%extend kaldi::Input {
  ValType Read ## Suffix() {
    HolderName holder;
    std::istream &is = $self->Stream();
    if (!holder.Read(is)) {
      PyErr_SetString(PyExc_IOError, "Unable to read basic type");
    }
    ValType val = holder.Value();
    return val;
  };
}
%extend kaldi::Output {
  void Write ## Suffix(bool binary, ValType val) {
    if (!HolderName ## ::Write($self->Stream(), binary, val)) {
      PyErr_SetString(PyExc_IOError, "Unable to write basic type");
    }
  };
}
%enddef

// int
EXTEND_IO_WITH_BASIC_NAME_AND_TYPE(Int32, kaldi::BasicHolder<int32_t >, int32_t);
EXTEND_IO_WITH_BASIC_NAME_AND_TYPE(Int32Vector, kaldi::BasicVectorHolder<int32_t >, std::vector<int32_t >);
EXTEND_IO_WITH_BASIC_NAME_AND_TYPE(Int32VectorVector, kaldi::BasicVectorVectorHolder<int32_t >, std::vector<std::vector<int32_t > >);
EXTEND_IO_WITH_BASIC_NAME_AND_TYPE(Int32PairVector, kaldi::BasicPairVectorHolder<int32_t >, std::vector<std::pair<int32_t, int32_t > >);

// double
EXTEND_IO_WITH_BASIC_NAME_AND_TYPE(Double, kaldi::BasicHolder<double >, double);

// base float
#if KALDI_DOUBLEPRECISION
EXTEND_IO_WITH_BASIC_NAME_AND_TYPE(BaseFloat, kaldi::BasicHolder<double >, double);
EXTEND_IO_WITH_BASIC_NAME_AND_TYPE(BaseFloatPairVector, kaldi::BasicPairVectorHolder<double >, std::vector<std::pair<double, double > >);
#else
EXTEND_IO_WITH_BASIC_NAME_AND_TYPE(BaseFloat, kaldi::BasicHolder<float >, float);
EXTEND_IO_WITH_BASIC_NAME_AND_TYPE(BaseFloatPairVector, kaldi::BasicPairVectorHolder<float >, std::vector<std::pair<float, float > >);
#endif

// bool
EXTEND_IO_WITH_BASIC_NAME_AND_TYPE(Bool, kaldi::BasicHolder<bool >, bool);
