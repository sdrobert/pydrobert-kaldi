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
%module(package="pydrobert.kaldi") internal

%{
  #define SWIG_FILE_WITH_INIT
  #define SWIG_PYTHON_2_UNICODE
%}

#include "base/version.h"

%include "typemaps.i"
// %include "stdint.i" // causes weird mapping issues in vectors
%include "std_string.i"
%include "std_vector.i"
%include "std_pair.i"
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

%template() std::vector<std::string >;
// we support the combinations of basic types/vectors that have typedefs in
// table-types.h
%template() std::vector<long >;
%template() std::vector<std::vector<long > >;
%template() std::pair<long, long >;
%template() std::vector<std::pair<long, long > >;
%template() std::pair<double, double >;
%template() std::vector<std::pair<double, double > >;
%template() std::pair<float, float >;
%template() std::vector<std::pair<float, float > >;

// to determine BaseFloat in python wrapper
#if KALDI_DOUBLEPRECISION
%constant bool kDoubleIsBase = true;
namespace kaldi {
  typedef double BaseFloat;
}
%numpy_typemaps(kaldi::BaseFloat, NPY_DOUBLE, kaldi::MatrixIndexT);
#else
%constant bool kDoubleIsBase = false;
namespace kaldi {
  typedef float BaseFloat;
}
%numpy_typemaps(kaldi::BaseFloat, NPY_FLOAT, kaldi::MatrixIndexT);
#endif

namespace kaldi {
  typedef int MatrixIndexT;
  typedef int SignedMatrixIndexT;
  typedef unsigned int UnsignedMatrixIndexT;
}

%numpy_typemaps(double, NPY_DOUBLE, kaldi::MatrixIndexT);
%numpy_typemaps(float, NPY_FLOAT, kaldi::MatrixIndexT);

%include "pydrobert/error.i"
%include "pydrobert/io/util.i"
%include "pydrobert/io/tables/tables.i"
%include "pydrobert/io/duck.i"
