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

'''Command line hooks for feature-related activities'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys

import numpy as np

from pydrobert.kaldi.io import open as kaldi_open
from pydrobert.kaldi.io.argparse import KaldiParser
from pydrobert.kaldi.logging import kaldi_logger_decorator
from pydrobert.kaldi.logging import kaldi_vlog_level_cmd_decorator
from pydrobert.kaldi.logging import register_logger_for_kaldi
from six.moves import cPickle as pickle

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2017 Sean Robertson"

__all__ = [
    'write_pickle_to_table',
    'write_table_to_pickle',
    'normalize_feat_lens',
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
        logger.warn("No entries were written (table was empty)")
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
    logger.warn('No entries were written (pickle file(s) was/were empty)')
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


def _normalize_feat_lens_parse_args(args, logger):
    parser = KaldiParser(
        description=normalize_feat_lens.__doc__,
        add_verbose=True,
        logger=logger,
    )
    parser.add_argument(
        'feats_in_rspecifier', type='kaldi_rspecifier',
        help='The features to be normalized',
    )
    parser.add_argument(
        'len_in_rspecifier', type='kaldi_rspecifier',
        help='The reference lengths (int32 table)',
    )
    parser.add_argument(
        'feats_out_wspecifier', type='kaldi_wspecifier',
        help='The output features',
    )
    parser.add_argument(
        '--type', type='kaldi_dtype', default='bm',
        help='The kaldi type of the input/output features',
    )
    parser.add_argument(
        '--tolerance', type=int, default=float('inf'),
        help='''\
How many frames deviation from reference to tolerate before error. The default
is to be infinitely tolerant (a feat I'm sure we all desire)
''')
    parser.add_argument(
        '--strict', type='kaldi_bool', default=False,
        help='''\
Whether missing keys in len_in and lengths beyond the threshold cause
an error (true) or are skipped with a warning (false)
''')
    parser.add_argument(
        '--pad-mode', default='edge',
        choices=('zero', 'constant', 'edge', 'symmetric', 'mean'),
        help='''\
If frames are being padded to the features, specify how they should be padded.
zero=zero pad, edge=pad with rightmost frame, symmetric=pad with reverse of
frame edges, mean=pad with mean feature values
''')
    parser.add_argument(
        '--side', default='right',
        choices=('left', 'right', 'center'),
        help='''\
If an utterance needs to be padded or truncated, specify what side of the
utterance to do this on. left=beginning, right=end, center=distribute
evenly on either side
'''
    )
    return parser.parse_args(args)


@kaldi_vlog_level_cmd_decorator
@kaldi_logger_decorator
def normalize_feat_lens(args=None):
    '''Ensure features match some reference lengths

    Incoming features are either clipped or padded to match
    reference lengths (stored as an int32 table), if they are within
    tolerance.
    '''
    logger = logging.getLogger(sys.argv[0])
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    register_logger_for_kaldi(sys.argv[0])
    options = _normalize_feat_lens_parse_args(args, logger)
    if options.pad_mode == 'zero':
        options.pad_mode = 'constant'
    feats_in = kaldi_open(
        options.feats_in_rspecifier, options.type, mode='r')
    len_in = kaldi_open(options.len_in_rspecifier, 'i', mode='r+')
    feats_out = kaldi_open(
        options.feats_out_wspecifier, options.type, mode='w')
    total_utts = 0
    processed_utts = 0
    for utt_id, feats in feats_in.items():
        total_utts += 1
        if utt_id not in len_in:
            msg = "Utterance '{}' absent in '{}'".format(
                utt_id, options.len_in_rspecifier)
            if options.strict:
                logger.error(msg)
                return 1
            else:
                logger.warning(msg)
                continue
        exp_feat_len = len_in[utt_id]
        act_feat_len = len(feats)
        logger.debug('{} exp len: {} act len: {}'.format(
            utt_id, exp_feat_len, act_feat_len))
        if act_feat_len < exp_feat_len:
            if act_feat_len < exp_feat_len - options.tolerance:
                msg = '{} has feature length {}, which is below the '
                msg += 'tolerance ({}) of the expected length {}'
                msg = msg.format(
                    utt_id, act_feat_len, options.tolerance, exp_feat_len)
                if options.strict:
                    logger.error(msg)
                    return 1
                else:
                    logger.warning(msg)
                    continue
            # for matrices or vectors, this cast shouldn't be necessary.
            # If the user tries some special type like token vectors,
            # however, this *might* work as intended
            feats = np.array(feats, copy=False)
            pad_list = [(0, 0)] * len(feats.shape)
            if options.side == 'right':
                pad_list[0] = (0, exp_feat_len - act_feat_len)
            elif options.side == 'left':
                pad_list[0] = (exp_feat_len - act_feat_len, 0)
            else:
                pad_list[0] = (
                    (exp_feat_len - act_feat_len) // 2,
                    (exp_feat_len - act_feat_len + 1) // 2
                )
            feats = np.pad(
                feats,
                pad_list,
                options.pad_mode
            )
        elif act_feat_len > exp_feat_len:
            if act_feat_len > exp_feat_len + options.tolerance:
                msg = '{} has feature length {}, which is above the '
                msg += 'tolerance ({}) of the expected length {}'
                msg = msg.format(
                    utt_id, act_feat_len, options.tolerance, exp_feat_len)
                if options.strict:
                    logger.error(msg)
                    return 1
                else:
                    logger.warning(msg)
                    continue
            if options.side == 'right':
                feats = feats[:exp_feat_len - act_feat_len]
            elif options.side == 'left':
                feats = feats[exp_feat_len - act_feat_len:]
            else:
                feats = feats[
                    (exp_feat_len - act_feat_len) // 2:
                    (exp_feat_len - act_feat_len + 1) // 2
                ]
        feats_out.write(utt_id, feats)
        processed_utts += 1
    logger.info('Processed {}/{} utterances'.format(
        processed_utts, total_utts))
    return 0
