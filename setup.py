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

if platform.system() == 'Linux':
    if 'MKLROOT' in environ:
        # IMPORTANT: make sure that BLAS_LIBRARIES stays in this order,
        # or you'll get failed symbol lookups
        MKL_ROOT = path.abspath(environ['MKLROOT'])
        MKL_THREADING = environ.get('MKL_THREADING_TYPE', 'sequential')
        if path.isdir(path.join(MKL_ROOT, 'mkl')) and \
                environ.get('FORCE_MKLROOT', '0') == '0':
            MKL_ROOT = path.join(MKL_ROOT, 'mkl')
            print(
                'Setting MKL root to "{}". If this is not desired, export the '
                'environment variable FORCE_MKLROOT'.format(MKL_ROOT),
                file=stderr
            )
        if path.isdir(path.join(MKL_ROOT, 'include')):
            BLAS_INCLUDES = [path.join(MKL_ROOT, 'include')]
        else:
            raise Exception('MKLROOT set, but could not find include dir')
        if IS_64_BIT:
            BLAS_LIBRARIES = ['mkl_intel_lp64',]
            if path.isdir(path.join(MKL_ROOT, 'lib', 'intel64')):
                BLAS_LIBRARY_DIRS = [path.join(MKL_ROOT, 'lib', 'intel64'),]
                if path.isdir(
                        path.join(path.dirname(MKL_ROOT), 'lib', 'intel64')):
                    BLAS_LIBRARY_DIRS.append(
                        path.join(path.dirname(MKL_ROOT), 'lib', 'intel64'))
            else:
                raise Exception('MKLROOT set, but could not find library dir')
        else:
            BLAS_LIBRARIES = ['mkl_intel',]
            if path.isdir(path.join(MKL_ROOT, 'lib', 'ia32')):
                BLAS_LIBRARY_DIRS = [path.join(MKL_ROOT, 'lib', 'ia32'),]
                if path.isdir(
                        path.join(path.dirname(MKL_ROOT), 'lib', 'ia32')):
                    BLAS_LIBRARY_DIRS.append(
                        path.join(path.dirname(MKL_ROOT), 'lib', 'ia32'))
            else:
                raise Exception('MKLROOT set, but could not find library dir')
        if MKL_THREADING in ('intel', 'iomp'):
            BLAS_LIBRARIES.append('mkl_intel_thread')
            BLAS_LIBRARIES.append('iomp5')
        elif MKL_THREADING in ('gnu', 'gomp'):
            BLAS_LIBRARIES.append('mkl_gnu_thread')
            BLAS_LIBRARIES.append('gomp')
        elif MKL_THREADING == 'sequential':
            BLAS_LIBRARIES.append('mkl_sequential')
        else:
            raise ValueError('Invalid MKL_THREADING setting')
        BLAS_LIBRARIES.append('mkl_core')
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
        BLAS_LIBRARIES = ['gfortran', 'openblas']
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
    else:
        raise Exception('One of OPENBLASROOT, MKLROOT must be set')
elif platform.system() == 'Darwin':
    FLAGS += ['-flax-vector-conversions', '-stdlib=libc++']
    DEFINES.append(('HAVE_CLAPACK', None))
    BLAS_LIBRARIES = []
    BLAS_LIBRARY_DIRS = []
    BLAS_INCLUDES = []
    LD_FLAGS = ['-framework', 'Accelerate', '-stdlib=libc++']
else:
    raise Exception('OS unsupported... for now')

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
    library_dirs=BLAS_LIBRARY_DIRS,
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
    cmdclass = {'build_ext': CustomBuildExtCommand},
    setup_requires=SETUP_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    ext_modules=[KALDI_LIBRARY],
    namespace_packages=['pydrobert'],
)
