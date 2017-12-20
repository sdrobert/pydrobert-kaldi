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

"""Pytests for `pydrobert.kaldi.io.table_streams`"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import platform

import numpy as np
import pytest

from pydrobert.kaldi.io import open as io_open
from pydrobert.kaldi.io import table_streams
from pydrobert.kaldi.io.enums import KaldiDataType


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
    ('ivv', tuple()),
    ('ipv', ((1, 2), (3, 4))),
    ('ipv', tuple()),
    ('d', .1),
    ('d', 1),
    ('b', -.1),
    ('b', -10000),
    ('bpv', ((0, 1.3), (4.5, 6))),
    ('bpv', tuple()),
    ('B', True),
    ('B', False),
])
@pytest.mark.parametrize('is_text', [True, False])
@pytest.mark.parametrize('bg', [True, False])
def test_read_write(temp_file_1_name, dtype, value, is_text, bg):
    opts = ['', 't'] if is_text else ['']
    specifier = 'ark' + ','.join(opts) + ':' + temp_file_1_name
    writer = io_open(specifier, dtype, mode='w')
    writer.write('a', value)
    writer.close()
    if bg:
        opts += ['bg']
        specifier = 'ark' + ','.join(opts) + ':' + temp_file_1_name
    reader = io_open(specifier, dtype)
    once = True
    for read_value in iter(reader):
        assert once, "Multiple values"
        try:
            assert np.allclose(read_value, value)
        except TypeError:
            assert read_value == value
        once = False
    reader.close()


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
    with io_open('ark:' + temp_file_1_name, ktype, mode='w') as writer:
        writer.write('key', npy_value)
    with io_open('ark:' + temp_file_1_name, ktype) as reader:
        act_value = next(reader)
    if ktype in ('b', 'bpv'):
        assert np.allclose(value, act_value)
    else:
        assert value == act_value


def test_write_int32_correct_size(temp_file_1_name):
    with io_open('ark:' + temp_file_1_name, 'i', mode='w') as writer:
        writer.write('9', 182)
    # size should be 9
    # 2 bytes for '9 '
    # 2 byte for binary marker \0B
    # 1 byte for size of type in bytes (4)
    # 4 bytes for actual int
    with open(temp_file_1_name, 'rb') as file_obj:
        buf = file_obj.read()
    assert len(buf) == 9


def test_cache(temp_file_1_name):
    with io_open('ark:' + temp_file_1_name, 'B', mode='w') as writer:
        writer.write('a', True)
        writer.write('b', False)
    with io_open('ark:' + temp_file_1_name, 'B', mode='r+', cache=True) as r:
        assert r.cache_dict == dict()
        assert 'a' not in r.cache_dict
        assert 'a' in r
        assert r['a']
        assert r.cache_dict == {'a': True}
        assert 'a' in r.cache_dict
        assert 'b' not in r.cache_dict
        assert 'b' in r
        assert not r['b']
        assert r.cache_dict == {'a': True, 'b': False}
        r.cache_dict['b'] = True
        assert r['b']


def test_invalid_tv_does_not_segfault(temp_file_1_name):
    # weird bug I found
    tv = 'foo bar'
    writer = io_open('ark:' + temp_file_1_name, 'tv', mode='w')
    with pytest.raises(Exception):
        writer.write('foo', tv)
    with pytest.raises(Exception):
        writer.write('foo', np.array(tv))


@pytest.mark.parametrize('ktype,value', [
    ('fv', (0, 1, 2, 3, 4, 5)),
    ('dv', (0, 1, 2, 3, 4, 5)),
    ('dm', ((0, 1, 2), (3, 4, 5))),
    ('fm', ((0, 1, 2), (3, 4, 5))),
    ('wm', np.random.randint(-255, 255, size=(3, 10)).astype(np.int16)),
    ('t', 'hrnnngh'),
    ('tv', ('who', 'am', 'I')),
    ('i', -420),
    ('iv', (7, 8, 9)),
    ('ivv', ((0, 1), (2,))),
    ('ipv', ((-1, -10), (-5, 4))),
    ('d', .4),
    # the base floats can be cast to ints. It's important for the speed
    # of testing that certain floats are small/negative
    ('b', 1.401298464324817e-44),
    ('b', -1.401298464324817e-44),
    ('bpv', ((1.401298464324817e-44, 2.5), (3, 4.5))),
    ('bpv', ((-1.401298464324817e-44, 2.5), (3, 4.5))),
    ('B', True)
])
@pytest.mark.parametrize('is_text', [True, False])
@pytest.mark.parametrize('bg', [True, False])
def test_incorrect_open_read(
        temp_file_1_name, temp_file_2_name, ktype, value, is_text, bg):
    if ktype == 'wm' and is_text:
        pytest.skip("WaveMatrix can only be written as binary")
    opts = ['', 't'] if is_text else ['']
    specifier_1 = 'ark' + ','.join(opts) + ':' + temp_file_1_name
    specifier_2 = 'ark' + ','.join(opts) + ':' + temp_file_2_name
    with io_open(specifier_1, ktype, mode='w') as writer_1, io_open(
            specifier_2, ktype, mode='w') as writer_2:
        writer_1.write('0', value)
        writer_2.write('0', value)
    if bg:
        opts += ['bg']
        specifier_1 = 'ark' + ','.join(opts) + ':' + temp_file_1_name
        specifier_2 = 'ark' + ','.join(opts) + ':' + temp_file_2_name
    for bad_ktype in KaldiDataType:
        try:
            with io_open(specifier_1, bad_ktype) as reader:
                next(reader)
        except Exception:
            # sometimes it'll work, and the expected output will be
            # correct (in the case of basic types). We don't care. All
            # we care about here is that we don't segfault
            pass
    # now we add some garbage data to the end of the file and try to
    # iterate through. Chances are this will end in failure (hopefully
    # not a segfault)
    with open(temp_file_1_name, mode='ab') as writer:
        writer.write(np.random.bytes(1000))
    try:
        with io_open(specifier_1, ktype) as reader:
            list(reader)
    except Exception:
        pass
    # do the same, but only corrupt *after* the key
    with open(temp_file_2_name, mode='ab') as writer:
        writer.write(b'1 ' + np.random.bytes(1000))
    try:
        with io_open(specifier_2, ktype) as reader:
            list(reader)
    except Exception:
        pass


def test_invalid_scp(temp_file_1_name):
    # make sure invalid scp files don't segfault
    with open(temp_file_1_name, mode='wb') as writer:
        writer.write(np.random.bytes(1000))
    try:
        with io_open('scp:' + temp_file_1_name) as reader:
            next(reader)
    except Exception:
        pass
    with open(temp_file_1_name, mode='wb') as writer:
        writer.write(b'foo ' + np.random.bytes(1000))
    try:
        with io_open('scp:' + temp_file_1_name) as reader:
            next(reader)
    except Exception:
        pass


@pytest.mark.parametrize('dtype,value', [
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
    ('tv', 'foo bar'),
    ('i', 'zimble'),
    ('iv', 1),
    ('ivv', [[[1]]]),
    ('ipv', ((1, 2), (3,))),
    ('d', 1 + 1j),
    ('b', 'akljdal'),
    ('bpv', ((1,), (2, 3))),
])
@pytest.mark.parametrize('is_text', [True, False])
def test_write_invalid(temp_file_1_name, dtype, value, is_text):
    if is_text:
        specifier = 'ark,t:{}'.format(temp_file_1_name)
    else:
        specifier = 'ark:{}'.format(temp_file_1_name)
    writer = io_open(specifier, dtype, mode='w')
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
    writer = io_open('ark:{}'.format(temp_file_1_name), 'fm', mode='w')
    for key, value in enumerate(values):
        writer.write(str(key), value)
    writer.close()
    count = 0
    reader = io_open('ark:{}'.format(temp_file_1_name), 'fm')
    for act_value, reader_value in zip(values, iter(reader)):
        assert np.allclose(act_value, reader_value)
        count += 1
    assert count == len(values)
    reader.close()
    # check that the keys are all savvy
    reader = io_open('ark:{}'.format(temp_file_1_name), 'fm')
    for idx, tup in enumerate(reader.items()):
        key, value = tup
        assert str(idx) == key


def test_read_random(temp_file_1_name):
    writer = io_open('ark:{}'.format(temp_file_1_name), 'dv', mode='w')
    writer.write('able', [])
    writer.write('was', [2])
    writer.write('I', [3, 3])
    writer.write('ere', [4, 4])
    writer.close()
    reader = io_open(
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
    writer = io_open(
        'ark,scp:{},{}'.format(temp_file_1_name, temp_file_2_name),
        'dm', mode='w'
    )
    # to make a missing entry, append it to the file's end with a subproc
    for key in keys:
        writer.write(key, values[key])
    writer.close()
    keys.reverse()
    reader = io_open('scp:{}'.format(temp_file_2_name), 'dm', mode='r+')
    for key in keys:
        assert np.allclose(reader[key], values[key]), key
    assert np.allclose(reader['bar'], values['bar']), "Failed doublecheck"


@pytest.mark.skipif(platform.system() == 'Windows', reason='Not posix')
def test_read_write_pipe_posix(temp_file_1_name):
    value = np.ones((1000, 10000), dtype=np.float32)
    writer = io_open(
        'ark:| gzip -c > {}'.format(temp_file_1_name), 'fm', mode='w')
    writer.write('bar', value)
    writer.close()
    reader = io_open(
        'ark:gunzip -c {}|'.format(temp_file_1_name), 'fm', mode='r+')
    assert np.allclose(reader['bar'], value)


def test_context_open(temp_file_1_name):
    specifier = 'ark:{}'.format(temp_file_1_name)
    with io_open(specifier, 'bm', mode='w') as kaldi_io:
        assert isinstance(kaldi_io, table_streams.KaldiTable)
        assert isinstance(kaldi_io, table_streams.KaldiWriter)
    with io_open(specifier, 'bm') as kaldi_io:
        assert isinstance(kaldi_io, table_streams.KaldiSequentialReader)
    with io_open(specifier, 'bm', mode='r') as kaldi_io:
        assert isinstance(kaldi_io, table_streams.KaldiSequentialReader)
    with io_open(specifier, 'bm', mode='r+') as kaldi_io:
        assert isinstance(kaldi_io, table_streams.KaldiRandomAccessReader)


def test_filehandle_open(temp_file_1_name):
    specifier = 'ark:{}'.format(temp_file_1_name)
    kaldi_io = io_open(specifier, 'bm', mode='w')
    assert isinstance(kaldi_io, table_streams.KaldiTable)
    assert isinstance(kaldi_io, table_streams.KaldiWriter)
    kaldi_io = io_open(specifier, 'bm')
    assert isinstance(kaldi_io, table_streams.KaldiSequentialReader)
    kaldi_io = io_open(specifier, 'bm', mode='r')
    assert isinstance(kaldi_io, table_streams.KaldiSequentialReader)
    kaldi_io = io_open(specifier, 'bm', mode='r+')
    assert isinstance(kaldi_io, table_streams.KaldiRandomAccessReader)


def test_open_string_or_data_type(temp_file_1_name):
    specifier = 'ark:{}'.format(temp_file_1_name)
    io_open(specifier, 'bm', mode='w')
    io_open(specifier, table_streams.KaldiDataType.BaseMatrix, mode='w')
    io_open(specifier, 'bm', mode='r')
    io_open(specifier, table_streams.KaldiDataType.BaseMatrix, mode='r')
    io_open(specifier, 'bm', mode='r+')
    io_open(specifier, table_streams.KaldiDataType.BaseMatrix, mode='r+')


def test_invalid_data_type(temp_file_1_name):
    specifier = 'ark:{}'.format(temp_file_1_name)
    with pytest.raises(ValueError):
        io_open(specifier, 'foo', mode='w')


def test_no_exception_on_double_close(temp_file_1_name):
    specifier = 'ark:{}'.format(temp_file_1_name)
    kaldi_io = io_open(specifier, 'bm', mode='w')
    kaldi_io.close()
    kaldi_io.close()


def test_wave_read_write_valid(temp_file_1_name):
    specifier = 'ark:{}'.format(temp_file_1_name)
    writer = io_open(specifier, 'wm', mode='w')
    n_waves = 10
    keys = [str(i) for i in range(n_waves)]
    n_samples = [np.random.randint(1, 100000) for _ in keys]
    n_channels = [np.random.randint(1, 3) for _ in keys]
    # always written as pcm 16
    bufs = [
        (np.random.random((y, x)) * 30000 - 15000).astype(np.int16)
        for x, y in zip(n_samples, n_channels)
    ]
    for key, buf in zip(keys, bufs):
        writer.write(key, buf)
    writer.close()
    reader = io_open(specifier, 'wm', value_style='sbd')
    for vals, expected_buf in zip(reader, bufs):
        sample_rate, actual_buf, dur = vals
        assert int(sample_rate) == 16000
        assert isinstance(dur, float)
        assert np.allclose(actual_buf, expected_buf)
        n_waves -= 1
    assert not n_waves, "Incorrect number of reads!"
