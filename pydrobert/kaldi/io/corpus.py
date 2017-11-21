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

from builtins import str as text
from collections import Iterable

import numpy as np

from pydrobert.kaldi.io import open as io_open
from pydrobert.kaldi.io.enums import RxfilenameType
from pydrobert.kaldi.io.util import parse_kaldi_input_path

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
                        sample,
                        pad_widths,
                        mode=pad_mode,
                        **pad_kwargs
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
    pad_kwargs : Keyword arguments, optional
        Additional keyword arguments are passed along to ``numpy.pad``
        if padding.

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
    partition. In a nutshell, you can use it like this:

    >>> train = TrainingData(
        'scp:feats.scp', 'scp:labels.scp', batch_size=10)
    >>> for feat_batch, label_batch in train:
    >>>     pass  # do something
    >>> for feat_batch, label_batch in train:
    >>>     pass  # loop over the data again

    Data are randomized every time the object is looped over. A more
    complex example: suppose you have variable-length features (w.r.t
    axis 0) that you wish to zero-pad to the each batch's maximal
    length. Further, you want to include a sub-batch of the original
    length of features. Also, you want to generate batches ad-infinitum.
    Then your code would look something like this:

    >>> train = TrainingData(
        'scp:feats.scp', 'scp:labels.scp', batch_size=10,
        add_axis_len=0, batch_pad_mode='constant', repeat=True)
    >>> for feat_batch, label_batch, len_batch in train:
    >>>     pass  # do something... forever

    Extended Summary
    ----------------

    The class takes an arbitrary positive number of positional
    arguments on initialization, each a table to open. Each argument is
    one of:

    1. An rspecifier (ideally for a script file). Assumed to be of type
       ``KaldiDataType.BaseMatrix``
    2. A sequence of length 2: the first element is the rspecifier, the
       second the rspecifier's ``KaldiDataType``
    3. A sequence of length 3: the first element is the rspecifier, the
       second the rspecifier's ``KaldiDataType``, and the third is a
       dictionary to be passed as keyword arguments to the ``open``
       function

    All tables are assumed to index data using the same keys. The tables
    are opened in random access mode and samples are retrieved using
    a shuffled list of keys. The list of keys can be specified as a
    keyword argument or, if unspecified, inferred from the first table.
    The latter option requires the table be read through sequentially
    to extract the keys, closed, and reopened as a random access table.
    As such, the list of keys must be provided as an argument if reading
    a table from standard input.

    If only one table is provided (and ``add_axis_len`` is ``None``)
    batches will be iterated over directly. Otherwise, "sub-batches",
    or batches from each table, will be encased in tuples. The iterator
    returns these tuples.

    If ``batch_size`` is set, data are stacked in batches along a new
    axis. The keyword arguments ``batch_axis``, ``batch_pad_mode``, and
    any dynamic keywords are sent to this module's ``batch_data``
    function. If ``batch_size`` is None or zero, samples are returned
    one-by-one. Data are always cast to numpy arrays before being
    returned. Consult that function for more information on batching.

    For batched sequence-to-sequence tasks, it is often important to
    know the original length of data before padding. Setting
    ``add_axis_len`` adds one or more sub-batches to the end of a
    batch tuple with this information. These sub-batches are filled
    with signed 32-bit integers. ``add_axis_len`` can be one of:

    1. An integer specifying an axis from the first table to get the
       lengths of.
    2. A pair of integers. The first element is the table index, the
       second is the axis index in that table.
    3. A sequence of pairs of integers. Sub-batches will be appended
       to the batch tuple in that order

    Note that axes in ``add_axis_len`` index the axes in individual
    samples, not the batch. For instance, if ``batch_axis == 0`` and
    ``add_axis_len == 0``, then the last sub-batch will refer to the
    pre-padded value of sub-batch 0's axis 1 (``batch[0].shape[1]``).

    The length of this object is the total number of batches it will
    serve.

    Parameters
    ----------
    table
        The first table specifier
    key_list : sequence, optional
        All the keys to be found in tables. If unspecified, keys will
        be inferred from the first table
    batch_size : int, optional
        The number of samples per (sub-)batch
    batch_axis : int or sequence
        The axis or axes (in the case of multiple tables) along which
        samples are stacked in (sub-)batches. batch_axis should take
        into account axis length sub-batches. Defaults to 0
    batch_pad_mode : str, optional
        If set, pads samples in (sub-)batches according to this
        ``numpy.pad`` strategy when samples do not have the same length
    rng : int or numpy.random.RandomState, optional
        Either a ``RandomState`` object or a seed to create one. Used
        when shuffling samples
    repeat : bool
        Whether to stop iterating after batches are exhausted (False) or
        to randomize and do it again forever. Defaults to False
    ignore_missing : bool
        If True and some provided table does not have some key, that
        key will simply be ignored. Otherwise, a missing key raises a
        ValueError. Default to False
    add_axis_len : int or sequence, optional
        If set, sub-batches of axis lengths will be appended to the end
        of a batch tuple
    additional_tables : Arguments, optional
        Table specifiers past the first. If not empty, will iterate over
        tuples of sub-batches
    batch_kwargs : Keyword arguments, optional
        Additional keyword arguments to pass to ``batch_data``

    Attributes
    ----------
    table_specifiers : sequence
        A tuple of triples indicating of rspecifier, kaldi_dtype, and
        open_kwargs for each table
    table_handles : sequence
        The tables, opened in random access mode
    key_list : sequence
    batch_size : int or None
    batch_axis : int or sequence
        If iterators return tuples (more than one table or an axis
        length has been added), this will always be a sequence
    batch_kwargs : dict
    repeat : bool
    rng : numpy.random.RandomState
    ignores_missing : bool
    '''

    def __init__(self, *tables, **kwargs):
        if not len(tables):
            raise TypeError('__init__() takes at least 2 arguments (1 given)')
        self.batch_size = kwargs.pop('batch_size', None)
        self.batch_pad_mode = kwargs.pop('batch_pad_mode', None)
        self.repeat = bool(kwargs.pop('repeat', False))
        self._ignore_missing = bool(kwargs.pop('ignore_missing', False))
        key_list = kwargs.pop('key_list', None)
        batch_axis = kwargs.pop('batch_axis', 0)
        rng = kwargs.pop('rng', None)
        add_axis_len = kwargs.pop('add_axis_len', None)
        self.batch_kwargs = kwargs
        table_specifiers = []
        for table_spec in tables:
            if isinstance(table_spec, str) or isinstance(table_spec, text):
                table_spec = (table_spec, 'bm', dict())
            elif len(table_spec) == 2:
                table_spec += (dict(),)
            elif len(table_spec) != 3:
                raise ValueError('Invalid table spec {}'.format(table_spec))
            table_specifiers.append(table_spec)
        self.table_specifiers = tuple(table_specifiers)
        if not key_list:
            _, _, rx_type, _ = parse_kaldi_input_path(table_specifiers[0][0])
            if rx_type == RxfilenameType.StandardInput:
                raise IOError('Cannot reopen stdin after keys are inferred')
            with io_open(
                    table_specifiers[0][0], table_specifiers[0][1], mode='r',
                    **table_specifiers[0][2]) as tab_f:
                key_list = tuple(tab_f.keys())
        else:
            key_list = tuple(key_list)
        self.key_list = key_list
        if self._ignore_missing:
            self._len = None  # will infer when they ask
        else:
            self._len = len(key_list)
        if add_axis_len is None:
            self._ax_tups = tuple()
        elif isinstance(add_axis_len, int):
            self._ax_tups = ((0, add_axis_len),)
        else:
            add_axis_len = tuple(add_axis_len)  # in case generator
            if len(add_axis_len) == 2 and \
                    isinstance(add_axis_len[0], int) and \
                    isinstance(add_axis_len[1], int):
                self._ax_tups = (add_axis_len,)
            else:
                self._ax_tups = add_axis_len
        num_yield = len(self._ax_tups) + len(table_specifiers)
        self._is_tup = num_yield > 1
        if self._is_tup:
            if isinstance(batch_axis, int):
                if len(self._ax_tups) and (
                        batch_axis > 1 or batch_axis < -1):
                    raise ValueError(
                        "batch_axis value {} invalid for axis-length "
                        "sub-batches. Specify all {} batch axes explicitly."
                        "".format(batch_axis, num_yield))
                self.batch_axis = (batch_axis,) * num_yield
            else:
                batch_axis = tuple(batch_axis)
                if len(batch_axis) != num_yield:
                    if len(batch_axis) == len(table_specifiers):
                        raise ValueError(
                            'Expected batch_axis length of {}, but got length '
                            '{} (did you remember to account for axis-length '
                            'sub-batches?)'.format(len(batch_axis), num_yield))
                    else:
                        raise ValueError(
                            'Expected batch_axis length of {}, but got length '
                            '{}'.format(len(batch_axis), num_yield))
                self.batch_axis = batch_axis
        else:
            self.batch_axis = batch_axis
        if isinstance(rng, np.random.RandomState):
            self.rng = rng
        else:
            self.rng = np.random.RandomState(rng)
        self.table_handles = tuple(
            io_open(rspec, dtype, mode='r+', **kwargs)
            for rspec, dtype, kwargs in self.table_specifiers
        )

    @property
    def ignores_missing(self):
        '''bool : does this iterator ignore missing keys or throw an error'''
        return self._ignore_missing

    def sample_generator(self):
        '''Yields shuffled samples'''
        shuffled_keys = np.array(self.key_list)
        self.rng.shuffle(shuffled_keys)
        for key in shuffled_keys:
            samp_tup = []
            missing = False
            for spec, handle in zip(self.table_specifiers, self.table_handles):
                if key not in handle:
                    if self._ignore_missing:
                        missing = True
                        break
                    else:
                        raise ValueError(
                            'Table {} missing key {}'.format(spec[0], key))
                samp_tup.append(np.array(handle[key], copy=False))
            for sub_batch_idx, axis_idx in self._ax_tups:
                samp_tup.append(samp_tup[sub_batch_idx].shape[axis_idx])
            if not missing:
                if self._is_tup:
                    yield tuple(samp_tup)
                else:
                    yield samp_tup[0]

    def __iter__(self):
        return batch_data(
            self.sample_generator(),
            batch_size=self.batch_size,
            axis=self.batch_axis,
            pad_mode=self.batch_pad_mode,
            is_tup=self._is_tup,
            **self.batch_kwargs
        )

    def __len__(self):
        if self._len is None:
            self._len = sum(
                all(key in handle for handle in self.table_handles)
                for key in self.key_list
            )
        return self._len
