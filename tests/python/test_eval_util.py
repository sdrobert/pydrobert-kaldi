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

'''Pytests for `pydrobert.kaldi.eval.util`'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pydrobert.kaldi.eval as kaldi_eval


def test_edit_distance():
    # An example from wikipedia. Thanks Wiki!
    ref = 'kitten'
    hyp = 'sitting'
    assert kaldi_eval.util.edit_distance(ref, hyp) == 3
    _, inserts, deletes, subs, totals = kaldi_eval.util.edit_distance(
        ref, hyp, return_tables=True)
    assert inserts == {'g': 1}
    assert deletes == dict()
    assert subs == {'k': 1, 'e': 1}
    assert totals == {'k': 1, 'i': 1, 't': 2, 'e': 1, 'n': 1}
    dist, inserts, deletes, subs, totals = kaldi_eval.util.edit_distance(
        ref, hyp, insertion_cost=0, substitution_cost=2, return_tables=True)
    assert dist == 2
    assert inserts == {'s': 1, 'i': 1, 'g': 1}
    assert deletes == {'k': 1, 'e': 1}
    assert subs == dict()
    assert totals == {'k': 1, 'i': 1, 't': 2, 'e': 1, 'n': 1}
