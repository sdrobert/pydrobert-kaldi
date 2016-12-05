/* -*- C++ -*- */

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
%extend kaldi::RandomAccessTableReader<kaldi::TokenHolder > {
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
%extend kaldi::RandomAccessTableReader<kaldi::TokenVectorHolder > {
  const std::vector<std::string >& Value(const std::string& key) {
    return $self->Value(key);
  };
}

%template(TokenWriter) kaldi::TableWriter<kaldi::TokenHolder >;
%template(SequentialTokenReader) kaldi::SequentialTableReader<kaldi::TokenHolder >;
%template(RandomAccessTokenReader) kaldi::RandomAccessTableReader<kaldi::TokenHolder >;

%template(TokenVectorWriter) kaldi::TableWriter<kaldi::TokenVectorHolder >;
%template(SequentialTokenVectorReader) kaldi::SequentialTableReader<kaldi::TokenVectorHolder >;
%template(RandomAccessTokenVectorReader) kaldi::RandomAccessTableReader<kaldi::TokenVectorHolder >;
