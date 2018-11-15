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

"""Pytests for `pydrobert.kaldi.feats.command_line`"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import pytest

from pydrobert.kaldi.feat import command_line
from pydrobert.kaldi.io import open as kaldi_open


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
