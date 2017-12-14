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
  #include "util/kaldi-table.h"
%}

namespace kaldi {
  template <class BasicType> class BasicHolder {};
  template <class BasicType> class BasicVectorHolder {};
  template <class BasicType> class BasicVectorVectorHolder {};
  template <class BasicType> class BasicPairVectorHolder {};
}

%define BASIC_TABLE_TEMPLATE_WITH_NAME_AND_TYPE(Name, HolderName, ValType...)
TEMPLATE_WITH_NAME_AND_HOLDER_TYPE(Name, HolderName);

%extend kaldi::SequentialTableReader<HolderName > {
  const ValType & Value() {
    return $self->Value();
  };
}
%extend kaldi::RandomAccessTableReaderMapped<HolderName > {
  const ValType & Value(const std::string& key) {
    return $self->Value(key);
  };
}
%extend kaldi::TableWriter<HolderName > {
  void Write(const std::string& key, const ValType & val) {
    $self->Write(key, val);
  };
}
%enddef

// int
%template() kaldi::BasicHolder<int32_t >;
BASIC_TABLE_TEMPLATE_WITH_NAME_AND_TYPE(Int32, kaldi::BasicHolder<int32_t >, int32_t);
%template() kaldi::BasicVectorHolder<int32_t >;
BASIC_TABLE_TEMPLATE_WITH_NAME_AND_TYPE(Int32Vector, kaldi::BasicVectorHolder<int32_t >, std::vector<int32_t >);
%template() kaldi::BasicVectorVectorHolder<int32_t >;
BASIC_TABLE_TEMPLATE_WITH_NAME_AND_TYPE(Int32VectorVector, kaldi::BasicVectorVectorHolder<int32_t >, std::vector<std::vector<int32_t > >);
%template() kaldi::BasicPairVectorHolder<int32_t >;
BASIC_TABLE_TEMPLATE_WITH_NAME_AND_TYPE(Int32PairVector, kaldi::BasicPairVectorHolder<int32_t >, std::vector<std::pair<int32_t, int32_t > >);

// double
%template(DoubleHolder) kaldi::BasicHolder<double >;
BASIC_TABLE_TEMPLATE_WITH_NAME_AND_TYPE(Double, kaldi::BasicHolder<double >, double);

// base float
#if KALDI_DOUBLEPRECISION
typedef DoubleHolder BaseFloatHolder;
typedef SequentialDoubleReader SequentialBaseFloatReader;
typedef RandomAccessDoubleReader RandomAccessBaseFloatReader;
typedef DoubleWriter BaseFloatWriter;
%template() kaldi::BasicPairVectorHolder<double >;
BASIC_TABLE_TEMPLATE_WITH_NAME_AND_TYPE(BaseFloatPairVector, kaldi::BasicPairVectorHolder<double >, std::vector<std::pair<double, double > >);
#else
%template() kaldi::BasicHolder<float >;
BASIC_TABLE_TEMPLATE_WITH_NAME_AND_TYPE(BaseFloat, kaldi::BasicHolder<float >, float);
%template() kaldi::BasicPairVectorHolder<float >;
BASIC_TABLE_TEMPLATE_WITH_NAME_AND_TYPE(BaseFloatPairVector, kaldi::BasicPairVectorHolder<float >, std::vector<std::pair<float, float > >);
#endif

// bool
%template() kaldi::BasicHolder<bool >;
BASIC_TABLE_TEMPLATE_WITH_NAME_AND_TYPE(Bool, kaldi::BasicHolder<bool >, bool);
