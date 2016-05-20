"""Setup for pydrobert.kaldi"""

from __future__ import print_function

import os
import shlex
import sys

import numpy
import pkgconfig

from setuptools import Extension
from setuptools import setup

assert pkgconfig.exists('kaldi-base')
assert pkgconfig.exists('kaldi-matrix')
assert pkgconfig.exists('kaldi-thread')
assert pkgconfig.exists('kaldi-util')
python_dir = os.path.abspath('python')
src_dir = os.path.abspath('src')
include_dir = os.path.abspath('include')

with open('README.rst') as f:
    readme_text = f.read()

kaldi_libraries = {'kaldi-base', 'kaldi-thread', 'kaldi-util', 'kaldi-matrix'}
kaldi_library_dirs = set()
kaldi_include_dirs = {include_dir, numpy.get_include()}

# pkg-config returns in unicode, so we should cast in case of py2.7
kaldi_compiler_args = shlex.split(
    pkgconfig.cflags('kaldi-util kaldi-matrix kaldi-base kaldi-thread'))
define_symbols = [] # extract for swig
idx = 0
while idx < len(kaldi_compiler_args):
    if kaldi_compiler_args[idx][:2] == '-I':
        if len(kaldi_compiler_args[idx]) == 2:
            del kaldi_compiler_args[idx]
            kaldi_include_dirs.add(kaldi_compiler_args[idx])
        else:
            kaldi_include_dirs.add(kaldi_compiler_args[idx][2:])
        del kaldi_compiler_args[idx]
    elif kaldi_compiler_args[idx][:2] == '-D':
        define_symbols.append(kaldi_compiler_args[idx])
        idx += 1
    else:
        idx += 1
kaldi_linker_args = shlex.split(
    pkgconfig.libs('kaldi-util kaldi-base kaldi-matrix kaldi-thread'))
idx = 0
while idx < len(kaldi_linker_args):
    if kaldi_linker_args[idx][:2] == '-L':
        if len(kaldi_linker_args[idx]) == 2:
            del kaldi_linker_args[idx]
            kaldi_library_dirs.add(kaldi_linker_args[idx])
        else:
            kaldi_library_dirs.add(kaldi_linker_args[idx][2:])
        del kaldi_linker_args[idx]
    elif kaldi_linker_args[idx][:2] == '-l':
        kaldi_libraries.add(kaldi_linker_args[idx][2:])
        del kaldi_linker_args[idx]
    else:
        idx += 1

swig_opts = ['-c++', '-builtin', '-Wall'] + define_symbols + \
        ['-I' + x for x in kaldi_include_dirs]

kaldi_module = Extension(
    'pydrobert.kaldi._internal',
    sources=[
        os.path.join(include_dir, 'pydrobert', 'kaldi.i'),
        os.path.join(src_dir, 'pydrobert', 'kaldi', 'vector.cpp'),
        os.path.join(src_dir, 'pydrobert', 'kaldi', 'matrix.cpp'),
    ],
    library_dirs=list(kaldi_library_dirs),
    libraries=list(kaldi_libraries),
    # runtime_library_dirs=list(kaldi_library_dirs),
    include_dirs=list(kaldi_include_dirs),
    language='c++',
    extra_compile_args=kaldi_compiler_args,
    extra_link_args=kaldi_linker_args,
    swig_opts=swig_opts,
)

setup(
    name='pydrobert-kaldi',
    ext_modules=[kaldi_module],
    namespace_packages=['pydrobert'],
    package_dir={'':python_dir},
    packages=['pydrobert', 'pydrobert.kaldi'],
    long_description=readme_text,
    zip_safe=False,
    py_modules=['pydrobert.kaldi.tables'],
)
