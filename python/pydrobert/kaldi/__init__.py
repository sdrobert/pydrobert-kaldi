"""Contains python/cython access to Kaldi.

See ``README.RST`` for more info.

Note:
    Kaldi tools usually run with 'C' locale. To make sure::

        $ export LC_ALL=C

    is called before you use any Kaldi utilities, importing this module
    prints a warning to stderr if it detects any other locale.
"""

from __future__ import print_function

import locale as _locale
import sys as _sys

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2016 Sean Robertson"

__all__ = ['tables']

_LOCALE_MESSAGE = """\
It looks like you did not 'export LC_ALL=C' before you started python.
This is important to do if you plan on using kaldi's sorted tables at
all."""
if _locale.getdefaultlocale() != (None, None):
    print(_LOCALE_MESSAGE, file=_sys.stderr)
