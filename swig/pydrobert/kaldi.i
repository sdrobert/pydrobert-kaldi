/* -*- C++ -*- */
%module(package="pydrobert.kaldi") internal

%{
  #define SWIG_FILE_WITH_INIT
  #define SWIG_PYTHON_2_UNICODE
  #include "util/kaldi-holder.h"
  #include "util/kaldi-table.h"
%}
%include "std_string.i"
%include "std_vector.i"
%include "stdint.i"
%include "numpy/numpy.i"
%include "exception.i"

%exception {
  // treat std::exception (kaldi) as a SytemError. If *I* set an error,
  // return NULL like a good python function.
  try {
    $action
    if (PyErr_Occurred()) return 0;
  } catch (const std::exception& e) {
    SWIG_exception(SWIG_RuntimeError, e.what());
  }
}

%init %{
  import_array();
%}

%template(StringVector) std::vector<std::string >;

// general table types
namespace kaldi {
  
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
      // const T &Value();
  };
  template <class Holder> class RandomAccessTableReaderMapped {
    public:
      typedef typename Holder::T T;
      bool Open(const std::string &table_rxfilename,
                const std::string &utt2spk_rxfilename);
      bool IsOpen() const;
      bool Close();
      bool HasKey(const std::string &key);
      // const T &Value(const std::string &key);
  };
  template <class Holder> class TableWriter {
    public:
      typedef typename Holder::T T;
      bool Open(const std::string &wspecifier);
      bool IsOpen() const;
      bool Close();
      // void Write(const std::string &key, const T &value) const;
  };
}

// to determine BaseFloat in python wrapper
#if KALDI_DOUBLEPRECISION
%constant bool kDoubleIsBase = true;
namespace kaldi {
  typedef double BaseFloat;
}
#else
%constant bool kDoubleIsBase = false;
namespace kaldi {
  typedef float BaseFloat;
}
#endif

%define TEMPLATE_WITH_KOBJECT_NAME_AND_TYPE(Name, Type)
%template(Name) Type;
%template(Name ## Holder) kaldi::KaldiObjectHolder<Type >;
%template(Sequential ## Name ## Reader) kaldi::SequentialTableReader<kaldi::KaldiObjectHolder<Type > >;
%template(RandomAccess ## Name ## Reader) kaldi::RandomAccessTableReaderMapped<kaldi::KaldiObjectHolder<Type > >;
%template(Name ## Writer) kaldi::TableWriter<kaldi::KaldiObjectHolder<Type > >;
%enddef

%include "pydrobert/mv_tables.i"
%include "pydrobert/wave_tables.i"
%include "pydrobert/token_tables.i"
%include "pydrobert/error.i"
