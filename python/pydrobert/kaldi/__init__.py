from __future__ import print_function

import locale as _locale
import sys as _sys

__all__ = ['tables']

_LOCALE_MESSAGE = """\
It looks like you did not 'export LC_ALL=C' before you started python.
This is important to do if you plan on using kaldi's sorted tables at
all."""
if _locale.getdefaultlocale() != (None, None):
    print(_LOCALE_MESSAGE, file=_sys.stderr)
