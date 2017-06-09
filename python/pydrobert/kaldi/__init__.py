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

from ._internal import SetPythonLogHandler as _set_log_handler
from ._internal import SetVerboseLevel as _set_verbose_level

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2016 Sean Robertson"

__all__ = ['tables']

LOCALE_MESSAGE = """\
It looks like you did not 'export LC_ALL=C' before you started python.
This is important to do if you plan on using kaldi's sorted tables at all."""
if locale.getdefaultlocale() != (None, None):
    print(LOCALE_MESSAGE, file=sys.stderr)

class KaldiLogger(logging.getLoggerClass()):
    """Logger subclass to make it easier to synchronize logging with Kaldi
    
    This class is almost the same as the class it inherits from, with two key
    changes:
     - line numbers, function names, paths, and levels will be overwritten if
       ``'kaldi_envelope'`` is a key provided in the `extra` argument. This is
       so that logs point to the actual source in Kaldi, rather than the python
       callback line
     - `setLevel` also adjusts the verbosity level in Kaldi as
       ``kaldi_level = max(-3, (lvl - 20) // -10)``
    """

    def makeRecord(self, *args, **kwargs):
        record = super(KaldiLogger, self).makeRecord(*args, **kwargs)
        if hasattr(record, 'kaldi_envelope'):
            record.level, record.func, record.pathname, record.lineno, = \
                record.kaldi_envelope
        return record

    def setLevel(self, lvl):
        _set_verbose_level(max(-3, (lvl - 20) // -10))
        return super(KaldiLogger, self).setLevel(lvl)

def _kaldi_logging_callback(envelope, message):
    # send LogHandler info from Kaldi to module's logger
    logger = logging.getLogger('pydrobert.kaldi')
    logger.log(envelope[0], message, extra={'kaldi_envelope': envelope})

logging.setLoggerClass(KaldiLogger)
_set_log_handler(_kaldi_logging_callback)
_set_verbose_level(max(
    -3,
    (logging.getLogger('pydrobert.kaldi').getEffectiveLevel() - 20) // -10,
))
