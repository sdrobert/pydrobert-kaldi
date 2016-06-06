"""Setup for pydrobert.kaldi"""

from __future__ import print_function

import os
import platform
import shlex
import sys

from setuptools import Extension
from setuptools import setup

kaldi_root = os.environ.get('KALDI_ROOT')
if kaldi_root is None:
    print('Environment variable KALDI_ROOT is not set', file=sys.stderr)
    sys.exit(1)
kaldi_src = os.path.abspath(os.path.join(kaldi_root, 'src'))

python_dir = os.path.abspath('python')
src_dir = os.path.abspath('src')
include_dir = os.path.abspath('include')

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
kaldi_include_dirs = {kaldi_src, os.path.join(kaldi_src, 'matrix')}
idx = 0
while idx < len(kaldi_cxxflags):
    if kaldi_cxxflags[idx] == '-I':
        del kaldi_cxxflags[idx]
        kaldi_include_dirs.add(kaldi_cxxflags[idx])
        del kaldi_cxxflags[idx]
    else:
        idx += 1

with open('kaldi_ldflags') as file_obj:
    text = file_obj.read()
    kaldi_ldflags = resolve_relative(shlex.split(text))
kaldi_runtime_dirs = {
    os.path.join(kaldi_src, 'base'),
    os.path.join(kaldi_src, 'thread'),
    os.path.join(kaldi_src, 'util'),
    os.path.join(kaldi_src, 'matrix'),
}
if platform.system() != 'Darwin':
    idx = 0
    while idx < len(kaldi_ldflags):
        if kaldi_ldflags[idx] == '-Wl,': # removing rpath stripped options
            del kaldi_ldflags[idx]
        elif '-rpath=' in kaldi_ldflags[idx]:
            start = kaldi_ldflags[idx].find('-rpath=')
            end = kaldi_ldflags[idx].find(',', start + 7)
            if end == -1:
                end = len(kaldi_ldflags[idx])
            kaldi_runtime_dirs.add(kaldi_ldflags[idx][(start + 7):end])
            kaldi_ldflags[idx] = kaldi_ldflags[idx][:start] + \
                    kaldi_ldflags[idx][(end+1):]
        else:
            idx += 1

with open('kaldi_ldlibs') as file_obj:
    text = file_obj.read()
    kaldi_ldlibs = resolve_relative(shlex.split(text))
kaldi_library_dirs = {
    kaldi_src,
    os.path.join(kaldi_src, 'base'),
    os.path.join(kaldi_src, 'thread'),
    os.path.join(kaldi_src, 'util'),
    os.path.join(kaldi_src, 'matrix'),
}
idx = 0
while idx < len(kaldi_ldlibs):
    if kaldi_ldlibs[idx] == '-Wl,':
        del kaldi_ldlibs[idx]
    elif '-rpath=' in kaldi_ldlibs[idx] and \
            platform.system() != 'Darwin':
        start = kaldi_ldlibs[idx].find('-rpath=')
        end = kaldi_ldlibs[idx].find(',', start + 7)
        if end == -1:
            end = len(kaldi_ldlibs[idx])
        kaldi_runtime_dirs.add(kaldi_ldlibs[idx][(start + 7):end])
        kaldi_ldlibs[idx] = kaldi_ldlibs[idx][:start] + \
                kaldi_ldlibs[idx][(end+1):]
    elif kaldi_ldlibs[idx] == '-L':
        del kaldi_ldlibs[idx]
        kaldi_library_dirs.add(kaldi_ldlibs[idx])
        del kaldi_ldlibs[idx]
    elif kaldi_ldlibs[idx][:2] == '-l':
        del kaldi_ldlibs[idx]
    else:
        idx += 1

kaldi_module = Extension(
    'pydrobert.kaldi._internal',
    sources=[
        os.path.join(include_dir, 'pydrobert', 'kaldi.i'),
    ],
    library_dirs=list(kaldi_library_dirs),
    libraries=[
        'kaldi-base',
        'kaldi-thread',
        'kaldi-util',
        'kaldi-matrix',
    ],
    include_dirs=[include_dir] + list(kaldi_include_dirs),
    language='c++',
    extra_compile_args=kaldi_cxxflags,
    runtime_library_dirs=list(kaldi_runtime_dirs),
    extra_link_args=kaldi_ldlibs + kaldi_ldflags,
    swig_opts=[
        '-c++', '-builtin',
        "-I{}".format(include_dir),
        "-I{}".format(kaldi_src),
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
