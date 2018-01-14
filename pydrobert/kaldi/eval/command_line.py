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

'''Command-line hooks for evalulation'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys

from itertools import chain
from math import log10

from pydrobert.kaldi.eval import util as kaldi_eval_util
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
    'compute_error_rate',
]


def _compute_error_rate_parse_args(args, logger):
    parser = KaldiParser(
        description=compute_error_rate.__doc__,
        add_verbose=True,
        logger=logger,
    )
    parser.add_argument(
        'ref_rspecifier', type='kaldi_rspecifier',
        help='Rspecifier pointing to reference (gold standard) transcriptions')
    parser.add_argument(
        'hyp_rspecifier', type='kaldi_wspecifier',
        help='Rspecifier pointing to hypothesis transcriptions')
    parser.add_argument(
        'out_path', nargs='?', default=None,
        help='Path to print results to. Default is stdout.')
    parser.add_argument(
        '--print-tables', type='kaldi_bool', default=False,
        help='If set, will print breakdown of insertions, deletions, and subs '
             'to out_path')
    parser.add_argument(
        '--strict', type='kaldi_bool', default=False,
        help='If set, missing utterances will cause an error')
    parser.add_argument(
        '--insertion-cost', type=int, default=1,
        help='Cost (in terms of edit distance) to perform an insertion')
    parser.add_argument(
        '--deletion-cost', type=int, default=1,
        help='Cost (in terms of edit distance) to perform a deletion')
    parser.add_argument(
        '--substitution-cost', type=int, default=1,
        help='Cost (in terms of edit distance) to perform a substitution')
    parser.add_argument(
        '--include-inserts-in-cost', type='kaldi_bool', default=True,
        help='Whether to include insertions in error rate calculations')
    parser.add_argument(
        '--report-accuracy', type='kaldi_bool', default=False,
        help='Whether to report accuracy (1 - error_rate) instead of '
             'the error rate'
    )
    options = parser.parse_args(args)
    return options


@kaldi_vlog_level_cmd_decorator
@kaldi_logger_decorator
def compute_error_rate(args=None):
    '''Compute error rates between reference and hypothesis token vectors

    Two common error rates in speech are the word (WER) and phone (PER),
    though the computation is the same. Given a reference and hypothesis
    sequence, the error rate is

    >>> error_rate = (substitutions + insertions + deletions) / (
    ...     ref_tokens * 100)

    Where the number of substitutions (e.g. ``A B C -> A D C``),
    deletions (e.g. ``A B C -> A C``), and insertions (e.g.
    ``A B C -> A D B C``) are determined by Levenshtein distance.
    '''
    logger = logging.getLogger(sys.argv[0])
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    register_logger_for_kaldi(sys.argv[0])
    options = _compute_error_rate_parse_args(args, logger)
    global_edit = 0
    global_token_count = 0
    global_sents = 0
    global_processed = 0
    inserts = dict()
    deletes = dict()
    subs = dict()
    totals = dict()

    def _err_on_utt_id(utt_id, missing_rxspecifier):
        msg = "Utterance '{}' absent in '{}'".format(
            utt_id, missing_rxspecifier)
        if options.strict:
            logger.error(msg)
            return 1
        else:
            logger.warning(msg)
            return 0
    return_tables = options.print_tables or not options.include_inserts_in_cost
    with kaldi_open(options.ref_rspecifier, 'tv') as ref_table, \
            kaldi_open(options.hyp_rspecifier, 'tv') as hyp_table:
        while not ref_table.done() and not hyp_table.done():
            global_sents += 1
            if ref_table.key() > hyp_table.key():
                if _err_on_utt_id(hyp_table.key(), options.ref_rspecifier):
                    return 1
                hyp_table.move()
            elif hyp_table.key() > ref_table.key():
                if _err_on_utt_id(ref_table.key(), options.hyp_rspecifier):
                    return 1
                ref_table.move()
            else:
                logger.debug('Processing {}: ref [{}] hyp [{}]'.format(
                    ref_table.key(),
                    ' '.join(ref_table.value()),
                    ' '.join(hyp_table.value())))
                global_token_count += len(ref_table.value())
                res = kaldi_eval_util.edit_distance(
                    ref_table.value(), hyp_table.value(),
                    return_tables=return_tables,
                    insertion_cost=options.insertion_cost,
                    deletion_cost=options.deletion_cost,
                    substitution_cost=options.substitution_cost,
                )
                if return_tables:
                    global_edit += res[0]
                    for global_dict, utt_dict in zip(
                            (inserts, deletes, subs, totals), res[1:]):
                        for token in ref_table.value() + hyp_table.value():
                            global_dict.setdefault(token, 0)
                        for token, count in utt_dict.items():
                            global_dict[token] += count
                else:
                    global_edit += res
            global_processed += 1
            ref_table.move()
            hyp_table.move()
        while not ref_table.done():
            if _err_on_utt_id(ref_table.key(), options.hyp_rspecifier):
                return 1
            global_sents += 1
            ref_table.move()
        while not hyp_table.done():
            if _err_on_utt_id(hyp_table.key(), options.ref_rspecifier):
                return 1
            global_sents += 1
            hyp_table.move()
    if options.out_path is None:
        out_file = sys.stdout
    else:
        out_file = open(options.out_path, 'w')
    print(
        "Processed {}/{}.".format(global_processed, global_sents),
        file=out_file, end=' '
    )
    if not options.include_inserts_in_cost:
        global_edit -= sum(inserts.values())
    if options.report_accuracy:
        print(
            'Accuracy: {:.2f}%'.format(
                (1 - global_edit / global_token_count) * 100),
            file=out_file,
        )
    else:
        print(
            'Error rate: {:.2f}%'.format(
                global_edit / global_token_count * 100),
            file=out_file,
        )
    if options.print_tables:
        print(
            "Total insertions: {}, deletions: {}, substitutions: {}".format(
                sum(inserts.values()), sum(deletes.values()),
                sum(subs.values())),
            file=out_file,
        )
        print("", file=out_file)
        tokens = list(set(inserts) | set(deletes) | set(subs))
        tokens.sort()
        token_len = max(max(len(token) for token in tokens), 5)
        max_count = max(
            chain(inserts.values(), deletes.values(), subs.values()))
        max_count_len = int(log10(max_count) + 1)
        divider_str = '+' + ('-' * (token_len + 1))
        divider_str += ('+' + ('-' * (max_count_len + 9))) * 4
        divider_str += '+'
        format_str = '|{{:<{}}}|'.format(token_len + 1)
        format_str += 4 * '{{:>{}}}({{:05.2f}}%)|'.format(max_count_len + 1)
        print(
            '|{2:<{0}}|{3:>{1}}(%)|{4:>{1}}(%)|{5:>{1}}(%)|{6:>{1}}(%)|'
            ''.format(
                token_len + 1, max_count_len + 6, 'token', 'inserts',
                'deletes', 'subs', 'errs',
            ),
            file=out_file,
        )
        print(divider_str, file=out_file)
        print(divider_str, file=out_file)
        for token in tokens:
            i, d, s = inserts[token], deletes[token], subs[token]
            t = totals[token]
            print(
                format_str.format(
                    token,
                    i, i / t * 100,
                    d, d / t * 100,
                    s, s / t * 100,
                    i + d + s, (i + d + s) / t * 100,
                ),
                file=out_file
            )
            print(divider_str, file=out_file)
    return 0
