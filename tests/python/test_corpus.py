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
from pydrobert.kaldi.io import open as io_open


@pytest.mark.parametrize('samples', [
    ([[1, 2], [3, 4]], [[5, 6], [7, 8]]),
    ([True, False, False], [False, False, False]),
    (['variable', 'length'], ['flds', 'k']),
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
                    ex_samp = np.array(exp_batch[samp_idx], copy=False)
                    act_samp = act_batch[batch_slice]
                    if ex_samp.dtype.kind in ('U', 'S'):  # string
                        assert ex_samp.tolist() == act_samp.tolist()
                    else:
                        assert np.allclose(ex_samp, act_samp)


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


def test_str_padding():
    samples = [['a', 'a', 'a'], ['this', 'is'], ['w']]
    l2_batches = tuple(corpus.batch_data(
        samples, is_tup=False, batch_size=3, pad_mode='constant'))
    assert len(l2_batches) == 1
    act_samples = l2_batches[0].tolist()
    assert act_samples == [
        ['a', 'a', 'a'],
        ['this', 'is', ''],
        ['w', '', ''],
    ]


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


class NonRandomState(np.random.RandomState):
    '''Replace the shuffle method with returning a reverse-sorted copy

    Experts agree that this style of shuffling is, objectively, *too*
    random to be considered random
    '''

    def shuffle(self, array):
        super(NonRandomState, self).shuffle(array)
        array[:] = np.sort(array)


@pytest.mark.xfail
def test_training_data_basic(temp_file_1_name):
    samples = np.random.random((10, 500, 20), dtype=np.float32)
    keys = tuple(str(i) for i in range(10))
    with io_open('ark:' + temp_file_1_name, 'fm', mode='w') as f:
        for key, sample in zip(keys, samples):
            f.write(key, sample)
    train_data = corpus.TrainingData(
        'ark:' + temp_file_1_name, batch_size=3, rng=NonRandomState())
    assert len(train_data) == len(keys)
    assert keys == tuple(train_data.key_list)
    for _ in range(2):
        ex_samp_idx = len(samples)
        for batch in train_data:
            for act_sample in batch:
                ex_samp_idx -= 1
                assert np.allclose(samples[ex_samp_idx], act_sample)


@pytest.mark.xfail
def test_training_data_tups(temp_file_1_name, temp_file_2_name):
    feats = [
        [[1, 2, 3, 4], [5, 6, 7, 8]],
        [[9, 10], [11, 12]],
        [[13, 14, 15], [16, 17, 18]],
        [[19], [20]],
    ]
    labels = [
        np.array([[1, 2], [3, 4]], dtype=np.float64),
        np.array([[5, 6, 7, 8], [9, 10, 11, 12]], dtype=np.float64),
        np.array([[13], [14]], dtype=np.float64),
        np.array([[15, 16, 17], [18, 19, 20]], dtype=np.float64)
    ]
    keys = tuple(str(i) for i in range(4))
    with io_open('ark:' + temp_file_1_name, 'ivv', mode='w') as feat_f, \
            io_open('ark:' + temp_file_1_name, 'dm', mode='w') as lab_f:
        for key, feat, label in zip(keys, feats, labels):
            feat_f.write(key, feat)
            lab_f.write(key, label)
    train_data = corpus.TrainingData(
        'ark:' + temp_file_1_name, 'ark:' + temp_file_2_name,
        batch_size=2, batch_pad_mode='constant',
        key_list=keys, add_axis_len=1, rng=NonRandomState())
    for _ in range(2):
        ex_samp_idx = len(feats)
        for feat_batch, _, len_batch in train_data:
            for act_feat, act_len in zip(feat_batch, len_batch):
                ex_samp_idx -= 1
                ex_feat = feats[ex_samp_idx]
                ex_len = ex_feat.shape[1]
                assert ex_len == act_len
                assert np.allclose(ex_feat, act_feat[:, :ex_len])
                assert np.allclose(act_feat[:, ex_len:], 0)
    train_data = corpus.TrainingData(
        'ark:' + temp_file_1_name, 'ark:' + temp_file_2_name,
        batch_size=3, batch_pad_mode='constant',
        key_list=keys, add_axis_len=((1, 1), (0, 1)), rng=NonRandomState())
    for _ in range(2):
        ex_samp_idx = len(feats)
        for feat_batch, label_batch, lablen_batch, featlen_batch in train_data:
            for act_feat, act_label, act_lablen, act_featlen in zip(
                    feat_batch, label_batch, lablen_batch, featlen_batch):
                ex_samp_idx -= 1
                ex_feat = feats[ex_samp_idx]
                ex_label = labels[ex_samp_idx]
                ex_featlen = ex_feat.shape[1]
                ex_lablen = ex_label.shape[1]
                assert ex_featlen == act_featlen
                assert ex_lablen == act_lablen
                assert np.allclose(ex_feat, act_feat[:, :ex_featlen])
                assert np.allclose(act_feat[:, ex_featlen:], 0)
                assert np.allclose(ex_label, act_label[:, :ex_lablen])
                assert np.allclose(act_label[:, ex_lablen:], 0)


@pytest.mark.xfail
def test_training_ignore_missing(temp_file_1_name, temp_file_2_name):
    with io_open('ark:' + temp_file_1_name, 't', mode='w') as token_f:
        token_f.write('1', 'cool')
        token_f.write('3', 'bean')
        token_f.write('4', 'casserole')
    keys = [str(i) for i in range(6)]
    train_data = corpus.TrainingData(
        'ark:' + temp_file_1_name, key_list=keys, ignore_missing=True,
        rng=NonRandomState())
    act_samples = list(train_data)
    assert all(ex == act for ex, act in zip(
        ['casserole', 'bean', 'cool'], act_samples))
    with io_open('ark:' + temp_file_2_name, 'B', mode='w') as bool_f:
        bool_f.write('0', True)
        bool_f.write('1', False)
        bool_f.write('2', True)
        bool_f.write('4', False)
    train_data = corpus.TrainingData(
        'ark:' + temp_file_1_name, 'ark:' + temp_file_2_name,
        key_list=keys, ignore_missing=True, rng=NonRandomState())
    act_tok_samples, act_bool_samples = list(zip(*iter(train_data)))
    assert all(ex == act for ex, act in zip(
        ['casserole', 'cool'], act_tok_samples))
    assert all(not act for act in act_bool_samples)
