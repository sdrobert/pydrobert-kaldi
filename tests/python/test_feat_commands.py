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

"""Pytests for `pydrobert.kaldi.feats.command_line`"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import pytest

from pydrobert.kaldi.feat import command_line
from pydrobert.kaldi.io import open as kaldi_open
from pydrobert.kaldi.io.util import infer_kaldi_data_type
from six.moves import cPickle as pickle


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


def test_normalize_feat_lens(
        temp_file_1_name, temp_file_2_name, temp_file_3_name):
    feats_a = np.random.random((10, 4))
    feats_b = np.random.random((5, 4))
    feats_c = np.random.random((4, 4))
    with kaldi_open('ark:' + temp_file_1_name, 'dm', 'w') as feats_in_writer:
        feats_in_writer.write('A', feats_a)
        feats_in_writer.write('B', feats_b)
        feats_in_writer.write('C', feats_c)
    with kaldi_open('ark:' + temp_file_2_name, 'i', 'w') as len_in_writer:
        len_in_writer.write('A', 9)
        len_in_writer.write('B', 7)
        len_in_writer.write('C', 4)
    ret_code = command_line.normalize_feat_lens([
        'ark:' + temp_file_1_name,
        'ark:' + temp_file_2_name,
        'ark:' + temp_file_3_name,
        '--type=dm',
        '--pad-mode=zero',
    ])
    assert ret_code == 0
    with kaldi_open('ark:' + temp_file_3_name, 'dm') as feats_out_reader:
        out_a = next(feats_out_reader)
        out_b = next(feats_out_reader)
        out_c = next(feats_out_reader)
        assert out_a.shape == (9, 4)
        assert np.allclose(out_a, feats_a[:9])
        assert out_b.shape == (7, 4)
        assert np.allclose(out_b[:5], feats_b)
        assert np.allclose(out_b[5:], 0)
        assert out_c.shape == (4, 4)
        assert np.allclose(out_c, feats_c)
    ret_code = command_line.normalize_feat_lens([
        'ark:' + temp_file_1_name,
        'ark:' + temp_file_2_name,
        'ark:' + temp_file_3_name,
        '--type=dm',
        '--tolerance=1',
        '--strict=true',
    ])
    assert ret_code == 1
