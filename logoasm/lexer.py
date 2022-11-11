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

"""LogoVM lexer."""

import logging

from ply import lex
from ply.lex import TOKEN


class IllegalCharacter(Exception):
    """Lexer exception."""

    def __init__(self, char, line):
        """Initialize error with detected invalid char."""
        super().__init__(f"Illegal character: '{char}', at line {line}")


# Characters to be ignored by lexer.
t_ignore = " \t\r"  # pylint: disable=invalid-name

RESERVED = (
    ".CODE",
    ".DATA",
    ".INIT",
    ".START",
    "RET",
    "HALT",
    "CALL",
    "PUSH",
    "POP",
    "DUP",
    "LOAD",
    "STOR",
    "CMP",
    "JP",
    "JZ",
    "JNZ",
    "JMORE",
    "JLESS",
    "DEF",
    "ADD",
    "SUB",
    "MUL",
    "DIV",
    "IDIV",
    "POW",
    "TRUNC",
    "RAND",
    "SET",
    "UNSET",
    "MVTO",
    "SETPX",
)
NON_RESERVED = ("NUMBER", "STRING", "ID", "LABEL")
OPERATORS = {
    #    r"\.": "DOT",
    ":": "COLON",
    #    r"\"|\'": "QUOTE",
    #    r"\*\*": "POWER",
    #    "\+": "PLUS",
    #    "-": "MINUS",
    #    "\*": "TIMES",
    #    "/": "DIVIDE",
    #    "%": "MODULUS",
    #    "==": "EQUALTO",
    #    "=": "ASSIGN",
    #    ">": "GT",
    #    "<": "LT",
    #    ">=": "GE",
    #    "<=": "LE",
    #    r"\&\&": "AND",
    #    r"\|\|": "OR",
}

tokens = tuple(
    tuple(r[1:] if r.startswith(".") else r for r in RESERVED)
    + NON_RESERVED
    + tuple(OPERATORS.values())
)

globals().update({f"t_{v}": k for k, v in OPERATORS.items()})


@TOKEN(r"[.](CODE|DATA|START|INIT)")
def t_CODE(t):  # pylint: disable=invalid-name
    """Extract code directives."""
    logging.log(5, "DIRECTIVE: '%s'", t.value)
    t.value = t.value[1:].upper()
    t.type = t.value
    return t


@TOKEN(r"[_a-zA-Z][_a-zA-Z0-9]*")
def t_ID(t):  # pylint: disable=invalid-name
    """Extract an identifier."""
    logging.log(5, "ID: '%s'", t.value)
    uppervalue = t.value.upper()
    if uppervalue in RESERVED:
        t.type = uppervalue
    else:
        t.type = "ID"
    return t


@TOKEN(r"[:][_a-zA-Z][_a-zA-Z0-9]*")
def t_LABEL(t):  # pylint: disable=invalid-name
    """Extract a label definition."""
    logging.log(5, "LABEL: '%s'", t.value)
    t.value = t.value[1:]
    return t


@TOKEN(r"'[^']*'|\"[^\"]*\"")
def t_STRING(t):  # pylint: disable=invalid-name
    """Extract an string."""
    logging.log(5, "STRING: '%s'", t.value)
    t.value = t.value[1:-1]
    return t


@TOKEN(r"[+-]?\d+([.]\d*)?")
def t_NUMBER(t):  # pylint: disable=invalid-name
    """Extract a number."""
    logging.log(5, "NUMBER: '%s'", t.value)
    if "." in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t


@TOKEN(r"\#[^\n]*")
def t_COMMENT(token):  # pylint: disable=invalid-name
    """Ignore comments."""
    logging.log(5, "Comment: '%s'", token.value)


@TOKEN(r"\n+")
def t_newline(token):
    """Count new lines."""
    logging.log(5, "NL: %d", len(token.value))
    # For some unknown reason, new lines are being doubled
    token.lexer.lineno += len(token.value) // 2


def t_error(t):
    """Report lexer error."""
    raise IllegalCharacter(t.value[0], t.lexer.lineno)


def lexer():
    """Create a new lexer object."""
    return lex.lex()
