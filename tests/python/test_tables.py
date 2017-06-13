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

"""Pytests for `pydrobert.kaldi.tables`"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import platform
import wave

from tempfile import NamedTemporaryFile

import numpy as np
import pytest

from pydrobert.kaldi import tables

@pytest.fixture
def temp_file_1_name():
    temp = NamedTemporaryFile(delete=False)
    temp.close()
    yield temp.name
    os.remove(temp.name)

@pytest.fixture
def temp_file_2_name():
    temp = NamedTemporaryFile(delete=False)
    temp.close()
    yield temp.name
    os.remove(temp.name)

@pytest.mark.parametrize('dtype,value', [
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
        np.arange(111, dtype=np.float32))), # upcast ok
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
])
@pytest.mark.parametrize('is_text', [True, False])
def test_read_write(temp_file_1_name, dtype, value, is_text):
    xfilename = None
    if is_text:
        xfilename = 'ark,t:{}'.format(temp_file_1_name)
    else:
        xfilename = 'ark:{}'.format(temp_file_1_name)
    writer = tables.open(xfilename, dtype, mode='w')
    writer.write('a', value)
    writer.close()
    reader = tables.open(xfilename, dtype)
    once = True
    for read_value in iter(reader):
        assert once, "Multiple values"
        if dtype in ('bv', 'bm', 'fv', 'fm', 'dv', 'dm'):
            assert np.allclose(read_value, value)
        else:
            assert read_value == value
        once = False
    reader.close()

@pytest.mark.parametrize('dtype,value', [
    ('bv', ['a', 2, 3]),
    ('bv', 'abc'),
    ('bv', [[1, 2]]),
    ('fv', np.arange(3, dtype=np.float64)), # downcast not ok
    ('bm', [['a', 2]]),
    ('bm', [0]),
    ('fm', np.random.random((10, 1)).astype(np.float64)),
    ('t', 1),
    ('t', []),
    ('t', 'was I'),
    ('tv', ['a', 1]),
    ('tv', ("it's", 'me DIO')),
    ('tv', 'foobar'),
])
@pytest.mark.parametrize('is_text', [True, False])
def test_read_write_invalid(temp_file_1_name, dtype, value, is_text):
    xfilename = None
    if is_text:
        xfilename = 'ark,t:{}'.format(temp_file_1_name)
    else:
        xfilename = 'ark:{}'.format(temp_file_1_name)
    writer = tables.open(xfilename, dtype, mode='w')
    with pytest.raises(Exception):
        writer.write('a', value)

def test_read_sequential(temp_file_1_name):
    values = (
        [[1, 2] * 10] * 10,
        np.eye(1000, dtype=np.float32),
        [[]],
        np.outer(
            np.arange(1000, dtype=np.float32),
            np.arange(1000, dtype=np.float32)),
    )
    writer = tables.open('ark:{}'.format(temp_file_1_name), 'fm', mode='w')
    for key, value in enumerate(values):
        writer.write(str(key), value)
    writer.close()
    # shouldn't need to close: writer should flush after each
    # we confound "once" and "background" testing here, but I assume
    # these are working in Kaldi and shouldn't be visible here
    count = 0
    reader = tables.open('ark,bg:{}'.format(temp_file_1_name), 'fm')
    for act_value, reader_value in zip(values, iter(reader)):
        assert np.allclose(act_value, reader_value)
        count += 1
    assert count == len(values)
    reader.close()
    # check that the keys are all savvy
    reader = tables.open('ark:{}'.format(temp_file_1_name), 'fm')
    for idx, tup in enumerate(reader.items()):
        key, value = tup
        assert str(idx) == key

def test_read_random(temp_file_1_name):
    writer = tables.open('ark:{}'.format(temp_file_1_name), 'dv', mode='w')
    writer.write('able', [])
    writer.write('was', [2])
    writer.write('I', [3, 3])
    writer.write('ere', [4, 4])
    writer.close()
    reader = tables.open(
        'ark,o:{}'.format(temp_file_1_name), 'dv', mode='r+')
    assert np.allclose(reader['I'], [3, 3])
    assert np.allclose(reader['able'], [])
    assert np.allclose(reader['was'], [2])

def test_write_script_and_archive(temp_file_1_name, temp_file_2_name):
    values = {
        'foo': np.ones((21, 32), dtype=np.float64),
        'bar': np.zeros((10, 1000), dtype=np.float64),
        'baz': -1e10 * np.eye(20, dtype=np.float64),
    }
    keys = list(values)
    writer = tables.open(
        'ark,scp:{},{}'.format(temp_file_1_name, temp_file_2_name),
        'dm', mode='w'
    )
    # to make a missing entry, append it to the file's end with a subproc
    for key in keys:
        writer.write(key, values[key])
    writer.close()
    keys.reverse()
    reader = tables.open('scp:{}'.format(temp_file_2_name), 'dm', mode='r+')
    for key in keys:
        assert np.allclose(reader[key], values[key]), key
    assert np.allclose(reader['bar'], values['bar']), "Failed doublecheck"

@pytest.mark.skipif(platform.system() == 'Windows', reason='Not posix')
def test_read_write_pipe_posix(temp_file_1_name):
    value = np.ones((1000,10000), dtype=np.float32)
    writer = tables.open(
        'ark:| gzip -c > {}'.format(temp_file_1_name), 'fm', mode='w')
    writer.write('bar', value)
    writer.close()
    reader = tables.open(
        'ark:gunzip -c {}|'.format(temp_file_1_name), 'fm', mode='r+')
    assert np.allclose(reader['bar'], value)

def test_context_open(temp_file_1_name):
    xfilename = 'ark:{}'.format(temp_file_1_name)
    with tables.open(xfilename, 'bm', mode='w') as kaldi_io:
        assert isinstance(kaldi_io, tables.KaldiTable)
        assert isinstance(kaldi_io, tables.KaldiWriter)
    with tables.open(xfilename, 'bm') as kaldi_io:
        assert isinstance(kaldi_io, tables.KaldiSequentialReader)
    with tables.open(xfilename, 'bm', mode='r') as kaldi_io:
        assert isinstance(kaldi_io, tables.KaldiSequentialReader)
    with tables.open(xfilename, 'bm', mode='r+') as kaldi_io:
        assert isinstance(kaldi_io, tables.KaldiRandomAccessReader)

def test_filehandle_open(temp_file_1_name):
    xfilename = 'ark:{}'.format(temp_file_1_name)
    kaldi_io = tables.open(xfilename, 'bm', mode='w')
    assert isinstance(kaldi_io, tables.KaldiTable)
    assert isinstance(kaldi_io, tables.KaldiWriter)
    kaldi_io = tables.open(xfilename, 'bm')
    assert isinstance(kaldi_io, tables.KaldiSequentialReader)
    kaldi_io = tables.open(xfilename, 'bm', mode='r')
    assert isinstance(kaldi_io, tables.KaldiSequentialReader)
    kaldi_io = tables.open(xfilename, 'bm', mode='r+')
    assert isinstance(kaldi_io, tables.KaldiRandomAccessReader)

def test_open_string_or_data_type(temp_file_1_name):
    xfilename = 'ark:{}'.format(temp_file_1_name)
    tables.open(xfilename, 'bm', mode='w')
    tables.open(xfilename, tables.KaldiDataType.BaseMatrix, mode='w')
    tables.open(xfilename, 'bm', mode='r')
    tables.open(xfilename, tables.KaldiDataType.BaseMatrix, mode='r')
    tables.open(xfilename, 'bm', mode='r+')
    tables.open(xfilename, tables.KaldiDataType.BaseMatrix, mode='r+')

def test_invalid_data_type(temp_file_1_name):
    xfilename = 'ark:{}'.format(temp_file_1_name)
    with pytest.raises(ValueError):
        tables.open(xfilename, 'foo', mode='w')

def test_no_exception_on_double_close(temp_file_1_name):
    xfilename = 'ark:{}'.format(temp_file_1_name)
    kaldi_io = tables.open(xfilename, 'bm', mode='w')
    kaldi_io.close()
    kaldi_io.close()

def test_wave_read_write_valid(temp_file_1_name):
    xfilename = 'ark:{}'.format(temp_file_1_name)
    writer = tables.open(xfilename, 'wm', mode='w')
    n_waves = 10
    keys = [str(i) for i in range(n_waves)]
    n_samples = [np.random.randint(1, 100000) for _ in keys]
    n_channels = [np.random.randint(1, 3) for _ in keys]
    # always written as pcm 16
    bufs = [
        (np.random.random((y, x))  * 30000 - 15000).astype(np.int16)
        for x, y in zip(n_samples, n_channels)
    ]
    for key, buf in zip(keys, bufs):
        writer.write(key, buf)
    writer.close()
    reader = tables.open(xfilename, 'wm', value_style='sbd')
    for vals, expected_buf in zip(reader, bufs):
        sample_rate, actual_buf, dur = vals
        assert int(sample_rate) == 16000
        assert isinstance(dur, float)
        assert np.allclose(actual_buf, expected_buf)
        n_waves -= 1
    assert not n_waves, "Incorrect number of reads!"