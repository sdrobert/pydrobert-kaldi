"""Test package metadata"""

import pydrobert.kaldi


def test_version():
    assert pydrobert.kaldi.__version__ != "inplace"
