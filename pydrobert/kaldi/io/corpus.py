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

from abc import abstractmethod
from builtins import str as text
try:
    from collections.abc import Iterable
    from collections.abc import Sized
except ImportError:
    from collections import Iterable
    from collections import Sized
from itertools import cycle
from warnings import warn

import numpy as np

from pydrobert.kaldi.io import open as io_open
from pydrobert.kaldi.io.enums import RxfilenameType
from pydrobert.kaldi.io.util import parse_kaldi_input_path

__all__ = [
    'batch_data',
    'Data',
    'ShuffledData',
    'SequentialData',
]


def _handle_sub_batch(sub_batch, axis, pad_mode, pad_kwargs):
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
        input_iter, subsamples=True, batch_size=None, axis=0,
        cast_to_array=None, pad_mode=None, **pad_kwargs):
    '''Generate batched data from an input generator

    Takes some fixed number of samples from `input_iter`, encapsulates
    them, and yields them.

    If `subsamples` is ``True``, data from `input_iter` are expected to
    be encapsulated in fixed-length sequences (e.g. ``(feat, label,
    len)``). Each sample will be batched separately into a sub-batch
    and returned in a tuple (e.g. ``(feat_batch, label_batch,
    len_batch)``).

    The format of a (sub-)batch depends on the properties of its
    samples:

    1. If `cast_to_array` applies to this sub-batch, cast it to a numpy
       array of the target type.
    2. If all samples in the (sub-)batch are numpy arrays of the same
       type and shape, samples are stacked in a bigger numpy array
       along the axis specified by `axis` (see Parameters).
    3. If all samples are numpy arrays of the same type but variable
       length and `pad_mode` is specified, pad all sample arrays to
       the right such that they all have the same (supremum) shape, then
       perform 2.
    4. Otherwise, simply return a list of samples as-is (ignoring axis).

    Parameters
    ----------
    input_iter :
        An iterator over samples
    subsamples : bool, optional
        `input_iter` yields tuples to be divided into different
        sub-batches if ``True``
    batch_size : int, optional
        The size of batches, except perhaps the last one. If not set or
        ``0``, will yield samples (casting and encapsulating in tuples
        when necessary)
    axis : int or sequence, optional
        Where to insert the batch index/indices into the shape/shapes of
        the inputs. If a sequence, `subsamples` must be ``True`` and
        `input_iter` should yield samples of the same length as axis. If
        an ``int`` and subsamples is ``True``, the same axis will be
        used for all sub-samples.
    cast_to_array : numpy.dtype or sequence, optional
        Dictates whether data should be cast to numpy arrays and of
        what type. If a sequence, `subsamples` must be ``True`` and
        `input_iter` should yield samples of the same length as
        `cast_to_array`. If a single value and `subsamples` is ``True``,
        the same value will be used for all sub-samples. Value(s) of
        ``None`` indicate no casting should be done for this
        (sub-)sample. Other values will be used to cast (sub-)samples to
        numpy arrays
    pad_mode : str or function, optional
        If set, inputs within a batch will be padded on the end to
        match the largest shapes in the batch. How the inputs are
        padded matches the argument to ``numpy.pad``. If not set, will
        raise a ``ValueError`` if they don't all have the same shape
    pad_kwargs : Keyword arguments, optional
        Additional keyword arguments are passed along to ``numpy.pad``
        if padding.

    See Also
    --------
    numpy.pad
        For different pad modes and options
    '''
    num_sub = None
    if subsamples:
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
            if subsamples:
                sample = tuple(sample)
                if num_sub is None:
                    num_sub = len(sample)
                elif num_sub != len(sample):
                    raise ValueError(
                        'Expected {} sub-samples per sample, got {}'.format(
                            num_sub, len(sample)))
                if cast_to_array[0] is not None:
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
        if subsamples:
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
            if subsamples:
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
        if subsamples:
            yield tuple(
                _handle_sub_batch(
                    sub_batch, sub_axis, pad_mode, pad_kwargs)
                for sub_batch, sub_axis in zip(cur_batch, cycle(axis))
            )
        else:
            yield _handle_sub_batch(cur_batch, axis, pad_mode, pad_kwargs)


class Data(Iterable, Sized):
    '''Metaclass for data iterables

    A template for providing iterators over kaldi tables. They can be
    used like this

    >>> data = DataSubclass(
    ...     'scp:feats.scp', 'scp:labels.scp', batch_size=10)
    >>> for feat_batch, label_batch in data:
    >>>     pass  # do something
    >>> for feat_batch, label_batch in data:
    >>>     pass  # do something again

    Where ``DataSubclass`` is some subclass of this virtual class.
    Calling ``iter()`` on an instance (which occurs implicitly in
    for-loops) will generate a new iterator over the entire data set.

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

    If `batch_size` is set, data are stacked in batches along a new
    axis. The keyword arguments `batch_axis`, `batch_pad_mode`, and
    any remaining keywords are sent to this module's ``batch_data``
    function. If `batch_size` is ``None`` or ``0``, samples are returned
    one-by-one. Data are always cast to numpy arrays before being
    returned. Consult that function for more information on batching.

    If only one table is specified and neither `axis_lengths` or
    `add_key` is specified, iterators will be of a batch of the
    table's data directly. Otherwise, iterators yield "batches" of
    tuples containing "sub-batches" from each respective data source.
    Sub-batches belonging to the same batch share the same subset of
    ordered keys.

    If `add_key` is ``True``, a sub-batch of referrent keys is added
    as the first element of a batch tuple.

    For batched sequence-to-sequence tasks, it is often important to
    know the original length of data before padding. Setting
    `axis_lengths` adds one or more sub-batches to the end of a
    batch tuple with this information. These sub-batches are filled
    with signed 32-bit integers. `axis_lengths` can be one of:

    1. An integer specifying an axis from the first table to get the
       lengths of.
    2. A pair of integers. The first element is the table index, the
       second is the axis index in that table.
    3. A sequence of pairs of integers. Sub-batches will be appended
       to the batch tuple in that order

    Note that axes in `axis_lengths` index the axes in individual
    samples, not the batch. For instance, if ``batch_axis == 0`` and
    ``axis_lengths == 0``, then the last sub-batch will refer to the
    pre-padded value of sub-batch 0's axis 1 (``batch[0].shape[1]``).

    The length of this object is the number of batches it serves per
    epoch.

    '''

    _DATA_PARAMS_DOC = '''
    Parameters
    ----------
    table
        The first table specifier
    additional_tables : Arguments, optional
        Table specifiers past the first. If not empty, will iterate over
        tuples of sub-batches
    add_key : bool
        If ``True``, will insert sub-samples into the 0th index of
        each sample sequence that specify the key that this sample was
        indexed by. Defaults to ``False``
    axis_lengths : int or sequence, optional
        If set, sub-batches of axis lengths will be appended to the end
        of a batch tuple
    batch_axis : int or sequence
        The axis or axes (in the case of multiple tables) along which
        samples are stacked in (sub-)batches. batch_axis should take
        into account axis length and key sub-batches when applicable.
        Defaults to ``0``
    batch_cast_to_array : dtype or sequence, optional
        A numpy type or sequence of types to cast each (sub-)batch to.
        ``None`` values indicate no casting should occur.
        `batch_cast_to_array` should take into acount axis length and
        key sub-batches when applicable
    batch_kwargs : Keyword arguments, optional
        Additional keyword arguments to pass to ``batch_data``
    batch_pad_mode : str, optional
        If set, pads samples in (sub-)batches according to this
        ``numpy.pad`` strategy when samples do not have the same length
    batch_size : int, optional
        The number of samples per (sub-)batch. Defaults to ``None``,
        which means samples are served without batching
    ignore_missing : bool, optional
        If ``True`` and some provided table does not have some key, that
        key will simply be ignored. Otherwise, a missing key raises a
        ValueError. Default to ``False``
    '''

    _DATA_ATTRIBUTES_DOC = '''
    Attributes
    ----------
    num_samples : int
        Total number of samples to serve per epoch
    num_batches : int
        Total number of batches to serve per epoch
    table_specifiers : tuple
        A tuple of triples indicating ``(rspecifier, kaldi_dtype,
        open_kwargs)`` for each table
    add_key : bool
        Whether a sub-batch of table keys has been prepended to existing
        sub-batches
    axis_lengths : tuple
        A tuple of pairs for each axis-length sub-batch requested. Each
        pair is ``(sub_batch_idx, axis)``.
    batch_axis : tuple
        A tuple of length num_sub indicating which axis (sub-)samples
        will be arrayed along in a given (sub-)batch when all
        (sub-)samples are (or are cast to) fixed length numpy arrays of
        the same type
    batch_cast_to_array : tuple
        A tuple of length `num_sub` indicating what numpy types, if any
        (sub-)samples should be cast to. Values of ``None`` indicate
        no casting should be done on that (sub-)sample
    batch_kwargs : dict
        Additional keyword arguments to pass to ``batch_data``
    batch_pad_mode : str or None
        If set, pads samples in (sub-)batches according to this
        ``numpy.pad`` strategy when samples do not have the same length
    batch_size : int or None
        The number of samples per (sub-)batch
    ignore_missing : bool
        If ``True`` and some provided table does not have some key, that
        key will simply be ignored. Otherwise, a missing key raises a
        ValueError
    num_sub : int
        The number of sub-batches per batch. If > 1, batches are
        yielded as tuples of sub-batches. This number accounts for
        key, table, and axis-length sub-batches
    '''

    __doc__ += _DATA_PARAMS_DOC + '\n' + _DATA_ATTRIBUTES_DOC

    def __init__(self, table, *additional_tables, **kwargs):
        table_specifiers = [table]
        table_specifiers += additional_tables
        for table_idx, table_spec in enumerate(table_specifiers):
            if isinstance(table_spec, str) or isinstance(table_spec, text):
                table_spec = (table_spec, 'bm', dict())
            elif len(table_spec) == 2:
                table_spec += (dict(),)
            elif len(table_spec) != 3:
                raise ValueError('Invalid table spec {}'.format(table_spec))
            table_specifiers[table_idx] = table_spec
        self.table_specifiers = tuple(table_specifiers)
        self.add_key = bool(kwargs.pop('add_key', False))
        axis_lengths = kwargs.pop('axis_lengths', None)
        batch_axis = kwargs.pop('batch_axis', 0)
        batch_cast_to_array = kwargs.pop('batch_cast_to_array', None)
        self.batch_pad_mode = kwargs.pop('batch_pad_mode', None)
        self.batch_size = kwargs.pop('batch_size', None)
        self.ignore_missing = bool(kwargs.pop('ignore_missing', False))
        self.batch_kwargs = kwargs
        invalid_kwargs = {'axis', 'cast_to_array', 'pad_mode', 'subsamples'}
        invalid_kwargs &= set(kwargs.keys())
        if invalid_kwargs:
            raise TypeError('Invalid argument {}'.format(invalid_kwargs.pop()))
        if axis_lengths is None:
            self.axis_lengths = tuple()
        elif isinstance(axis_lengths, int):
            self.axis_lengths = ((0, axis_lengths),)
        else:
            axis_lengths = tuple(axis_lengths)  # in case generator
            if len(axis_lengths) == 2 and \
                    isinstance(axis_lengths[0], int) and \
                    isinstance(axis_lengths[1], int):
                self.axis_lengths = (axis_lengths,)
            else:
                self.axis_lengths = tuple(tuple(pair) for pair in axis_lengths)
        self.num_sub = len(table_specifiers) + int(self.add_key)
        self.num_sub += len(self.axis_lengths)
        for attribute_name, variable in (
                ('batch_axis', batch_axis),
                ('batch_cast_to_array', batch_cast_to_array)):
            try:
                variable = tuple(variable)
                if len(variable) != self.num_sub:
                    error_msg = 'Expected {} to be a scalar or '.format(
                        attribute_name)
                    error_msg += 'container of length {}, got {}'.format(
                        self.num_sub, len(variable))
                    if len(variable) >= len(table_specifiers):
                        error_msg += ' (did you forget to account for '
                        error_msg += 'axis_lengths or add_key?)'
                    raise ValueError(error_msg)
                setattr(self, attribute_name, variable)
            except TypeError:
                setattr(self, attribute_name, (variable,) * self.num_sub)

    @property
    @abstractmethod
    def num_samples(self):
        '''int : the number of samples yielded per epoch

        This number takes into account the number of terms missing if
        ``self.ignore_missing == True``
        '''
        pass

    @property
    def num_batches(self):
        '''int : the number of batches yielded per epoch

        This number takes into account the number of terms missing if
        ``self.ignore_missing == True``
        '''
        if self.batch_size:
            return int(np.ceil(self.num_samples / self.batch_size))
        else:
            return self.num_samples

    def __len__(self):
        return self.num_batches

    @abstractmethod
    def sample_generator_for_epoch(self):
        '''A generator which yields individual samples from data for an epoch

        An epoch means one pass through the data from start to finish.
        Equivalent to ``sample_generator(False)``.

        Yields
        ------
        A sample if ``self.num_sub == 1``, otherwise a tuple of
        sub-samples
        '''
        pass

    def sample_generator(self, repeat=False):
        '''A generator which yields individual samples from data

        Parameters
        ----------
        repeat : bool
            Whether to stop generating after one epoch (False) or keep
            restart and continue generating indefinitely

        Yields
        ------
        A sample if ``self.num_sub == 1``, otherwise a tuple of
        sub-samples
        '''
        while True:
            for sample in self.sample_generator_for_epoch():
                yield sample
            if not repeat:
                break

    def batch_generator(self, repeat=False):
        '''A generator which yields batches of data

        Parameters
        ----------
        repeat : bool
            Whether to stop generating after one epoch (False) or keep
            restart and continue generating indefinitely

        Yields
        ------
        A batch if ``self.num_sub == 1``, otherwise a tuple of
        sub-batches. If self.batch_size does not divide an epoch's
        worth of data evenly, the last batch of every epoch will be
        smaller
        '''
        subsamples = self.num_sub != 1
        while True:
            for batch in batch_data(
                    self.sample_generator_for_epoch(),
                    subsamples=subsamples,
                    batch_size=self.batch_size,
                    axis=self.batch_axis if subsamples else self.batch_axis[0],
                    pad_mode=self.batch_pad_mode,
                    cast_to_array=(
                        self.batch_cast_to_array if subsamples else
                        self.batch_cast_to_array[0]),
                    **self.batch_kwargs):
                yield batch
            if not repeat:
                break

    def __iter__(self):
        for batch in self.batch_generator():
            yield batch


class ShuffledData(Data):
    '''Provides iterators over shuffled data

    A master list of keys is either provided by keyword argument or
    inferred from the first table. Every new iterator requested shuffles
    that list of keys and returns batches in that order. Appropriate for
    training data.

    Notes
    -----
        For efficiency, it is highly recommended to use scripts
        to access tables rather than archives.
    '''

    __doc__ += Data._DATA_PARAMS_DOC + '''
    key_list : sequence, optional
        A master list of keys. No other keys will be queried. If not
        specified, the key list will be inferred by passing through the
        first table once
    rng : int or numpy.random.RandomState, optional
        Either a ``RandomState`` object or a seed to create a
        ``RandomState`` object. It will be used to shuffle the list of
        keys

    '''

    __doc__ += '\n' + Data._DATA_ATTRIBUTES_DOC + '''
    key_list : tuple
        The master list of keys
    rng : numpy.random.RandomState
        Used to shuffle the list of keys every epoch
    table_holders : tuple
        A tuple of table readers opened in random access mode

    '''

    def __init__(self, table, *additional_tables, **kwargs):
        key_list = kwargs.pop('key_list', None)
        rng = kwargs.pop('rng', None)
        super(ShuffledData, self).__init__(table, *additional_tables, **kwargs)
        try:
            key_list = tuple(key_list)
        except TypeError:
            pass
        if key_list is None:
            _, rx_fn, rx_type, _ = parse_kaldi_input_path(
                self.table_specifiers[0][0])
            if rx_type == RxfilenameType.InvalidInput:
                raise IOError('Invalid rspecifier {}'.format(rx_fn))
            elif rx_type == RxfilenameType.StandardInput:
                raise IOError(
                    'Cannot infer key list from stdin (cannot reopen)')
            with io_open(*self.table_specifiers[0][:2]) as reader:
                self.key_list = tuple(reader.keys())
        else:
            self.key_list = tuple(key_list)
        if self.ignore_missing:
            self._num_samples = None
        else:
            self._num_samples = len(self.key_list)
        if isinstance(rng, np.random.RandomState):
            self.rng = rng
        else:
            self.rng = np.random.RandomState(rng)
        self.table_handles = tuple(
            io_open(rspecifier, kdtype, mode='r+', **o_kwargs)
            for rspecifier, kdtype, o_kwargs in self.table_specifiers
        )

    @property
    def num_samples(self):
        if self._num_samples is None:
            self._num_samples = 0
            for key in self.key_list:
                missing = False
                for handle in self.table_handles:
                    if key not in handle:
                        missing = True
                        break
                if not missing:
                    self._num_samples += 1
        return self._num_samples

    def sample_generator_for_epoch(self):
        shuffled_keys = np.array(self.key_list)
        self.rng.shuffle(shuffled_keys)
        num_samples = 0
        for key in shuffled_keys:
            samp_tup = []
            missing = False
            for spec, handle in zip(self.table_specifiers, self.table_handles):
                if key not in handle:
                    if self.ignore_missing:
                        missing = True
                        break
                    else:
                        raise IOError(
                            'Table {} missing key {}'.format(spec[0], key))
                samp_tup.append(handle[key])
            if missing:
                continue
            num_samples += 1
            for sub_batch_idx, axis_idx in self.axis_lengths:
                samp_tup.append(
                    np.array(
                        samp_tup[sub_batch_idx], copy=False).shape[axis_idx])
            if self.add_key:
                samp_tup.insert(0, key)
            if self.num_sub != 1:
                yield tuple(samp_tup)
            else:
                yield samp_tup[0]
        if self._num_samples is None:
            self._num_samples = num_samples
        elif self._num_samples != num_samples:
            raise IOError('Different number of samples from last time!')

    sample_generator_for_epoch.__doc__ = Data.num_samples.__doc__


class SequentialData(Data):
    '''Provides iterators to read data sequentially

    Tables are always assumed to be sorted so reading can proceed in
    lock-step.

    Warning
    -------
        Each time an iterator is requested, new sequential readers are
        opened. Be careful with stdin!

    '''

    __doc__ += Data._DATA_PARAMS_DOC + '\n' + Data._DATA_ATTRIBUTES_DOC

    def __init__(self, table, *additional_tables, **kwargs):
        super(SequentialData, self).__init__(
            table, *additional_tables, **kwargs)
        self._num_samples = None
        sorteds = tuple(
            parse_kaldi_input_path(spec[0])[3]['sorted']
            for spec in self.table_specifiers
        )
        if not all(sorteds):
            uns_rspec = self.table_specifiers[sorteds.index(False)][0]
            uns_rspec_split = uns_rspec.split(':')
            uns_rspec_split[0] += ',s'
            sor_rspec = ':'.join(uns_rspec_split)
            warn(
                'SequentialData assumes data are sorted, and "{}" does '
                'not promise to be sorted. To supress this warning, '
                'check that this table is sorted, then add the sorted '
                'flag to this rspecifier ("{}")'.format(
                    uns_rspec, sor_rspec))
        if self.ignore_missing and len(self.table_specifiers) > 1:
            self._sample_generator_for_epoch = self._ignore_epoch
        else:
            self._sample_generator_for_epoch = self._no_ignore_epoch

    def _ignore_epoch(self):
        '''Epoch of samples w/ ignore_missing'''
        iters = tuple(
            io_open(spec[0], spec[1], **spec[2]).items()
            for spec in self.table_specifiers
        )
        num_samples = 0
        num_tabs = len(iters)
        try:
            while True:
                samp_tup = [None] * num_tabs
                high_key = None
                tab_idx = 0
                while tab_idx < num_tabs:
                    if samp_tup[tab_idx] is None:
                        key, value = next(iters[tab_idx])
                        if high_key is None:
                            high_key = key
                        elif high_key < key:
                            # key is further along than keys in
                            # samp_tup. Discard those and keep this
                            samp_tup = [None] * num_tabs
                            samp_tup[tab_idx] = value
                            high_key = key
                            tab_idx = 0
                            continue
                        elif high_key > key:
                            # key is behind high_key. keep pushing this
                            # iterator forward
                            continue
                        samp_tup[tab_idx] = value
                    tab_idx += 1
                num_samples += 1
                for sub_batch_idx, axis_idx in self.axis_lengths:
                    samp_tup.append(
                        np.array(
                            samp_tup[sub_batch_idx],
                            copy=False).shape[axis_idx])
                if self.add_key:
                    samp_tup.insert(0, key)
                if self.num_sub != 1:
                    yield tuple(samp_tup)
                else:
                    yield samp_tup[0]
        except StopIteration:
            pass
        # don't care if one iterator ends first - rest will be missing
        # that iterator's value
        if self._num_samples is None:
            self._num_samples = num_samples
        elif self._num_samples != num_samples:
            raise IOError(
                'Different number of samples from last time! (is a '
                'table from stdin?)')

    def _no_ignore_epoch(self):
        '''Epoch of samples w/o ignore_missing'''
        iters = tuple(
            io_open(spec[0], spec[1], **spec[2]).items()
            for spec in self.table_specifiers
        )
        num_samples = 0
        for kv_pairs in zip(*iters):
            samp_tup = []
            past_key = None
            for tab_idx, (key, sample) in enumerate(kv_pairs):
                if past_key is None:
                    past_key = key
                elif past_key != key:
                    # assume sorted, base on which is first
                    if past_key < key:
                        miss_rspec = self.table_specifiers[tab_idx][0]
                        miss_key = past_key
                    else:
                        miss_rspec = self.table_specifiers[tab_idx - 1][0]
                        miss_key = key
                    raise IOError(
                        'Table {} missing key {} (or tables are sorted '
                        'differently)'.format(miss_rspec, miss_key))
                samp_tup.append(sample)
            num_samples += 1
            for sub_batch_idx, axis_idx in self.axis_lengths:
                samp_tup.append(
                    np.array(
                        samp_tup[sub_batch_idx], copy=False).shape[axis_idx])
            if self.add_key:
                samp_tup.insert(0, key)
            if self.num_sub != 1:
                yield tuple(samp_tup)
            else:
                yield samp_tup[0]
        # make sure all iterators ended at the same time
        for tab_idx, it in enumerate(iters):
            try:
                miss_key, _ = next(it)
                if tab_idx:
                    miss_rspec = self.table_specifiers[0][0]
                else:
                    miss_rspec = self.table_specifiers[1][0]
                raise IOError(
                    'Table {} missing key {}'.format(miss_rspec, miss_key))
            except StopIteration:
                pass
        if self._num_samples is None:
            self._num_samples = num_samples
        elif self._num_samples != num_samples:
            raise IOError(
                'Different number of samples from last time! (is a '
                'table from stdin?)')

    @property
    def num_samples(self):
        if self._num_samples is None:
            # gets set after you run through an epoch
            assert (
                sum(1 for _ in self.sample_generator_for_epoch()) ==
                self._num_samples)
        return self._num_samples

    def sample_generator_for_epoch(self):
        return self._sample_generator_for_epoch()

    sample_generator_for_epoch.__doc__ = \
        Data.sample_generator_for_epoch.__doc__


try:
    SequentialData.num_samples.__doc__ = Data.num_samples.__doc__
    ShuffledData.num_samples.__doc__ = Data.num_samples.__doc__
except (TypeError, AttributeError):
    pass  # we're in python 2.7 or 3.4 Forget it. Suggestions?
