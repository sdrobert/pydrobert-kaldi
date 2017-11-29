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

"""Pytests for `pydrobert.kaldi.logging`"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

import numpy as np
import pytest

from builtins import chr
from six.moves import StringIO

from pydrobert.kaldi import io
from pydrobert.kaldi._internal import VerboseLog as verbose_log
from pydrobert.kaldi.logging import KaldiLogger
from pydrobert.kaldi.logging import deregister_logger_for_kaldi
from pydrobert.kaldi.logging import register_logger_for_kaldi


@pytest.fixture
def kaldi_logger():
    logger_name = ''.join(chr(x + 97) for x in np.random.choice(26, 100))
    old_class = logging.getLoggerClass()
    logging.setLoggerClass(KaldiLogger)
    ret_logger = logging.getLogger(logger_name)
    logging.setLoggerClass(old_class)
    s_stream = StringIO()
    ret_logger.addHandler(logging.StreamHandler(s_stream))
    register_logger_for_kaldi(logger_name)
    yield ret_logger
    deregister_logger_for_kaldi(logger_name)
    for handler in ret_logger.handlers:
        ret_logger.removeHandler(handler)


@pytest.fixture
def registered_regular_logger():
    logger_name = ''.join(chr(x + 97) for x in np.random.choice(26, 100))
    ret_logger = logging.getLogger(logger_name)
    s_stream = StringIO()
    ret_logger.addHandler(logging.StreamHandler(s_stream))
    register_logger_for_kaldi(logger_name)
    yield ret_logger
    deregister_logger_for_kaldi(logger_name)
    ret_logger.removeHandler(s_stream)


def test_kaldi_logger_basic_write(kaldi_logger):
    kaldi_logger.setLevel(logging.WARNING)
    s_stream = kaldi_logger.handlers[-1].stream
    assert not s_stream.tell()
    test_string = "I'm a dude playing a dude disguised as another dude"
    kaldi_logger.warning(test_string)
    assert s_stream.tell()
    assert test_string + '\n' == s_stream.getvalue()
    kaldi_logger.info(test_string)
    assert test_string + '\n' == s_stream.getvalue()


def test_callback_delivers_correct_messages(
        kaldi_logger, registered_regular_logger):
    kaldi_logger.setLevel(logging.INFO)
    k_stream = kaldi_logger.handlers[-1].stream
    registered_regular_logger.setLevel(logging.WARNING)
    r_stream = registered_regular_logger.handlers[-1].stream
    verbose_log(-1, 'everyone gets this')
    verbose_log(0, 'not r_stream, here')
    verbose_log(1, 'noone gets this')
    assert 'everyone gets this\nnot r_stream, here\n' == k_stream.getvalue()
    assert 'everyone gets this\n' == r_stream.getvalue()


def test_do_not_callback_unregistered(kaldi_logger):
    kaldi_logger.setLevel(logging.WARNING)
    verbose_log(-1, 'should see this')
    deregister_logger_for_kaldi(kaldi_logger.name)
    verbose_log(-1, 'should not see this')
    register_logger_for_kaldi('bingobangobongo')
    verbose_log(-1, 'still nothing')
    register_logger_for_kaldi(kaldi_logger.name)
    verbose_log(-1, 'but see this')
    s_stream = kaldi_logger.handlers[-1].stream
    assert 'should see this\nbut see this\n' == s_stream.getvalue()


def elicit_warning(filename, threaded=False):
    # helper to elicit a natural warning from kaldi
    writer = io.open('ark,t:{}'.format(filename), 'bv', 'w')
    writer.write('zz', [np.infty])
    writer.close()
    reader = io.open(
        'ark,t{}:{}'.format(',bg' if threaded else '', filename), 'bv')
    next(reader)
    reader.close()


@pytest.mark.parametrize('threaded', [False])
def test_elicit_kaldi_warning(kaldi_logger, temp_file_1_name, threaded):
    s_stream = kaldi_logger.handlers[-1].stream
    assert not s_stream.tell()
    elicit_warning(temp_file_1_name, threaded)
    assert s_stream.tell()
    assert 'Reading infinite value into vector.\n' == s_stream.getvalue()


def test_log_source_is_appropriate(kaldi_logger, temp_file_1_name):
    handler = kaldi_logger.handlers[-1]
    s_stream = handler.stream
    handler.setFormatter(logging.Formatter('%(filename)s: %(message)s'))
    assert not s_stream.tell()
    kaldi_logger.warning('pokeymans')
    assert 'test_logging.py' in s_stream.getvalue()
    assert 'kaldi-vector.cc' not in s_stream.getvalue()
    s_stream.seek(0)
    elicit_warning(temp_file_1_name)
    assert 'kaldi-vector.cc' in s_stream.getvalue()
    assert '__init__.py' not in s_stream.getvalue()


def test_python_error_doesnt_segfault(
        registered_regular_logger, temp_file_1_name):
    def _raise_exception(*args, **kwargs):
        raise Exception()
    registered_regular_logger.makeRecord = _raise_exception
    with pytest.raises(Exception):
        registered_regular_logger.warning('foo')
    with pytest.raises(Exception):
        elicit_warning(temp_file_1_name)
