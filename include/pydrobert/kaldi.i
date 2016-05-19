
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
  #include "pydrobert/kaldi/vector.hpp"
  #include "pydrobert/kaldi/matrix.hpp"
  #include "pydrobert/kaldi/tables.hpp"
%}

%include "numpy/numpy.i"
%init %{
  import_array();
%}
%numpy_typemaps(double, NPY_DOUBLE, long);
%numpy_typemaps(float, NPY_FLOAT, long);
%apply(double* IN_ARRAY1, long DIM1) {(const double* vec_in, const long len)};
%apply(float* IN_ARRAY1, long DIM1) {(const float* vec_in, const long len)};
// swapped dim and array b/c 'len' strictly input whilst 'vec_inout' both
%apply(long DIM1, double* INPLACE_ARRAY1) {(const long len, double* vec_inout)};
%apply(long DIM1, float* INPLACE_ARRAY1) {(const long len, float* vec_inout)};
%apply(double* IN_ARRAY2, long DIM1, long DIM2) {(const double* matrix_in, const long dim_row, const long dim_col)};
%apply(float* IN_ARRAY2, long DIM1, long DIM2) {(const float* matrix_in, const long dim_row, const long dim_col)};
%apply(long DIM1, long DIM2, double* INPLACE_ARRAY2) {(const long dim_row, const long dim_col, double* matrix_inout)};
%apply(long DIM1, long DIM2, float* INPLACE_ARRAY2) {(const long dim_row, const long dim_col, float* matrix_inout)};

// to determine BaseFloat in python wrapper
%constant bool kDoubleIsBase = sizeof(kaldi::BaseFloat) == sizeof(double);

// all SWIG needs to know about various parents
%import "base/kaldi-common.h"
%import "util/common-utils.h"
%import "matrix/matrix-common.h"
namespace kaldi {
  template <typename Real> class Vector {
    public:
      long Dim() const;
  };
  template <typename Real> class Matrix {
    public:
      long NumRows() const;
      long NumCols() const;
  };
  template <class KaldiType> class KaldiObjectHolder {};
  template <class Holder> class SequentialTableReader {
    public:
      bool Open(const std::string &rspecifier);
      bool Done();
      std::string Key();
      void Next();
      bool IsOpen() const;
      bool Close();
  };
  template <class Holder> class RandomAccessTableReader {
    public:
      bool Open(const std::string &rspecifier);
      bool IsOpen() const;
      bool Close();
      bool HasKey(const std::string &key);
  };
  template <class Holder> class RandomAccessTableReaderMapped {
    public:
      bool Open(const std::string &table_rxfilename,
                const std::string &utt2spk_rxfilename);
      bool IsOpen() const;
      bool Close();
      bool HasKey(const std::string &key);
  };
  template <class Holder> class TableWriter {
    public:
      bool Open(const std::string &wspecifier);
      bool IsOpen() const;
      bool Close();
  };
}

// vectors
%template(DoubleVector) kaldi::Vector<double>;
%template(FloatVector) kaldi::Vector<float>;

%include "pydrobert/kaldi/vector.hpp"

%template(NumpyDoubleVector) NumpyVector<double>;
%template(NumpyFloatVector) NumpyVector<float>;

// matrices
%template(DoubleMatrix) kaldi::Matrix<double>;
%template(FloatMatrix) kaldi::Matrix<float>;

%include "pydrobert/kaldi/matrix.hpp"

%template(NumpyDoubleMatrix) NumpyMatrix<double>;
%template(NumpyFloatMatrix) NumpyMatrix<float>;

// tables (TODO: this is ugly. make into macros)
%template(NumpyDoubleVectorHolder) kaldi::KaldiObjectHolder<NumpyVector<double> >;
%template(SequentialNumpyDoubleVectorReader) kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<NumpyVector<double> > >;
%template(RandomAccessNumpyDoubleVectorReader) kaldi::RandomAccessTableReader<kaldi::KaldiObjectHolder<NumpyVector<double> > >;
%template(RandomAccessNumpyDoubleVectorReaderMapped) kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<NumpyVector<double> > >;
%template(NumpyDoubleVectorWriter) kaldi::TableWriter<kaldi::KaldiObjectHolder<NumpyVector<double> > >;

%template(NumpyFloatVectorHolder) kaldi::KaldiObjectHolder<NumpyVector<float> >;
%template(SequentialNumpyFloatVectorReader) kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<NumpyVector<float> > >;
%template(RandomAccessNumpyFloatVectorReader) kaldi::RandomAccessTableReader<kaldi::KaldiObjectHolder<NumpyVector<float> > >;
%template(RandomAccessNumpyFloatVectorReaderMapped) kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<NumpyVector<float> > >;
%template(NumpyFloatVectorWriter) kaldi::TableWriter<kaldi::KaldiObjectHolder<NumpyVector<float> > >;

%template(NumpyDoubleMatrixHolder) kaldi::KaldiObjectHolder<NumpyMatrix<double> >;
%template(SequentialNumpyDoubleMatrixReader) kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<NumpyMatrix<double> > >;
%template(RandomAccessNumpyDoubleMatrixReader) kaldi::RandomAccessTableReader<kaldi::KaldiObjectHolder<NumpyMatrix<double> > >;
%template(RandomAccessNumpyDoubleMatrixReaderMapped) kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<NumpyMatrix<double> > >;
%template(NumpyDoubleMatrixWriter) kaldi::TableWriter<kaldi::KaldiObjectHolder<NumpyMatrix<double> > >;

%template(NumpyFloatMatrixHolder) kaldi::KaldiObjectHolder<NumpyMatrix<float> >;
%template(SequentialNumpyFloatMatrixReader) kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<NumpyMatrix<float> > >;
%template(RandomAccessNumpyFloatMatrixReader) kaldi::RandomAccessTableReader<kaldi::KaldiObjectHolder<NumpyMatrix<float> > >;
%template(RandomAccessNumpyFloatMatrixReaderMapped) kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<NumpyMatrix<float> > >;
%template(NumpyFloatMatrixWriter) kaldi::TableWriter<kaldi::KaldiObjectHolder<NumpyMatrix<float> > >;

%include "pydrobert/kaldi/tables.hpp"

%template(ExtSequentialNumpyDoubleVectorReader) ExtSequentialNumpyVectorReader<double>;
%template(ExtSequentialNumpyFloatVectorReader) ExtSequentialNumpyVectorReader<float>;
%template(ExtRandomAccessNumpyDoubleVectorReader) ExtRandomAccessNumpyVectorReader<double>;
%template(ExtRandomAccessNumpyFloatVectorReader) ExtRandomAccessNumpyVectorReader<float>;
%template(ExtRandomAccessNumpyDoubleVectorReaderMapped) ExtRandomAccessNumpyVectorReaderMapped<double>;
%template(ExtRandomAccessNumpyFloatVectorReaderMapped) ExtRandomAccessNumpyVectorReaderMapped<float>;
%template(ExtNumpyDoubleVectorWriter) ExtNumpyVectorWriter<double>;
%template(ExtNumpyFloatVectorWriter) ExtNumpyVectorWriter<float>;

%template(ExtSequentialNumpyDoubleMatrixReader) ExtSequentialNumpyMatrixReader<double>;
%template(ExtSequentialNumpyFloatMatrixReader) ExtSequentialNumpyMatrixReader<float>;
%template(ExtRandomAccessNumpyDoubleMatrixReader) ExtRandomAccessNumpyMatrixReader<double>;
%template(ExtRandomAccessNumpyFloatMatrixReader) ExtRandomAccessNumpyMatrixReader<float>;
%template(ExtRandomAccessNumpyDoubleMatrixReaderMapped) ExtRandomAccessNumpyMatrixReaderMapped<double>;
%template(ExtRandomAccessNumpyFloatMatrixReaderMapped) ExtRandomAccessNumpyMatrixReaderMapped<float>;
%template(ExtNumpyDoubleMatrixWriter) ExtNumpyMatrixWriter<double>;
%template(ExtNumpyFloatMatrixWriter) ExtNumpyMatrixWriter<float>;
