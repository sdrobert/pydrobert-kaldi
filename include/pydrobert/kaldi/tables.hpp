#ifndef PYDROBERT_KALDI_TABLES_H_
#define PYDROBERT_KALDI_TABLES_H_

#include "util/kaldi-holder.h"
#include "util/kaldi-table.h"
#include "pydrobert/kaldi/vector.hpp"
#include "pydrobert/kaldi/matrix.hpp"

// These classes are a workaround since swig doesn't seem to understand
// that Holder::T refers to the holder's type. There might be a more swig-gy way
// of handling this that I just don't understand.

//// Sequential Readers

template<typename Real>
class ExtSequentialNumpyVectorReader : public
    kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<NumpyVector<Real> > > {
 public:
  inline const NumpyVector<Real> &Value() {
    return kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<NumpyVector<Real> > >::Value();
  }
};

template class ExtSequentialNumpyVectorReader<double>;
template class ExtSequentialNumpyVectorReader<float>;

template<typename Real>
class ExtSequentialNumpyMatrixReader : public
    kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<NumpyMatrix<Real> > > {
 public:
  inline const NumpyMatrix<Real> &Value() {
    return kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<NumpyMatrix<Real> > >::Value();
  }
};

template class ExtSequentialNumpyMatrixReader<double>;
template class ExtSequentialNumpyMatrixReader<float>;


//// Random Access Readers

template<typename Real>
class ExtRandomAccessNumpyVectorReader : public
    kaldi::RandomAccessTableReader<kaldi::KaldiObjectHolder<NumpyVector<Real> > > {
 public:
  inline const NumpyVector<Real> &Value(const std::string &key) {
    return kaldi::RandomAccessTableReader<kaldi::KaldiObjectHolder<NumpyVector<Real> > >::Value(key);
  }
};

template class ExtRandomAccessNumpyVectorReader<double>;
template class ExtRandomAccessNumpyVectorReader<float>;

template<typename Real>
class ExtRandomAccessNumpyMatrixReader : public
    kaldi::RandomAccessTableReader<kaldi::KaldiObjectHolder<NumpyMatrix<Real> > > {
 public:
  inline const NumpyMatrix<Real> &Value(const std::string &key) {
    return kaldi::RandomAccessTableReader<kaldi::KaldiObjectHolder<NumpyMatrix<Real> > >::Value(key);
  }
};

template class ExtRandomAccessNumpyMatrixReader<double>;
template class ExtRandomAccessNumpyMatrixReader<float>;


//// Random Access Mapped Readers
template <typename Real>
class ExtRandomAccessNumpyVectorReaderMapped : public
    kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<NumpyVector<Real> > > {
 public:
  inline const NumpyVector<Real> &Value(const std::string &key) {
    return kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<NumpyVector<Real> > >::Value(key);
  }
};

template class ExtRandomAccessNumpyVectorReaderMapped<double>;
template class ExtRandomAccessNumpyVectorReaderMapped<float>;

template<typename Real>
class ExtRandomAccessNumpyMatrixReaderMapped : public
    kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<NumpyMatrix<Real> > > {
 public:
  inline const NumpyMatrix<Real> &Value(const std::string &key) {
    return kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<NumpyMatrix<Real> > >::Value(key);
  }
};

template class ExtRandomAccessNumpyMatrixReaderMapped<double>;
template class ExtRandomAccessNumpyMatrixReaderMapped<float>;

//// Writers

template<typename Real>
class ExtNumpyVectorWriter : public
    kaldi::TableWriter<kaldi::KaldiObjectHolder<NumpyVector<Real> > > {
 public:
  // we do not include the 'Open' constructor because we want to avoid Kaldi
  // throwing whenever we can.
  inline void Write(const std::string &key,
                    const NumpyVector<Real> &value) const {
    kaldi::TableWriter<kaldi::KaldiObjectHolder<NumpyVector<Real> > >::Write(
      key, value);
  }
  inline void WriteData(const std::string &key, const Real* vec_in,
                        const long len) const {
    NumpyVector<Real> vector;
    vector.SetData(vec_in, len);
    Write(key, vector);
  }
};

template class ExtNumpyVectorWriter<double>;
template class ExtNumpyVectorWriter<float>;

template<typename Real>
class ExtNumpyMatrixWriter : public
    kaldi::TableWriter<kaldi::KaldiObjectHolder<NumpyMatrix<Real> > > {
 public:
  inline void Write(const std::string &key,
                    const NumpyMatrix<Real> &value) const {
    kaldi::TableWriter<kaldi::KaldiObjectHolder<NumpyMatrix<Real> > >::Write(
      key, value);
  }
  inline void WriteData(const std::string &key, const Real* matrix_in,
                        const long dim_row, const long dim_col) const {
    NumpyMatrix<Real> matrix;
    matrix.SetData(matrix_in, dim_row, dim_col);
    Write(key, matrix);
  }
};

template class ExtNumpyMatrixWriter<double>;
template class ExtNumpyMatrixWriter<float>;

#endif  // PYDROBERT_KALDI_TABLES_H_