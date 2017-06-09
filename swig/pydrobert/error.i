/* -*- C++ -*- */

// wrapping kaldi's logging to fit into python-o-sphere

%{

#include "base/kaldi-error.h"

namespace kaldi {
  PyObject *g_py_log_handler = NULL;
  
  void SetPythonLogHandler(PyObject *py_func) {
    Py_XDECREF(g_py_log_handler);
    g_py_log_handler = py_func;
    if (g_py_log_handler) {
      SetLogHandler([=]
        (const LogMessageEnvelope &envelope, const char * message)
        {
          PyObject *envelope_obj = Py_BuildValue(
            "(issi)",
            -10 * envelope.severity + 20, // to roughly match python logging
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
}
%}

namespace kaldi {
  int32_t GetVerboseLevel();
  void SetVerboseLevel(int32_t i);
  void SetPythonLogHandler(PyObject *py_func);
}  // namespace kaldi

%typemap(python, in) PyObject *py_func {
  if (!PyCallable_Check($input)) {
      PyErr_SetString(PyExc_TypeError, "Expected callable");
      return NULL;
  }
  $1 = $input;
}
