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
from itertools import cycle

import numpy as np

from pydrobert.kaldi.io import open as io_open
from pydrobert.kaldi.io.enums import RxfilenameType
from pydrobert.kaldi.io.util import parse_kaldi_input_path

__all__ = [
    'batch_data',
    'TrainingData',
]


def _handle_sub_batch(sub_batch, axis, pad_mode, pad_kwargs):
    '''Put together a sub-batch according to the rules outlined in batch_data\
    '''
    assert len(sub_batch)
    try:
        first_dtype = sub_batch[0].dtype
        first_shape = sub_batch[0].shape
    except AttributeError:
        return sub_batch
    mismatched_shapes = False
    max_shape = first_shape
    for sample in sub_batch:
        if not isinstance(sample, (np.ndarray, np.generic)) or (
                not np.issubdtype(sample.dtype, first_dtype)):
            return sub_batch
        if sample.shape != first_shape:
            if pad_mode:
                max_shape = (
                    max(x, y) for x, y in zip(sample.shape, max_shape))
                mismatched_shapes = True
            else:
                return sub_batch
    if mismatched_shapes:
        max_shape = tuple(max_shape)
        for samp_idx in range(len(sub_batch)):
            sample = sub_batch[samp_idx]
            if sample.shape != max_shape:
                pad_widths = tuple(
                    (0, y - x) for x, y in zip(sample.shape, max_shape))
                sample = np.pad(
                    sample,
                    pad_widths,
                    mode=pad_mode,
                    **pad_kwargs
                )
                sub_batch[samp_idx] = sample
    ret = np.stack(sub_batch, axis=axis)
    return ret


def batch_data(
        input_iter, in_tup=True, batch_size=None, axis=0,
        cast_to_array=None, pad_mode=None, **pad_kwargs):
    '''Generate batched data from an input generator

    Takes some fixed number of samples from ``input_iter``, encapsulates
    them, and yields them.

    If ``in_tup`` is ``True``, data from ``input_iter`` are expected to
    be encapsulated in fixed-length sequences (e.g. (feat, label,
    len)). Each sample will be batched separately into a sub-batch
    and returned in a tuple (e.g. (feat_batch, label_batch, len_batch)).

    The format of a (sub-)batch depends on the properties of its
    samples:
    1. If ``cast_to_array`` applies to this sub-batch (see Parameters),
       cast it to a numpy array of the target type.
    2. If all samples in the (sub-)batch are numpy arrays of the same
       type and shape, samples are stacked in a bigger numpy array
       along the axis specified by ``axis`` (see Parameters).
    3. If all samples are numpy arrays of the same type but variable
       length and `pad_mode` is specified, pad all sample arrays to
       the right such that they all have the same (supremum) shape, then
       perform 2.
    4. Otherwise, simply return a list of samples as-is (ignoring axis).

    Parameters
    ----------
    input_iter :
        An iterator over samples
    in_tup : bool
    batch_size : int, optional
        The size of batches, except perhaps the last one. If not set or
        0, will yield samples (casting and encapsulating in tuples when
        necessary).
    axis : int or sequence
        Where to insert the batch index/indices into the shape/shapes of
        the inputs. If a sequence, in_tup must be True and input_iter
        should yield samples of the same length as axis. If an int and
        in_tup is True, the same axis will be used for all sub-samples.
    cast_to_array : numpy.dtype or sequence, optional
        Dictates whether data should be cast to numpy arrays and of
        what type. If a sequence, in_tup must be True and input_iter
        should yield samples of the same length as cast_to_array. If a
        single value and in_tup is True, the same value will be used
        for all sub-samples. Value(s) of None indicate no casting should
        be done for this (sub-)sample. Other values will be used to cast
        (sub-)samples to numpy arrays.
    pad_mode : str or function, optional
        If set, inputs within a batch will be padded on the end to
        match the largest shapes in the batch. How the inputs are
        padded matches the argument to ``numpy.pad``. If not set, will
        raise a ValueError if they don't all have the same shape
    pad_kwargs : Keyword arguments, optional
        Additional keyword arguments are passed along to ``numpy.pad``
        if padding.

    See Also
    --------
    numpy.pad
        For different pad modes and options
    '''
    num_sub = None
    if in_tup:
        try:
            axis = tuple(axis)
            num_sub = len(axis)
        except TypeError:  # one value
            axis = (axis,)
        try:
            cast_to_array = tuple(cast_to_array)
            if num_sub is None:
                num_sub = len(cast_to_array)
            elif len(cast_to_array) != num_sub:
                raise ValueError(
                    'axis and cast_to_array should be of the same '
                    'length if both sequences (got {} and {} resp)'.format(
                        num_sub, len(cast_to_array)))
        except TypeError:
            cast_to_array = (cast_to_array,)
    if not batch_size:
        # ideally we factor this out into some helper, but py2.7 doesn't
        # have yield-from syntax
        for sample in input_iter:
            if in_tup:
                sample = tuple(sample)
                if num_sub is None:
                    num_sub = len(sample)
                elif num_sub != len(sample):
                    raise ValueError(
                        'Expected {} sub-samples per sample, got {}'.format(
                            num_sub, len(sample)))
                if cast_to_array != (None,):
                    yield tuple(
                        np.array(
                            sub_sample, dtype=cast_to_array[0], copy=False)
                        for sub_sample in sample)
                else:
                    yield sample
            elif cast_to_array is not None:
                yield np.array(sample, dtype=cast_to_array[0], copy=False)
            else:
                yield sample
        return
    cur_batch = []
    cur_batch_size = 0
    for sample in input_iter:
        if in_tup:
            for sub_batch_idx, (sub_sample, sub_cast) in enumerate(
                    zip(sample, cycle(cast_to_array))):
                if sub_cast is not None:
                    sub_sample = np.array(
                        sub_sample, dtype=sub_cast, copy=False)
                if len(cur_batch) == sub_batch_idx:
                    cur_batch.append([sub_sample])
                else:
                    cur_batch[sub_batch_idx].append(sub_sample)
            if num_sub is None:
                num_sub = len(cur_batch)
            elif num_sub != len(cur_batch):
                raise ValueError(
                    'Expected {} sub-samples per sample, got {}'.format(
                        num_sub, len(cur_batch)))
        else:
            if cast_to_array is not None:
                sample = np.array(sample, dtype=cast_to_array, copy=False)
            cur_batch.append(sample)
        cur_batch_size += 1
        if cur_batch_size == batch_size:
            if in_tup:
                yield tuple(
                    _handle_sub_batch(
                        sub_batch, sub_axis, pad_mode, pad_kwargs)
                    for sub_batch, sub_axis in zip(cur_batch, cycle(axis))
                )
            else:
                yield _handle_sub_batch(cur_batch, axis, pad_mode, pad_kwargs)
            cur_batch_size = 0
            cur_batch = []
    if cur_batch_size:
        if in_tup:
            yield tuple(
                _handle_sub_batch(
                    sub_batch, sub_axis, pad_mode, pad_kwargs)
                for sub_batch, sub_axis in zip(cur_batch, cycle(axis))
            )
        else:
            yield _handle_sub_batch(cur_batch, axis, pad_mode, pad_kwargs)


class Data(Iterable):
    '''Metaclass for data iterables

    A template for providing iterators over kaldi tables. They can be
    used like this::

    >>> data = DataSubclass(
        'scp:feats.scp', 'scp:labels.scp', batch_size=10)
    >>> for feat_batch, label_batch in data:
    >>>     pass  # do something
    >>> for feat_batch, label_batch in data:
    >>>     pass  # do something again

    Where `DataSubclass` is some subclass of this virtual class. Calling
    iter() on this class (which occurs implicitly in for-loops) will
    generate a new iterator over the entire data set.

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

    All tables are assumed to index data using the same keys.

    If ``batch_size`` is set, data are stacked in batches along a new
    axis. The keyword arguments ``batch_axis``, ``batch_pad_mode``, and
    any remaining keywords are sent to this module's ``batch_data``
    function. If ``batch_size`` is None or zero, samples are returned
    one-by-one. Data are always cast to numpy arrays before being
    returned. Consult that function for more information on batching.

    If only one table is specified and neither ``add_axis_len`` or
    ``add_key`` is specified, iterators will be of a batch of the
    table's data directly. Otherwise, iterators yield "batches" of
    tuples containing "sub-batches" from each respective data source.
    Sub-batches belonging to the same batch share the same subset of
    ordered keys.

    If ``add_key`` is ``True``, a sub-batch of referrent keys is added
    as the first element of a batch tuple.

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

    Parameters
    ----------
    table
        The first table specifier
    batch_size : int, optional
        The number of samples per (sub-)batch
    batch_axis : int or sequence
        The axis or axes (in the case of multiple tables) along which
        samples are stacked in (sub-)batches. batch_axis should take
        into account axis length and key sub-batches when applicable.
        Defaults to 0
    batch_cast_to_array : dtype or sequence, optional
        A numpy type or sequence of types to cast each (sub-)batch to.
        ``None`` values indicate no casting should occur.
        batch_cast_to_array should take into acount axis length and
        key sub-batches when applicable.
    batch_pad_mode : str, optional
        If set, pads samples in (sub-)batches according to this
        ``numpy.pad`` strategy when samples do not have the same length
    repeat : bool
        Whether to stop iterating after batches are exhausted (False) or
        to restart the iteration.
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
    in_tup : bool
        If true, indicates that batches are tuples of sub-batches (as
        opposed to direct numpy arrays of batches).
    batch_size : int or None
    batch_axis : int or sequence
    axin_tups :
    batch_pad_mode : str or None
    batch_kwargs : dict
    repeat : bool
    '''
    pass


class TrainingData(Data):
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
        batch_cast_to_array = kwargs.pop('batch_cast_to_array', None)
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
            self._num_samples = None  # will infer when they ask
        else:
            self._num_samples = len(key_list)
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
        self._in_tup = num_yield > 1
        if self._in_tup:
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
            try:
                batch_cast_to_array = tuple(batch_cast_to_array)
                if len(batch_cast_to_array) != num_yield:
                    if len(batch_cast_to_array) == len(table_specifiers):
                        raise ValueError(
                            'Expected batch_cast_to_array length of {}, but '
                            'got length {} (did you remember to account for '
                            'axis-length sub-batches?)'.format(
                                len(batch_cast_to_array), num_yield))
                    else:
                        raise ValueError(
                            'Expected batch_cast_to_array length of {}, but '
                            'got length {} (did you remember to account for '
                            'axis-length sub-batches?)'.format(
                                len(batch_cast_to_array), num_yield))
                self.batch_cast_to_array = batch_cast_to_array
            except TypeError:
                self.batch_cast_to_array = (batch_cast_to_array,) * num_yield
        else:
            self.batch_axis = batch_axis
            self.batch_cast_to_array = batch_cast_to_array
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
                samp_tup.append(handle[key])
            for sub_batch_idx, axis_idx in self._ax_tups:
                samp_tup.append(
                    np.array(
                        samp_tup[sub_batch_idx], copy=False).shape[axis_idx])
            if not missing:
                if self._in_tup:
                    yield tuple(samp_tup)
                else:
                    yield samp_tup[0]

    def __iter__(self):
        return batch_data(
            self.sample_generator(),
            batch_size=self.batch_size,
            axis=self.batch_axis,
            pad_mode=self.batch_pad_mode,
            cast_to_array=self.batch_cast_to_array,
            in_tup=self._in_tup,
            **self.batch_kwargs
        )

    def __len__(self):
        if self._num_samples is None:
            self._num_samples = sum(
                all(key in handle for handle in self.table_handles)
                for key in self.key_list
            )
        if self.batch_size:
            return int(np.ceil(self._num_samples / self.batch_size))
        else:
            return self._num_samples
