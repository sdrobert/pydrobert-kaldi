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

// wrapping kaldi's logging to fit into python-o-sphere

%{

#include "base/kaldi-error.h"

namespace kaldi {
  static PyObject *g_py_log_handler = NULL;
  
  void SetPythonLogHandler(PyObject *py_func) {
    Py_XDECREF(g_py_log_handler);
    g_py_log_handler = py_func;
    if (g_py_log_handler) {
      SetLogHandler([]
        (const LogMessageEnvelope &envelope, const char * message)
        {
          PyObject *envelope_obj = Py_BuildValue(
            "(issi)",
            envelope.severity,
            envelope.func, envelope.file, envelope.line
          );
          PyObject *arg_list = Py_BuildValue("(Os)", envelope_obj, message);
          // TODO(sdrobert): stack trace, maybe?
          PyObject *result = PyObject_CallObject(g_py_log_handler, arg_list);
          Py_DECREF(arg_list);
          Py_DECREF(envelope_obj);
          Py_XDECREF(result);
        }
      );
    } else {
      SetLogHandler(NULL);
    }
    Py_XINCREF(py_func);
  }

  void VerboseLog(int32_t lvl, const char * message) {
    KALDI_VLOG(lvl) << message;
  }
}
%}

namespace kaldi {
  int32_t GetVerboseLevel();
  void SetVerboseLevel(int32_t i);
  void SetPythonLogHandler(PyObject *py_func);
  void VerboseLog(int32_t lvl, const char * message);
}  // namespace kaldi

%typemap(in) PyObject *py_func {
  if (!PyCallable_Check($input)) {
      PyErr_SetString(PyExc_TypeError, "Expected callable");
      return NULL;
  }
  $1 = $input;
}
