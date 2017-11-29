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

// #if KALDI_DOUBLEPRECISION
// %numpy_typemaps(kaldi::BaseFloat, NPY_DOUBLE, kaldi::MatrixIndexT);
// #else
// %numpy_typemaps(kaldi::BaseFloat, NPY_FLOAT, kaldi::MatrixIndexT);
// #endif
%apply(kaldi::BaseFloat* IN_ARRAY2, kaldi::MatrixIndexT DIM1, kaldi::MatrixIndexT DIM2) {(const kaldi::BaseFloat* matrix_in, const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col)};
%apply(kaldi::BaseFloat** ARGOUTVIEWM_ARRAY2, kaldi::MatrixIndexT* DIM1, kaldi::MatrixIndexT* DIM2) {(kaldi::BaseFloat** matrix_out, kaldi::MatrixIndexT* dim_row, kaldi::MatrixIndexT* dim_col)};

%{
  #include "feat/wave-reader.h"
%}

namespace kaldi {
  class WaveData {};
  class WaveHolder {
  public:
    typedef WaveData T;
  };
  class WaveInfoHolder {
  public:
    typedef WaveData T;
  };
}

%extend kaldi::SequentialTableReader<kaldi::WaveHolder > {
  void Value(kaldi::BaseFloat **matrix_out,
             kaldi::MatrixIndexT *dim_row,
             kaldi::MatrixIndexT *dim_col) {
    const kaldi::Matrix<kaldi::BaseFloat > &matr = $self->Value().Data();
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
  };

  kaldi::BaseFloat SampFreq() { return $self->Value().SampFreq(); };
  kaldi::BaseFloat Duration() { return $self->Value().Duration(); };
}

%extend kaldi::RandomAccessTableReaderMapped<kaldi::WaveHolder > {
  void Value(const std::string &key, kaldi::BaseFloat **matrix_out,
             kaldi::MatrixIndexT *dim_row,
             kaldi::MatrixIndexT *dim_col) {
    const kaldi::Matrix<kaldi::BaseFloat > &matr = $self->Value(key).Data();
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
  };

  kaldi::BaseFloat SampFreq(const std::string &key) {
    return $self->Value(key).SampFreq();
  };
  kaldi::BaseFloat Duration(const std::string &key) {
    return $self->Value(key).Duration();
  };
}

%extend kaldi::TableWriter<kaldi::WaveHolder > {
  void Write(const std::string &key,
                 const kaldi::BaseFloat *matrix_in,
                 const kaldi::MatrixIndexT dim_row,
                 const kaldi::MatrixIndexT dim_col) const {
    if (!(dim_row && dim_col)) {
      PyErr_SetString(PyExc_ValueError, "Cannot write an empty wave file");
      return;
    }
    kaldi::Matrix<kaldi::BaseFloat> matrix(dim_row, dim_col,
                               kaldi::kUndefined, kaldi::kStrideEqualNumCols);
    std::memcpy(matrix.Data(), matrix_in,
                  dim_row * dim_col * sizeof(kaldi::BaseFloat));
    // I'm not sure if this copy gets optimized into a swap...
    const kaldi::WaveData wave_data(16000.0, matrix);
    $self->Write(key, wave_data);
  };
}

%extend kaldi::SequentialTableReader<kaldi::WaveInfoHolder > {
  kaldi::BaseFloat SampFreq() { return $self->Value().SampFreq(); };
  kaldi::BaseFloat Duration() { return $self->Value().Duration(); };
}

%extend kaldi::RandomAccessTableReaderMapped<kaldi::WaveInfoHolder > {
  kaldi::BaseFloat SampFreq(const std::string &key) {
    return $self->Value(key).SampFreq();
  };
  kaldi::BaseFloat Duration(const std::string &key) {
    return $self->Value(key).Duration();
  };
}

TEMPLATE_WITH_NAME_AND_HOLDER_TYPE(Wave, kaldi::WaveHolder);

EXTEND_RW_WITH_IS_BINARY(kaldi::SequentialTableReader, kaldi::WaveInfoHolder);
EXTEND_RW_WITH_IS_BINARY(kaldi::RandomAccessTableReaderMapped, kaldi::WaveInfoHolder);
%template(SequentialWaveInfoReader) kaldi::SequentialTableReader<kaldi::WaveInfoHolder >;
%template(RandomAccessWaveInfoReaderMapped) kaldi::RandomAccessTableReaderMapped<kaldi::WaveInfoHolder >;
