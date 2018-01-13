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

"""Pytests for `pydrobert.kaldi.argparse`"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from pydrobert.kaldi.io import argparse
from pydrobert.kaldi.logging import kaldi_lvl_to_logging_lvl


def test_can_parse_equals():
    parser = argparse.KaldiParser()
    parser.add_argument('--foo', type=int, default=1)
    assert parser.parse_args([]).foo == 1
    assert parser.parse_args(['--foo', '2']).foo == 2
    assert parser.parse_args(['--foo=2']).foo == 2


def test_config(temp_file_1_name):
    with open(temp_file_1_name, mode='w') as conf_file:
        conf_file.write('--foo 2\n')
        conf_file.write('#--foo 3\n')
        conf_file.write('#--foo 4\n')
    parser = argparse.KaldiParser()
    parser.add_argument('--foo', type=int, default=1)
    assert parser.parse_args([]).foo == 1
    assert parser.parse_args(['--config', temp_file_1_name]).foo == 2
    assert parser.parse_args(
        ['--foo', '4', '--config', temp_file_1_name]).foo == 4


def test_can_parse_kaldi_types():
    parser = argparse.KaldiParser()
    parser.add_argument('a', type='kaldi_bool')
    parser.add_argument('b', type='kaldi_rspecifier')
    parser.add_argument('c', type='kaldi_wspecifier')
    parser.add_argument('d', type='kaldi_rxfilename')
    parser.add_argument('e', type='kaldi_wxfilename')
    parser.add_argument('f', type='kaldi_dtype')
    parser.add_argument('g', type='numpy_dtype')
    parser.parse_args(['true', 'ark:-', 'ark:-', '-', '-', 'bm', 'int32'])


def test_verbosity():
    logger = logging.getLogger('this_should_not_be_used')
    parser = argparse.KaldiParser(logger=logger)
    assert logger.level == kaldi_lvl_to_logging_lvl(0)
    parser.parse_args(['-v', '-1'])
    assert logger.level == kaldi_lvl_to_logging_lvl(-1)
    parser.parse_args(['-v', '9'])
    assert logger.level == kaldi_lvl_to_logging_lvl(9)
