# Copyright 2018 Sean Robertson

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''Command line entry points for pydrobert.kaldi

This submodule simply collects the command line entry points from other
submodules
'''

from __future__ import absolute_import

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2017 Sean Robertson"

import pydrobert.kaldi.eval.command_line as _eval_command_line
import pydrobert.kaldi.feat.command_line as _feat_command_line
import pydrobert.kaldi.io.command_line as _io_command_line

from pydrobert.kaldi.eval.command_line import *
from pydrobert.kaldi.feat.command_line import *
from pydrobert.kaldi.io.command_line import *


__all__ = (
    _eval_command_line.__all__ +
    _feat_command_line.__all__ +
    _io_command_line.__all__
)
