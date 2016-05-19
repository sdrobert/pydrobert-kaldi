"""Nosetests for `pydrobert.kaldi.tables`"""

from __future__ import division
from __future__ import print_function

import os
import platform

from itertools import product
from tempfile import NamedTemporaryFile

import numpy

from nose.plugins.skip import SkipTest

import pydrobert.kaldi.tables as tables

class TestTables:

    @classmethod
    def setup_class(cls):
        cls._wrapped_map = {
            'bm': lambda: arrays.KaldiMatrix(),
            'bv': lambda: arrays.KaldiVector(),
            'dm': lambda: arrays.KaldiMatrix(dtype=numpy.float64),
            'dv': lambda: arrays.KaldiVector(dtype=numpy.float64),
            'fm': lambda: arrays.KaldiMatrix(dtype=numpy.float32),
            'fv': lambda: arrays.KaldiVector(dtype=numpy.float32),
        }
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
        writer = tables.KaldiTableWriter()
        reader = tables.KaldiSequentialTableReader()
        valid_pairs = (
            ('bv', []),
            ('bm', []),
            ('bv', [numpy.infty]),
            ('bv', [1] * 100),
            ('bm', [[1, 2], [3, 4]]),
            ('dv', numpy.arange(1000, dtype=numpy.float64)),
            ('dm', numpy.outer(
                numpy.arange(100, dtype=numpy.float64),
                numpy.arange(111, dtype=numpy.float64))),
        )
        for is_text, valid_pair in product((True, False), valid_pairs):
            dbg_text = ' (Text={}, Pair={})'.format(
                is_text, valid_pair)
            try:
                dtype, value = valid_pair
                if is_text:
                    writer.open('ark,t:{}'.format(self._temp_name_1), dtype)
                else:
                    writer.open('ark:{}'.format(self._temp_name_1), dtype)
                writer.write('a', value)
                writer.close()
                if is_text:
                    reader.open('ark,t:{}'.format(self._temp_name_1), dtype)
                else:
                    reader.open('ark:{}'.format(self._temp_name_1), dtype)
                once = True
                for read_value in iter(reader):
                    assert once, "Multiple values" + dbg_text
                    assert numpy.allclose(read_value, value), \
                            "Values not equal" + dbg_text
                    once = False
            except Exception as exc:
                exc.args = tuple([exc.args[0] + dbg_text] + list(exc.args[1:]))
                raise

    def test_read_sequential(self):
        writer = tables.KaldiTableWriter()
        reader = tables.KaldiSequentialTableReader()
        values = (
            [[1, 2] * 10] * 10,
            numpy.eye(1000, dtype=numpy.float32),
            [],
            numpy.outer(
                numpy.arange(1000, dtype=numpy.float32),
                numpy.arange(1000, dtype=numpy.float32)),
        )
        writer.open('ark:{}'.format(self._temp_name_1), 'fm')
        for value in values:
            writer.write('foo', value)
        # shouldn't need to close: writer should flush after each
        # we confound "once" and "background" testing here, but I assume
        # these are working in Kaldi and shouldn't be visible here
        reader.open('ark,bg:{}'.format(self._temp_name_1), 'fm')
        for act_value, reader_value in zip(values, iter(reader)):
            assert numpy.allclose(act_value, reader_value)

    def test_read_random(self):
        writer = tables.KaldiTableWriter()
        reader = tables.KaldiRandomAccessTableReader()
        writer.open('ark:{}'.format(self._temp_name_1), 'dv')
        writer.write('able', [])
        writer.write('was', [2])
        writer.write('I', [3, 3])
        writer.write('ere', [4, 4])
        writer.close()
        reader.open('ark,o:{}'.format(self._temp_name_1), 'dv')
        assert numpy.allclose(reader['I'], [3, 3])
        assert numpy.allclose(reader['able'], [])
        assert numpy.allclose(reader['was'], [2])

    def test_write_script_and_archive(self):
        writer = tables.KaldiTableWriter()
        reader = tables.KaldiRandomAccessTableReader()
        values = {
            'foo': numpy.ones((21, 32), dtype=numpy.float64),
            'bar': numpy.zeros((10, 1000), dtype=numpy.float64),
            'baz': -1e10 * numpy.eye(20, dtype=numpy.float64),
        }
        keys = list(values)
        writer.open(
            'ark,scp:{},{}'.format(self._temp_name_1, self._temp_name_2), 'dm')
        # to make a missing entry, append it to the file's end with a subproc
        for key in keys:
            writer.write(key, values[key])
        writer.close()
        keys.reverse()
        reader.open('scp:{}'.format(self._temp_name_2), 'dm')
        for key in keys:
            assert numpy.allclose(reader[key], values[key]), key
        assert numpy.allclose(reader['bar'], values['bar']), "Failed doublechk"

    def test_read_write_pipe_unix(self):
        if self._windows:
            raise SkipTest
        writer = tables.KaldiTableWriter()
        reader = tables.KaldiRandomAccessTableReader()
        value = numpy.ones((1000,10000), dtype=numpy.float32)
        writer.open('ark:| gzip -c > {}'.format(self._temp_name_1), 'fm')
        writer.write('bar', value)
        writer.close()
        reader.open('ark:gunzip -c {}|'.format(self._temp_name_1), 'fm')
        assert numpy.allclose(reader['bar'], value)

    def test_context_open(self):
        xfilename = 'ark:{}'.format(self._temp_name_1)
        with tables.open(xfilename, 'bm', mode='w') as kaldi_io:
            assert isinstance(kaldi_io, tables.KaldiIO)
            assert isinstance(kaldi_io, tables.KaldiTableWriter)
        with tables.open(xfilename, 'bm') as kaldi_io:
            assert isinstance(kaldi_io, tables.KaldiSequentialTableReader)
        with tables.open(xfilename, 'bm', mode='r') as kaldi_io:
            assert isinstance(kaldi_io, tables.KaldiSequentialTableReader)
        with tables.open(xfilename, 'bm', mode='r+') as kaldi_io:
            assert isinstance(kaldi_io, tables.KaldiRandomAccessTableReader)
