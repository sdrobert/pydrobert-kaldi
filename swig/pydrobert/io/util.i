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
#include "base/kaldi-error.h"
#include "util/kaldi-table.h"

namespace kaldi {
  PyObject* ParseInputPath(const std::string &rspecifier) {
    std::string rxfilename = rspecifier;
    RspecifierOptions options;
    RspecifierType rspecifer_type = ClassifyRspecifier(rspecifier,
                                                       &rxfilename, &options);
    InputType input_type = ClassifyRxfilename(rxfilename);
    PyObject *ret = Py_BuildValue("(isiOOOOO)",
      rspecifer_type,
      rxfilename.c_str(),
      input_type,
      options.once ? Py_True : Py_False,
      options.sorted ? Py_True : Py_False,
      options.called_sorted ? Py_True : Py_False,
      options.permissive ? Py_True : Py_False,
      options.background ? Py_True : Py_False
    );
    return ret;
  }

  PyObject* ParseOutputPath(const std::string &wspecifier) {
    std::string arch_wxfilename, script_wxfilename;
    WspecifierOptions options;
    WspecifierType wspecifier_type = ClassifyWspecifier(wspecifier,
                                                        &arch_wxfilename,
                                                        &script_wxfilename,
                                                        &options);
    PyObject *ret;
    switch (wspecifier_type) {
      case kArchiveWspecifier:
        ret = Py_BuildValue("(isiOOO)",
          wspecifier_type,
          arch_wxfilename.c_str(),
          ClassifyWxfilename(arch_wxfilename),
          options.binary ? Py_True : Py_False,
          options.flush ? Py_True : Py_False,
          options.permissive ? Py_True : Py_False
        );
        break;
      case kScriptWspecifier:
        ret = Py_BuildValue("(isiOOO)",
          wspecifier_type,
          script_wxfilename.c_str(),
          ClassifyWxfilename(script_wxfilename),
          options.binary ? Py_True : Py_False,
          options.flush ? Py_True : Py_False,
          options.permissive ? Py_True : Py_False
        );
        break;
      case kBothWspecifier:
        ret = Py_BuildValue("(issiiOOO)",
          wspecifier_type,
          arch_wxfilename.c_str(),
          script_wxfilename.c_str(),
          ClassifyWxfilename(arch_wxfilename),
          ClassifyWxfilename(script_wxfilename),
          options.binary ? Py_True : Py_False,
          options.flush ? Py_True : Py_False,
          options.permissive ? Py_True : Py_False
        );
        break;
      case kNoWspecifier: default:
        ret = Py_BuildValue("(isi)",
          wspecifier_type,
          wspecifier.c_str(),
          ClassifyWxfilename(wspecifier)
        );
      break;
    }
    return ret;
  }
}
%}

namespace kaldi {
  PyObject* ParseInputPath(const std::string &rspecifier);
  PyObject* ParseOutputPath(const std::string &wspecifier);
}
