from codecs import open
from os import environ
from os import path
from os import walk
from setuptools import setup
from setuptools.extension import Extension
from sys import version_info

PWD = path.abspath(path.dirname(__file__))
PYTHON_DIR = path.join(PWD, 'python')
SRC_DIR = path.join(PWD, 'src')
SWIG_DIR = path.join(PWD, 'swig')
DEFINES = [
    ('KALDI_DOUBLEPRECISION', environ.get('KALDI_DOUBLEPRECISION', '0')),
    # ('_GLIBCXX_USE_CXX11_ABI', '0'),
]
FLAGS = ['-std=c++11']

if 'MKLROOT' in environ:
    assert False, "FIXME - Untested"
    MKL_ROOT = path.abspath(environ['MKLROOT'])
    if not path.isdir(path.join(MKL_ROOT, 'include')):
        BLAS_INCLUDES = [path.join(MKL_ROOT, 'include')]
    else:
        raise Exception('MKLROOT set, but could not find include dir')
    if path.isdir(path.join(MKL_ROOT, 'lib', 'em64t')):
        BLAS_LIBRARY_DIRS = [path.join(MKL_ROOT, 'lib', 'em64t')]
    elif path.isdir(path.join(MKL_ROOT, 'lib', 'intel64')):
        BLAS_LIBRARY_DIRS = [path.join(MKL_ROOT, 'lib', 'intel64')]
    else:
        raise Exception('MKLROOT set, but could not find library dir')
    BLAS_LIBRARIES = ['mkl_solver_lp64_sequential', ]
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
        raise Exception('OPENBLASROOT set, but could not find library')
    BLAS_LIBRARIES = ['gfortran', 'openblas']
    DEFINES.append(('HAVE_OPENBLAS', None))
else:
    raise Exception('One of OPENBLASROOT, MKLROOT must be set')

# Get the long description from the README file
with open(path.join(PWD, 'README.rst'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

SRC_FILES = [path.join(SWIG_DIR, 'pydrobert', 'kaldi.i')]
for base_dir, _, files in walk(SRC_DIR):
    SRC_FILES += [path.join(base_dir, f) for f in files if f.endswith('.cc')]

try:
    import numpy as np
    NPY_INCLUDES = np.get_include()
except ImportError:
    raise Exception('Numpy needed for install')

INSTALL_REQUIRES = ['numpy', 'six', 'future']
if version_info < (3, 0):
    INSTALL_REQUIRES.append('enum34')
SETUP_REQUIRES = ['pytest-runner', 'numpy']
TESTS_REQUIRE = ['pytest']

KALDI_LIBRARY = Extension(
    'pydrobert.kaldi._internal',
    sources=SRC_FILES,
    libraries=['pthread'] + BLAS_LIBRARIES,
    runtime_library_dirs=BLAS_LIBRARY_DIRS,
    library_dirs=BLAS_LIBRARY_DIRS,
    include_dirs=[SRC_DIR, NPY_INCLUDES] + BLAS_INCLUDES,
    extra_compile_args=FLAGS,
    define_macros=DEFINES,
    swig_opts=['-c++', '-builtin', '-Wall', '-I{}'.format(SWIG_DIR)],
    language='c++',
)

setup(
    name='pydrobert-kaldi',
    version='1.0.0', #FIXME(sdrobert)
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
    packages=['pydrobert', 'pydrobert.kaldi'],
    setup_requires=SETUP_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    ext_modules=[KALDI_LIBRARY],
    namespace_packages=['pydrobert'],
    package_dir={'':PYTHON_DIR},
)
