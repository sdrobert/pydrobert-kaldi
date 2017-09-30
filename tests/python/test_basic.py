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

'''Tests for `pydrobert.kaldi.io.basic`'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from random import shuffle

import numpy as np

from pydrobert.kaldi.io import open as io_open

def test_chained(temp_file_1_name):
    # wholly too limited a test
    obj_list = [
        ('fv', [x for x in range(1000)]),
        ('fm', [[1,2.5], [1e-10, 4]]),
        ('dv', np.random.random(1)),
        ('dm', np.random.random((100, 20))),
        ('t', 'fiddlesticks'),
        ('t', 'munsters'),
    ]
    shuffle(obj_list)
    with io_open(temp_file_1_name, mode='w') as outp:
        for _, obj in obj_list:
            outp.write(obj)
    with io_open(temp_file_1_name) as inp:
        for dtype, obj in obj_list:
            read = inp.read(dtype)
            if dtype in ('fv', 'fm', 'dv', 'dm'):
                assert np.allclose(read, obj)
            else:
                assert read == obj
