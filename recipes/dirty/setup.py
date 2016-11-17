"""Setup for pydrobert.kaldi... dirty"""

from __future__ import print_function

import os
import platform
import shlex
import sys

import numpy

from setuptools import Extension
from setuptools import setup

kaldi_root = os.environ.get('KALDI_ROOT')
if kaldi_root is None:
    print('Environment variable KALDI_ROOT is not set', file=sys.stderr)
    exit(1)
kaldi_root = os.path.abspath(kaldi_root)
kaldi_src = os.path.join(kaldi_root, 'src')
kaldi_base = os.path.join(kaldi_src, 'base')
kaldi_thread = os.path.join(kaldi_src, 'thread')
kaldi_matrix = os.path.join(kaldi_src, 'matrix')
kaldi_util = os.path.join(kaldi_src, 'util')
kaldi_library_dirs = set()
kaldi_runtime_dirs = set()
kaldi_libraries = set()
for kaldi_dir in (kaldi_base, kaldi_thread, kaldi_matrix, kaldi_util):
    dym_dir_libs = set(
        fn for fn in os.listdir(kaldi_dir)
        if fn.endswith('.so') or fn.endswith('.dylib')
    )
    if dym_dir_libs:
        kaldi_runtime_dirs.add(kaldi_dir)
        kaldi_libraries.add('kaldi-' + os.path.basename(kaldi_dir))
        continue
    static_dir_libs = set(
        fn for fn in os.listdir(kaldi_dir)
        if fn.endswith('.a')
    )
    if static_dir_libs:
        kaldi_library_dirs.add(kaldi_dir)
        kaldi_libraries.add('kaldi-' + os.path.basename(kaldi_dir))
        continue
    print('Could not find library in {}'.format(kaldi_dir), file=sys.stderr)
    exit(1)

kaldi_include_dirs = [kaldi_src]

python_dir = os.path.abspath('python')
src_dir = os.path.abspath('src')
swig_include_dir = os.path.abspath('include')
cur_path = os.path.abspath('.')

def resolve_relative(lst):
    new_list = []
    resolve = None
    resolve_end = None
    for elem in lst:
        if elem[:2] in ('-I', '-L'):
            new_list.append(elem[:2])
            resolve = 0
            if elem in ('-I', '-L'):
                continue # no space before flag allowed
            elem = elem[2:].strip()
            resolve_end = len(elem)
        elif '-rpath=' in elem:
            resolve = elem.find('-rpath=') + 7
            resolve_end = elem.find(',', resolve)
            if resolve_end == -1:
                resolve_end = len(elem)
        if resolve is not None:
            if elem[resolve] == '/':
                new_list.append(elem)
            else:
                new_list.append(os.path.abspath(
                    os.path.join(kaldi_src, elem[resolve:resolve_end])))
            resolve = None
        else:
            new_list.append(elem)
    return new_list

with open('kaldi_cxxflags') as file_obj:
    text = file_obj.read()
    kaldi_cxxflags = resolve_relative(shlex.split(text))
idx = 0
while idx < len(kaldi_cxxflags):
    if kaldi_cxxflags[idx] == '-I':
        del kaldi_cxxflags[idx]
        if not kaldi_cxxflags[idx].startswith('..'):
            kaldi_include_dirs.append(kaldi_cxxflags[idx])
        del kaldi_cxxflags[idx]
    else:
        idx += 1

kaldi_ldflags = []
# with open('kaldi_ldflags') as file_obj:
#     text = file_obj.read()
#     kaldi_ldflags = resolve_relative(shlex.split(text))
# idx = 0
# while idx < len(kaldi_ldflags):
#     if kaldi_ldflags[idx] == '-Wl,': # removing rpath stripped options
#         del kaldi_ldflags[idx]
#     elif '-rpath=' in kaldi_ldflags[idx]:
#         del kaldi_ldflags[idx]
#         start = kaldi_ldflags[idx].find('-rpath=')
#         end = kaldi_ldflags[idx].find(',', start + 7)
#         if end == -1:
#             end = len(kaldi_ldflags[idx])
#         dymlib_path = kaldi_ldflags[idx][(start + 7):end]
#         if 'openfst' not in dymlib_path:
#             kaldi_runtime_dirs.add(dymlib_path)
#         kaldi_ldflags[idx] = kaldi_ldflags[idx][:start] + \
#                 kaldi_ldflags[idx][(end+1):]
#     else:
#         idx += 1
# if we're on OS X, runtime libary dirs are not added as "rpath" options
# to the linker (they're just -L flags)
if platform.system() == 'Darwin' and kaldi_runtime_dirs:
    new_flag = '-Wl'
    for path in kaldi_runtime_dirs:
        new_flag += ',-rpath,{}'.format(path)
    assert len(new_flag) > 3
    kaldi_ldflags.append(new_flag)

kaldi_ldlibs = []
# with open('kaldi_ldlibs') as file_obj:
#     text = file_obj.read()
#     kaldi_ldlibs = resolve_relative(shlex.split(text))
# idx = 0
# while idx < len(kaldi_ldlibs):
#     if kaldi_ldlibs[idx] == '-L':
#         del kaldi_ldlibs[idx]
#         del kaldi_ldlibs[idx]
#     elif kaldi_ldlibs[idx] == '-lfst' or \
#             kaldi_ldlibs[idx].find('libfst') != -1:
#         del kaldi_ldlibs[idx]
#     else:
#         idx += 1

kaldi_module = Extension(
    'pydrobert.kaldi._internal',
    sources=[
        os.path.join(swig_include_dir, 'pydrobert', 'kaldi.i'),
    ],
    libraries=list(kaldi_libraries),
    include_dirs=[numpy.get_include()] + list(kaldi_include_dirs),
    language='c++',
    extra_compile_args=kaldi_cxxflags,
    library_dirs=list(kaldi_library_dirs),
    runtime_library_dirs=list(kaldi_runtime_dirs),
    extra_link_args=kaldi_ldlibs + kaldi_ldflags,
    swig_opts=[
        '-c++', '-builtin',
        "-I{}".format(swig_include_dir),
    ],
)

setup(
    name='pydrobert-kaldi',
    ext_modules=[kaldi_module],
    namespace_packages=['pydrobert'],
    package_dir={'':python_dir},
    packages=['pydrobert', 'pydrobert.kaldi'],
    py_modules=['pydrobert.kaldi.tables'],
)
