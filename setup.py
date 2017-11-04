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

from codecs import open
from os import environ
from os import path
from os import walk
from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension
from sys import maxsize
from sys import stderr
from sys import version_info

PWD = path.abspath(path.dirname(__file__))
PYTHON_DIR = path.join(PWD, 'python')
SRC_DIR = path.join(PWD, 'src')
SWIG_DIR = path.join(PWD, 'swig')
DEFINES = [
    ('KALDI_DOUBLEPRECISION', environ.get('KALDI_DOUBLEPRECISION', '0')),
    # ('_GLIBCXX_USE_CXX11_ABI', '0'),
    ('HAVE_EXECINFO_H', '1'),
    ('HAVE_CXXABI_H', None),
]
IS_64_BIT = maxsize > 2 ** 32
FLAGS = ['-std=c++11', '-m64' if IS_64_BIT else '-m32', '-msse', '-msse2']
FLAGS += ['-pthread', '-fPIC']
LD_FLAGS = []
    
if 'MKLROOT' in environ:
    # IMPORTANT: make sure that BLAS_LIBRARIES stays in this order,
    # or you'll get failed symbol lookups
    MKL_ROOT = path.abspath(environ['MKLROOT'])
    MKL_THREADING = environ.get('MKL_THREADING_TYPE', None)
    FOUND_MKL_LIBS = {
        'mkl_rt': False,
        'mkl_intel': False,
        'mkl_intel_lp64': False,
        'mkl_intel_thread': False,
        'mkl_gnu_thread': False,
        'mkl_sequential': False,
        'mkl_tbb_thread': False,
    }
    BLAS_LIBRARY_DIRS = set()
    BLAS_INCLUDES = None
    for root_name, _, base_names in walk(MKL_ROOT):
        for base_name in base_names:
            library_name = base_name[3:].split('.')[0]
            if library_name in FOUND_MKL_LIBS:
                FOUND_MKL_LIBS[library_name] = True
                BLAS_LIBRARY_DIRS.add(root_name)
            if base_name == 'mkl.h':
                BLAS_INCLUDES = [root_name]
    if not BLAS_INCLUDES:
        raise Exception('Could not find mkl.h')
    BLAS_LIBRARY_DIRS = list(BLAS_LIBRARY_DIRS)
    if MKL_THREADING is None:
        if FOUND_MKL_LIBS['mkl_rt']:
            MKL_THREADING = 'dynamic'
        elif FOUND_MKL_LIBS['mkl_intel_thread']:
            MKL_THREADING = 'intel'
        elif FOUND_MKL_LIBS['mkl_tbb_thread']:
            MKL_THREADING = 'tbb'
        elif FOUND_MKL_LIBS['mkl_sequential']:
            MKL_THREADING = 'sequential'
        elif FOUND_MKL_LIBS['mkl_gnu_thread']:
            MKL_THREADING = 'gnu'
        else:
            raise Exception('Could not find a threading library for MKL')
    if MKL_THREADING == 'dynamic':
        BLAS_LIBRARIES = ['mkl_rt']
    else:
        BLAS_LIBRARIES = ['mkl_intel_lp64'] if IS_64_BIT else ['mkl_intel']
        if MKL_THREADING in ('intel', 'iomp'):
            BLAS_LIBRARIES += ['mkl_intel_thread', 'iomp5']
        elif MKL_THREADING in ('gnu', 'gomp'):
            BLAS_LIBRARIES += ['mkl_gnu_thread', 'gomp']
        elif MKL_THREADING == 'tbb':
            BLAS_LIBRARIES.append('mkl_tbb_thread')
        elif MKL_THREADING == 'sequential':
            BLAS_LIBRARIES.append('mkl_sequential')
        else:
            raise Exception(
                'Invalid MKL_THREADING_TYPE: {}'.format(MKL_THREADING))
        BLAS_LIBRARIES.append('mkl_core')
    if not all(FOUND_MKL_LIBS[lib] for lib in BLAS_LIBRARIES):
        raise Exception('MKL_THREADING_TYPE=={} requires {} libs'.format(
            MKL_THREADING, BLAS_LIBRARIES))
    LD_FLAGS.append('-Wl,--no-as-needed')
    DEFINES.append(('HAVE_MKL', None))
elif 'OPENBLASROOT' in environ:
    OPENBLAS_ROOT = path.abspath(environ['OPENBLASROOT'])
    if path.isdir(path.join(OPENBLAS_ROOT, 'include')):
        BLAS_INCLUDES = [path.join(OPENBLAS_ROOT, 'include')]
    else:
        raise Exception('OPENBLASROOT set, but could not find include dir')
    BLAS_LIBRARY_DIRS = []
    if path.isdir(path.join(OPENBLAS_ROOT, 'lib64')):
        BLAS_LIBRARY_DIRS.append(path.join(OPENBLAS_ROOT, 'lib64'))
    if path.isdir(path.join(OPENBLAS_ROOT, 'lib')):
        BLAS_LIBRARY_DIRS.append(path.join(OPENBLAS_ROOT, 'lib'))
    if not BLAS_LIBRARY_DIRS:
        raise Exception('OPENBLASROOT set, but could not find library dir')
    BLAS_LIBRARIES = ['openblas']
    DEFINES.append(('HAVE_OPENBLAS', None))
elif 'ATLASROOT' in environ:
    ATLAS_ROOT = path.abspath(environ['ATLASROOT'])
    if path.isdir(path.join(ATLAS_ROOT, 'include')):
        BLAS_INCLUDES = [path.join(ATLAS_ROOT, 'include')]
        if path.isdir(path.join(BLAS_INCLUDES[0], 'atlas')):
            BLAS_INCLUDES.append(path.join(BLAS_INCLUDES[0], 'atlas'))
    else:
        raise Exception('ATLASROOT set, but could not find include dir')
    BLAS_LIBRARY_DIRS = []
    if path.isdir(path.join(ATLAS_ROOT, 'lib64')):
        BLAS_LIBRARY_DIRS.append(path.join(ATLAS_ROOT, 'lib64'))
    if path.isdir(path.join(ATLAS_ROOT, 'lib')):
        BLAS_LIBRARY_DIRS.append(path.join(ATLAS_ROOT, 'lib'))
    if not BLAS_LIBRARY_DIRS:
        raise Exception('ATLASROOT set, but could not find library dir')
    BLAS_LIBRARIES = ['atlas']
    DEFINES.append(('HAVE_ATLAS', None))
elif platform.system() == 'Darwin':
    DEFINES.append(('HAVE_CLAPACK', None))
    BLAS_LIBRARIES = []
    BLAS_LIBRARY_DIRS = []
    BLAS_INCLUDES = []
    LD_FLAGS += ['-framework', 'Accelerate']
else:
    raise Exception('No blas libary found')

if platform.system() == 'Darwin':
    FLAGS += ['-flax-vector-conversions', '-stdlib=libc++']
    LD_FLAGS += ['-stdlib=libc++']

# Get the long description from the README file
with open(path.join(PWD, 'README.rst'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

SRC_FILES = [path.join(SWIG_DIR, 'pydrobert', 'kaldi.i')]
for base_dir, _, files in walk(SRC_DIR):
    SRC_FILES += [path.join(base_dir, f) for f in files if f.endswith('.cc')]

# https://stackoverflow.com/questions/2379898/
# make-distutils-look-for-numpy-header-files-in-the-correct-place
class CustomBuildExtCommand(build_ext):
    def run(self):
        import numpy
        self.include_dirs.append(numpy.get_include())
        build_ext.run(self)

INSTALL_REQUIRES = ['numpy', 'six', 'future']
if version_info < (3, 0):
    INSTALL_REQUIRES.append('enum34')
SETUP_REQUIRES = ['pytest-runner', 'setuptools_scm']
TESTS_REQUIRE = ['pytest']

KALDI_LIBRARY = Extension(
    'pydrobert.kaldi._internal',
    sources=SRC_FILES,
    libraries=['pthread', 'm', 'dl'] + BLAS_LIBRARIES,
    runtime_library_dirs=BLAS_LIBRARY_DIRS,
    include_dirs=[SRC_DIR] + BLAS_INCLUDES,
    extra_compile_args=FLAGS,
    extra_link_args=LD_FLAGS,
    define_macros=DEFINES,
    swig_opts=['-c++', '-builtin', '-Wall', '-I{}'.format(SWIG_DIR)],
    language='c++',
)

setup(
    name='pydrobert-kaldi',
    use_scm_version=True,
    description='Swig bindings for kaldi',
    long_description=LONG_DESCRIPTION,
    url='https://github.com/pydrobert-kaldi',
    author='Sean Robertson',
    author_email='sdrobert@cs.toronto.edu',
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Researchers',
        'License :: OSI Approved :: Apache 2.0',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=['pydrobert', 'pydrobert.kaldi', 'pydrobert.kaldi.io'],
    cmdclass={'build_ext': CustomBuildExtCommand},
    setup_requires=SETUP_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    ext_modules=[KALDI_LIBRARY],
    namespace_packages=['pydrobert'],
    entry_points={
        'console_scripts': [
            'write-table-to-pickle = pydrobert.kaldi.command_line:'
            'write_table_to_pickle',
            'write-pickle-to-table = pydrobert.kaldi.command_line:'
            'write_pickle_to_table',
        ]
    }
)
