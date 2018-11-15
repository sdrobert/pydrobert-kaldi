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

"""Pytests for `pydrobert.kaldi.io.command_line`"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import numpy as np
import pytest
import pydrobert.kaldi.io.command_line as command_line

from six.moves import cPickle as pickle
from pydrobert.kaldi.io.util import infer_kaldi_data_type
from pydrobert.kaldi.io import open as kaldi_open


@pytest.mark.parametrize('values', [
    [
        np.array([1, 2, 3], dtype=np.float32),
        np.array([4], dtype=np.float32),
        np.array([], dtype=np.float32),
    ],
    [
        np.random.random((100, 20)),
    ],
    ['foo', 'bar', 'baz'],
    [
        ('foo', 'bar'),
        ('baz',),
    ],
    [],
])
def test_write_pickle_to_table(values, temp_file_1_name, temp_file_2_name):
    if len(values):
        kaldi_dtype = infer_kaldi_data_type(values[0]).value
    else:
        kaldi_dtype = 'bm'
    with open(temp_file_1_name, 'wb') as pickle_file:
        for num, value in enumerate(values):
            pickle.dump((str(num), value), pickle_file)
    ret_code = command_line.write_pickle_to_table(
        [temp_file_1_name, 'ark:' + temp_file_2_name, '-o', kaldi_dtype])
    assert ret_code == 0
    kaldi_reader = kaldi_open('ark:' + temp_file_2_name, kaldi_dtype, 'r')
    num_entries = 0
    for key, value in kaldi_reader.items():
        num_entries = int(key) + 1
        try:
            values[num_entries - 1].dtype
            assert np.allclose(value, values[num_entries - 1])
        except AttributeError:
            assert value == values[num_entries - 1]
    assert num_entries == len(values)


@pytest.mark.parametrize('values', [
    [
        np.array([1, 2, 3], dtype=np.float32),
        np.array([4], dtype=np.float32),
        np.array([], dtype=np.float32),
    ],
    [
        np.random.random((100, 20)),
    ],
    ['foo', 'bar', 'baz'],
    [
        ('foo', 'bar'),
        ('baz',),
    ],
    [],
])
def test_write_table_to_pickle(values, temp_file_1_name, temp_file_2_name):
    if len(values):
        kaldi_dtype = infer_kaldi_data_type(values[0]).value
    else:
        kaldi_dtype = 'bm'
    with kaldi_open('ark:' + temp_file_1_name, kaldi_dtype, 'w') as writer:
        for num, value in enumerate(values):
            writer.write(str(num), value)
    ret_code = command_line.write_table_to_pickle(
        ['ark:' + temp_file_1_name, temp_file_2_name, '-i', kaldi_dtype])
    assert ret_code == 0
    num_entries = 0
    pickle_file = open(temp_file_2_name, 'rb')
    num_entries = 0
    try:
        while True:
            key, value = pickle.load(pickle_file)
            num_entries = int(key) + 1
            try:
                values[num_entries - 1].dtype
                assert np.allclose(value, values[num_entries - 1])
            except AttributeError:
                assert value == values[num_entries - 1]
    except EOFError:
        pass
    assert num_entries == len(values)


@pytest.mark.pytorch
def test_write_table_to_torch_dir(temp_dir):
    import torch
    out_dir = os.path.join(temp_dir, 'test_write_table_to_torch_dir')
    os.makedirs(out_dir)
    rwspecifier = 'ark:' + os.path.join(out_dir, 'table.ark')
    a = torch.rand(10, 4)
    b = torch.rand(5, 2)
    c = torch.rand(5, 100)
    with kaldi_open(rwspecifier, 'bm', mode='w') as table:
        table.write('a', a.numpy())
        table.write('b', b.numpy())
        table.write('c', c.numpy())
    assert not command_line.write_table_to_torch_dir([rwspecifier, out_dir])
    assert torch.allclose(c, torch.load(os.path.join(out_dir, 'c.pt')))
    assert torch.allclose(b, torch.load(os.path.join(out_dir, 'b.pt')))
    assert torch.allclose(a, torch.load(os.path.join(out_dir, 'a.pt')))


@pytest.mark.pytorch
def test_write_torch_dir_to_table(temp_dir):
    import torch
    in_dir = os.path.join(temp_dir, 'test_write_torch_dir_to_table')
    rwspecifier = 'ark:' + os.path.join(in_dir, 'table.ark')
    os.makedirs(in_dir)
    a = torch.rand(5, 4)
    b = torch.rand(4, 3)
    c = torch.rand(3, 2)
    torch.save(a, os.path.join(in_dir, 'a.pt'))
    torch.save(b, os.path.join(in_dir, 'b.pt'))
    torch.save(c, os.path.join(in_dir, 'c.pt'))
    assert not command_line.write_torch_dir_to_table([in_dir, rwspecifier])
    with kaldi_open(rwspecifier, 'bm') as table:
        keys, vals = zip(*table.items())
        keys = tuple(keys)
        vals = tuple(vals)
    assert keys == ('a', 'b', 'c')
    assert len(vals) == 3
    for dval, tval in zip((a, b, c), vals):
        assert torch.allclose(dval, torch.from_numpy(tval))
