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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import locale
import warnings

from pkg_resources import DistributionNotFound
from pkg_resources import get_distribution

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2016 Sean Robertson"

__all__ = ['io']

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    pass

LOCALE_MESSAGE = """\
It looks like you did not 'export LC_ALL=C' before you started python.
This is important to do if you plan on using kaldi's sorted tables at all."""
if locale.getdefaultlocale() != (None, None):
    warnings.warn(LOCALE_MESSAGE)
