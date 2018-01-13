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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pydrobert.kaldi.io as kaldi_io

from pydrobert.kaldi.eval import command_line


def test_compute_error_rate(
        temp_file_1_name, temp_file_2_name, temp_file_3_name):
    with kaldi_io.open('ark:' + temp_file_1_name, 'tv', 'w') as ref_writer:
        ref_writer.write('A', ('lorem', 'ipsum', 'dolor', 'sit', 'amet'))
        ref_writer.write('B', ('consectetur', 'adipiscing', 'elit'))
    with kaldi_io.open('ark:' + temp_file_2_name, 'tv', 'w') as hyp_writer:
        hyp_writer.write(
            'A', ('laura', 'ipsum', 'dollars', 'sit', 'down', 'amet'))
        hyp_writer.write(
            'B', ('consecutive', 'elite'))
    # A : lorem -> laura, dolor -> dollars, -> down
    # B : consectetur -> consecutive, adipiscing -> , elit -> elite
    # with insertions = 6 / 8
    # without insertions = 5 / 8
    ret_code = command_line.compute_error_rate([
        'ark:' + temp_file_1_name,
        'ark:' + temp_file_2_name,
        temp_file_3_name,
    ])
    assert ret_code == 0
    with open(temp_file_3_name) as out_file_reader:
        out_text = out_file_reader.read()
    assert 'Error rate: 75.00%' in out_text
    ret_code = command_line.compute_error_rate([
        'ark:' + temp_file_1_name,
        'ark:' + temp_file_2_name,
        temp_file_3_name,
        '--include-inserts-in-cost=false',
        '--report-accuracy=true',
    ])
    assert ret_code == 0
    with open(temp_file_3_name) as out_file_reader:
        out_text = out_file_reader.read()
    assert 'Accuracy: {:.2f}%'.format((1 - 5 / 8) * 100) in out_text
