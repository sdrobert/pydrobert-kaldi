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
import sys

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
    'kaldi_lvl_to_logging_lvl',
    'logging_lvl_to_kaldi_lvl',
    'kaldi_vlog_level_cmd_decorator',
]


class KaldiLogger(logging.getLoggerClass()):
    """Logger subclass that overwrites log info with kaldi's

    Setting the ``Logger`` class of the python module ``logging`` (thru
    ``logging.setLoggerClass``) to ``KaldiLogger`` will allow new
    loggers to intercept messages from Kaldi and inject Kaldi's trace
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

    makeRecord.__doc__ = logging.getLoggerClass().__doc__


def kaldi_logger_decorator(func):
    '''Sets the default logger class to KaldiLogger over the func call'''
    def _new_func(*args, **kwargs):
        logger_class = logging.getLoggerClass()
        logging.setLoggerClass(KaldiLogger)
        try:
            ret = func(*args, **kwargs)
        finally:
            logging.setLoggerClass(logger_class)
        return ret
    _new_func.__doc__ = func.__doc__
    return _new_func


def register_logger_for_kaldi(logger):
    '''Register logger to receive Kaldi's messages

    See module docstring for more info

    Parameters
    ----------
    logger : str or logger
        Either the logger or its name. When a new message comes along
        from Kaldi, the callback will send a message to the logger
    '''
    # set verbosity as high as we can and let the loggers filter out
    # what they want
    _set_verbose_level(2147483647)
    try:
        _REGISTERED_LOGGER_NAMES.add(logger.name)
    except AttributeError:
        _REGISTERED_LOGGER_NAMES.add(logger)


def deregister_logger_for_kaldi(name):
    '''Deregister logger previously registered w register_logger_for_kaldi'''
    _REGISTERED_LOGGER_NAMES.discard(name)
    if not _REGISTERED_LOGGER_NAMES:
        _set_verbose_level(0)


def deregister_all_loggers_for_kaldi():
    '''Deregister all loggers registered w register_logger_for_kaldi'''
    _REGISTERED_LOGGER_NAMES.clear()
    _set_verbose_level(0)


def kaldi_vlog_level_cmd_decorator(func):
    '''Decorator to rename, then revert, level names according to Kaldi [1]_

    See ``pydrobert.kaldi.logging`` for the conversion chart. After the
    return of the function, the level names before the call are
    reverted. This function is insensitive to renaming while the
    function executes

    References
    ----------
    .. [1] Povey, D., et al (2011). The Kaldi Speech Recognition
       Toolkit. ASRU
    '''
    def _new_func(*args, **kwargs):
        old_level_names = [logging.getLevelName(0)]
        for level in range(1, 10):
            old_level_names.append(logging.getLevelName(level))
            logging.addLevelName(level, 'VLOG [{:d}]'.format(11 - level))
        for level in range(10, 51):
            old_level_names.append(logging.getLevelName(level))
            if level // 10 == 1:
                logging.addLevelName(level, 'VLOG [1]')
            elif level // 10 == 2:
                logging.addLevelName(level, 'LOG')
            elif level // 10 == 3:
                logging.addLevelName(level, 'WARNING')
            elif level // 10 == 4:
                logging.addLevelName(level, 'ERROR')
            elif level // 10 == 5:
                logging.addLevelName(level, 'ASSERTION_FAILED ')
        try:
            ret = func(*args, **kwargs)
        finally:
            for level, name in enumerate(old_level_names):
                logging.addLevelName(level, name)
        return ret
    _new_func.__doc__ = func.__doc__
    return _new_func


def _kaldi_logging_handler(envelope, message):
    '''Kaldi message handler that plays nicely with logging module

    If no loggers are registered to receive messages, messages that
    are warnings, errors, or critical are printed directly to stdout.

    Otherwise, errors are propagated to registered loggers
    '''
    message = message.decode(encoding='utf8', errors='replace')
    if _REGISTERED_LOGGER_NAMES:
        py_severity = kaldi_lvl_to_logging_lvl(envelope[0])
        for logger_name in _REGISTERED_LOGGER_NAMES:
            logger = logging.getLogger(logger_name)
            logger.log(
                py_severity, message, extra={'kaldi_envelope': envelope})
    elif envelope[0] < 0:
        print(message, file=sys.stderr)


def kaldi_lvl_to_logging_lvl(lvl):
    '''Convert kaldi level to logging level'''
    if lvl <= 1:
        lvl = lvl * -10 + 20
    else:
        lvl = 11 - lvl
    return lvl


def logging_lvl_to_kaldi_lvl(lvl):
    '''Convert logging level to kaldi level'''
    if lvl >= 10:
        lvl = max(-3, (lvl - 20) // -10)
    else:
        lvl = 11 - lvl
    return lvl


_REGISTERED_LOGGER_NAMES = set()
'''The loggers who will receive kaldi's messages'''


_set_log_handler(_kaldi_logging_handler)
