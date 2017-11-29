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

#include "util/text-utils.h"

%}

namespace kaldi {
  class TokenHolder {
  public:
    typedef std::string T;
  };
  class TokenVectorHolder {
  public:
    typedef std::vector<std::string> T;
  };
}

%extend kaldi::TableWriter<kaldi::TokenHolder > {
  void Write(const std::string& key, const std::string& token) {
    if (!kaldi::IsToken(token)) {
      PyErr_SetString(PyExc_ValueError, "Value is not a token");
      return;
    }
    $self->Write(key, token);
  };
}

%extend kaldi::SequentialTableReader<kaldi::TokenHolder > {
  const std::string& Value() {
    return $self->Value();
  };
}

%extend kaldi::RandomAccessTableReaderMapped<kaldi::TokenHolder > {
  const std::string& Value(const std::string& key) {
    return $self->Value(key);
  };
}

%extend kaldi::TableWriter<kaldi::TokenVectorHolder > {
  void Write(const std::string& key, const std::vector<std::string >& token_vec) {
    for (std::vector<std::string >::const_iterator iter = token_vec.begin();
         iter != token_vec.end(); ++iter) {
      if (!kaldi::IsToken(*iter)) {
        PyErr_SetString(PyExc_ValueError, "At least one element is not a token");
        return;
      }
    }
    $self->Write(key, token_vec);
  };
}

%extend kaldi::SequentialTableReader<kaldi::TokenVectorHolder > {
  const std::vector<std::string >& Value() {
    return $self->Value();
  };
}

%extend kaldi::RandomAccessTableReaderMapped<kaldi::TokenVectorHolder > {
  const std::vector<std::string >& Value(const std::string& key) {
    return $self->Value(key);
  };
}

TEMPLATE_WITH_NAME_AND_HOLDER_TYPE(Token, kaldi::TokenHolder);
TEMPLATE_WITH_NAME_AND_HOLDER_TYPE(TokenVector, kaldi::TokenVectorHolder);
