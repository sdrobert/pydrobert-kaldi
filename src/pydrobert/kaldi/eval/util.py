# Copyright 2021 Sean Robertson

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for evaluation"""

from typing import Sequence, Tuple, Union
import numpy as np

__all__ = ["edit_distance"]


def edit_distance(
    ref: Sequence,
    hyp: Sequence,
    insertion_cost: int = 1,
    deletion_cost: int = 1,
    substitution_cost: int = 1,
    return_tables: bool = False,
) -> Union[int, Tuple[int, dict, dict, dict, dict]]:
    """Levenshtein (edit) distance

    Parameters
    ----------
    ref : sequence
        Sequence of tokens of reference text (source)
    hyp : sequence
        Sequence of tokens of hypothesis text (target)
    insertion_cost : int
        Penalty for `hyp` inserting a token to ref
    deletion_cost : int
        Penalty for `hyp` deleting a token from ref
    substitution_cost : int
        Penalty for `hyp` swapping tokens in ref
    return_tables : bool
        See below

    Returns
    -------
    int or (int, dict, dict, dict, dict)
        Returns the edit distance of `hyp` from `ref`. If `return_tables`
        is `True`, this returns a tuple of the edit distance, a dict of
        insertion counts, a dict of deletion , a dict of substitution
        counts per ref token, and a dict of counts of ref tokens. Any
        tokens with count 0 are excluded from the dictionary.
    """
    # we keep track of the whole dumb matrix in case we need to
    # backtrack (for `return_tables`). Should be okay for WER/PER, since
    # the number of tokens per vector will be on the order of tens
    distances = np.zeros((len(ref) + 1, len(hyp) + 1), dtype=int)
    distances[0, :] = tuple(insertion_cost * x for x in range(len(hyp) + 1))
    distances[:, 0] = tuple(deletion_cost * x for x in range(len(ref) + 1))
    for hyp_idx in range(1, len(hyp) + 1):
        hyp_token = hyp[hyp_idx - 1]
        for ref_idx in range(1, len(ref) + 1):
            ref_token = ref[ref_idx - 1]
            sub_cost = 0 if hyp_token == ref_token else substitution_cost
            distances[ref_idx, hyp_idx] = min(
                distances[ref_idx - 1, hyp_idx] + deletion_cost,
                distances[ref_idx, hyp_idx - 1] + insertion_cost,
                distances[ref_idx - 1, hyp_idx - 1] + sub_cost,
            )
    if not return_tables:
        return distances[-1, -1]
    # backtrack to get a count of insertions, deletions, and subs
    # prefer insertions to deletions to substitutions
    inserts, deletes, subs, totals = dict(), dict(), dict(), dict()
    for token in ref:
        totals[token] = totals.get(token, 0) + 1
    ref_idx = len(ref)
    hyp_idx = len(hyp)
    while ref_idx or hyp_idx:
        if not ref_idx:
            hyp_idx -= 1
            inserts[hyp[hyp_idx]] = inserts.get(hyp[hyp_idx], 0) + 1
        elif not hyp_idx:
            ref_idx -= 1
            deletes[ref[ref_idx]] = deletes.get(ref[ref_idx], 0) + 1
        elif ref[ref_idx - 1] == hyp[hyp_idx - 1]:
            hyp_idx -= 1
            ref_idx -= 1
        elif (
            distances[ref_idx, hyp_idx - 1] <= distances[ref_idx - 1, hyp_idx]
            and distances[ref_idx, hyp_idx - 1] <= distances[ref_idx - 1, hyp_idx - 1]
        ):
            hyp_idx -= 1
            inserts[hyp[hyp_idx]] = inserts.get(hyp[hyp_idx], 0) + 1
        elif distances[ref_idx - 1, hyp_idx] <= distances[ref_idx - 1, hyp_idx - 1]:
            ref_idx -= 1
            deletes[ref[ref_idx]] = deletes.get(ref[ref_idx], 0) + 1
        else:
            hyp_idx -= 1
            ref_idx -= 1
            subs[ref[ref_idx]] = subs.get(ref[ref_idx], 0) + 1
    return distances[-1, -1], inserts, deletes, subs, totals
