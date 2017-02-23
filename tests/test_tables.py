"""Nosetests for `pydrobert.kaldi.tables`"""

from __future__ import division
from __future__ import print_function

import os
import platform
import wave

from itertools import product
from tempfile import NamedTemporaryFile

import numpy

from nose.plugins.skip import SkipTest
from pydrobert.kaldi import tables

class TestTables:

    @classmethod
    def setup_class(cls):
        cls._windows = platform.system() == 'Windows'

    def setup(self):
        temp = NamedTemporaryFile(delete=False)
        temp.close()
        self._temp_name_1 = temp.name
        temp = NamedTemporaryFile(delete=False)
        temp.close()
        self._temp_name_2 = temp.name

    def teardown(self):
        os.remove(self._temp_name_1)
        os.remove(self._temp_name_2)

    def test_read_write_data_types(self):
        valid_pairs = (
            ('bv', []),
            ('bm', [[]]),
            ('bv', [numpy.infty]),
            ('bv', [1] * 100),
            ('bm', [[1, 2], [3, 4]]),
            ('fv', [-1, -1, 0, .1]),
            ('fm', numpy.random.random((10, 10)).astype(numpy.float32)),
            ('dv', numpy.arange(1000, dtype=numpy.float64) - 10),
            ('dm', numpy.outer(
                numpy.arange(100, dtype=numpy.float32),
                numpy.arange(111, dtype=numpy.float32))), # upcast ok
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
        )
        for is_text, valid_pair in product((True, False), valid_pairs):
            dbg_text = ' (Text={}, Pair={})'.format(is_text, valid_pair)
            dtype, value = valid_pair
            try:
                xfilename = None
                if is_text:
                    xfilename = 'ark,t:{}'.format(self._temp_name_1)
                else:
                    xfilename = 'ark:{}'.format(self._temp_name_1)
                writer = tables.open(xfilename, dtype, mode='w')
                writer.write('a', value)
                writer.close()
                reader = tables.open(xfilename, dtype)
                once = True
                for read_value in iter(reader):
                    assert once, "Multiple values"
                    if dtype in ('bv', 'bm', 'fv', 'fm', 'dv', 'dm'):
                        assert numpy.allclose(read_value, value), \
                            "Values not equal: {} {}".format(read_value, value)
                    else:
                        assert read_value == value, \
                            "Values not equal: {} {}".format(read_value, value)
                    once = False
                reader.close()
            except Exception as exc:
                exc.args = tuple([exc.args[0] + dbg_text] + list(exc.args[1:]))
                raise

    def test_write_invalid(self):
        invalid_pairs = (
            ('bv', ['a', 2, 3]),
            ('bv', 'abc'),
            ('bv', [[1, 2]]),
            ('fv', numpy.arange(3, dtype=numpy.float64)), # downcast not ok
            ('bm', [['a', 2]]),
            ('bm', [0]),
            ('fm', numpy.random.random((10, 1)).astype(numpy.float64)),
            ('t', 1),
            ('t', []),
            ('t', 'was I'),
            ('tv', ['a', 1]),
            ('tv', ("it's", 'me DIO')),
            ('tv', 'foobar'),
        )
        for is_text, invalid_pair in product((True, False), invalid_pairs):
            dtype, value = invalid_pair
            dbg_text = ' (Text={}, Pair={})'.format(is_text, invalid_pair)
            try:
                xfilename = None
                if is_text:
                    xfilename = 'ark,t:{}'.format(self._temp_name_1)
                else:
                    xfilename = 'ark:{}'.format(self._temp_name_1)
                writer = tables.open(xfilename, dtype, mode='w')
                try:
                    writer.write('a', value)
                    # will not get here if all is well
                    writer.close()
                    print('Invalid archive contents:')
                    with open(self._temp_name_1) as fobj:
                        for line in fobj:
                            print(line)
                    raise AssertionError('Could write value')
                except (TypeError, ValueError):
                    pass
            except Exception as exc:
                exc.args = tuple([exc.args[0] + dbg_text] + list(exc.args[1:]))
                raise

    def test_read_sequential(self):
        values = (
            [[1, 2] * 10] * 10,
            numpy.eye(1000, dtype=numpy.float32),
            [[]],
            numpy.outer(
                numpy.arange(1000, dtype=numpy.float32),
                numpy.arange(1000, dtype=numpy.float32)),
        )
        writer = tables.open('ark:{}'.format(self._temp_name_1), 'fm', mode='w')
        for key, value in enumerate(values):
            writer.write(str(key), value)
        # shouldn't need to close: writer should flush after each
        # we confound "once" and "background" testing here, but I assume
        # these are working in Kaldi and shouldn't be visible here
        reader = tables.open('ark,bg:{}'.format(self._temp_name_1), 'fm')
        for act_value, reader_value in zip(values, iter(reader)):
            assert numpy.allclose(act_value, reader_value)
        # check that the keys are all savvy
        reader.close()
        reader = tables.open('ark:' + self._temp_name_1, 'fm')
        for idx, tup in enumerate(reader.items()):
            key, value = tup
            assert str(idx) == key

    def test_read_random(self):
        writer = tables.open('ark:{}'.format(self._temp_name_1), 'dv', mode='w')
        writer.write('able', [])
        writer.write('was', [2])
        writer.write('I', [3, 3])
        writer.write('ere', [4, 4])
        writer.close()
        reader = tables.open(
            'ark,o:{}'.format(self._temp_name_1), 'dv', mode='r+')
        assert numpy.allclose(reader['I'], [3, 3])
        assert numpy.allclose(reader['able'], [])
        assert numpy.allclose(reader['was'], [2])

    def test_write_script_and_archive(self):
        values = {
            'foo': numpy.ones((21, 32), dtype=numpy.float64),
            'bar': numpy.zeros((10, 1000), dtype=numpy.float64),
            'baz': -1e10 * numpy.eye(20, dtype=numpy.float64),
        }
        keys = list(values)
        writer = tables.open(
            'ark,scp:{},{}'.format(self._temp_name_1, self._temp_name_2),
            'dm', mode='w'
        )
        # to make a missing entry, append it to the file's end with a subproc
        for key in keys:
            writer.write(key, values[key])
        writer.close()
        keys.reverse()
        reader = tables.open(
            'scp:{}'.format(self._temp_name_2), 'dm', mode='r+')
        for key in keys:
            assert numpy.allclose(reader[key], values[key]), key
        assert numpy.allclose(reader['bar'], values['bar']), "Failed doublechk"

    def test_read_write_pipe_unix(self):
        if self._windows:
            raise SkipTest
        value = numpy.ones((1000,10000), dtype=numpy.float32)
        writer = tables.open(
            'ark:| gzip -c > {}'.format(self._temp_name_1), 'fm', mode='w')
        writer.write('bar', value)
        writer.close()
        reader = tables.open(
            'ark:gunzip -c {}|'.format(self._temp_name_1), 'fm', mode='r+')
        assert numpy.allclose(reader['bar'], value)

    def test_context_open(self):
        xfilename = 'ark:{}'.format(self._temp_name_1)
        with tables.open(xfilename, 'bm', mode='w') as kaldi_io:
            assert isinstance(kaldi_io, tables.KaldiTable)
            assert isinstance(kaldi_io, tables.KaldiWriter)
        with tables.open(xfilename, 'bm') as kaldi_io:
            assert isinstance(kaldi_io, tables.KaldiSequentialReader)
        with tables.open(xfilename, 'bm', mode='r') as kaldi_io:
            assert isinstance(kaldi_io, tables.KaldiSequentialReader)
        with tables.open(xfilename, 'bm', mode='r+') as kaldi_io:
            assert isinstance(kaldi_io, tables.KaldiRandomAccessReader)

    def test_filehandle_open(self):
        xfilename = 'ark:{}'.format(self._temp_name_1)
        kaldi_io = tables.open(xfilename, 'bm', mode='w')
        assert isinstance(kaldi_io, tables.KaldiTable)
        assert isinstance(kaldi_io, tables.KaldiWriter)
        kaldi_io = tables.open(xfilename, 'bm')
        assert isinstance(kaldi_io, tables.KaldiSequentialReader)
        kaldi_io = tables.open(xfilename, 'bm', mode='r')
        assert isinstance(kaldi_io, tables.KaldiSequentialReader)
        kaldi_io = tables.open(xfilename, 'bm', mode='r+')
        assert isinstance(kaldi_io, tables.KaldiRandomAccessReader)

    def test_open_string_or_data_type(self):
        xfilename = 'ark:{}'.format(self._temp_name_1)
        tables.open(xfilename, 'bm', mode='w')
        tables.open(xfilename, tables.KaldiDataType.BaseMatrix, mode='w')
        tables.open(xfilename, 'bm', mode='r')
        tables.open(xfilename, tables.KaldiDataType.BaseMatrix, mode='r')
        tables.open(xfilename, 'bm', mode='r+')
        tables.open(xfilename, tables.KaldiDataType.BaseMatrix, mode='r+')

    def test_invalid_data_type(self):
        xfilename = 'ark:{}'.format(self._temp_name_1)
        try:
            tables.open(xfilename, 'foo', mode='w')
            assert False, "Could open with invalid data type"
        except ValueError:
            pass

    def test_no_exception_on_double_close(self):
        xfilename = 'ark:{}'.format(self._temp_name_1)
        kaldi_io = tables.open(xfilename, 'bm', mode='w')
        kaldi_io.close()
        kaldi_io.close()

    def test_wave_read_write_valid(self):
        xfilename = 'ark:{}'.format(self._temp_name_1)
        writer = tables.open(xfilename, 'wm', mode='w')
        n_waves = 10
        keys = [str(i) for i in range(n_waves)]
        n_samples = [numpy.random.randint(1, 100000) for _ in keys]
        n_channels = [numpy.random.randint(1, 3) for _ in keys]
        # always written as pcm 16
        bufs = [
            (numpy.random.random((y, x))  * 30000 - 15000).astype(numpy.int16)
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
            assert numpy.allclose(actual_buf, expected_buf)
            n_waves -= 1
        assert not n_waves, "Incorrect number of reads!"
