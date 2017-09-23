# Copyright 2016 Sean Robertson

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Contains python/cython access to Kaldi.

See ``README.rst`` for more info.

Note:
    Kaldi tools usually run with 'C' locale. To make sure::

        $ export LC_ALL=C

    is called before you use any Kaldi utilities, importing this module
    prints a warning to stderr if it detects any other locale.
"""

from __future__ import division
from __future__ import print_function

import locale
import logging
import sys
import warnings

from ._internal import SetPythonLogHandler as _set_log_handler
from ._internal import SetVerboseLevel as _set_verbose_level

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2016 Sean Robertson"

__all__ = ['tables', 'KaldiLogger']

LOCALE_MESSAGE = """\
It looks like you did not 'export LC_ALL=C' before you started python.
This is important to do if you plan on using kaldi's sorted tables at all."""
if locale.getdefaultlocale() != (None, None):
    warnings.warn(LOCALE_MESSAGE)

_KALDI_LOG_LEVEL = logging.INFO
'''The log level kaldi is set to'''

_REGISTERED_LOGGER_NAMES = set()
'''The loggers who will receive kaldi's messages'''

class KaldiLogger(logging.getLoggerClass()):
    """Logger subclass to make it easier to synchronize logging with Kaldi

    This class is almost the same as the class it inherits from, with
    three key changes:
     - line numbers, function names, paths, and levels will be overwritten if
       ``'kaldi_envelope'`` is a key provided in the `extra` argument. This is
       so that logs point to the actual source in Kaldi, rather than the python
       callback line
     - ``getEffectiveLevel`` and ``setLevel`` have been hijacked to
       synchronize logger levels with kaldi. The relationship is
       +----------------+------------+
       | logging        | kaldi      |
       +================+============+
       | CRITICAL(50+)  | -3+        |
       +----------------+------------+
       | ERROR(40-49)   | -2         |
       +----------------+------------+
       | WARNING(30-39) | -1         |
       +----------------+------------+
       | INFO(20-29)    | 0          |
       +----------------+------------+
       | DEBUG(10-19)   | 1          |
       +----------------+------------+
       | 9 down to 1    | 2 up to 10 |
       +----------------+------------+
       We never increase kaldi's `logging level` (decrease its internal
       level) because some logger in the logging tree might still need
       info at that granularity. Instead, we rely on individual
       instances of ``KaldiLogger`` to filter appropriately
    """

    def __new__(cls, name, *args, **kwargs):
        _REGISTERED_LOGGER_NAMES.add(name)
        return super(KaldiLogger, cls).__new__(cls, name, *args, **kwargs)

    def makeRecord(self, *args, **kwargs):
        # unfortunately, the signature for this method differs between
        # python 2 and python 3 (there's an additional keyword argument
        # in python 3). They are, however, in the same order:
        # name, level, fn, lno, msg, args, exc_info, func, extra, sinfo
        if len(args) >= 9:
            extra = args[8]
        else:
            extra = kwargs.get('extra', None)
        if extra and 'kaldi_envelope' in extra:
            kaldi_envelope = extra['kaldi_envelope']
            args = list(args)
            args[1] = _kaldi_lvl_to_logging_lvl(kaldi_envelope[0])
            args[2] = kaldi_envelope[2]
            args[3] = kaldi_envelope[3]
            if len(args) >= 8:
                args[7] = kaldi_envelope[1]
            else:
                kwargs['func'] = kaldi_envelope[1]
        record = super(KaldiLogger, self).makeRecord(*args, **kwargs)
        return record

    def setLevel(self, lvl):
        _convert_logging_lvl_to_kaldi_lvl(lvl)
        return super(KaldiLogger, self).setLevel(lvl)

    def getEffectiveLevel(self):
        lvl = super(KaldiLogger, self).getEffectiveLevel()
        _convert_logging_lvl_to_kaldi_lvl(lvl)
        return lvl

def _convert_logging_lvl_to_kaldi_lvl(lvl):
    global _KALDI_LOG_LEVEL
    if lvl < _KALDI_LOG_LEVEL:
        if lvl >= 10:
            _set_verbose_level((lvl - 20) // -10)
        else:
            _set_verbose_level(11 - lvl)
        _KALDI_LOG_LEVEL = lvl

def _kaldi_lvl_to_logging_lvl(lvl):
    if lvl <= 1:
        lvl = lvl * -10 + 20
    else:
        lvl = 11 - lvl
    return lvl

def _kaldi_logging_callback(envelope, message):
    # propagate to all subclasses
    py_severity = _kaldi_lvl_to_logging_lvl(envelope[0])
    for logger_name in _REGISTERED_LOGGER_NAMES:
        logger = logging.getLogger(logger_name)
        logger.log(py_severity, message, extra={'kaldi_envelope': envelope})

def _initialize_module_logging():
    old_logger_class = logging.getLoggerClass()
    logging.setLoggerClass(KaldiLogger)
    logger = logging.getLogger('pydrobert.kaldi')
    logging.setLoggerClass(old_logger_class)
    logger.addHandler(logging.StreamHandler())

_set_log_handler(_kaldi_logging_callback)
_initialize_module_logging()
