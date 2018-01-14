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

'''Contains a custom ArgumentParser, KaldiParser, and a number of arg types'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import logging
import sys

import numpy as np

from future.utils import raise_from
from pydrobert import kaldi
from pydrobert.kaldi.io import enums as kaldi_io_enums
from pydrobert.kaldi.io import util as kaldi_io_util
from pydrobert.kaldi.logging import kaldi_lvl_to_logging_lvl
from pydrobert.kaldi.logging import kaldi_vlog_level_cmd_decorator
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
    'kaldi_config_arg_type',
    'numpy_dtype_arg_type',
    'kaldi_bool_arg_type',
    'parse_kaldi_config_file',
    'KaldiVerbosityAction',
    'KaldiParser',
]


def kaldi_rspecifier_arg_type(string):
    '''argument type to make sure string is a valid rspecifier'''
    table_type, _, _, _ = kaldi_io_util.parse_kaldi_input_path(string)
    if table_type == kaldi_io_enums.TableType.NotATable:
        raise argparse.ArgumentTypeError('Not a valid rspecifier')
    return string


def kaldi_wspecifier_arg_type(string):
    '''argument type to make sure string is a valid wspecifier'''
    table_type, _, _, _ = kaldi_io_util.parse_kaldi_output_path(string)
    if table_type == kaldi_io_enums.TableType.NotATable:
        raise argparse.ArgumentTypeError('Not a valid wspecifier')
    return string


def kaldi_rxfilename_arg_type(string):
    '''argument type to make sure string is a valid extended readable file'''
    table_type, _, rxfilename_type, _ = kaldi_io_util.parse_kaldi_input_path(
        string)
    if table_type != kaldi_io_enums.TableType.NotATable:
        raise argparse.ArgumentTypeError(
            'Expected an extended file name, got an rspecifier (starts with '
            "'ark:' or 'scp:')")
    elif rxfilename_type == kaldi_io_enums.RxfilenameType.InvalidInput:
        raise argparse.ArgumentTypeError('Not a valid rxfilename')
    return string


def kaldi_wxfilename_arg_type(string):
    '''argument type to make sure string is a valid extended readable file'''
    table_type, _, wxfilename_type, _ = kaldi_io_util.parse_kaldi_output_path(
        string)
    if table_type != kaldi_io_enums.TableType.NotATable:
        raise argparse.ArgumentTypeError(
            'Expected an extended file name, got an rspecifier (starts with '
            "'ark:' or 'scp:')")
    elif wxfilename_type == kaldi_io_enums.WxfilenameType.InvalidOutput:
        raise argparse.ArgumentTypeError('Not a valid wxfilename')
    return string


def kaldi_dtype_arg_type(string):
    '''argument type for string reps of KaldiDataType'''
    try:
        ret = kaldi_io_enums.KaldiDataType(string)
    except ValueError:
        raise argparse.ArgumentTypeError(
            'Invalid kaldi data type (must be one of {})'.format(
                ','.join(
                    "'{}'".format(x.value)
                    for x in kaldi_io_enums.KaldiDataType)))
    return ret


def kaldi_bool_arg_type(string):
    '''argument type for bool strings of "true","t","false", or "f"'''
    if string in ("true", "t"):
        return True
    elif string in ("false", "f"):
        return False
    else:
        raise argparse.ArgumentTypeError(
            "Must be 'true'/'t' or 'false'/'f'")


def numpy_dtype_arg_type(string):
    '''argument type for string reps of numpy dtypes'''
    try:
        ret = np.dtype(string)
    except TypeError as error:
        raise argparse.ArgumentTypeError(error.message)
    return ret


def kaldi_config_arg_type(string):
    '''Encapsulate parse_kaldi_config_file as an argument type'''
    try:
        return parse_kaldi_config_file(string)
    except (IOError, ValueError) as error:
        raise_from(argparse.ArgumentTypeError('config file error:'), error)


def parse_kaldi_config_file(file_path, allow_space=True):
    '''Return a list of arguments from a kaldi config file

    Parameters
    ----------
    file_path : str
        Points to the config file in question
    allow_spaces : bool, optional
        If ``True``, treat the first space on a line as splitting key
        and value if no equals sign exists on the line. If ``False``, no
        equals sign will chunk the whole line (as if a boolean flag).
        Kaldi does not split on spaces, but python does. Note that
        `allow_spaces` does not split the entire line on spaces, unlike
        shell arguments.
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


class KaldiVerbosityAction(argparse.Action):
    '''Read kaldi-style verbosity levels, setting logger to python level

    Kaldi verbosities tend to range from [-3, 9]. This action takes in a
    kaldi verbosity level and converts it to python logging levels with
    `pydrobert.kaldi.logging.kaldi_lvl_to_logging_lvl`

    If the parser has a `logger` attribute, the `logger` will be set to
    the new level.
    '''

    def __init__(
            self, option_strings, dest, default=logging.INFO, required=False,
            help='Verbose level (higher->more logging)', metavar=None):
        super(KaldiVerbosityAction, self).__init__(
            option_strings, dest, nargs=None, default=default,
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
    compatible with kaldi command-line scripts. It makes the following
    changes to ``argparse.ArgumentParser``:

    1. Creates a ``logging.Formatter`` instance that formats messages
       similarly to kaldi using the `prog` keyword as the program name.
    2. Sets the default help and usage locations to ``sys.stderr``
       (instead of ``sys.stdout``)
    3. Registers ``'kaldi_bool'``, ``'kaldi_rspecifier'``,
       ``'kaldi_wspecifier'``, ``'kaldi_wxfilename'``,
       ``'kaldi_rxfilename'``, ``'kaldi_config'``, ``'kaldi_dtype'``,
       and ``'numpy_dtype'`` as argument types
    4. Registers ``'kaldi_verbose'`` as an action
    5. Adds `logger`, `update_formatters`, `add_config`, and
       `add_verbose` parameters to initialization (see below)
    6. Wraps `parse_args` and `parse_known_args` with
       ``kaldi_vlog_level_cmd_decorator`` (so loggers use the right
       level names on error)

    KaldiParser differs from kaldi's command line parsing in a few key
    ways. First, though '=' syntax is supported, the parser will also
    group using the command-line splitting (on unquoted whitespace). For
    the ``KaldiParser``, ``--foo bar`` and ``--foo=bar`` are equivalent
    (assuming foo takes one optional argument), whereas, in Kaldi,
    ``--foo bar`` would be parsed as the boolean flag ``--foo`` followed
    by a positional with value ``bar``. This ambiguity is the source of
    the next difference: boolean flags. Because kaldi command-line
    parsing splits around ``=``, it can use ``--foo=true`` and ``--foo``
    interchangeably. To avoid gobbling up a positional argument,
    ``KaldiParser`` allows for only one type of boolean flag syntax. For
    the former, use ``action='store_true'`` in `add_argument`. For the
    latter, use ``type='kaldi_bool'``.

    Parameters
    ----------
    prog : str, optional
        Name of the program. Defaults to ``sys.argv[0]``
    usage : str, optional
        A usage message. Default: auto-generated from arguments
    description : str, optional
        A description of what the program does
    epilog : str, optional
        Text following the argument descriptions
    parents : sequence, optional
        Parsers whose arguments should be copied into this one
    formatter_class : argparse.HelpFormatter
        Class for printing help messages
    prefix_chars : str, optional
        Characters that prefix optional arguments
    fromfile_prefix_chars : str, optional
        Characters that prefix files containing additional arguments
    argument_default : optional
        The default value for all arguments
    conflict_handler : {'error', 'resolve'}, optional
        String indicating how to handle conflicts
    add_help : bool, optional
        Add a ``-h/--help`` option
    add_verbose : bool, optional
        Add a ``-v/--verbose`` option. The option requires an integer
        argument specifying a verbosiy level at the same degrees as
        Kaldi. The level will be converted to the appropriate python
        level when parsed
    add_config : bool, optional
        Whether to add the standard ``--config`` option to the
        parser. If ``True``, a first-pass will extract all config file
        options and put them at the beginning of the argument string
        to be re-parsed.
    add_print_args : bool, optional
        Whether to add the standard ``--print-args`` to the parser. If
        ``True``, a first-pass of the will search for the value of
        ``--print-args`` and, if ``True``, will print that value to
        stderr (only on `parse_args`, not `parse_known_args`)
    update_formatters : bool, optional
        If `logger` is set, the logger's handlers' formatters will be
        set to a kaldi-style formatter
    logger : logging.Logger, optional
        Errors will be written to this logger when parse_args fails. If
        `add_verbose` has been set to ``True``, the logger will be set
        to the appropriate python level if verbose is set (note: the
        logger will be set to the default level - ``INFO`` - on
        initialization)
    version : str, optional
        A version string to use for logs. If not set,
        ``pydrobert.kaldi.__version__`` will be used by default

    Attributes
    ----------
    logger : logging.Logger
        The logger this parse was printing out to
    formatter : logging.Formatter
        A log formatter that formats with kaldi-style headers
    add_config : bool
        Whether this parser has a ``--config`` flag
    add_print_args : bool
        Whether this parser has a ``--print-args`` flag
    version : str
        Version string used by this parser and `logger`
    '''

    def __init__(
            self, prog=None, usage=None, description=None, epilog=None,
            parents=tuple(), formatter_class=argparse.HelpFormatter,
            prefix_chars='-', fromfile_prefix_chars=None,
            argument_default=None, conflict_handler='error', add_help=True,
            add_verbose=True, add_config=True, update_formatters=True,
            add_print_args=True, logger=None, version=None):
        super(KaldiParser, self).__init__(
            prog=prog, usage=usage, description=description, epilog=epilog,
            parents=parents, formatter_class=formatter_class,
            prefix_chars=prefix_chars,
            fromfile_prefix_chars=fromfile_prefix_chars,
            argument_default=argument_default,
            conflict_handler=conflict_handler, add_help=add_help)
        if version is None:
            self.version = kaldi.__version__
        else:
            self.version = version
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
            '%(levelname)s (' + self.prog + '[' + self.version +
            ']:%(funcName)s():%(filename)s:%(lineno)d) %(message)s')
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

    print_help.__doc__ = argparse.ArgumentParser.print_help.__doc__

    def print_usage(self, file=None):
        if file is None:
            file = sys.stderr
        super(KaldiParser, self).print_usage(file=file)

    print_usage.__doc__ = argparse.ArgumentParser.print_usage.__doc__

    def error(self, message):
        if self.logger:
            self.logger.error(message)
            self.print_usage(file=sys.stderr)
            self.exit(2)
        else:
            super(KaldiParser, self).error(message)

    error.__doc__ = argparse.ArgumentParser.error.__doc__

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

    parse_known_args.__doc__ = argparse.ArgumentParser.parse_known_args.__doc__
