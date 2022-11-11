# This file is part of LogoVM
#
# Copyright (C) 2022 Rafael Guterres Jeffman
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

"""LogoVM program."""

import sys
import argparse
import logging

from logovm.logovm import Flags, set_flag, call, stack_push

from logoasm.parser import add_symbol, get_symbol, parse_program
from logoasm.lexer import IllegalCharacter

import logovm.machinery
from logovm.loader import UndefinedReference, loader


def welcome(filename):
    """Print welcome message."""
    logging.info("Welcome to the LogoVM.")
    logging.info("Loading program: %s", filename)


def cli_parser():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="LogoVM",
        description="LogoVM is a Compiler teaching tool",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-n",
        "--netpbm",
        action="store_true",
        help="Forces PGM/PPM image output.",
    )
    group.add_argument(
        "-p", "--png", action="store_true", help="Forces PNG image output."
    )
    group.add_argument(
        "-j", "--jpg", action="store_true", help="Forces JPEG image output."
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="count",
        default=0,
        help="Turn on logging debug mode. Implies PGM/PPM graphics.",
    )
    parser.add_argument("filename", help="LogoASM source file name.")
    parser.add_argument("args", nargs="*", help="Program parameters.")

    return parser.parse_args()


def parse_command_line():
    """Parse command line arguments."""
    options = cli_parser()
    log_format = "%(levelname)s (%(funcName)s) %(message)s"
    level = 30 - (10 * (3 if options.debug > 3 else options.debug))
    logging.basicConfig(force=True, format=log_format, level=level)
    logging.addLevelName(5, "PARSER")
    if options.debug or options.netpbm:
        logovm.machinery.image_format = "pgm"
    elif options.jpg:
        logovm.machinery.image_format = "jpg"
    elif options.png:
        logovm.machinery.image_format = "png"
    for value in options.args:
        try:
            try:
                stack_push(int(value))
            except ValueError:
                stack_push(float(value))
        except ValueError:
            stack_push(value)
    return options.filename


def run_program(start):
    """Execute the program defined in symtable, starting from start."""
    # Load program
    if start is None:
        return 2

    loader()
    # start program
    call(start)
    return 0


def add_internal_functions():
    """Add ROM functions to symbol table using provided add_symbol function."""
    # Turtle functions.
    add_symbol("CLRSCR", "INT", lineno=0)
    add_symbol("MOVE", "INT", lineno=0)
    # Console functions
    add_symbol("READ", "INT", lineno=0)
    add_symbol("WRITE", "INT", lineno=0)


def main():
    """Entry point for the LogoVM."""
    program = parse_command_line()
    # initialize VM
    set_flag(Flags.PEN)
    add_internal_functions()
    welcome(program)
    # parse source code
    try:
        start = parse_program(program)
    except IllegalCharacter as illchar:
        logging.exception(str(illchar))
    except UndefinedReference as unref:
        logging.exception(str(unref))
    else:
        if start is None:
            return 2
        try:
            args = {}
            obj = get_symbol("__turtle")
            if obj:
                obj = obj["value"]
                args["x"] = obj.x
                args["y"] = obj.y
                obj = get_symbol("__window")
                if not obj:
                    raise Exception("InternalError: Window object undefined.")
                obj = obj["value"]
                args["width"] = obj.w
                args["height"] = obj.h
            logovm.machinery.init(**args)

            return run_program(start)
        except KeyboardInterrupt:
            logging.exception("SIGINT: Keyboard interrupt.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
