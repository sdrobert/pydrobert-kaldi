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

import platform
import sys

from distutils.spawn import find_executable
from os import environ
from os import path
from os import walk
from re import findall
from setuptools import setup
from setuptools.extension import Extension
import numpy as np

IS_64_BIT = sys.maxsize > 2 ** 32
ON_WINDOWS = platform.system() == "Windows"

if ON_WINDOWS:
    LIBRARY_SUFFIXES = {"lib"}
elif platform.system() == "Darwin":
    LIBRARY_SUFFIXES = {"a", "dylib"}
else:
    LIBRARY_SUFFIXES = {"a", "so"}

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
        RE_CMD_LEX = r""""((?:\\["\\]|[^"])*)"|'([^']*)'|(\\.)|(&&?|\|\|?|\d?'
            r'\>|[<])|([^\s'"\\&|<>]+)|(\s+)|(.)"""
    else:
        RE_CMD_LEX = r""""((?:""|\\["\\]|[^"])*)"?()|(\\\\(?=\\*")|\\")|(&&?|\|\|?'
            r'|\d?>|[<])|([^\s"&|<>]+)|(\s+)|(.)"""
    args = []
    accu = None  # collects pieces of one arg
    for qs, qss, esc, pipe, word, white, fail in findall(RE_CMD_LEX, s):
        if word:
            pass  # most frequent
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
            word = qs.replace('\\"', '"').replace("\\\\", "\\")
            if platform == 0:
                word = word.replace('""', '"')
        else:
            word = qss  # may be even empty; must be last
        accu = (accu or "") + word
    if accu is not None:
        args.append(accu)
    return args


def mkl_setup(roots, mkl_threading=None):
    found_mkl_libs = {
        "mkl_rt": False,
        "mkl_intel": False,
        "mkl_intel_lp64": False,
        "mkl_intel_thread": False,
        "mkl_gnu_thread": False,
        "mkl_sequential": False,
        "mkl_tbb_thread": False,
    }
    blas_library_dirs = set()
    blas_includes = set()
    for root in roots:
        root = path.abspath(root)
        for root_name, _, base_names in walk(root):
            for base_name in base_names:
                if base_name.split(".")[-1] in LIBRARY_SUFFIXES:
                    library_name = base_name.rsplit(".", maxsplit=1)[0]
                    if not ON_WINDOWS:
                        if library_name.startswith("lib"):
                            library_name = library_name[3:]
                        else:
                            library_name = None  # not sure what to do with this
                else:
                    library_name = None
                if library_name in found_mkl_libs and not found_mkl_libs[library_name]:
                    found_mkl_libs[library_name] = True
                    blas_library_dirs.add(root_name)
                elif base_name == "mkl.h" and not blas_includes:
                    blas_includes.add(root_name)
    if not blas_includes:
        raise Exception("Could not find mkl.h")
    blas_library_dirs = list(blas_library_dirs)
    blas_includes = list(blas_includes)
    if mkl_threading is None:
        if found_mkl_libs["mkl_rt"]:
            mkl_threading = "dynamic"
        elif found_mkl_libs["mkl_intel_thread"]:
            mkl_threading = "intel"
        elif found_mkl_libs["mkl_tbb_thread"]:
            mkl_threading = "tbb"
        elif found_mkl_libs["mkl_sequential"]:
            mkl_threading = "sequential"
        elif found_mkl_libs["mkl_gnu_thread"]:
            mkl_threading = "gnu"
        else:
            raise Exception("Could not find a threading library for MKL")
    if mkl_threading == "dynamic":
        blas_libraries = ["mkl_rt"]
    else:
        blas_libraries = ["mkl_intel_lp64"] if IS_64_BIT else ["mkl_intel"]
        if mkl_threading in ("intel", "iomp"):
            blas_libraries += ["mkl_intel_thread", "iomp5"]
        elif mkl_threading in ("gnu", "gomp"):
            blas_libraries += ["mkl_gnu_thread", "gomp"]
        elif mkl_threading == "tbb":
            blas_libraries.append("mkl_tbb_thread")
        elif mkl_threading == "sequential":
            blas_libraries.append("mkl_sequential")
        else:
            raise Exception("Invalid MKL_THREADING_TYPE: {}".format(mkl_threading))
        blas_libraries.append("mkl_core")
    if not all(found_mkl_libs[lib] for lib in blas_libraries):
        raise Exception(
            "MKL_THREADING_TYPE=={} requires {} libs".format(
                mkl_threading, blas_libraries
            )
        )
    return {
        "BLAS_LIBRARIES": blas_libraries,
        "BLAS_LIBRARY_DIRS": blas_library_dirs,
        "BLAS_INCLUDES": blas_includes,
        # 'LD_FLAGS': ['-Wl,--no-as-needed'],
        "DEFINES": [("HAVE_MKL", None)],
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
                if base_name.split(".")[-1] in LIBRARY_SUFFIXES:
                    library_name = base_name.rsplit(".", maxsplit=1)[0]
                    if not ON_WINDOWS:
                        if library_name.startswith("lib"):
                            library_name = library_name[3:]
                        else:
                            library_name = None  # not sure what to do with this
                else:
                    library_name = None
                if library_name in library_names and not library_names[library_name]:
                    library_names[library_name] = True
                    library_dirs.add(root_name)
                elif base_name in headers and not headers[base_name]:
                    headers[base_name] = True
                    include_dirs.add(root_name)
    if not all(library_names.values()):
        raise Exception(
            "Could not find {}".format(
                tuple(key for key, val in library_names.items() if not val)
            )
        )
    if not all(headers.values()):
        raise Exception(
            "Could not find {}".format(
                tuple(key for key, val in headers.items() if not val)
            )
        )
    ret = dict(extra_entries_on_success)
    ret["BLAS_LIBRARIES"] = list(library_names)
    ret["BLAS_LIBRARY_DIRS"] = list(library_dirs)
    ret["BLAS_INCLUDES"] = list(include_dirs)
    return ret


def openblas_setup(roots):
    return blas_setup(
        roots,
        ("openblas",),
        ("cblas.h", "lapacke.h"),
        {"DEFINES": [("HAVE_OPENBLAS", None)]},
    )


def atlas_setup(roots):
    # FIXME(sdrobert): There are a variety of ways that atlas could've been distributed.
    # I'm assuming Fedora b/c it works with my CI.
    return blas_setup(
        roots,
        ("satlas", "tatlas"),
        ("cblas.h", "clapack.h"),
        {"DEFINES": [("HAVE_ATLAS", None)]},
    )


def lapacke_setup(roots):
    # only relies on the routines from lapack, so don't link to lapacke
    return blas_setup(
        roots,
        ("blas", "cblas", "lapack"),
        ("cblas.h", "lapacke.h"),
        {"DEFINES": [("HAVE_OPENBLAS", None)]},
    )


def clapack_setup(roots):
    return blas_setup(
        roots,
        ("blas", "lapack", "f2c", "clapack"),
        ("cblas.h", "f2c.h", "clapack.h"),
        {"DEFINES": [("HAVE_CLAPACK", None)]},
    )


def accelerate_setup():
    return {
        "DEFINES": [("HAVE_CLAPACK", None)],
        "LD_FLAGS": ["-framework", "Accelerate"],
    }


def noblas_setup():
    return {"DEFINES": [("HAVE_NOBLAS", None)]}


PWD = path.abspath(path.dirname(__file__))
PYTHON_DIR = path.join(PWD, "python")
SRC_DIR = path.join(PWD, "src")
SWIG_DIR = path.join(PWD, "swig")
DEFINES = [
    ("KALDI_DOUBLEPRECISION", environ.get("KALDI_DOUBLEPRECISION", "0")),
]
LD_FLAGS = []
if platform.system() != "Windows":
    FLAGS = ["-std=c++11", "-m64" if IS_64_BIT else "-m32", "-msse", "-msse2", "-FPIC"]
    if platform.system() == "Darwin":
        FLAGS += ["-flax-vector-conversions", "-stdlib=libc++"]
        LD_FLAGS += ["-stdlib=libc++"]
    DEFINES += [
        ("_GLIBCXX_USE_CXX11_ABI", "0"),
        ("HAVE_EXECINFO_H", "1"),
        ("HAVE_CXXABI_H", None),
    ]
    LIBRARIES = ["m", "dl"]
else:
    FLAGS = []
    LIBRARIES = []
    DEFINES += []
SRC_FILES = []
INCLUDE_DIRS = [SRC_DIR, np.get_include()]
LIBRARY_DIRS = []

if find_executable("swig"):
    SRC_FILES.append(path.join(SWIG_DIR, "pydrobert", "kaldi.i"))
elif path.exists(path.join(SWIG_DIR, "pydrobert", "kaldi_wrap.cpp")):
    print(
        "SWIG could not be found, but kaldi_wrap.cpp exists. Using that",
        file=sys.stderr,
    )
    SRC_FILES.append(path.join(SWIG_DIR, "pydrobert", "kaldi_wrap.cpp"))
else:
    print(
        "SWIG could not be found and kaldi_wrap.cpp does not exist. Cannot " "succeed",
        file=sys.stderr,
    )
    sys.exit(1)
for base_dir, _, files in walk(SRC_DIR):
    SRC_FILES += [path.join(base_dir, f) for f in files if f.endswith(".cc")]

# Adds additional libraries. Primarily for alpine libc (musllinux build),
# which doesn't package execinfo by default.
LIBRARIES += cmdline_split(environ.get("ADDITIONAL_LIBS", ""))

MKL_ROOT = cmdline_split(environ.get("MKLROOT", ""))
OPENBLAS_ROOT = cmdline_split(environ.get("OPENBLASROOT", ""))
ATLAS_ROOT = cmdline_split(environ.get("ATLASROOT", ""))
CLAPACK_ROOT = cmdline_split(environ.get("CLAPACKROOT", ""))
LAPACKE_ROOT = cmdline_split(environ.get("LAPACKEROOT", ""))
USE_ACCELERATE = environ.get("ACCELERATE", None)
NUM_BLAS_OPTS = sum(
    bool(x)
    for x in (
        MKL_ROOT,
        OPENBLAS_ROOT,
        ATLAS_ROOT,
        USE_ACCELERATE,
        CLAPACK_ROOT,
        LAPACKE_ROOT,
    )
)
if NUM_BLAS_OPTS > 1:
    raise Exception("Only one BLAS type should be specified")
elif NUM_BLAS_OPTS:
    if MKL_ROOT:
        BLAS_DICT = mkl_setup(MKL_ROOT, environ.get("MKL_THREADING_TYPE", None))
    elif OPENBLAS_ROOT:
        BLAS_DICT = openblas_setup(OPENBLAS_ROOT)
    elif ATLAS_ROOT:
        BLAS_DICT = atlas_setup(ATLAS_ROOT)
    elif CLAPACK_ROOT:
        BLAS_DICT = clapack_setup(CLAPACK_ROOT)
    elif LAPACKE_ROOT:
        BLAS_DICT = lapacke_setup(LAPACKE_ROOT)
    elif platform.system() == "Darwin":
        BLAS_DICT = accelerate_setup()
    else:
        raise Exception("Accelerate is only available on OSX")
else:
    BLAS_DICT = noblas_setup()


LIBRARIES += BLAS_DICT.get("BLAS_LIBRARIES", [])
LIBRARY_DIRS += BLAS_DICT.get("BLAS_LIBRARY_DIRS", [])
INCLUDE_DIRS += BLAS_DICT.get("BLAS_INCLUDES", [])
LD_FLAGS += BLAS_DICT.get("LD_FLAGS", [])
DEFINES += BLAS_DICT.get("DEFINES", [])
FLAGS += BLAS_DICT.get("FLAGS", [])


KALDI_LIBRARY = Extension(
    "pydrobert.kaldi._internal",
    sources=SRC_FILES,
    libraries=LIBRARIES,
    library_dirs=LIBRARY_DIRS,
    include_dirs=INCLUDE_DIRS,
    extra_compile_args=FLAGS,
    extra_link_args=LD_FLAGS,
    define_macros=DEFINES,
    swig_opts=["-py3", "-c++", "-builtin", "-castmode", "-O", "-I{}".format(SWIG_DIR)],
    language="c++",
)


setup(ext_modules=[KALDI_LIBRARY])
