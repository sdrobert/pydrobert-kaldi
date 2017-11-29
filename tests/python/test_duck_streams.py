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

'''Tests for `pydrobert.kaldi.io.duck_streams`'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from random import shuffle

import numpy as np
import pytest

from pydrobert.kaldi.io import open as io_open


def test_chained(temp_file_1_name):
    # wholly too limited a test
    obj_list = [
        ('iv', tuple(x for x in range(1000))),
        ('fm', [[1, 2.5], [1e-10, 4]]),
        ('dv', np.random.random(1)),
        ('dm', np.random.random((100, 20))),
        ('t', 'fiddlesticks'),
        ('t', 'munsters'),
    ]
    shuffle(obj_list)
    with io_open(temp_file_1_name, mode='w') as outp:
        for dtype, obj in obj_list:
            outp.write(obj, dtype)
    with io_open(temp_file_1_name) as inp:
        for dtype, obj in obj_list:
            read = inp.read(dtype)
            if dtype in ('fv', 'fm', 'dv', 'dm'):
                assert np.allclose(read, obj)
            else:
                assert read == obj


@pytest.mark.parametrize('ktype,value', [
    ('bv', []),
    ('bm', [[]]),
    ('bv', [np.infty]),
    ('bv', [1] * 100),
    ('bm', [[1, 2], [3, 4]]),
    ('fv', [-1, -1, 0, .1]),
    ('fm', np.random.random((10, 10)).astype(np.float32)),
    ('dv', np.arange(1000, dtype=np.float64) - 10),
    ('dm', np.outer(
        np.arange(100, dtype=np.float32),
        np.arange(111, dtype=np.float32))),  # upcast ok
    ('t', 'able'),
    # our methods can accept unicode, but always return strings,
    # so we don't enforce that these be unicode type.
    ('t', '\u00D6a'),
    ('t', 'n\u00F9'),
    # lists can be written, but tuples are read
    ('tv', tuple()),
    ('tv', ('foo', 'bar')),
    ('tv', ('skryyyyy',)),
    ('tv', ('\u00D6a', 'n\u00F9')),
    ('i', -10),
    ('iv', (0, 1, 2)),
    ('iv', tuple()),
    ('ivv', ((100,), (10, 40))),
    ('ipv', ((1, 2), (3, 4))),
    ('d', .1),
    ('d', 1),
    ('b', -.1),
    ('b', -10000),
    ('bpv', ((0, 1.3), (4.5, 6))),
    ('B', True),
    ('B', False),
])
@pytest.mark.parametrize('binary', [True, False])
def test_read_write_valid(temp_file_1_name, ktype, value, binary):
    with io_open(temp_file_1_name, mode='w', header=False) as outp:
        outp.write(value, ktype, write_binary=binary)
    with io_open(temp_file_1_name, header=False) as inp:
        read_value = inp.read(ktype, read_binary=binary)
    if ktype in ('bv', 'bm', 'fv', 'fm', 'dv', 'dm', 'b', 'd', 'bpv'):
        assert np.allclose(read_value, value)
    else:
        assert read_value == value


@pytest.mark.parametrize('ktype,dtype,value', [
    ('b', np.float32, 3.14),  # upcast ok (if applicable)
    ('bpv', np.float32, ((0, 1.2), (3.4, 5), (6, 7.89))),  # upcast ok (if app)
    ('i', np.int32, 420),
    ('iv', np.int32, (1, 1, 2, 3, 5, 8, 13, 21)),
    ('ivv', np.int32, ((0, 1), (2, 3), (4, 5))),
    ('ipv', np.int32, ((0, 1), (2, 3), (4, 5))),
    ('t', np.str, 'foo'),
    ('tv', np.str, ('foo', 'bar')),
])
def test_write_read_numpy_versions(temp_file_1_name, ktype, dtype, value):
    npy_value = np.array(value).astype(dtype)
    with io_open(temp_file_1_name, mode='w', header=False) as outp:
        outp.write(npy_value, ktype)
    with io_open(temp_file_1_name, header=False) as inp:
        act_value = inp.read(ktype)
    if ktype in ('b', 'bpv'):
        assert np.allclose(value, act_value)
    else:
        assert value == act_value


@pytest.mark.parametrize('ktype,value', [
    ('bv', ['a', 2, 3]),
    ('bv', 'abc'),
    ('bv', [[1, 2]]),
    ('fv', np.arange(3, dtype=np.float64)),  # downcast not ok
    ('bm', [['a', 2]]),
    ('bm', [0]),
    ('fm', np.random.random((10, 1)).astype(np.float64)),
    ('t', 1),
    ('t', []),
    ('t', 'was I'),
    ('tv', ['a', 1]),
    ('tv', ("it's", 'me DIO')),
    ('tv', 'foobar'),
    ('i', 'zimble'),
    ('iv', 1),
    ('ivv', [[[1]]]),
    ('ipv', ((1, 2), (3,))),
    ('d', 1 + 1j),
    ('b', 'akljdal'),
    ('bpv', ((1,), (2, 3))),
])
@pytest.mark.parametrize('binary', [True, False])
def test_write_invalid(temp_file_1_name, ktype, value, binary):
    outp = io_open(temp_file_1_name, mode='w')
    with pytest.raises(Exception):
        outp.write(value, ktype, write_binary=binary)
