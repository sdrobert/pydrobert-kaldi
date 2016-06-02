
%module(package="pydrobert.kaldi") internal
%include "std_string.i"
%include "exception.i"

%exception {
  try {
    $action
  } catch (const std::exception& e) {
    SWIG_exception(SWIG_RuntimeError, e.what());
  }
}

%{
  #define SWIG_FILE_WITH_INIT
  #include "matrix/kaldi-matrix.h"
  #include "matrix/kaldi-vector.h"
  #include "util/kaldi-holder.h"
  #include "util/kaldi-table.h"
%}

// all SWIG needs to know about various parents
namespace kaldi {
  typedef enum {
    kSetZero,
    kUndefined,
    kCopyData
  } MatrixResizeType;
  typedef enum {
    kDefaultStride,
    kStrideEqualNumCols,
  } MatrixStrideType;
  typedef int MatrixIndexT;
  typedef int SignedMatrixIndexT;
  typedef unsigned int UnsignedMatrixIndexT;
  template <typename Real> class Vector {
    public:
      MatrixIndexT Dim() const;
  };
  template <typename Real> class Matrix {
    public:
      MatrixIndexT NumRows() const;
      MatrixIndexT NumCols() const;
  };
  template <class KaldiType> class KaldiObjectHolder {
    public:
      typedef KaldiType T;
  };
  template <class Holder> class SequentialTableReader {
    public:
      typedef typename Holder::T T;
      bool Open(const std::string &rspecifier);
      bool Done();
      std::string Key();
      void Next();
      bool IsOpen() const;
      bool Close();
      const T &Value();
  };
  template <class Holder> class RandomAccessTableReader {
    public:
      typedef typename Holder::T T;
      bool Open(const std::string &rspecifier);
      bool IsOpen() const;
      bool Close();
      bool HasKey(const std::string &key);
      const T &Value(const std::string &key);
  };
  template <class Holder> class RandomAccessTableReaderMapped {
    public:
      typedef typename Holder::T T;
      bool Open(const std::string &table_rxfilename,
                const std::string &utt2spk_rxfilename);
      bool IsOpen() const;
      bool Close();
      bool HasKey(const std::string &key);
      const T &Value(const std::string &key);
  };
  template <class Holder> class TableWriter {
    public:
      typedef typename Holder::T T;
      bool Open(const std::string &wspecifier);
      bool IsOpen() const;
      bool Close();
      void Write(const std::string &key, const T &value) const;
  };
}

%include "numpy/numpy.i"
%init %{
  import_array();
%}
%numpy_typemaps(double, NPY_DOUBLE, kaldi::MatrixIndexT);
%numpy_typemaps(float, NPY_FLOAT, kaldi::MatrixIndexT);
%apply(double* IN_ARRAY1, kaldi::MatrixIndexT DIM1) {(const double* vec_in, const kaldi::MatrixIndexT len)};
%apply(float* IN_ARRAY1, kaldi::MatrixIndexT DIM1) {(const float* vec_in, const kaldi::MatrixIndexT len)};
// swapped dim and array b/c 'len' strictly input whilst 'vec_inout' both
%apply(kaldi::MatrixIndexT DIM1, double* INPLACE_ARRAY1) {(const kaldi::MatrixIndexT len, double* vec_inout)};
%apply(kaldi::MatrixIndexT DIM1, float* INPLACE_ARRAY1) {(const kaldi::MatrixIndexT len, float* vec_inout)};
%apply(double* IN_ARRAY2, kaldi::MatrixIndexT DIM1, kaldi::MatrixIndexT DIM2) {(const double* matrix_in, const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col)};
%apply(float* IN_ARRAY2, kaldi::MatrixIndexT DIM1, kaldi::MatrixIndexT DIM2) {(const float* matrix_in, const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col)};
%apply(kaldi::MatrixIndexT DIM1, kaldi::MatrixIndexT DIM2, double* INPLACE_ARRAY2) {(const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col, double* matrix_inout)};
%apply(kaldi::MatrixIndexT DIM1, kaldi::MatrixIndexT DIM2, float* INPLACE_ARRAY2) {(const kaldi::MatrixIndexT dim_row, const kaldi::MatrixIndexT dim_col, float* matrix_inout)};

// to determine BaseFloat in python wrapper
%constant bool kDoubleIsBase = sizeof(kaldi::BaseFloat) == sizeof(double);

%define EXTEND_WITH_REAL(Real)
%extend kaldi::Vector<Real> {
  // SetData copies data from Real array into internal memory
  void SetData(const Real* vec_in, const kaldi::MatrixIndexT len) {
    if ($self->Dim() != len) {
      $self->Resize(len, kaldi::kUndefined);
    }
    if (len) std::memcpy($self->Data(), vec_in, len * sizeof(Real));
  }
  // ReadDataInto reads the existing data pointer into memory assumed allocated
  // len better match Dim()
  bool ReadDataInto(const kaldi::MatrixIndexT len, Real* vec_inout) const {
    if ($self->Dim() != len) return false;
    if (!len) return true;  // empty; skip memcpy call
    std::memcpy(vec_inout, $self->Data(), len * sizeof(Real));
    return true;
  }
};
%extend kaldi::Matrix<Real> {
  void SetData(const Real* matrix_in, const kaldi::MatrixIndexT dim_row,
                                      const kaldi::MatrixIndexT dim_col) {
    if (!(dim_row * dim_col)) {
      // numpy can pass (x, 0) or (0, x) into this signature, but Kaldi can't
      // handle it. Just skip to the correct logic
      $self->Resize(0, 0);
      return;
    }
    if ($self->NumRows() != dim_row ||
        $self->NumCols() != dim_col) {
      $self->Resize(dim_row, dim_col, kaldi::kUndefined);
    }
    const kaldi::MatrixIndexT stride = $self->Stride();
    Real* data = $self->Data();
    if (stride == dim_col) {
      // copy contiguously
      std::memcpy(data, matrix_in, dim_row * dim_col * sizeof(Real));
    } else {
      // stride != cols means matrix isn't contiguous, but rows are :D
      for (kaldi::MatrixIndexT row = 0; row < dim_row; ++row) {
        std::memcpy(data + (row * stride), matrix_in + (row * dim_col),
                    dim_col * sizeof(Real));
      }
    }
  }

  bool ReadDataInto(const kaldi::MatrixIndexT dim_row,
                    const kaldi::MatrixIndexT dim_col,
                    Real* matrix_inout) const {
    if (!(dim_row * dim_col)) {
      return (!$self->NumRows() || !$self->NumCols());
    }
    if ($self->NumRows() != dim_row || $self->NumCols() != dim_col) {
      return false;
    }
    const kaldi::MatrixIndexT stride = $self->Stride();
    const Real* data = $self->Data();
    if (stride == dim_col) {
      std::memcpy(matrix_inout, data, dim_row * dim_col * sizeof(Real));
    } else {
      for (kaldi::MatrixIndexT row = 0; row < dim_row; ++row) {
        std::memcpy(matrix_inout + (row * dim_col), data + (row * stride),
                    dim_col * sizeof(Real));
      }
    }
    return true;
  }
};
%extend kaldi::TableWriter<kaldi::KaldiObjectHolder<kaldi::Vector<Real> > > {
  void WriteData(const std::string &key, const Real* vec_in,
                 const kaldi::MatrixIndexT len) {
    kaldi::Vector<Real> vector(len, kaldi::kUndefined);
    std::memcpy(vector.Data(), vec_in, len * sizeof(Real));
    $self->Write(key, vector);
  }
};
%extend kaldi::TableWriter<kaldi::KaldiObjectHolder<kaldi::Matrix<Real> > > {
  void WriteData(const std::string &key, const Real* matrix_in,
                 const kaldi::MatrixIndexT dim_row,
                 const kaldi::MatrixIndexT dim_col) const {
    kaldi::Matrix<Real> matrix(dim_row, dim_col, kaldi::kUndefined,
                               kaldi::kStrideEqualNumCols);
    std::memcpy(matrix.Data(), matrix_in, dim_row * dim_col * sizeof(Real));
    $self->Write(key, matrix);
  }
};
%enddef
EXTEND_WITH_REAL(double)
EXTEND_WITH_REAL(float)

%define TEMPLATE_WITH_NAME_AND_TYPE(Name, Type)
%template(Name) Type;
%template(Name ## Holder) kaldi::KaldiObjectHolder<Type >;
%template(Sequential ## Name ## Reader) kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<Type > >;
%template(RandomAccess ## Name ## Reader) kaldi::RandomAccessTableReader<kaldi::KaldiObjectHolder<Type > >;
%template(RandomAccess ## Name ## ReaderMapped) kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<Type > >;
%template(Name ## Writer) kaldi::TableWriter<kaldi::KaldiObjectHolder<Type > >;
%enddef
TEMPLATE_WITH_NAME_AND_TYPE(DoubleVector, kaldi::Vector<double>)
TEMPLATE_WITH_NAME_AND_TYPE(FloatVector, kaldi::Vector<float>)
TEMPLATE_WITH_NAME_AND_TYPE(DoubleMatrix, kaldi::Matrix<double>)
TEMPLATE_WITH_NAME_AND_TYPE(FloatMatrix, kaldi::Matrix<float>)
