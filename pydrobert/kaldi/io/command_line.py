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

'''Command line hooks for I/O-related activities'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys
import os

import numpy as np
import pydrobert.kaldi.io.enums as enums

from pydrobert.kaldi.io import open as kaldi_open
from pydrobert.kaldi.io.argparse import KaldiParser
from pydrobert.kaldi.logging import kaldi_logger_decorator
from pydrobert.kaldi.logging import kaldi_vlog_level_cmd_decorator
from pydrobert.kaldi.logging import register_logger_for_kaldi
from six.moves import cPickle as pickle

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2018 Sean Robertson"

__all__ = [
    'write_pickle_to_table',
    'write_table_to_pickle',
    'write_table_to_torch_dir',
    'write_torch_dir_to_table',
]


def _write_table_to_pickle_parse_args(args, logger):
    '''Parse args for write_table_to_pickle'''
    parser = KaldiParser(
        description=write_table_to_pickle.__doc__,
        add_verbose=True, logger=logger)
    parser.add_argument(
        'rspecifier', type='kaldi_rspecifier', help='The table to read')
    parser.add_argument(
        'value_out',
        help='A path to write (key,value) pairs to, or just values if key_out '
        'was set. If it ends in ".gz", the file will be gzipped')
    parser.add_argument(
        'key_out', nargs='?', default=None,
        help='A path to write keys to. If it ends in ".gz", the file will be '
        'gzipped')
    parser.add_argument(
        '-i', '--in-type', type='kaldi_dtype', default='bm',
        help='The type of kaldi data type to read. Defaults to base matrix')
    parser.add_argument(
        '-o', '--out-type', type='numpy_dtype',
        default=None,
        help='The numpy data type to cast values to. The default is dependent '
        'on the input type. String types will be written as (tuples of) '
        'strings')
    options = parser.parse_args(args)
    return options


@kaldi_vlog_level_cmd_decorator
@kaldi_logger_decorator
def write_table_to_pickle(args=None):
    '''Write a kaldi table to pickle file(s)

    The inverse is write-pickle-to-table
    '''
    logger = logging.getLogger(sys.argv[0])
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    register_logger_for_kaldi(logger)
    try:
        options = _write_table_to_pickle_parse_args(args, logger)
    except SystemExit as ex:
        return ex.code
    out_type = options.out_type
    if out_type is None:
        if options.in_type.is_floating_point:
            if options.in_type.is_double:
                out_type = np.float64
            else:
                out_type = np.float32
        else:
            out_type = np.str
    from six.moves import cPickle as pickle
    try:
        reader = kaldi_open(options.rspecifier, options.in_type, 'r')
        if options.value_out.endswith('.gz'):
            import gzip
            value_out = gzip.open(options.value_out, 'wb')
        else:
            value_out = open(options.value_out, 'wb')
        if options.key_out:
            if options.key_out.endswith('.gz'):
                import gzip
                key_out = gzip.open(options.key_out, 'wt')
            else:
                key_out = open(options.key_out, 'w')
        else:
            key_out = None
    except IOError as error:
        logger.error(error.message, exc_info=True)
        return 1
    num_entries = 0
    try:
        for key, value in reader.items():
            num_entries += 1
            if not np.issubdtype(out_type, np.dtype(str).type):
                value = value.astype(out_type)
            if key_out:
                pickle.dump(value, value_out)
                pickle.dump(key, key_out)
            else:
                pickle.dump((key, value), value_out)
            if num_entries % 10 == 0:
                logger.info('Processed {} entries'.format(num_entries))
            logger.debug('Processed key {}'.format(key))
    except (IOError, ValueError) as error:
        logger.error(error.message, exc_info=True)
        return 1
    finally:
        value_out.close()
        if key_out:
            key_out.close()
    if num_entries == 0:
        logger.warning("No entries were written (table was empty)")
    else:
        logger.info("Wrote {} entries".format(num_entries))
    return 0


def _write_pickle_to_table_parse_args(args, logger):
    '''Parse args for write_pickle_to_table'''
    parser = KaldiParser(
        description=write_pickle_to_table.__doc__,
        add_verbose=True, logger=logger)
    parser.add_argument(
        'value_in',
        help='A path to read (key,value) pairs from, or just values if key_in '
        'was set. If it ends in ".gz", the file is assumed to be gzipped')
    parser.add_argument(
        'key_in', nargs='?', default=None,
        help='A path to read keys from. If it ends in ".gz", the file is '
        'assumed to be gzipped')
    parser.add_argument(
        'wspecifier', type='kaldi_wspecifier', help='The table to write to')
    parser.add_argument(
        '-o', '--out-type', type='kaldi_dtype', default='bm',
        help='The type of kaldi data type to read. Defaults to base matrix')
    options = parser.parse_args(args)
    return options


def _write_pickle_to_table_empty(wspecifier, logger):
    '''Special case when pickle file(s) was/were empty'''
    # doesn't matter what type we choose; we're not writing anything
    try:
        kaldi_open(wspecifier, 'bm', 'w')
    except IOError as error:
        logger.error(error.message, exc_info=True)
        return 1
    logger.warning('No entries were written (pickle file(s) was/were empty)')
    return 0


def _write_pickle_to_table_value_only(options, logger):
    '''write_pickle_to_table when only value_in has been specified'''
    from six.moves import cPickle as pickle
    try:
        if options.value_in.endswith('.gz'):
            import gzip
            value_in = gzip.open(options.value_in, 'rb')
        else:
            value_in = open(options.value_in, 'rb')
    except IOError as error:
        logger.error(error.message, exc_info=True)
        return 1
    try:
        key, value = pickle.load(value_in)
    except pickle.UnpicklingError as error:
        logger.error(error.message, exc_info=True)
        return 1
    except EOFError:
        value_in.close()
        return _write_pickle_to_table_empty(options.wspecifier, logger)
    out_type = options.out_type
    try:
        writer = kaldi_open(options.wspecifier, out_type, 'w')
    except IOError as error:
        value_in.close()
        logger.error(error.message, exc_info=True)
        return 1
    num_entries = 0
    try:
        while True:
            if out_type.is_floating_point:
                if out_type.is_double:
                    try:
                        value = value.astype(np.float64, copy=False)
                    except AttributeError:
                        pass
                else:
                    try:
                        value = value.astype(np.float32, copy=False)
                    except AttributeError:
                        pass
            writer.write(key, value)
            num_entries += 1
            if num_entries % 10 == 0:
                logger.info('Processed {} entries'.format(num_entries))
            logger.debug('Processed key {}'.format(key))
            key, value = pickle.load(value_in)
    except EOFError:
        pass
    except (IOError, ValueError, TypeError, pickle.UnpicklingError) as error:
        if hasattr(error, 'message'):
            logger.error(error.message, exc_info=True)
        else:
            logger.error('error', exc_info=True)
        return 1
    finally:
        value_in.close()
    logger.info("Wrote {} entries".format(num_entries))
    return 0


def _write_pickle_to_table_key_value(options, logger):
    try:
        logger.info('Opening {}'.format(options.value_in))
        if options.value_in.endswith('.gz'):
            import gzip
            value_in = gzip.open(options.value_in, 'rb')
        else:
            value_in = open(options.value_in, 'rb')
        logger.info('Opening {}'.format(options.key_in))
        if options.key_in.endswith('.gz'):
            import gzip
            key_in = gzip.open(options.key_in, 'rt')
        else:
            key_in = open(options.key_in, 'r')
    except IOError as error:
        logger.error(error.message, exc_info=True)
        return 1
    try:
        value = pickle.load(value_in)
    except pickle.UnpicklingError as error:
        value_in.close()
        key_in.close()
        logger.error(error.message, exc_info=True)
        return 1
    except EOFError:
        value_in.close()
        try:
            pickle.load(key_in)
            logger.error('Number of keys (1) and values (0) do not match')
            return 1
        except pickle.UnpicklingError as error:
            key_in.close()
            logger.error(error.message, exc_info=True)
            return 1
        key_in.close()
        return _write_pickle_to_table_empty(options.wspecifier, logger)
    try:
        key = pickle.load(key_in)
    except EOFError:
        value_in.close()
        key_in.close()
        logger.error('Number of keys (0) and values (1) do not match')
        return 1
    except pickle.UnpicklingError as error:
        value_in.close()
        key_in.close()
        logger.error(error.message, exc_info=True)
        return 1
    out_type = options.out_type
    try:
        logging.info('Opening {}'.format(options.wspecifier))
        writer = kaldi_open(options.wspecifier, out_type, 'w')
    except IOError as error:
        value_in.close()
        key_in.close()
        logger.error(error.message, exc_info=True)
        return 1
    num_entries = 0
    try:
        while True:
            if out_type.is_floating_point:
                if out_type.is_double:
                    try:
                        value = value.astype(np.float64, copy=False)
                    except AttributeError:
                        pass  # will happen implicitly
                else:
                    try:
                        value = value.astype(np.float32, copy=False)
                    except AttributeError:
                        pass  # will happen implicitly
            writer.write(key, value)
            num_entries += 1
            if num_entries % 10 == 0:
                logger.info('Processed {} entries'.format(num_entries))
            logger.debug('Processed key {}'.format(key))
            key = pickle.load(key_in)
            value = pickle.load(value_in)
    except EOFError:
        pass
    except (IOError, ValueError, TypeError, pickle.UnpicklingError) as error:
        logger.error(error.message, exc_info=True)
        return 1
    try:
        pickle.load(value_in)
        value_in.close()
        key_in.close()
        logger.error(
            'Number of keys ({}) and values ({}) do not match'.format(
                num_entries, num_entries + 1))
        return 1
    except EOFError:
        pass
    except (IOError, pickle.UnpicklingError) as error:
        value_in.close()
        key_in.close()
        logger.error(error.message, exc_info=True)
        return 1
    try:
        pickle.load(key_in)
        value_in.close()
        key_in.close()
        logger.error(
            'Number of keys ({}) and values ({}) do not match'.format(
                num_entries + 1, num_entries))
        return 1
    except EOFError:
        pass
    except (IOError, pickle.UnpicklingError) as error:
        logger.error(error.message, exc_info=True)
        return 1
    finally:
        value_in.close()
        key_in.close()
    logger.info("Wrote {} entries".format(num_entries))
    return 0


@kaldi_vlog_level_cmd_decorator
@kaldi_logger_decorator
def write_pickle_to_table(args=None):
    '''Write pickle file(s) contents to a table

    The inverse is write-table-to-pickle
    '''
    logger = logging.getLogger(sys.argv[0])
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    register_logger_for_kaldi(logger)
    try:
        options = _write_pickle_to_table_parse_args(args, logger)
    except SystemExit as ex:
        return ex.code
    if options.key_in is None:
        return _write_pickle_to_table_value_only(options, logger)
    else:
        return _write_pickle_to_table_key_value(options, logger)


def _write_table_to_torch_dir_parse_args(args, logger):
    parser = KaldiParser(
        description=write_table_to_torch_dir.__doc__,
        add_verbose=True, logger=logger,
    )
    parser.add_argument(
        'rspecifier', type='kaldi_rspecifier', help='The table to read')
    parser.add_argument('dir', type=str, help='The folder to write files to')
    parser.add_argument(
        '-i', '--in-type', type='kaldi_dtype',
        default=enums.KaldiDataType.BaseMatrix,
        help='The type of table to read'
    )
    parser.add_argument(
        '-o', '--out-type', default=None,
        choices=[
            'float', 'double', 'half', 'byte', 'char', 'short', 'int', 'long',
        ],
        help='The type of torch tensor to write. If unset, it is inferrred '
        'from the input type'
    )
    parser.add_argument(
        '--file-prefix', default='',
        help='The file prefix indicating a torch data file'
    )
    parser.add_argument(
        '--file-suffix', default='.pt',
        help='The file suffix indicating a torch data file'
    )
    options = parser.parse_args(args)
    return options


@kaldi_vlog_level_cmd_decorator
@kaldi_logger_decorator
def write_table_to_torch_dir(args=None):
    '''Write a Kaldi table to a series of PyTorch data files in a directory

    Writes to a folder in the format:

    ::
        folder/
          <file_prefix><key_1><file_suffix>
          <file_prefix><key_2><file_suffix>
          ...

    The contents of the file ``<file_prefix><key_1><file_suffix>`` will be
    a PyTorch tensor corresponding to the entry in the table for ``<key_1>``
    '''
    logger = logging.getLogger(sys.argv[0])
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    register_logger_for_kaldi(logger)
    try:
        options = _write_table_to_torch_dir_parse_args(args, logger)
    except SystemExit as ex:
        return ex.code
    out_type = options.out_type
    if out_type is None:
        if options.in_type in {
                enums.KaldiDataType.BaseMatrix,
                enums.KaldiDataType.BaseVector,
                enums.KaldiDataType.WaveMatrix,
                enums.KaldiDataType.Base,
                enums.KaldiDataType.BasePairVector}:
            if options.in_type.is_double:
                out_type = 'double'
            else:
                out_type = 'float'
        elif options.in_type in {
                enums.KaldiDataType.FloatMatrix,
                enums.KaldiDataType.FloatVector}:
            out_type = 'float'
        elif options.in_type in {
                enums.KaldiDataType.DoubleMatrix,
                enums.KaldiDataType.Double}:
            out_type = 'double'
        elif options.in_type in {
                enums.KaldiDataType.Int32,
                enums.KaldiDataType.Int32Vector,
                enums.KaldiDataType.Int32VectorVector}:
            out_type = 'int'
        elif options.in_type == enums.KaldiDataType.Boolean:
            out_type = 'byte'
        else:
            print(
                'Do not know how to convert {} to torch type'.format(
                    options.in_type),
                file=sys.stderr)
            return 1
    import torch
    if out_type == 'float':
        out_type = torch.float
    elif out_type == 'double':
        out_type = torch.double
    elif out_type == 'half':
        out_type = torch.half
    elif out_type == 'byte':
        out_type = torch.uint8
    elif out_type == 'char':
        out_type = torch.int8
    elif out_type == 'short':
        out_type = torch.short
    elif out_type == 'int':
        out_type = torch.int
    elif out_type == 'long':
        out_type = torch.long
    try:
        os.makedirs(options.dir)
    except FileExistsError:
        pass
    with kaldi_open(options.rspecifier, options.in_type) as table:
        for key, value in table.items():
            value = torch.tensor(value).type(out_type)
            torch.save(
                value, os.path.join(
                    options.dir,
                    options.file_prefix + key + options.file_suffix))
    return 0


def _write_torch_dir_to_table_parse_args(args, logger):
    parser = KaldiParser(
        description=write_torch_dir_to_table.__doc__,
        add_verbose=True, logger=logger,
    )
    parser.add_argument('dir', type=str, help='The folder to read files from')
    parser.add_argument(
        'wspecifier', type='kaldi_wspecifier', help='The table to write to')
    parser.add_argument(
        '-o', '--out-type', type='kaldi_dtype',
        default=enums.KaldiDataType.BaseMatrix,
        help='The type of table to write to'
    )
    parser.add_argument(
        '--file-prefix', default='',
        help='The file prefix indicating a torch data file'
    )
    parser.add_argument(
        '--file-suffix', default='.pt',
        help='The file suffix indicating a torch data file'
    )
    options = parser.parse_args(args)
    return options


@kaldi_vlog_level_cmd_decorator
@kaldi_logger_decorator
def write_torch_dir_to_table(args=None):
    '''Write a data directory containing PyTorch data files to a Kaldi table

    Reads from a folder in the format:

    ::
        folder/
          <file_prefix><key_1><file_suffix>
          <file_prefix><key_2><file_suffix>
          ...

    Where each file contains a PyTorch tensor. The contents of the file
    ``<file_prefix><key_1><file_suffix>`` will be written as a value in
    a Kaldi table with key ``<key_1>``
    '''
    logger = logging.getLogger(sys.argv[0])
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    register_logger_for_kaldi(logger)
    try:
        options = _write_torch_dir_to_table_parse_args(args, logger)
    except SystemExit as ex:
        return ex.code
    if not os.path.isdir(options.dir):
        print("'{}' is not a directory".format(options.dir), file=sys.stderr)
        return 1
    import torch
    is_bool = False
    if options.out_type in {
            enums.KaldiDataType.BaseMatrix,
            enums.KaldiDataType.BaseVector,
            enums.KaldiDataType.WaveMatrix,
            enums.KaldiDataType.Base,
            enums.KaldiDataType.BasePairVector}:
        if options.out_type.is_double:
            torch_type = torch.double
        else:
            torch_type = torch.float
    elif options.out_type in {
            enums.KaldiDataType.FloatMatrix,
            enums.KaldiDataType.FloatVector}:
        torch_type = torch.float
    elif options.out_type in {
            enums.KaldiDataType.DoubleMatrix,
            enums.KaldiDataType.Double}:
        torch_type = torch.double
    elif options.out_type in {
            enums.KaldiDataType.Int32,
            enums.KaldiDataType.Int32Vector,
            enums.KaldiDataType.Int32VectorVector}:
        torch_type = torch.int
    elif options.out_type == enums.KaldiDataType.Boolean:
        torch_type = torch.uint8
        is_bool = True
    else:
        print(
            'Do not know how to convert {} from torch type'.format(
                options.out_type),
            file=sys.stderr)
        return 1
    neg_fsl = -len(options.file_suffix)
    if not neg_fsl:
        neg_fsl = None
    fpl = len(options.file_prefix)
    utt_ids = sorted(
        os.path.basename(x)[fpl:neg_fsl]
        for x in os.listdir(options.dir)
        if x.startswith(options.file_prefix) and
        x.endswith(options.file_suffix)
    )
    with kaldi_open(options.wspecifier, options.out_type, mode='w') as table:
        for utt_id in utt_ids:
            val = torch.load(os.path.join(
                options.dir,
                options.file_prefix + utt_id + options.file_suffix))
            val = val.cpu().type(torch_type).numpy()
            if is_bool:
                val = bool(val)  # make sure val is a scalar!
            table.write(utt_id, val)
    return 0
