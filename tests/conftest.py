# This file is part of LogoVM
#
# Copyright (C) 2023 Rafael Guterres Jeffman
#
# This software is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <https://www.gnu.org/licenses/>.

"""Tests for LogoVM example code."""

import pytest

from example_programs import gen_program, get_example_program_and_data

from logovm.machine import LogoVM
from logovm.loader import LogoVMLoader


@pytest.fixture
def program_code():
    """Retrieve code and data for a program."""

    def get_program(name):
        return gen_program(*get_example_program_and_data(name))

    return get_program


@pytest.fixture
def logovm():
    """Retrieve a configured LogoVM."""

    def get_logovm(program_data, os_class):
        vminstance = LogoVM()
        osinit, *machine_data = LogoVMLoader.load_program(
            program_data, LogoVM.__version__
        )
        vminstance.setup(*machine_data)
        os_class(vminstance, osinit)
        return vminstance

    return get_logovm
