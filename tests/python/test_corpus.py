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
from pydrobert.kaldi.io.enums import KaldiDataType


@pytest.mark.parametrize('samples', [
    np.random.random((100, 20, 10)),
    np.random.random(1),
    np.arange(100),
    np.array(['foo', 'barz', 'ba']),
    np.array([['foo', 'bar'], ['baz', 'bump']]),
    np.eye(100).reshape((10, 10, 10, 10)),
])
def test_batch_data_numpy(samples):
    # samples are numpy data of the same shape and type
    batch_start = 0
    for ex_samp, act_samp in zip(
            samples, corpus.batch_data(samples, subsamples=False)):
        try:
            assert np.allclose(ex_samp, act_samp)
        except TypeError:
            assert ex_samp.tolist() == act_samp.tolist()
        batch_start += 1
    assert batch_start == len(samples)
    for axis in range(-1, len(samples.shape)):
        batch_slice = [slice(None)] * len(samples.shape)
        for batch_size in range(1, len(samples) + 2):
            batch_start = 0
            for act_batch in corpus.batch_data(
                    samples, batch_size=batch_size, subsamples=False,
                    axis=axis):
                ex_batch = samples[batch_start:batch_start + batch_size]
                assert len(ex_batch) == act_batch.shape[axis]
                for samp_idx in range(len(ex_batch)):
                    batch_slice[axis] = samp_idx
                    try:
                        assert np.allclose(
                            ex_batch[samp_idx], act_batch[tuple(batch_slice)])
                    except TypeError:
                        assert (
                            ex_batch[samp_idx].flatten().tolist() ==
                            act_batch[tuple(batch_slice)].flatten().tolist())
                batch_start += len(ex_batch)
        assert batch_start == len(samples)


@pytest.mark.parametrize('samples', [
    ([[1, 2], [3, 4]], [[5, 6], [7, 8]]),
    ([True, False, False], [False, False, False]),
    ('a', 'b', 'c'),
    ('de',),
    ([10, 4], [1]),
    tuple(),
    (np.arange(100, dtype=np.int32), np.arange(100, dtype=np.int64)),
    (np.arange(100).reshape(10, 10), np.arange(1000).reshape(10, 100)),
])
def test_batch_data_alt(samples):
    # data that are:
    # - not in sub-batches
    # - not numpy arrays (and not casted)
    # - variable shape
    # - variable type
    batch_start = 0
    for ex_samp, act_samp in zip(
            samples, corpus.batch_data(samples, subsamples=False)):
        try:
            assert np.allclose(ex_samp, act_samp)
        except TypeError:
            assert ex_samp == act_samp
        batch_start += 1
    assert batch_start == len(samples)
    for batch_size in range(1, len(samples) + 2):
        batch_start = 0
        for act_batch in corpus.batch_data(
                samples, batch_size=batch_size, subsamples=False):
            ex_batch = samples[batch_start:batch_start + batch_size]
            assert len(ex_batch) == len(act_batch)
            for ex_samp, act_samp in zip(ex_batch, act_batch):
                try:
                    assert np.allclose(ex_samp, act_samp)
                except TypeError:
                    assert ex_samp == act_samp
            batch_start += len(act_batch)
        assert batch_start == len(samples)


@pytest.mark.parametrize('samples', [
    np.random.random((10, 5, 4)),
    np.random.random((4, 1)),
    np.random.randint(0, 2, size=(3, 4, 2, 1, 2)).astype(bool),
    np.eye(10).reshape((10, 10)),
    np.array([
        [['able', 'was']],
        [['I', 'ere']],
        [['I', 'saw']],
        [['elba', 'dawg']]]),
])
def test_batch_data_tups_numpy(samples):
    input_shapes = tuple(sample.shape for sample in samples[0])
    axes = tuple(product(*(range(len(shape) + 1) for shape in input_shapes)))
    axes += (0, -1)
    batch_start = 0
    for ex_samp, act_samp in zip(samples, corpus.batch_data(samples)):
        assert isinstance(act_samp, tuple)
        for ex_sub_samp, act_sub_samp in zip(ex_samp, act_samp):
            assert ex_sub_samp.shape == act_sub_samp.shape
            try:
                assert np.allclose(ex_sub_samp, act_sub_samp)
            except TypeError:
                assert (
                    ex_sub_samp.flatten().tolist() ==
                    act_sub_samp.flatten().tolist()
                )
        batch_start += 1
    assert batch_start == len(samples)
    for axis in axes:
        batch_slices = tuple(
            [slice(None)] * (len(shape) + 1) for shape in input_shapes)
        if isinstance(axis, int):
            axis_iter = repeat(axis)
        else:
            axis_iter = axis
        for batch_size in range(1, len(samples) + 2):
            batch_start = 0
            for act_batch in corpus.batch_data(
                    samples, subsamples=True, batch_size=batch_size,
                    axis=axis):
                assert len(act_batch) == len(input_shapes)
                assert isinstance(act_batch, tuple)
                ex_batch = samples[batch_start:batch_start + batch_size]
                for sub_batch_idx, sub_axis in zip(
                        range(len(input_shapes)), axis_iter):
                    act_sub_batch = act_batch[sub_batch_idx]
                    assert len(ex_batch) == act_sub_batch.shape[sub_axis]
                    sub_batch_slice = batch_slices[sub_batch_idx]
                    for sub_samp_idx in range(len(ex_batch)):
                        sub_batch_slice[sub_axis] = sub_samp_idx
                        ex_sub_samp = ex_batch[sub_samp_idx, sub_batch_idx]
                        act_sub_samp = act_sub_batch[tuple(sub_batch_slice)]
                        # the == 2 is to account for the case when
                        # ex_sub_samp are going to be np.generics (as
                        # opposed to a arrays)
                        assert (len(input_shapes) == 2) or (
                            ex_sub_samp.shape == act_sub_samp.shape, sub_axis)
                        try:
                            assert np.allclose(ex_sub_samp, act_sub_samp)
                        except TypeError:
                            assert (
                                ex_sub_samp.flatten().tolist() ==
                                act_sub_samp.flatten().tolist()
                            )
                batch_start += len(ex_batch)
            assert batch_start == len(samples)


@pytest.mark.parametrize('samples', [
    (([1, 2], [3, 4]), ([5, 6], [7, 8])),
    ((['a', 'bc', 'd'], 'e'), ('f', ['ghi', 'j'])),
    ((np.array(50),), (np.array(1),), (np.arange(10),)),
    tuple(),
])
def test_batch_data_tups_alt(samples):
    batch_start = 0
    for ex_samp, act_samp in zip(samples, corpus.batch_data(samples)):
        assert isinstance(act_samp, tuple)
        for ex_sub_samp, act_sub_samp in zip(ex_samp, act_samp):
            try:
                assert np.allclose(ex_sub_samp, act_sub_samp)
            except TypeError:
                assert ex_sub_samp == act_sub_samp
        batch_start += 1
    assert batch_start == len(samples)
    for batch_size in range(1, len(samples) + 2):
        batch_start = 0
        for act_batch in corpus.batch_data(samples, batch_size=batch_size):
            ex_batch = samples[batch_start:batch_start + batch_size]
            assert len(ex_batch[0]) == len(act_batch)  # same num sub-batches
            for sub_batch_idx, act_sub_batch in enumerate(act_batch):
                assert len(act_sub_batch) == len(ex_batch)
                for sub_samp_idx, act_sub_samp in enumerate(act_sub_batch):
                    ex_sub_samp = ex_batch[sub_samp_idx][sub_batch_idx]
                    try:
                        assert np.allclose(ex_sub_samp, act_sub_samp)
                    except TypeError:
                        assert ex_samp == act_samp
            batch_start += len(ex_batch)
        assert batch_start == len(samples)


def test_padding():
    samples = [([1], [2], [3]), ([4, 5], [6, 7]), ([8], [9])]
    l1_batches = tuple(corpus.batch_data(
        samples, subsamples=False, batch_size=1, pad_mode='maximum',
        cast_to_array=np.int32,
    ))
    assert len(l1_batches) == 3
    assert np.allclose(l1_batches[0], [[1], [2], [3]])
    assert np.allclose(l1_batches[1], [[4, 5], [6, 7]])
    assert np.allclose(l1_batches[2], [[8], [9]])
    l2_batches = tuple(corpus.batch_data(
        samples, subsamples=False, batch_size=2, pad_mode='maximum',
        cast_to_array=np.int32,
    ))
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
        samples, subsamples=False, batch_size=3, pad_mode='wrap',
        cast_to_array=np.int32,
    ))
    assert len(l3_batches) == 1
    assert np.allclose(
        l3_batches[0],
        [
            [[1, 1], [2, 2], [3, 3]],
            [[4, 5], [6, 7], [4, 5]],
            [[8, 8], [9, 9], [8, 8]],
        ]
    )
    # if we do not set cast_to_array, no padding should occur
    no_cast_batches = tuple(corpus.batch_data(
        samples, subsamples=False, batch_size=3, pad_mode='wrap'))
    assert len(no_cast_batches) == 1
    assert no_cast_batches[0] == samples


class NonRandomState(np.random.RandomState):
    '''Replace the shuffle method with returning a reverse-sorted copy

    Experts agree that this style of shuffling is, objectively, *too*
    random to be considered random
    '''

    def shuffle(self, array):
        super(NonRandomState, self).shuffle(array)
        array[::-1] = np.sort(array)


def test_shuffled_data_basic(temp_file_1_name):
    samples = np.arange(100000).reshape((10, 200, 50)).astype(
        np.float64 if KaldiDataType.BaseMatrix.is_double else np.float32)
    keys = tuple(str(i) for i in range(10))
    with io_open('ark:' + temp_file_1_name, 'bm', mode='w') as f:
        for key, sample in zip(keys, samples):
            f.write(key, sample)
    data = corpus.ShuffledData(
        'ark:' + temp_file_1_name, batch_size=3, rng=NonRandomState())
    assert isinstance(data.rng, NonRandomState)
    assert len(data) == int(np.ceil(len(keys) / 3))
    assert keys == tuple(data.key_list)
    for _ in range(2):
        ex_samp_idx = len(samples)
        for batch in data:
            for act_sample in batch:
                ex_samp_idx -= 1
                assert np.allclose(samples[ex_samp_idx], act_sample)


@pytest.mark.parametrize('seed', [1234, 4321])
def test_seeded_shuffled_is_predictable(temp_file_1_name, seed):
    samples = np.arange(100000).reshape((1000, 100)).astype(np.float32)
    with io_open('ark:' + temp_file_1_name, 'fv', mode='w') as f:
        for idx, sample in enumerate(samples):
            f.write(str(idx), sample)
    data_1 = corpus.ShuffledData(
        ('ark:' + temp_file_1_name, 'fv'), batch_size=13, rng=seed)
    data_2 = corpus.ShuffledData(
        ('ark:' + temp_file_1_name, 'fv'), batch_size=13, rng=seed)
    for _ in range(2):
        for batch_1, batch_2 in zip(data_1, data_2):
            assert np.allclose(batch_1, batch_2)


def test_shuffled_data_tups(temp_file_1_name, temp_file_2_name):
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
            io_open('ark:' + temp_file_2_name, 'dm', mode='w') as lab_f:
        for key, feat, label in zip(keys, feats, labels):
            feat_f.write(key, feat)
            lab_f.write(key, label)
    data = corpus.ShuffledData(
        ('ark:' + temp_file_1_name, 'ivv'), ('ark:' + temp_file_2_name, 'dm'),
        batch_size=2, batch_pad_mode='constant',
        key_list=keys, axis_lengths=1, rng=NonRandomState(),
        batch_cast_to_array=(np.int32, None, None))
    for _ in range(2):
        ex_samp_idx = len(feats)
        for feat_batch, _, len_batch in data:
            for act_feat, act_len in zip(feat_batch, len_batch):
                ex_samp_idx -= 1
                ex_feat = np.array(feats[ex_samp_idx], copy=False)
                ex_len = ex_feat.shape[1]
                assert ex_len == act_len
                assert np.allclose(ex_feat, act_feat[:, :ex_len])
                assert np.allclose(act_feat[:, ex_len:], 0)
    data = corpus.ShuffledData(
        ('ark:' + temp_file_1_name, 'ivv'), ('ark:' + temp_file_2_name, 'dm'),
        batch_size=3, batch_pad_mode='constant',
        key_list=keys, axis_lengths=((1, 1), (0, 1)), rng=NonRandomState(),
        batch_cast_to_array=(np.int32, None, None, None))
    for _ in range(2):
        ex_samp_idx = len(feats)
        for feat_batch, label_batch, lablen_batch, featlen_batch in data:
            for act_feat, act_label, act_lablen, act_featlen in zip(
                    feat_batch, label_batch, lablen_batch, featlen_batch):
                ex_samp_idx -= 1
                ex_feat = np.array(feats[ex_samp_idx], copy=False)
                ex_label = labels[ex_samp_idx]
                ex_featlen = ex_feat.shape[1]
                ex_lablen = ex_label.shape[1]
                assert ex_featlen == act_featlen
                assert ex_lablen == act_lablen
                assert np.allclose(ex_feat, act_feat[:, :ex_featlen])
                assert np.allclose(act_feat[:, ex_featlen:], 0)
                assert np.allclose(ex_label, act_label[:, :ex_lablen])
                assert np.allclose(act_label[:, ex_lablen:], 0)


def test_shuffled_ignore_missing(temp_file_1_name, temp_file_2_name):
    with io_open('ark:' + temp_file_1_name, 't', mode='w') as token_f:
        token_f.write('1', 'cool')
        token_f.write('3', 'bean')
        token_f.write('4', 'casserole')
    keys = [str(i) for i in range(6)]
    data = corpus.ShuffledData(
        ('ark:' + temp_file_1_name, 't'), key_list=keys, ignore_missing=True,
        rng=NonRandomState())
    assert len(data) == 3
    act_samples = list(data)
    assert all(ex == act for ex, act in zip(
        ['casserole', 'bean', 'cool'], act_samples))
    with io_open('ark:' + temp_file_2_name, 'B', mode='w') as bool_f:
        bool_f.write('0', True)
        bool_f.write('1', False)
        bool_f.write('2', True)
        bool_f.write('4', False)
    data = corpus.ShuffledData(
        ('ark:' + temp_file_1_name, 't'), ('ark:' + temp_file_2_name, 'B'),
        key_list=keys, ignore_missing=True, rng=NonRandomState())
    assert len(data) == 2
    act_tok_samples, act_bool_samples = list(zip(*iter(data)))
    assert all(ex == act for ex, act in zip(
        ['casserole', 'cool'], act_tok_samples))
    assert all(not act for act in act_bool_samples)


def test_sequential_basic(temp_file_1_name):
    samples = np.arange(1000).reshape((10, 100)).astype(np.int32)
    with io_open('ark:' + temp_file_1_name, 'iv', mode='w') as f:
        for idx, sample in enumerate(samples):
            f.write(str(idx), sample)
    data = corpus.SequentialData(
        ('ark,s:' + temp_file_1_name, 'iv'), batch_size=3)
    assert len(data) == 4
    batch_start = 0
    for act_batch in data:
        ex_batch = samples[batch_start:batch_start + 3]
        assert np.allclose(ex_batch, act_batch)
        batch_start += len(ex_batch)
    assert batch_start == len(samples)


def test_sequential_data_tups(temp_file_1_name, temp_file_2_name):
    feats = np.random.random((4, 10, 100)).astype(np.float64)
    labels = [
        ('foo',), ('bar', 'baz',),
        ('bingo',), ('bango', 'bongo', 'eugene'),
    ]
    with io_open('ark:' + temp_file_1_name, 'dm', mode='w') as feats_f, \
            io_open('ark:' + temp_file_2_name, 'tv', mode='w') as labels_f:
        for idx, (feat, label) in enumerate(zip(feats, labels)):
            feats_f.write(str(idx), feat)
            labels_f.write(str(idx), label)
    data = corpus.SequentialData(
        ('ark,s:' + temp_file_1_name, 'dm'),
        ('ark,s:' + temp_file_2_name, 'tv'), axis_lengths=0)
    batch_start = 0
    for ex_feat, ex_label, (act_feat, act_label, act_len) in zip(
            feats, labels, data):
        assert np.allclose(ex_feat, act_feat)
        assert ex_label == act_label
        assert act_len == 10
        batch_start += 1
    assert batch_start == len(feats)
    assert len(data) == batch_start


def test_sequential_ignore_missing(temp_file_1_name, temp_file_2_name):
    with io_open('ark:' + temp_file_1_name, 'ipv', mode='w') as pair_f:
        pair_f.write('10', [(10, 9), (8, 7), (6, 5)])
        pair_f.write('11', [(11, 10), (9, 8)])
        pair_f.write('12', [(12, 11)])
        pair_f.write('14', [])
    with io_open('ark:' + temp_file_2_name, 'd', mode='w') as double_f:
        double_f.write('09', 3.14)
        double_f.write('10', .159)
        double_f.write('12', .265)
        double_f.write('13', .357)
    data = corpus.SequentialData(
        ('ark,s:' + temp_file_1_name, 'ipv'),
        ('ark,s:' + temp_file_2_name, 'd'), ignore_missing=True)
    act_pair_samples, act_double_samples = list(zip(*iter(data)))
    assert act_pair_samples == (
        ((10, 9), (8, 7), (6, 5)),
        ((12, 11),)
    )
    assert np.allclose(act_double_samples, (.159, .265))
