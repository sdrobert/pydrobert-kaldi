# Copyright 2021 Sean Robertson

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Fixtures for pytests"""

import os
import locale

import pytest

from tempfile import NamedTemporaryFile
from tempfile import mkdtemp
from shutil import rmtree

locale.setlocale(locale.LC_ALL, "C")


def pytest_runtest_setup(item):
    if any(mark.name == "pytorch" for mark in item.iter_markers()):
        pytest.importorskip("torch")


@pytest.fixture
def temp_file_1_name():
    temp = NamedTemporaryFile(delete=False, suffix="_1")
    temp.close()
    yield temp.name
    os.remove(temp.name)


@pytest.fixture
def temp_file_2_name():
    temp = NamedTemporaryFile(delete=False, suffix="_2")
    temp.close()
    yield temp.name
    os.remove(temp.name)


@pytest.fixture
def temp_file_3_name():
    temp = NamedTemporaryFile(suffix="_2", delete=False)
    temp.close()
    yield temp.name
    os.remove(temp.name)


@pytest.fixture
def temp_dir():
    dir_name = mkdtemp()
    yield dir_name
    rmtree(dir_name)


@pytest.fixture(autouse=True)
def logging_cleanup():
    yield
    from pydrobert.kaldi.logging import deregister_all_loggers_for_kaldi

    deregister_all_loggers_for_kaldi()
