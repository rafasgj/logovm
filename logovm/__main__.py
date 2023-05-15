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

"""Entry point for runing logovm programs."""

import logging

import argparse

import sys
import importlib

from logovm import __extensions__
from logovm.loader import LogoVMLoader, DataTranslator
from logovm.machine import LogoVM
from logovm.errors import ExtensionError


def cli_parser():
    """Parse command line."""
    parser = argparse.ArgumentParser(
        prog="logovm",
        description="LogoVM: a Logo virtual machine.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {'.'.join(str(x) for x in LogoVM.__version__)}",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="count",
        dest="debug",
        default=0,
        help="Set debug mode. Add multiple times for increased detail.",
    )
    parser.add_argument(
        "-o",
        "--osname",
        nargs=1,
        dest="osname",
        action="store",
        required=False,
        help="Set extension to use.",
    )
    parser.add_argument(
        "program",
        metavar="PROGRAM",
        help="Program to execute",
    )

    return parser.parse_args()


def main():
    """Execute a LogoVM program."""
    options = cli_parser()

    debuglevel = 30 - 10 * options.debug

    logging.basicConfig(level=debuglevel)

    try:
        logovm = LogoVM()
        with open(options.program, "rb") as progfile:
            osinit, *machine_data = LogoVMLoader.load_program(
                progfile, LogoVM.__version__
            )
        logovm.setup(*machine_data)
        if options.osname:
            osname = options.osname[0]
        else:
            osname = DataTranslator.parse_data(osinit, [("name", "s")])["name"]
        # load extension (currently limited to LogoVM provided ones).
        importlib.import_module(f"logovm.{osname.lower()}")
        # init extension
        try:
            extension = __extensions__[osname]
        except KeyError:
            raise ExtensionError(f"Invalid extension: {osname}") from None
        extension(logovm, osinit)
        logovm.execute()
        return 0
    except FileNotFoundError as fnfe:
        print(fnfe, file=sys.stderr)
    return 1


if __name__ == "__main__":
    main()
