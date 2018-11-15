# Copyright 2018 Sean Robertson

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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

from tempfile import NamedTemporaryFile
from tempfile import mkdtemp
from shutil import rmtree

import pytest


@pytest.fixture
def temp_file_1_name():
    temp = NamedTemporaryFile(delete=False, suffix='_1')
    temp.close()
    yield temp.name
    os.remove(temp.name)


@pytest.fixture
def temp_file_2_name():
    temp = NamedTemporaryFile(delete=False, suffix='_2')
    temp.close()
    yield temp.name
    os.remove(temp.name)


@pytest.fixture
def temp_file_3_name():
    temp = NamedTemporaryFile(suffix='_2', delete=False)
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
