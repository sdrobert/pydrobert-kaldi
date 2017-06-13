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

try:
    from StringIO import StringIO # py 2.7
except ImportError:
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
    old_makeRecord = ret_logger.makeRecord
    yield ret_logger
    ret_logger.makeRecord = old_makeRecord
    ret_logger.removeHandler(handler)
    ret_logger.setLevel(logging.NOTSET)

def test_basic_write(logger):
    s_stream = logger.handlers[-1].stream
    assert not s_stream.tell()
    test_string = "I'm a dude playing a dude disguised as another dude"
    logger.warning(test_string)
    assert s_stream.tell()
    assert test_string + '\n' == s_stream.getvalue()

def elicit_warning(filename, threaded=False):
    # helper to elicit a warning from kaldi
    writer = kaldi.tables.open('ark,t:{}'.format(filename), 'bv', 'w')
    writer.write('zz', [np.infty])
    writer.close()
    reader = kaldi.tables.open(
        'ark,t{}:{}'.format(',bg' if threaded else '', filename), 'bv')
    next(reader)
    reader.close()

@pytest.mark.parametrize('threaded', [True, False])
def test_elicit_kaldi_warning(logger, temp_file_1_name, threaded):
    s_stream = logger.handlers[-1].stream
    assert not s_stream.tell()
    elicit_warning(temp_file_1_name, threaded)
    assert s_stream.tell()
    assert 'Reading infinite value into vector.\n' == s_stream.getvalue()

def test_set_level(logger, temp_file_1_name):
    s_stream = logger.handlers[-1].stream
    assert not s_stream.tell()
    rwspecifier = 'ark,t:{}'.format(temp_file_1_name)
    logger.setLevel(logging.ERROR)
    logger.warning('sound of silence')
    assert not s_stream.tell()
    elicit_warning(temp_file_1_name)
    assert not s_stream.tell()
    logger.setLevel(logging.INFO)
    elicit_warning(temp_file_1_name)
    assert s_stream.tell()
    assert 'Reading infinite value into vector.\n' == s_stream.getvalue()

def test_log_source_is_appropriate(logger, temp_file_1_name):
    handler = logger.handlers[-1]
    s_stream = handler.stream
    rwspecifier = 'ark,t:{}'.format(temp_file_1_name)
    handler.setFormatter(logging.Formatter('%(filename)s: %(message)s'))
    assert not s_stream.tell()
    logger.warning('pokeymans')
    assert 'test_logging.py' in s_stream.getvalue()
    assert 'kaldi-vector.cc' not in s_stream.getvalue()
    s_stream.seek(0)
    elicit_warning(temp_file_1_name)
    assert 'kaldi-vector.cc' in s_stream.getvalue()
    assert '__init__.py' not in s_stream.getvalue()

def test_python_error_doesnt_segfault(logger, temp_file_1_name):
    def _raise_exception(*args, **kwargs):
        raise Exception()
    logger.makeRecord = _raise_exception
    with pytest.raises(Exception):
        logger.warning('foo')
    with pytest.raises(Exception):
        elicit_warning(temp_file_1_name)
