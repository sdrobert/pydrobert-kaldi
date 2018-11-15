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

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2017 Sean Robertson"

__all__ = [
    'normalize_feat_lens',
]


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
