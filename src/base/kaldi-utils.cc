// base/kaldi-utils.cc
// Copyright 2009-2011   Karel Vesely;  Yanmin Qian;  Microsoft Corporation

// Modified by Sean Robertson 2022. Updates listed below.

// See ../../COPYING for clarification regarding multiple authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//  http://www.apache.org/licenses/LICENSE-2.0

// THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
// WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
// MERCHANTABLITY OR NON-INFRINGEMENT.
// See the Apache 2 License for the specific language governing permissions and
// limitations under the License.

#include "base/kaldi-utils.h"

#include <chrono>
#include <cstdio>
#include <thread>

// sdrobert: Not guaranteed to have been included beforehand on all MSVC for
// some reason
#include <cctype>

// sdrobert: std::snprintf did not exist pre-2015 on MSVC
#if defined(_MSC_VER) && _MSC_VER < 1900
  #define mysnprintf c99_snprintf
#else
  #define mysnprintf std::snprintf
#endif

namespace kaldi {

std::string CharToString(const char &c) {
  char buf[20];
  if (std::isprint(c))
    mysnprintf(buf, sizeof(buf), "\'%c\'", c);
  else
    mysnprintf(buf, sizeof(buf), "[character %d]", static_cast<int>(c));
  return buf;
}

void Sleep(double sec) {
  // duration_cast<> rounds down, add 0.5 to compensate.
  auto dur_nanos = std::chrono::duration<double, std::nano>(sec * 1E9 + 0.5);
  auto dur_syshires = std::chrono::duration_cast<
    typename std::chrono::high_resolution_clock::duration>(dur_nanos);
  std::this_thread::sleep_for(dur_syshires);
}

#undef mysnprintf

}  // end namespace kaldi
