# Copyright 2021 Sean Robertson

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Python access to kaldi"""

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2021 Sean Robertson"

__all__ = [
    "io",
    "feat",
    "eval",
    "logging",
    "KaldiLocaleWarning",
    "command_line",
]

try:
    from .version import version as __version__  # type: ignore
except ImportError:
    __version__ = "inplace"


class KaldiLocaleWarning(Warning):
    """Class used when LC_ALL != 'C' when pydrobert.kaldi.io is imported"""

    LOCALE_MESSAGE = """\
It looks like you did not 'export LC_ALL=C' before you started python.
This is important to do if you plan on using kaldi's sorted tables at all."""
