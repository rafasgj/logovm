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

"""Program execution tests."""

# pylint: disable=too-many-arguments

import io

from unittest.mock import patch, mock_open
from textwrap import dedent

import pytest

from logovm.logoos import LogoOS
from logovm.turtleos import TurtleOS


@pytest.mark.parametrize(
    "name, datain, dataout",
    [
        ("hello", None, "Hello World!\n"),
        ("hello2", None, "Hello World!\n"),
        ("swap", None, "1"),
        ("circle_area", "5\n", "Circle ray: Circle area: 78.5398\n"),
    ],
)
@pytest.mark.parametrize("vmos", [LogoOS, TurtleOS])
def test_program_with_os(logovm, program_code, datain, dataout, name, vmos):
    """Test execution of example programs."""
    with (
        io.StringIO() as stdout,
        io.StringIO(datain) as stdin,
        io.StringIO() as stderr,
        io.BytesIO(program_code(name)) as program,
    ):
        logovm(program, vmos).execute(
            stdin=stdin, stdout=stdout, stderr=stderr
        )
        observed = stdout.getvalue()
        err_output = stderr.getvalue()
    assert err_output == "", "Stderr is not empty."
    assert dataout == observed, "Mismatch in stdout."


@pytest.mark.parametrize(
    "name, dataout, graphic_out",
    [
        (
            "square",
            "000.0",
            """\
            P2
            10 10
            255
            255 255 255 255 255 255 255 255 255 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 255 255 255 255 255 255 255 255 255
            """,
        ),
        (
            "square2",
            "0090.0",
            """\
            P2
            10 10
            255
            255 255 255 255 255 255 255 255 255 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 0 0 0 0 0 0 0 0 255
            255 255 255 255 255 255 255 255 255 255
            """,
        ),
        ("clrscr", "", ""),
    ],
)
def test_program_with_graphics(
    logovm, program_code, name, dataout, graphic_out
):
    """Test execution of example programs with turtle graphics."""
    with (
        io.StringIO() as stderr,
        io.StringIO() as stdout,
        io.StringIO() as stdin,
        io.BytesIO(program_code(name)) as program,
    ):
        testvm = logovm(program, TurtleOS)  # only TurtleOS support graphics
        # Execute program mocking 'open()'
        openmock = mock_open()
        with patch("builtins.open", openmock, create=True):
            testvm.execute(stdin=stdin, stdout=stdout, stderr=stderr)
            graphic_result = "\n".join(
                line
                for line in (
                    "".join(
                        " ".join(args)
                        for (name, args, _) in openmock.mock_calls
                        if name.endswith("write")
                    )
                ).split("\n")
                if not line.startswith("#")
            )
        observed = stdout.getvalue()
        err_output = stderr.getvalue()
    assert err_output == "", "Stderr is not empty."
    assert dataout == observed, "Mismatch in stdout."
    assert dedent(graphic_out) == graphic_result, "Mismatch in graphic file."
