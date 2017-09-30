# Copyright 2017 Sean Robertson

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tie Kaldi's logging into python's builtin logging module

By default, Kaldi's warning, error, and critical messages are all piped
directly to stderr. Any ``logging.Logger`` instance can register with
``register_logger_for_kaldi`` to receive Kaldi messages. If some
logger is registered to receive Kaldi messages, messages will no longer
be sent to stderr by default. Kaldi codes are converted to ``logging``
codes according to the following chart
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

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from sys import stderr

from pydrobert.kaldi._internal import GetVerboseLevel as _get_verbose_level
from pydrobert.kaldi._internal import SetPythonLogHandler as _set_log_handler
from pydrobert.kaldi._internal import SetVerboseLevel as _set_verbose_level

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2016 Sean Robertson"

__all__ = [
    'KaldiLogger',
    'register_logger_for_kaldi',
    'deregister_logger_for_kaldi',
]

class KaldiLogger(logging.getLoggerClass()):
    """Logger subclass that overwrites log info with kaldi's

    Setting the `Logger` class of the python module `logging` (thru
    ``logging.setLoggerClass``) to `KaldiLogger` will allow new loggers
    to intercept messages from Kaldi and inject Kaldi's trace
    information into the record. With this injection, the logger will
    point to the location in Kaldi's source that the message originated
    from. Without it, the logger will point to a location within this
    submodule (``pydrobert.kaldi.logging``).
    """

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
            args[2] = kaldi_envelope[2]
            args[3] = kaldi_envelope[3]
            if len(args) >= 8:
                args[7] = kaldi_envelope[1]
            else:
                kwargs['func'] = kaldi_envelope[1]
        record = super(KaldiLogger, self).makeRecord(*args, **kwargs)
        return record

def register_logger_for_kaldi(name):
    '''Register logger to receive Kaldi's messages

    See module docstring for more info

    Parameters
    ----------
    name : str
        logger name. When a new message comes along from Kaldi, the
        callback will send a message to ``logging.getLogger(name)``
    '''
    # set verbosity as high as we can and let the loggers filter out
    # what they want
    _set_verbose_level(2147483647)
    _REGISTERED_LOGGER_NAMES.add(name)

def deregister_logger_for_kaldi(name):
    '''Deregister logger previously registered w register_logger_for_kaldi'''
    _REGISTERED_LOGGER_NAMES.discard(name)
    if not _REGISTERED_LOGGER_NAMES:
        _set_verbose_level(0)

def _kaldi_logging_handler(envelope, message):
    '''Kaldi message handler that plays nicely with logging module

    If no loggers are registered to receive messages, messages that
    are warnings, errors, or critical are printed directly to stdout.

    Otherwise, errors are propagated to registered loggers
    '''
    if _REGISTERED_LOGGER_NAMES:
        py_severity = _kaldi_lvl_to_logging_lvl(envelope[0])
        for logger_name in _REGISTERED_LOGGER_NAMES:
            logger = logging.getLogger(logger_name)
            logger.log(
                py_severity, message, extra={'kaldi_envelope': envelope})
    elif envelope[0] < 0:
        print(message, file=stderr)

def _kaldi_lvl_to_logging_lvl(lvl):
    '''Convert kaldi level to logging level. See module docstring'''
    if lvl <= 1:
        lvl = lvl * -10 + 20
    else:
        lvl = 11 - lvl
    return lvl

def _logging_lvl_to_kaldi_lvl(lvl):
    '''Convert logging level to kaldi level. See module docstring'''
    if lvl >= 10:
        lvl = max(-3, (lvl - 20) // -10)
    else:
        lvl = 11 - lvl
    return lvl

_REGISTERED_LOGGER_NAMES = set()
'''The loggers who will receive kaldi's messages'''

_set_log_handler(_kaldi_logging_handler)
