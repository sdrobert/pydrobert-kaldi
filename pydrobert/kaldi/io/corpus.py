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

'''Submodule for corpus iterators'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import Iterable

import numpy as np

__all__ = [
    'batch_data',
    'TrainingData',
]


def _handle_batch(batch_list, is_tup, axis, pad_mode, pad_kwargs):
    '''Put together a batch for batch_data'''
    if is_tup:
        # split grouped data into their own containers
        # i.e. ((sample_1, sample_2, ...),
        #   (sample_1, sample_2, ...), ...)
        # instead of ((sample_1, sample_1, ...),
        #   (sample_2, sample_2, ...), ...)
        batch_list = tuple(zip(*batch_list))
        if hasattr(axis, '__len__'):
            axes = axis
            if len(axes) != len(batch_list):
                raise ValueError(
                    'axis must be the same length as input tuples')
        else:
            axes = (axis,) * len(batch_list)
    else:
        batch_list = (batch_list,)
        axes = (axis,)
    ret = []
    for sub_batch, axis in zip(batch_list, axes):
        first_shape = sub_batch[0].shape
        if any(len(sample.shape) != len(first_shape) for sample in sub_batch):
            raise ValueError(
                "Batch samples do not all have the same length shape")
        elif any(sample.shape != first_shape for sample in sub_batch):
            if pad_mode is None:
                raise ValueError(
                    "Batch samples do not all have the same shape")
            max_shape = (0,) * len(first_shape)
            for sample in sub_batch:
                max_shape = tuple(
                    max(x, y) for x, y in zip(sample.shape, max_shape))
            new_sub_batch = []
            for sample in sub_batch:
                if sample.shape != max_shape:
                    pad_widths = tuple(
                        (0, y - x) for x, y in zip(sample.shape, max_shape))
                    sample = np.pad(
                        pad_widths,
                        mode=pad_mode,
                        **pad_kwargs,
                    )
                new_sub_batch.append(sample)
            sub_batch = new_sub_batch
        ret.append(np.stack(sub_batch, axis=axis))
    if is_tup:
        return tuple(ret)
    else:
        return ret[0]


def batch_data(
        input_iter, is_tup=True, batch_size=None, axis=0,
        pad_mode=None, **pad_kwargs):
    '''Generate batched data from an input generator

    Parameters
    ----------
    input_iter :
        An iterator over input data
    is_tup : bool
        If True, the data from input-iter is grouped into tuples (e.g.
        (input, label)), which should each be batched separately
    batch_size : int, optional
        The size of batches, except perhaps the last one. If not set,
        this function will not batch, only cast to numpy arrays
    axis : int or sequence
        Where to insert the batch index/indices into the shape/shapes of
        the inputs. If a tuple, is_tup must be True and input_iter
        should yield data of the same length as axis. If an int and
        is_tup is True, the same axis will be used for all inputs.
    pad_mode : str or function, optional
        If set, inputs within a batch will be padded on the end to
        match the largest shapes in the batch. How the inputs are
        padded matches the argument to ``numpy.pad``. If not set, will
        raise a ValueError if they don't all have the same shape

    Additional keyword arguments are passed along to ``numpy.pad``, if
    applicable.

    Yields
    ------
    tuple or np.array
        Either the batch or tuples of batches if len(other_input_shapes)

    Raises
    ------
    ValueError
        On shape errors or invalid axis
    '''
    cur_batch = []
    cur_batch_size = 0
    for elem in input_iter:
        if is_tup:
            elem = tuple(np.array(e, copy=False) for e in elem)
        else:
            elem = np.array(elem, copy=False)
        if batch_size:
            cur_batch.append(elem)
            cur_batch_size += 1
            if cur_batch_size == batch_size:
                yield _handle_batch(
                    cur_batch, is_tup, axis, pad_mode, pad_kwargs)
                cur_batch_size = 0
                cur_batch = []
        else:
            yield elem
    if cur_batch_size:
        yield _handle_batch(cur_batch, is_tup, axis, pad_mode, pad_kwargs)


class TrainingData(Iterable):
    '''Provides iterators over training data

    This class provides a convenient wrapper over tables from a training
    partition. It takes an arbitrary number of arguments, each
    representing a table. Each argument is one of

    1. An rspecifier (ideally for a script file). Assumed to be of type
       ``KaldiDataType.BaseMatrix``
    2. A sequence of length 2: the first element is the rspecifier, the
       second the rspecifier's ``KaldiDataType``
    3. A sequence of length 3: the first element is the rspecifier, the
       second the rspecifier's ``KaldiDataType``, and the third is a
       dictionary to be passed as keyword arguments to the ``open``
       function

    The rspecifiers are expected to refer to the same data.

    Parameters
    ----------

    '''

    def __init__(
            self, *rspec_tups, shuffle=True, batch_size=None,
            batch_axis=0, rng=None, repeat=False, permissive=None,
            **batch_kwargs):
        pass
