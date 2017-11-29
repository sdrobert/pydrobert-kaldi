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
    Py_BEGIN_ALLOW_THREADS;
    Py_XDECREF(g_py_log_handler);
    g_py_log_handler = py_func;
    if (g_py_log_handler) {
      SetLogHandler([]
        (const LogMessageEnvelope &envelope, const char * message)
        {
          PyGILState_STATE gstate;
          int acquire_gil = PyEval_ThreadsInitialized();
          if (acquire_gil)
            gstate = PyGILState_Ensure();
          PyObject *envelope_obj = Py_BuildValue(
            "(issi)",
            envelope.severity,
            envelope.func, envelope.file, envelope.line
          );
          // kaldi does not guarantee that the message is of a specific
          // encoding, so we send it as bytes and decode it there, replacing
          // errors with <?>
#if PY_VERSION_HEX >= 0x03000000
          PyObject *arg_list = Py_BuildValue("(Oy)", envelope_obj, message);
#else
          PyObject *arg_list = Py_BuildValue("(Os)", envelope_obj, message);
#endif
          PyObject *result = PyObject_CallObject(g_py_log_handler, arg_list);
          Py_DECREF(arg_list);
          Py_DECREF(envelope_obj);
          Py_XDECREF(result);
          if (acquire_gil)
            PyGILState_Release(gstate);
        }
      );
    } else {
      SetLogHandler(NULL);
    }

    Py_XINCREF(py_func);
    Py_END_ALLOW_THREADS;
  }

  void VerboseLog(long lvl, const char * message) {
    KALDI_VLOG(lvl) << message;
  }
}
%}

namespace kaldi {
  long GetVerboseLevel();
  void SetVerboseLevel(long i);
  void SetPythonLogHandler(PyObject *py_func);
  void VerboseLog(long lvl, const char * message);
}  // namespace kaldi

%typemap(in) PyObject *py_func {
  if (!PyCallable_Check($input)) {
      PyErr_SetString(PyExc_TypeError, "Expected callable");
      return NULL;
  }
  $1 = $input;
}
