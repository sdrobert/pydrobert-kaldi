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

'''Command line entry points and utilities for pydrobert-kaldi'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import logging
import platform
import sys

import numpy as np
import pydrobert.kaldi.io as kaldi_io

from future.utils import raise_from
from pydrobert.kaldi.logging import kaldi_logger_decorator
from pydrobert.kaldi.logging import kaldi_lvl_to_logging_lvl
from pydrobert.kaldi.logging import kaldi_vlog_level_cmd_decorator
from pydrobert.kaldi.logging import register_logger_for_kaldi
from six.moves import cPickle as pickle
from six.moves import shlex_quote

__author__ = "Sean Robertson"
__email__ = "sdrobert@cs.toronto.edu"
__license__ = "Apache 2.0"
__copyright__ = "Copyright 2017 Sean Robertson"

__all__ = [
    'kaldi_rspecifier_arg_type',
    'kaldi_wspecifier_arg_type',
    'kaldi_rxfilename_arg_type',
    'kaldi_wxfilename_arg_type',
    'kaldi_dtype_arg_type',
    'kaldi_bool_arg_type',
    'numpy_dtype_arg_type',
    'KaldiVerbosityAction',
    'KaldiParser',
    'write_table_to_pickle',
    'write_pickle_to_table',
]


def kaldi_rspecifier_arg_type(string):
    '''Make sure string is a valid rspecifier

    Raises
    ------
    argparse.ArgumentTypeError
    '''
    table_type, _, _, _ = kaldi_io.util.parse_kaldi_input_path(string)
    if table_type == kaldi_io.enums.TableType.NotATable:
        raise argparse.ArgumentTypeError('Not a valid rspecifier')
    return string


def kaldi_wspecifier_arg_type(string):
    '''Make sure string is a valid wspecifier

    Raises
    ------
    argparse.ArgumentTypeError
    '''
    table_type, _, _, _ = kaldi_io.util.parse_kaldi_output_path(string)
    if table_type == kaldi_io.enums.TableType.NotATable:
        raise argparse.ArgumentTypeError('Not a valid wspecifier')
    return string


def kaldi_rxfilename_arg_type(string):
    '''Make sure string is a valid extended readable file name

    Raises
    ------
    argparse.ArgumentTypeError
    '''
    table_type, _, rxfilename_type, _ = \
        kaldi_io.util.parse_kaldi_input_path(string)
    if table_type != kaldi_io.enums.TableType.NotATable:
        raise argparse.ArgumentTypeError(
            'Expected an extended file name, got an rspecifier (starts with '
            "'ark:' or 'scp:')")
    elif rxfilename_type == kaldi_io.enums.RxfilenameType.InvalidInput:
        raise argparse.ArgumentTypeError('Not a valid rxfilename')
    return string


def kaldi_wxfilename_arg_type(string):
    '''Make sure string is a valid extended writable file name

    Raises
    ------
    argparse.ArgumentTypeError
    '''
    table_type, _, wxfilename_type, _ = \
        kaldi_io.util.parse_kaldi_output_path(string)
    if table_type != kaldi_io.enums.TableType.NotATable:
        raise argparse.ArgumentTypeError(
            'Expected an extended file name, got an rspecifier (starts with '
            "'ark:' or 'scp:')")
    elif wxfilename_type == kaldi_io.enums.WxfilenameType.InvalidOutput:
        raise argparse.ArgumentTypeError('Not a valid wxfilename')
    return string


def kaldi_dtype_arg_type(string):
    '''Make sure string refers to a KaldiDataType and return it

    Raises
    ------
    argparse.ArgumentTypeError
    '''
    try:
        ret = kaldi_io.enums.KaldiDataType(string)
    except ValueError:
        raise argparse.ArgumentTypeError(
            'Invalid kaldi data type (must be one of {})'.format(
                ','.join(
                    "'{}'".format(x.value)
                    for x in kaldi_io.enums.KaldiDataType)))
    return ret


def kaldi_bool_arg_type(string):
    '''Make sure string is either "true"/"t" or "false"/"f", return bool

    Raises
    ------
    argparse.ArumentTypeError
    '''
    if string in ("true", "t"):
        return True
    elif string in ("false", "f"):
        return False
    else:
        raise argparse.ArgumentTypeError(
            "Must be 'true'/'t' or 'false'/'f'")


def numpy_dtype_arg_type(string):
    '''Make sure string refers to a numpy data type, returns that type

    Raises
    ------
    argparse.ArgumentTypeError
    '''
    try:
        ret = np.dtype(string)
    except TypeError as error:
        raise argparse.ArgumentTypeError(error.message)
    return ret


def parse_kaldi_config_file(file_path, allow_space=True):
    '''Return a list of arguments from a kaldi config file

    Parameters
    ----------
    file_path : str
        Points to the config file in question
    allow_spaces : bool
        If True, treat the first space on a line as splitting key and
        value if no equals sign exists on the line. If false, no equals
        sign will chunk the whole line (as if a boolean flag). Kaldi
        does not split on spaces, but python does. Note that
        allow_spaces does not split the entire line on spaces, unlike
        shell arguments.

    Raises
    ------
    ValueError
        If config file has formatting issues
    '''
    args = []
    with open(file_path) as config_file:
        for line_no, line in enumerate(config_file):
            line = line.split('#')[0].strip()
            if not line:
                continue
            if not line.startswith('--'):
                raise ValueError(
                    'Reading config file {} : line {} does not look '
                    'like a line from a Kaldi command-line program\'s '
                    'config file: should be of the form --x=y. Note: '
                    'config files intended to be sourced by shell '
                    "scripts lack the '--'.".format(file_path, line_no + 1))
            equals_index = line.find('=')
            if equals_index == 2:
                raise ValueError('Invalid option (no key): '.format(line))
            elif allow_space and equals_index == -1:
                space_index = line.find(' ')
                assert space_index != 2
                if space_index == -1:
                    args.append(line)
                else:
                    args.extend([line[:space_index], line[space_index + 1:]])
            else:
                args.append(line)
    return args


def kaldi_config_arg_type(string):
    '''Encapsulate parse_kaldi_config_file as an argument type'''
    try:
        return parse_kaldi_config_file(string)
    except (IOError, ValueError) as error:
        raise_from(argparse.ArgumentTypeError('config file error:'), error)


class KaldiVerbosityAction(argparse.Action):
    '''Read kaldi-style verbosity levels, setting logger to python level

    Kaldi verbosities tend to range from [-3, 9]. This action takes in a kaldi
    verbosity level and converts it to python logging levels with
    `pydrobert.kaldi.logging.kaldi_lvl_to_logging_lvl`

    If the parser has a `logger` attribute, the logger will be set to the new
    level.
    '''

    def __init__(
            self, option_strings, dest, default=logging.INFO, required=False,
            help='Verbose level (higher->more logging)', metavar=None):
        super(KaldiVerbosityAction, self).__init__(
            option_strings, dest, nargs=1, default=default,
            type=int, required=required, help=help, metavar=metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        if values < -3 or values > 9:
            raise argparse.ArgumentTypeError(
                'Verbosity must be between -3 and 9 inclusive')
        logging_lvl = kaldi_lvl_to_logging_lvl(values)
        setattr(namespace, self.dest, logging_lvl)
        if hasattr(parser, 'logger'):
            parser.logger.setLevel(logging_lvl)


class KaldiParser(argparse.ArgumentParser):
    '''Kaldi-compatible wrapper for argument parsing

    KaldiParser intends to make command-line entry points in python more
    compatible with kaldi command-line scripts. It makes the following changes
    to argparse.ArgumentParser:

    1. Creates a logging.Formatter instance that formats messages
       similarly to kaldi using the 'prog' keyword as the program name.
    2. Sets the default help and usage locations to sys.stderr (instead
       of out)
    3. Registers 'kaldi_bool', 'kaldi_rspecifier', 'kaldi_wspecifier',
       'kaldi_wxfilename', 'kaldi_rxfilename', 'kaldi_config',
       'kaldi_dtype', and 'numpy_dtype' as argument types
    4. Registers `kaldi_verbose` a an action
    5. Adds `logger`, `update_formatters`, `add_config`, and `add_verbose`
       parameters to initialization (see below)
    6. Wraps `parse_args` and `parse_known_args` with
       `kaldi_vlog_level_cmd_decorator` (so loggers use the right level names
       on error)

    KaldiParser differs from kaldi's command line parsing in a few key
    ways. First, though '=' syntax is supported, the parser will also
    group using the command-line splitting (on unquoted whitespace). For
    the KaldiParser, ``--foo bar`` and ``--foo=bar`` are equivalent
    (assuming foo takes one optional argument), whereas, in Kaldi,
    ``--foo bar`` would be parsed as the boolean flag ``--foo`` followed
    by a positional with value ``bar``. This ambiguity is the source of
    the next difference: boolean flags. Because kaldi command-line
    parsing splits around ``=``, it can use ``--foo=true`` and ``--foo``
    interchangeably. To avoid gobbling up a positional argument,
    KaldiParser allows for only one type of boolean flag syntax. For
    the former, use ``action='store_true'`` in `add_argument`. For the
    latter, use ``type='kaldi_bool'``.


    Parameters
    ----------
    prog : str, optional
        Name of the program. Defaults to sys.argv[0]
    usage : str, optional
        A usage message. Default: auto-generated from arguments
    description : str, optional
        A description of what the program does
    epilog : str, optional
        Text following the argument descriptions
    parents :
        Parsers whose arguments should be copied into this one
    formatter_class : argparse.HelpFormatter
        class for printing help messages
    prefix_chars : str
        Characters that prefix optional arguments
    fromfile_prefix_chars : str, optional
        Characters that prefix files containing additional arguments
    argument_default : optional
        The default value for all arguments
    conflict_handler : {'error', 'resolve'}
        String indicating how to handle conflicts
    add_help : bool
        Add a -h/--help option
    add_verbose : bool
        Add a -v/--verbose option. The option requires an integer
        argument specifying a verbosiy level at the same degrees as
        Kaldi. The level will be converted to the appropriate python
        level when parsed
    add_config : bool
        Whether to add the standard '--config' option to the
        parser. If True, a first-pass will extract all config file
        options and put them at the beginning of the argument string
        to be re-parsed.
    add_print_args : bool
        Whether to add the standard '--print-args' to the parser. If
        True, a first-pass of the will search for the value of
        '--print-args' and, if True, will print that value to stderr
        (only on `parse_args`, not `parse_known_args`)
    update_formatters : bool
        If logger is set, the logger's handlers' formatters will be set
        to a kaldi-style formatter
    logger : logging.Logger, optional
        Errors will be written to this logger when parse_args fails. If
        `add_verbose` has been set to True, the logger will be set to
        the appropriate python level if verbose is set (note: the logger
        will be set to the default level - INFO - on initialization).

    Attributes
    ----------
    logger : logging.Logger
    formatter : logging.Formatter
        A log formatter that formats with kaldi-style headers
    add_config : bool
    add_print_args : bool
    '''

    def __init__(
            self, prog=None, usage=None, description=None, epilog=None,
            parents=tuple(), formatter_class=argparse.HelpFormatter,
            prefix_chars='-', fromfile_prefix_chars=None,
            argument_default=None, conflict_handler='error', add_help=True,
            add_verbose=True, add_config=True, update_formatters=True,
            add_print_args=True, logger=None):
        super(KaldiParser, self).__init__(
            prog=prog, usage=usage, description=description, epilog=epilog,
            parents=parents, formatter_class=formatter_class,
            prefix_chars=prefix_chars,
            fromfile_prefix_chars=fromfile_prefix_chars,
            argument_default=argument_default,
            conflict_handler=conflict_handler, add_help=add_help)
        self.add_config = bool(add_config)
        self.add_print_args = bool(add_print_args)
        self.register('type', 'kaldi_bool', kaldi_bool_arg_type)
        self.register('type', 'kaldi_rspecifier', kaldi_rspecifier_arg_type)
        self.register('type', 'kaldi_wspecifier', kaldi_wspecifier_arg_type)
        self.register('type', 'kaldi_rxfilename', kaldi_rxfilename_arg_type)
        self.register('type', 'kaldi_wxfilename', kaldi_wxfilename_arg_type)
        self.register('type', 'kaldi_dtype', kaldi_dtype_arg_type)
        self.register('type', 'numpy_dtype', numpy_dtype_arg_type)
        self.register('type', 'kaldi_config', kaldi_config_arg_type)
        self.register('action', 'kaldi_verbose', KaldiVerbosityAction)
        self.logger = logger
        self.formatter = logging.Formatter(
            '%(levelname)s (' + self.prog + '[x.x]:%(funcName)s():'
            '%(filename)s:%(lineno)d) %(message)s')
        if logger:
            logger.setLevel(logging.INFO)
            for handler in logger.handlers:
                handler.setFormatter(self.formatter)
        default_prefix = '-' if '-' in prefix_chars else prefix_chars[0]
        if add_verbose:
            self.add_argument(
                default_prefix + 'v', default_prefix * 2 + 'verbose',
                action='kaldi_verbose')
        if add_config:
            self.add_argument(
                default_prefix * 2 + 'config', type='kaldi_config')
        if add_print_args:
            self.add_argument(
                default_prefix * 2 + 'print-args', type='kaldi_bool')

    def print_help(self, file=None):
        if file is None:
            file = sys.stderr
        super(KaldiParser, self).print_help(file=file)

    def print_usage(self, file=None):
        if file is None:
            file = sys.stderr
        super(KaldiParser, self).print_usage(file=file)

    def error(self, message):
        if self.logger:
            self.logger.error(message)
            self.print_usage(file=sys.stderr)
            self.exit(2)
        else:
            super(KaldiParser, self).error(message)

    @kaldi_vlog_level_cmd_decorator
    def parse_known_args(self, args=None, namespace=None):
        if args is None:
            args = sys.argv[1:]
        else:
            args = list(args)
        if self.add_print_args:
            # we do a cursory pass for --print-args, since we want to
            # print even if there's an error
            arg_idx = 0
            print_args = True
            while arg_idx < len(args):
                arg = args[arg_idx]
                if (arg[:1] not in self.prefix_chars) or (
                        arg[1:2] not in self.prefix_chars):
                    pass
                elif arg[2:] == 'print-args':
                    arg_idx += 1
                    if arg_idx == len(args):
                        self.error(
                            'argument {}: expected one argument'.format(arg))
                    elif args[arg_idx] in ('true', 't'):
                        print_args = True
                    elif args[arg_idx] in ('false', 'f'):
                        print_args = False
                    else:
                        self.error(
                            "argument {}: Must be 'true'/'t' or 'false'/'f'"
                            "".format(arg)
                        )
                elif arg[2:].startswith('print-args='):
                    value = arg[2:].split('=', 1)[1]
                    if value in ('true', 't'):
                        print_args = True
                    elif value in ('false', 'f'):
                        print_args = False
                    else:
                        self.error(
                            "argument {}: Must be 'true'/'t' or 'false'/'f'"
                            "".format(arg)
                        )
                arg_idx += 1
            if print_args:
                print(
                    ' '.join(shlex_quote(arg) for arg in [self.prog] + args),
                    file=sys.stderr
                )
        ns, remainder = super(KaldiParser, self).parse_known_args(
            args=args, namespace=namespace)
        add_config = self.add_config and ns.config
        if add_config:
            args = ns.config + args
            # ignoring the possibility that they nested print-args in
            # the config
            ns, remainder = super(KaldiParser, self).parse_known_args(
                args=args, namespace=namespace)
        return ns, remainder


def _write_table_to_pickle_parse_args(args, logger):
    '''Parse args for write_table_to_pickle'''
    parser = KaldiParser(
        description=write_table_to_pickle.__doc__,
        add_verbose=True, logger=logger)
    parser.add_argument(
        'rspecifier', type='kaldi_rspecifier', help='The table to read')
    parser.add_argument(
        'value_out',
        help='A path to write (key,value) pairs to, or just values if key_out '
        'was set. If it ends in ".gz", the file will be gzipped')
    parser.add_argument(
        'key_out', nargs='?', default=None,
        help='A path to write keys to. If it ends in ".gz", the file will be '
        'gzipped')
    parser.add_argument(
        '-i', '--in-type', type='kaldi_dtype',
        default=kaldi_io.enums.KaldiDataType.BaseMatrix,
        help='The type of kaldi data type to read. Defaults to base matrix')
    parser.add_argument(
        '-o', '--out-type', type='numpy_dtype',
        default=None,
        help='The numpy data type to cast values to. The default is dependent '
        'on the input type. String types will be written as (tuples of) '
        'strings')
    options = parser.parse_args(args)
    return options


@kaldi_vlog_level_cmd_decorator
@kaldi_logger_decorator
def write_table_to_pickle(args=None):
    '''Write a kaldi table to pickle file(s)

    The inverse is write_pickle_to_table
    '''
    logger = logging.getLogger(sys.argv[0])
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    register_logger_for_kaldi(logger)
    try:
        options = _write_table_to_pickle_parse_args(args, logger)
    except SystemExit as ex:
        return ex.code
    out_type = options.out_type
    if out_type is None:
        if options.in_type.is_floating_point:
            if options.in_type.is_double:
                out_type = np.float64
            else:
                out_type = np.float32
        else:
            out_type = np.str
    from six.moves import cPickle as pickle
    try:
        logger.info('Opening {}'.format(options.rspecifier))
        reader = kaldi_io.open(options.rspecifier, options.in_type, 'r')
        logger.info('Opening {}'.format(options.value_out))
        if options.value_out.endswith('.gz'):
            import gzip
            value_out = gzip.open(options.value_out, 'wb')
        else:
            value_out = open(options.value_out, 'wb')
        if options.key_out:
            logger.info('Opening {}'.format(options.key_out))
            if options.key_out.endswith('.gz'):
                import gzip
                key_out = gzip.open(options.key_out, 'wt')
            else:
                key_out = open(options.key_out, 'w')
        else:
            key_out = None
    except IOError as error:
        logger.error(error.message, exc_info=True)
        return 1
    num_entries = 0
    try:
        for key, value in reader.items():
            num_entries += 1
            if not np.issubdtype(out_type, np.str):
                value = value.astype(out_type)
            if key_out:
                pickle.dump(value, value_out)
                pickle.dump(key, key_out)
            else:
                pickle.dump((key, value), value_out)
            if num_entries % 10 == 0:
                logger.info('Processed {} entries'.format(num_entries))
            logger.log(9, 'Processed key {}'.format(key))
    except (IOError, ValueError) as error:
        logger.error(error.message, exc_info=True)
        return 1
    finally:
        value_out.close()
        if key_out:
            key_out.close()
    if num_entries == 0:
        logger.warn("No entries were written (table was empty)")
    else:
        logger.info("Wrote {} entries".format(num_entries))
    return 0


def _write_pickle_to_table_parse_args(args, logger):
    '''Parse args for write_pickle_to_table'''
    parser = KaldiParser(
        description=write_pickle_to_table.__doc__,
        add_verbose=True, logger=logger)
    parser.add_argument(
        'value_in',
        help='A path to read (key,value) pairs from, or just values if key_in '
        'was set. If it ends in ".gz", the file is assumed to be gzipped')
    parser.add_argument(
        'key_in', nargs='?', default=None,
        help='A path to read keys from. If it ends in ".gz", the file is '
        'assumed to be gzipped')
    parser.add_argument(
        'wspecifier', type='kaldi_wspecifier', help='The table to write to')
    parser.add_argument(
        '-o', '--out-type', type='kaldi_dtype',
        default=kaldi_io.enums.KaldiDataType.BaseMatrix,
        help='The type of kaldi data type to read. Defaults to base matrix')
    options = parser.parse_args(args)
    return options


def _write_pickle_to_table_empty(wspecifier, logger):
    '''Special case when pickle file(s) was/were empty'''
    logger.info('Opening {}'.format(wspecifier))
    # doesn't matter what type we choose; we're not writing anything
    try:
        kaldi_io.open(wspecifier, 'bm', 'w')
    except IOError as error:
        logger.error(error.message, exc_info=True)
        return 1
    logger.warn('No entries were written (pickle file(s) was/were empty)')
    return 0


def _write_pickle_to_table_value_only(options, logger):
    '''write_pickle_to_table when only value_in has been specified'''
    from six.moves import cPickle as pickle
    try:
        logger.info('Opening {}'.format(options.value_in))
        if options.value_in.endswith('.gz'):
            import gzip
            value_in = gzip.open(options.value_in, 'rb')
        else:
            value_in = open(options.value_in, 'rb')
    except IOError as error:
        logger.error(error.message, exc_info=True)
        return 1
    try:
        key, value = pickle.load(value_in)
    except pickle.UnpicklingError as error:
        logger.error(error.message, exc_info=True)
        return 1
    except EOFError:
        value_in.close()
        return _write_pickle_to_table_empty(options.wspecifier, logger)
    out_type = options.out_type
    try:
        logging.info('Opening {}'.format(options.wspecifier))
        writer = kaldi_io.open(options.wspecifier, out_type, 'w')
    except IOError as error:
        value_in.close()
        logger.error(error.message, exc_info=True)
        return 1
    num_entries = 0
    try:
        while True:
            if out_type.is_floating_point:
                if out_type.is_double:
                    try:
                        value = value.astype(np.float64, copy=False)
                    except AttributeError:
                        pass
                else:
                    try:
                        value = value.astype(np.float32, copy=False)
                    except AttributeError:
                        pass
            writer.write(key, value)
            num_entries += 1
            if num_entries % 10 == 0:
                logger.info('Processed {} entries'.format(num_entries))
            logger.log(9, 'Processed key {}'.format(key))
            key, value = pickle.load(value_in)
    except EOFError:
        pass
    except (IOError, ValueError, TypeError, pickle.UnpicklingError) as error:
        if hasattr(error, 'message'):
            logger.error(error.message, exc_info=True)
        else:
            logger.error('error', exc_info=True)
        return 1
    finally:
        value_in.close()
    logger.info("Wrote {} entries".format(num_entries))
    return 0


def _write_pickle_to_table_key_value(options, logger):
    try:
        logger.info('Opening {}'.format(options.value_in))
        if options.value_in.endswith('.gz'):
            import gzip
            value_in = gzip.open(options.value_in, 'rb')
        else:
            value_in = open(options.value_in, 'rb')
        logger.info('Opening {}'.format(options.key_in))
        if options.key_in.endswith('.gz'):
            import gzip
            key_in = gzip.open(options.key_in, 'rt')
        else:
            key_in = open(options.key_in, 'r')
    except IOError as error:
        logger.error(error.message, exc_info=True)
        return 1
    try:
        value = pickle.load(value_in)
    except pickle.UnpicklingError as error:
        value_in.close()
        key_in.close()
        logger.error(error.message, exc_info=True)
        return 1
    except EOFError:
        value_in.close()
        try:
            pickle.load(key_in)
            logger.error('Number of keys (1) and values (0) do not match')
            return 1
        except pickle.UnpicklingError as error:
            key_in.close()
            logger.error(error.message, exc_info=True)
            return 1
        key_in.close()
        return _write_pickle_to_table_empty(options.wspecifier, logger)
    try:
        key = pickle.load(key_in)
    except EOFError:
        value_in.close()
        key_in.close()
        logger.error('Number of keys (0) and values (1) do not match')
        return 1
    except pickle.UnpicklingError as error:
        value_in.close()
        key_in.close()
        logger.error(error.message, exc_info=True)
        return 1
    out_type = options.out_type
    try:
        logging.info('Opening {}'.format(options.wspecifier))
        writer = kaldi_io.open(options.wspecifier, out_type, 'w')
    except IOError as error:
        value_in.close()
        key_in.close()
        logger.error(error.message, exc_info=True)
        return 1
    num_entries = 0
    try:
        while True:
            if out_type.is_floating_point:
                if out_type.is_double:
                    try:
                        value = value.astype(np.float64, copy=False)
                    except AttributeError:
                        pass  # will happen implicitly
                else:
                    try:
                        value = value.astype(np.float32, copy=False)
                    except AttributeError:
                        pass  # will happen implicitly
            writer.write(key, value)
            num_entries += 1
            if num_entries % 10 == 0:
                logger.info('Processed {} entries'.format(num_entries))
            logger.log(9, 'Processed key {}'.format(key))
            key = pickle.load(key_in)
            value = pickle.load(value_in)
    except EOFError:
        pass
    except (IOError, ValueError, TypeError, pickle.UnpicklingError) as error:
        logger.error(error.message, exc_info=True)
        return 1
    try:
        pickle.load(value_in)
        value_in.close()
        key_in.close()
        logger.error(
            'Number of keys ({}) and values ({}) do not match'.format(
                num_entries, num_entries + 1))
        return 1
    except EOFError:
        pass
    except (IOError, pickle.UnpicklingError) as error:
        value_in.close()
        key_in.close()
        logger.error(error.message, exc_info=True)
        return 1
    try:
        pickle.load(key_in)
        value_in.close()
        key_in.close()
        logger.error(
            'Number of keys ({}) and values ({}) do not match'.format(
                num_entries + 1, num_entries))
        return 1
    except EOFError:
        pass
    except (IOError, pickle.UnpicklingError) as error:
        logger.error(error.message, exc_info=True)
        return 1
    finally:
        value_in.close()
        key_in.close()
    logger.info("Wrote {} entries".format(num_entries))
    return 0


@kaldi_vlog_level_cmd_decorator
@kaldi_logger_decorator
def write_pickle_to_table(args=None):
    '''Write pickle file(s) contents to a table

    The inverse is write-table-to-pickle
    '''
    logger = logging.getLogger(sys.argv[0])
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    register_logger_for_kaldi(logger)
    try:
        options = _write_pickle_to_table_parse_args(args, logger)
    except SystemExit as ex:
        return ex.code
    if options.key_in is None:
        return _write_pickle_to_table_value_only(options, logger)
    else:
        return _write_pickle_to_table_key_value(options, logger)
