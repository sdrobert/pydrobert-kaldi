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
  #include "util/kaldi-holder.h"
  #include "util/kaldi-table.h"
%}

// general table types
namespace kaldi {
  
  template <class KaldiType> class KaldiObjectHolder {
    public:
      typedef KaldiType T;
  };
  template <class Holder> class SequentialTableReader {
    public:
      typedef typename Holder::T T;
      bool Done();
      std::string Key();
      bool IsOpen() const;
      bool Close();
      bool Open(const std::string &rspecifier);
      void Next();
      // const T &Value();
      %extend {
        bool OpenThreaded(const std::string &rspecifier) {
          // If we're trying to open a "background" sequential table reader, we
          // have to initialize python threads. We do this lazily since there's
          // a performance penalty.
          PyEval_InitThreads();
          bool ret;
          Py_BEGIN_ALLOW_THREADS;
          ret = $self->Open(rspecifier);
          Py_END_ALLOW_THREADS;
          return ret;
        };

        void NextThreaded() {
          Py_BEGIN_ALLOW_THREADS;
          $self->Next();
          Py_END_ALLOW_THREADS;
        };

        bool CloseThreaded() {
          bool ret;
          Py_BEGIN_ALLOW_THREADS;
          ret = $self->Close();
          Py_END_ALLOW_THREADS;
          return ret;
        }
      }
  };
  template <class Holder> class RandomAccessTableReaderMapped {
    public:
      typedef typename Holder::T T;
      bool Open(const std::string &table_rxfilename,
                const std::string &utt2spk_rxfilename);
      bool IsOpen() const;
      bool Close();
      bool HasKey(const std::string &key);
  };
  template <class Holder> class TableWriter {
    public:
      typedef typename Holder::T T;
      bool Open(const std::string &wspecifier);
      bool IsOpen() const;
      bool Close();
  };
}

%define EXTEND_RW_WITH_IS_BINARY(RWName, HolderName)
%extend RWName ## < ## HolderName > {
  static bool IsBinary() {
    return HolderName ## ::IsReadInBinary();
  };
}
%enddef

%define TEMPLATE_WITH_NAME_AND_HOLDER_TYPE(Name, HolderName)
%template(Sequential ## Name ## Reader) kaldi::SequentialTableReader<HolderName >;
%template(RandomAccess ## Name ## Reader) kaldi::RandomAccessTableReaderMapped<HolderName >;
%template(Name ## Writer) kaldi::TableWriter<HolderName >;
EXTEND_RW_WITH_IS_BINARY(kaldi::SequentialTableReader, HolderName);
EXTEND_RW_WITH_IS_BINARY(kaldi::RandomAccessTableReaderMapped, HolderName);
EXTEND_RW_WITH_IS_BINARY(kaldi::TableWriter, HolderName);
%enddef

%define TEMPLATE_WITH_KOBJECT_NAME_AND_TYPE(Name, Type)
%template() Type;
%template() kaldi::KaldiObjectHolder<Type >;
TEMPLATE_WITH_NAME_AND_HOLDER_TYPE(Name, kaldi::KaldiObjectHolder<Type >);
%enddef

%include "pydrobert/io/tables/mv_tables.i"
%include "pydrobert/io/tables/token_tables.i"
%include "pydrobert/io/tables/wave_tables.i"
%include "pydrobert/io/tables/basic_tables.i"
