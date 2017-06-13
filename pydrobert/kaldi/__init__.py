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
            args[1] = kaldi_envelope[0]
            args[2] = kaldi_envelope[2]
            args[3] = kaldi_envelope[3]
            if len(args) >= 8:
                args[7] = kaldi_envelope[1]
            else:
                kwargs['func'] = kaldi_envelope[1]
        record = super(KaldiLogger, self).makeRecord(*args, **kwargs)
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
