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

""" Pytests for `pydrobert.kaldi` logging """

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os

from io import StringIO
from tempfile import NamedTemporaryFile

import numpy as np
import pytest

import pydrobert.kaldi as kaldi

@pytest.fixture
def temp_file_1_name():
    temp = NamedTemporaryFile(delete=False)
    temp.close()
    yield temp.name
    os.remove(temp.name)

@pytest.fixture
def logger():
    ret_logger = logging.getLogger('pydrobert.kaldi')
    s_stream = StringIO()
    handler = logging.StreamHandler(s_stream)
    ret_logger.addHandler(handler)
    yield ret_logger
    ret_logger.removeHandler(handler)
    ret_logger.setLevel(logging.NOTSET)

def test_basic_write(logger):
    s_stream = logger.handlers[0].stream
    assert not s_stream.tell()
    test_string = "I'm a dude playing a dude disguised as another dude"
    logger.warning(test_string)
    assert s_stream.tell()
    assert test_string + '\n' == s_stream.getvalue()

@pytest.mark.parametrize('threaded', [True, False])
def test_elicit_kaldi_warning(logger, temp_file_1_name, threaded):
    s_stream = logger.handlers[0].stream
    assert not s_stream.tell()
    wspecifier = 'ark,t{}:{}'.format(
        ',bg' if threaded else '', temp_file_1_name)
    writer = kaldi.tables.open('ark,t:{}'.format(temp_file_1_name), 'bv', 'w')
    writer.write('zz', [np.infty])
    writer.write('zz', [np.infty])
    writer.close()
    reader = kaldi.tables.open(
        'ark,t{}:{}'.format(',bg' if threaded else '', temp_file_1_name), 'bv')
    next(reader)
    next(reader)
    reader.close()
    assert s_stream.tell()
    assert 'Reading infinite value into vector.\n' * 2 == s_stream.getvalue()

def test_set_level(logger, temp_file_1_name):
    s_stream = logger.handlers[0].stream
    assert not s_stream.tell()
    rwspecifier = 'ark,t:{}'.format(temp_file_1_name)
    logger.setLevel(logging.ERROR)
    logger.warning('sound of silence')
    assert not s_stream.tell()
    writer = kaldi.tables.open(rwspecifier, 'bv', 'w')
    writer.write('zz', [np.infty])
    writer.close()
    reader = kaldi.tables.open(rwspecifier, 'bv')
    next(reader)
    reader.close()
    assert not s_stream.tell()
    logger.setLevel(logging.INFO)
    reader = kaldi.tables.open(rwspecifier, 'bv')
    next(reader)
    reader.close()
    assert s_stream.tell()
    assert 'Reading infinite value into vector.\n' == s_stream.getvalue()

def test_log_source_is_appropriate(logger, temp_file_1_name):
    handler = logger.handlers[0]
    s_stream = handler.stream
    rwspecifier = 'ark,t:{}'.format(temp_file_1_name)
    handler.setFormatter(logging.Formatter('%(filename)s: %(message)s'))
    assert not s_stream.tell()
    logger.warning('pokeymans')
    assert 'test_logging.py' in s_stream.getvalue()
    assert 'kaldi-matrix.cc' not in s_stream.getvalue()
    s_stream.seek(0)
    writer = kaldi.tables.open(rwspecifier, 'bv', 'w')
    writer.write('zz', [np.infty])
    writer.close()
    reader = kaldi.tables.open(rwspecifier, 'bv')
    next(reader)
    reader.close()
    assert 'kaldi-matrix.cc' in s_stream.getvalue()
    assert '__init__.py' not in s_stream.getvalue()
