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

"""Pytests for `pydrobert.kaldi.io.corpus`"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from itertools import product
from itertools import repeat

import numpy as np
import pytest

from pydrobert.kaldi.io import corpus


@pytest.mark.parametrize('samples', [
    ([[1, 2], [3, 4]], [[5, 6], [7, 8]]),
    ([True, False, False], [False, False, False]),
    np.random.random((10, 50, 40)),
    np.random.randint(-10, 1000, size=(5, 4, 10, 1)),
])
def test_batch_data_basic(samples):
    input_shape = np.array(samples[0], copy=False).shape
    for axis in range(-1, len(input_shape) + 1):
        batch_slice = [slice(None)] * (len(input_shape) + 1)
        for batch_size in range(1, len(samples) + 1):
            for batch_num, act_batch in enumerate(corpus.batch_data(
                    samples, is_tup=False, batch_size=batch_size,
                    axis=axis)):
                exp_batch = samples[
                    batch_num * batch_size:(batch_num + 1) * batch_size]
                assert act_batch.shape[axis] == len(exp_batch)
                for samp_idx in range(len(exp_batch)):
                    batch_slice[axis] = samp_idx
                    assert np.allclose(
                        exp_batch[samp_idx], act_batch[batch_slice])


@pytest.mark.parametrize('samples', [
    ([[1, 2], [3, 4]], [[5, 6], [7, 8]]),
    ([[1., 2.], 3.], [[4., 5.], 6.], [[7., 8.], 9.]),
    ([1, [2, 3], [4, 5, 6]], [7, [8, 9], [10, 11, 12]]),
    np.random.random((10, 5, 4)),
    np.random.randint(-10, 1000, size=(3, 4, 2, 1, 2)),
])
def test_batch_data_tups(samples):
    input_shapes = tuple(
        np.array(sample, copy=False).shape for sample in samples[0])
    axes = tuple(product(*(range(len(shape) + 1) for shape in input_shapes)))
    axes += (0, -1)
    for axis in axes:
        batch_slices = tuple(
            [slice(None)] * (len(shape) + 1) for shape in input_shapes)
        if isinstance(axis, int):
            axis_iter = repeat(axis)
        else:
            axis_iter = axis
        for batch_size in range(1, len(samples) + 1):
            for batch_num, act_batch in enumerate(corpus.batch_data(
                    samples, is_tup=True, batch_size=batch_size, axis=axis)):
                assert len(act_batch) == len(input_shapes)
                exp_batch = samples[
                    batch_num * batch_size:(batch_num + 1) * batch_size]
                for sub_batch_idx, sub_axis in \
                        zip(range(len(input_shapes)), axis_iter):
                    act_sub_batch = act_batch[sub_batch_idx]
                    assert act_sub_batch.shape[sub_axis] == len(exp_batch)
                    sub_batch_slice = batch_slices[sub_batch_idx]
                    for samp_idx in range(len(exp_batch)):
                        sub_batch_slice[sub_axis] = samp_idx
                        assert np.allclose(
                            exp_batch[samp_idx][sub_batch_idx],
                            act_sub_batch[sub_batch_slice])


def test_padding():
    samples = ([[1], [2], [3]], [[4, 5], [6, 7]], [[8], [9]])
    l1_batches = tuple(corpus.batch_data(
        samples, is_tup=False, batch_size=1, pad_mode='maximum'))
    assert len(l1_batches) == 3
    assert np.allclose(l1_batches[0], [[1], [2], [3]])
    assert np.allclose(l1_batches[1], [[4, 5], [6, 7]])
    assert np.allclose(l1_batches[2], [[8], [9]])
    l2_batches = tuple(corpus.batch_data(
        samples, is_tup=False, batch_size=2, pad_mode='maximum'))
    assert len(l2_batches) == 2
    assert np.allclose(
        l2_batches[0],
        [
            [[1, 1], [2, 2], [3, 3]],
            [[4, 5], [6, 7], [6, 7]],
        ]
    )
    assert np.allclose(l2_batches[1], [[8], [9]])
    l3_batches = tuple(corpus.batch_data(
        samples, is_tup=False, batch_size=3, pad_mode='wrap'))
    assert len(l3_batches) == 1
    assert np.allclose(
        l3_batches[0],
        [
            [[1, 1], [2, 2], [3, 3]],
            [[4, 5], [6, 7], [4, 5]],
            [[8, 8], [9, 9], [8, 8]],
        ]
    )


@pytest.mark.parametrize('is_tup', [True, False])
@pytest.mark.parametrize('batch_size', [0, 1])
def test_empty_samples(is_tup, batch_size):
    samples = []
    batches = list(corpus.batch_data(
        samples, is_tup=is_tup, batch_size=batch_size))
    assert samples == batches


@pytest.mark.parametrize('is_tup', [True, False])
def test_zero_batch(is_tup):
    samples = np.random.random((10, 2, 4, 100))
    batches = list(corpus.batch_data(samples, is_tup=is_tup))
    assert len(batches) == len(samples)
    assert np.allclose(samples, np.stack(batches))
