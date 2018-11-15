# Copyright 2016 Sean Robertson

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import platform
import sys

from codecs import open
from distutils.spawn import find_executable
from os import environ
from os import path
from os import walk
from re import findall
from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension

IS_64_BIT = sys.maxsize > 2 ** 32
ON_WINDOWS = platform.system() == 'Windows'


# modified this bad boy from
# https://stackoverflow.com/questions/33560364/python-windows-parsing-command-lines-with-shlex
def cmdline_split(s, platform=not ON_WINDOWS):
    """Multi-platform variant of shlex.split() for command-line splitting.
    For use with subprocess, for argv injection etc. Using fast REGEX.

    platform: 'this' = auto from current platform;
              1 = POSIX;
              0 = Windows/CMD
              (other values reserved)
    """
    if platform:
        RE_CMD_LEX = (
            r'''"((?:\\["\\]|[^"])*)"|'([^']*)'|(\\.)|(&&?|\|\|?|\d?'
            r'\>|[<])|([^\s'"\\&|<>]+)|(\s+)|(.)'''
        )
    else:
        RE_CMD_LEX = (
            r'''"((?:""|\\["\\]|[^"])*)"?()|(\\\\(?=\\*")|\\")|(&&?|\|\|?'
            r'|\d?>|[<])|([^\s"&|<>]+)|(\s+)|(.)'''
        )
    args = []
    accu = None   # collects pieces of one arg
    for qs, qss, esc, pipe, word, white, fail in findall(RE_CMD_LEX, s):
        if word:
            pass   # most frequent
        elif esc:
            word = esc[1]
        elif white or pipe:
            if accu is not None:
                args.append(accu)
            if pipe:
                args.append(pipe)
            accu = None
            continue
        elif fail:
            raise ValueError("invalid or incomplete shell string")
        elif qs:
            word = qs.replace('\\"', '"').replace('\\\\', '\\')
            if platform == 0:
                word = word.replace('""', '"')
        else:
            word = qss   # may be even empty; must be last
        accu = (accu or '') + word
    if accu is not None:
        args.append(accu)
    return args


def mkl_setup(roots, mkl_threading=None):
    found_mkl_libs = {
        'mkl_rt': False,
        'mkl_intel': False,
        'mkl_intel_lp64': False,
        'mkl_intel_thread': False,
        'mkl_gnu_thread': False,
        'mkl_sequential': False,
        'mkl_tbb_thread': False,
    }
    blas_library_dirs = set()
    blas_includes = set()
    for root in roots:
        root = path.abspath(root)
        for root_name, _, base_names in walk(root):
            for base_name in base_names:
                if ON_WINDOWS:
                    if base_name.endswith('.dll'):
                        # this is a windows runtime library. We want to link
                        # the static .lib stub, so skip this
                        continue
                    library_name = base_name.split('.')[0]
                else:
                    library_name = base_name[3:].split('.')[0]
                if library_name in found_mkl_libs and \
                        not found_mkl_libs[library_name]:
                    found_mkl_libs[library_name] = True
                    blas_library_dirs.add(root_name)
                elif base_name == 'mkl.h' and not blas_includes:
                    blas_includes.add(root_name)
    if not blas_includes:
        raise Exception('Could not find mkl.h')
    blas_library_dirs = list(blas_library_dirs)
    blas_includes = list(blas_includes)
    if mkl_threading is None:
        if found_mkl_libs['mkl_rt']:
            mkl_threading = 'dynamic'
        elif found_mkl_libs['mkl_intel_thread']:
            mkl_threading = 'intel'
        elif found_mkl_libs['mkl_tbb_thread']:
            mkl_threading = 'tbb'
        elif found_mkl_libs['mkl_sequential']:
            mkl_threading = 'sequential'
        elif found_mkl_libs['mkl_gnu_thread']:
            mkl_threading = 'gnu'
        else:
            raise Exception('Could not find a threading library for MKL')
    if mkl_threading == 'dynamic':
        blas_libraries = ['mkl_rt']
    else:
        blas_libraries = ['mkl_intel_lp64'] if IS_64_BIT else ['mkl_intel']
        if mkl_threading in ('intel', 'iomp'):
            blas_libraries += ['mkl_intel_thread', 'iomp5']
        elif mkl_threading in ('gnu', 'gomp'):
            blas_libraries += ['mkl_gnu_thread', 'gomp']
        elif mkl_threading == 'tbb':
            blas_libraries.append('mkl_tbb_thread')
        elif mkl_threading == 'sequential':
            blas_libraries.append('mkl_sequential')
        else:
            raise Exception(
                'Invalid MKL_THREADING_TYPE: {}'.format(mkl_threading))
        blas_libraries.append('mkl_core')
    if not all(found_mkl_libs[lib] for lib in blas_libraries):
        raise Exception('MKL_THREADING_TYPE=={} requires {} libs'.format(
            mkl_threading, blas_libraries))
    return {
        'BLAS_LIBRARIES': blas_libraries,
        'BLAS_LIBRARY_DIRS': blas_library_dirs,
        'BLAS_INCLUDES': blas_includes,
        # 'LD_FLAGS': ['-Wl,--no-as-needed'],
        'DEFINES': [('HAVE_MKL', None)],
    }


def blas_setup(roots, library_names, headers, extra_entries_on_success):
    library_names = dict((lib, False) for lib in library_names)
    headers = dict((header, False) for header in headers)
    library_dirs = set()
    include_dirs = set()
    for root in roots:
        root = path.abspath(root)
        for root_name, _, base_names in walk(root):
            for base_name in base_names:
                if ON_WINDOWS:
                    library_name = base_name.split('.')[0]
                else:
                    library_name = base_name[3:].split('.')[0]
                if library_name in library_names and \
                        not library_names[library_name]:
                    library_names[library_name] = True
                    library_dirs.add(root_name)
                elif base_name in headers and not headers[base_name]:
                    headers[base_name] = True
                    include_dirs.add(root_name)
    if not all(library_names.values()):
        raise Exception('Could not find {}'.format(
            tuple(key for key, val in library_names.items() if not val)))
    if not all(headers.values()):
        raise Exception('Could not find {}'.format(
            tuple(key for key, val in headers.items() if not val)))
    ret = dict(extra_entries_on_success)
    ret['BLAS_LIBRARIES'] = list(library_names)
    ret['BLAS_LIBRARY_DIRS'] = list(library_dirs)
    ret['BLAS_INCLUDES'] = list(include_dirs)
    return ret


def openblas_setup(roots):
    return blas_setup(
        roots,
        ('openblas',),
        ('cblas.h', 'lapacke.h',),
        {'DEFINES': [('HAVE_OPENBLAS', None)]},
    )


def atlas_setup(roots):
    return blas_setup(
        roots,
        ('atlas',),
        ('cblas.h', 'clapack.h',),
        {'DEFINES': [('HAVE_ATLAS', None)]},
    )


def lapacke_setup(roots):
    return blas_setup(
        roots,
        ('blas', 'lapack', 'lapacke'),
        ('cblas.h', 'lapacke.h'),
        {'DEFINES': [('HAVE_LAPACKE', None)]},
    )


def clapack_setup(roots):
    return blas_setup(
        roots,
        ('blas', 'lapack', 'f2c', 'clapack'),
        ('cblas.h', 'f2c.h', 'clapack.h'),
        {'DEFINES': [('HAVE_CLAPACK', None)]},
    )


def accelerate_setup():
    return {
        'DEFINES': [('HAVE_CLAPACK', None)],
        'LD_FLAGS': ['-framework', 'Accelerate'],
    }


def custom_blas_setup(blas_includes, blas_libraries):
    # blas includes must be a directory/directories. Blas libraries
    # could be the library names or paths to the libraries themselves.
    blas_includes = set(blas_includes)
    for include_dir in blas_includes:
        if not path.isdir(include_dir):
            raise Exception(
                'path "{}" in BLAS_INCLUDES is not a directory'.format(
                    include_dir))
    library_names = set()
    library_dirs = set()
    ldflags = set()
    candidate_blas_types = set()
    for blas_library in blas_libraries:
        if path.isfile(blas_library):
            library_name = path.basename(blas_library)
            if ON_WINDOWS:
                library_names.add(library_name.split('.')[0])
            elif platform.system() == 'Linux':
                ldflags.add('-l:{}'.format(library_name))
            else:
                library_names.add(library_name[3:].split('.'))
            library_dirs.add(path.abspath(path.dirname(blas_library)))
        else:
            library_name = blas_library
            library_names.add(library_name)
        for blas_type in ('atlas', 'mkl', 'openblas', 'lapacke', 'clapack'):
            if blas_type in library_name:
                candidate_blas_types.add(blas_type)
    if not len(candidate_blas_types):
        raise Exception(
            'Could not determine appropriate BLAS type for libraries listed '
            'in BLAS_LIBRARIES')
    elif len(candidate_blas_types) != 1:
        raise Exception(
            'BLAS_LIBRARIES contains libraries that could refer to any '
            'of {}'.format(candidate_blas_types))
    blas_type = candidate_blas_types.pop()
    # we need to check if the requisite libraries are present in the
    # inferred directories & get the appropriate defines. We then force
    # *our* directories and libraries. Any problems with this should be
    # caught at compile/link time
    if blas_type == 'atlas':
        ret = atlas_setup(library_dirs | blas_includes)
    elif blas_type == 'mkl':
        ret = mkl_setup(library_dirs | blas_includes)
    elif blas_type == 'openblas':
        ret = openblas_setup(library_dirs | blas_includes)
    elif blas_type == 'lapacke':
        ret = lapacke_setup(library_dirs | blas_includes)
    else:
        ret = clapack_setup(library_dirs | blas_includes)
    ret['BLAS_LIBRARIES'] = list(library_names)
    ret['BLAS_LIBRARY_DIRS'] = list(library_dirs)
    ret['BLAS_INCLUDES'] = list(blas_includes)
    ret['LD_FLAGS'] = ret.get('LD_FLAGS', []) + list(ldflags)
    return ret


PWD = path.abspath(path.dirname(__file__))
PYTHON_DIR = path.join(PWD, 'python')
SRC_DIR = path.join(PWD, 'src')
SWIG_DIR = path.join(PWD, 'swig')
DEFINES = [
    ('KALDI_DOUBLEPRECISION', environ.get('KALDI_DOUBLEPRECISION', '0')),
]
if platform.system() != 'Windows':
    FLAGS = ['-std=c++11', '-m64' if IS_64_BIT else '-m32', '-msse', '-msse2']
    FLAGS += ['-fPIC']
    DEFINES += [
        ('_GLIBCXX_USE_CXX11_ABI', '0'),
        ('HAVE_EXECINFO_H', '1'),
        ('HAVE_CXXABI_H', None),
    ]
    LIBRARIES = ['m', 'dl']
else:
    FLAGS = []
    LIBRARIES = []
LD_FLAGS = []

MKL_ROOT = cmdline_split(environ.get('MKLROOT', ''))
OPENBLAS_ROOT = cmdline_split(environ.get('OPENBLASROOT', ''))
ATLAS_ROOT = cmdline_split(environ.get('ATLASROOT', ''))
CLAPACK_ROOT = cmdline_split(environ.get('CLAPACKROOT', ''))
LAPACKE_ROOT = cmdline_split(environ.get('LAPACKEROOT', ''))
USE_ACCELERATE = environ.get('ACCELERATE', None)
BLAS_INCLUDES = cmdline_split(environ.get('BLAS_INCLUDES', ''))
BLAS_LIBRARIES = cmdline_split(environ.get('BLAS_LIBRARIES', ''))
NUM_BLAS_OPTS = sum(bool(x) for x in (
    MKL_ROOT, OPENBLAS_ROOT, ATLAS_ROOT, USE_ACCELERATE,
    CLAPACK_ROOT, LAPACKE_ROOT, BLAS_LIBRARIES
))
if NUM_BLAS_OPTS > 1:
    raise Exception('Only one BLAS type should be specified')
elif NUM_BLAS_OPTS:
    if MKL_ROOT:
        BLAS_DICT = mkl_setup(
            MKL_ROOT, environ.get('MKL_THREADING_TYPE', None))
    elif OPENBLAS_ROOT:
        BLAS_DICT = openblas_setup(OPENBLAS_ROOT)
    elif ATLAS_ROOT:
        BLAS_DICT = atlas_setup(ATLAS_ROOT)
    elif BLAS_INCLUDES or BLAS_LIBRARIES:
        if bool(BLAS_INCLUDES) != bool(BLAS_LIBRARIES):
            raise Exception(
                'Both BLAS_LIBRARIES and BLAS_INCLUDES must be set if one '
                'is set')
        BLAS_DICT = custom_blas_setup(BLAS_INCLUDES, BLAS_LIBRARIES)
    elif CLAPACK_ROOT:
        BLAS_DICT = clapack_setup(CLAPACK_ROOT)
    elif LAPACKE_ROOT:
        BLAS_DICT = lapacke_setup(LAPACKE_ROOT)
    elif platform.system() == 'Darwin':
        BLAS_DICT = accelerate_setup()
    else:
        raise Exception('Accelerate is only available on OSX')
else:
    print(
        'No BLAS library specified at command line. Will look via numpy. If '
        'you have problems with linking, please specify BLAS via command line.'
    )
    BLAS_DICT = dict()


LIBRARIES += BLAS_DICT.get('BLAS_LIBRARIES', [])
LIBRARY_DIRS = BLAS_DICT.get('BLAS_LIBRARY_DIRS', [])
INCLUDE_DIRS = BLAS_DICT.get('BLAS_INCLUDES', []) + [SRC_DIR]
LD_FLAGS += BLAS_DICT.get('LD_FLAGS', [])
DEFINES += BLAS_DICT.get('DEFINES', [])
FLAGS += BLAS_DICT.get('FLAGS', [])

if platform.system() == 'Darwin':
    FLAGS += ['-flax-vector-conversions', '-stdlib=libc++']
    LD_FLAGS += ['-stdlib=libc++']

# Get the long description from the README file
with open(path.join(PWD, 'README.rst'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

SRC_FILES = []
if find_executable('swig'):
    SRC_FILES.append(path.join(SWIG_DIR, 'pydrobert', 'kaldi.i'))
elif path.exists(path.join(SWIG_DIR, 'pydrobert', 'kaldi_wrap.cpp')):
    print(
        'SWIG could not be found, but kaldi_wrap.cpp exists. Using that',
        file=sys.stderr
    )
    SRC_FILES.append(path.join(SWIG_DIR, 'pydrobert', 'kaldi_wrap.cpp'))
else:
    print(
        'SWIG could not be found and kaldi_wrap.cpp does not exist. Cannot '
        'succeed', file=sys.stderr)
    sys.exit(1)
for base_dir, _, files in walk(SRC_DIR):
    SRC_FILES += [path.join(base_dir, f) for f in files if f.endswith('.cc')]

INSTALL_REQUIRES = ['numpy >= 1.11.3', 'six', 'future']
SETUP_REQUIRES = ['setuptools_scm']
if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
    SETUP_REQUIRES.append('pytest-runner')
try:
    import numpy
except ImportError:
    SETUP_REQUIRES.append('numpy == 1.11.3')
TESTS_REQUIRE = ['pytest']

KALDI_LIBRARY = Extension(
    'pydrobert.kaldi._internal',
    sources=SRC_FILES,
    libraries=LIBRARIES,
    library_dirs=LIBRARY_DIRS,
    include_dirs=INCLUDE_DIRS,
    extra_compile_args=FLAGS,
    extra_link_args=LD_FLAGS,
    define_macros=DEFINES,
    swig_opts=['-c++', '-builtin', '-castmode', '-O', '-I{}'.format(SWIG_DIR)],
    language='c++',
)


# https://stackoverflow.com/questions/2379898/
# make-distutils-look-for-numpy-header-files-in-the-correct-place
class CustomBuildExtCommand(build_ext):

    def look_for_blas(self):
        '''Look for blas libraries through numpy'''
        injection_lookup = {
            'BLAS_LIBRARIES': (KALDI_LIBRARY, 'libraries'),
            'BLAS_LIBRARY_DIRS': (KALDI_LIBRARY, 'library_dirs'),
            'BLAS_INCLUDES': (KALDI_LIBRARY, 'include_dirs'),
            'LD_FLAGS': (KALDI_LIBRARY, 'extra_link_args'),
            'DEFINES': (KALDI_LIBRARY, 'define_macros'),
            'libraries': (KALDI_LIBRARY, 'libraries'),
            'library_dirs': (KALDI_LIBRARY, 'library_dirs'),
            'include_dirs': (self, 'include_dirs'),
            'define_macros': (KALDI_LIBRARY, 'define_macros'),
            'extra_compile_args': (KALDI_LIBRARY, 'extra_compile_args'),
            'extra_link_args': (KALDI_LIBRARY, 'extra_link_args'),
        }
        from numpy.distutils import system_info
        found_blas = False
        blas_to_check = [
            ('mkl', 'HAVE_MKL', mkl_setup),
            ('openblas_lapack', 'HAVE_OPENBLAS', openblas_setup),
            ('atlas', 'HAVE_ATLAS', atlas_setup),
            # numpy only cares about lapack, not c wrappers. It uses
            # f77blas, after all
            ('blas_opt', 'HAVE_LAPACKE', lapacke_setup),
            ('blas_opt', 'HAVE_CLAPACK', clapack_setup),
        ]
        if platform.system() == 'Darwin':
            blas_to_check.append(
                ('accelerate', 'HAVE_CLAPACK', accelerate_setup))
        for info_name, define, setup_func in blas_to_check:
            info = system_info.get_info(info_name)
            if not info:
                continue
            if info_name == 'accelerate':
                # should be sufficient
                for key, value in info.items():
                    if key in injection_lookup:
                        obj, attribute = injection_lookup[key]
                        past_attr = getattr(obj, attribute)
                        if past_attr is None:
                            setattr(obj, attribute, value)
                        else:
                            setattr(obj, attribute, past_attr + value)
                KALDI_LIBRARY.define_macros.append((define, None))
                print('Using {}'.format(info_name))
                found_blas = True
                break
            elif 'library_dirs' not in info:
                continue
            # otherwise we try setting up in the library dirs, then in the
            # directories above them.
            check_dirs = list(info['library_dirs'])
            check_dirs += [
                path.abspath(path.join(x, '..')) for x in check_dirs]
            check_dirs = list(info.get('include_dirs', [])) + check_dirs
            try:
                blas_dict = setup_func(check_dirs)
            except Exception:
                continue
            for key, value in blas_dict.items():
                obj, attribute = injection_lookup[key]
                past_attr = getattr(obj, attribute)
                if past_attr is None:
                    setattr(obj, attribute, value)
                else:
                    setattr(obj, attribute, past_attr + value)
            print('Using {}'.format(info_name))
            found_blas = True
        if not found_blas:
            raise Exception('Unable to find BLAS library via numpy')

    def finalize_options(self):
        build_ext.finalize_options(self)
        import numpy
        if not len(BLAS_DICT):
            self.look_for_blas()
        self.include_dirs.append(numpy.get_include())


setup(
    name='pydrobert-kaldi',
    use_scm_version=True,
    description='Swig bindings for kaldi',
    long_description=LONG_DESCRIPTION,
    url='https://github.com/pydrobert-kaldi',
    author='Sean Robertson',
    author_email='sdrobert@cs.toronto.edu',
    license='Apache 2.0',
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=[
        'pydrobert',
        'pydrobert.kaldi',
        'pydrobert.kaldi.io',
        'pydrobert.kaldi.feat',
        'pydrobert.kaldi.eval',
    ],
    cmdclass={'build_ext': CustomBuildExtCommand},
    setup_requires=SETUP_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    ext_modules=[KALDI_LIBRARY],
    entry_points={
        'console_scripts': [
            'write-table-to-pickle = pydrobert.kaldi.command_line:'
            'write_table_to_pickle',
            'write-pickle-to-table = pydrobert.kaldi.command_line:'
            'write_pickle_to_table',
            'compute-error-rate = pydrobert.kaldi.command_line:'
            'compute_error_rate',
            'normalize-feat-lens = pydrobert.kaldi.command_line:'
            'normalize_feat_lens',
            'write-table-to-torch-dir = pydrobert.kaldi.command_line:'
            'write_table_to_torch_dir [pytorch]',
            'write-torch-dir-to-table = pydrobert.kaldi.command_line:'
            'write_torch_dir_to_table [pytorch]'
        ]
    },
    extras_require={
        ':python_version<"3.4"': ['enum34'],
        'pytorch': ['pytorch'],
    }
)
