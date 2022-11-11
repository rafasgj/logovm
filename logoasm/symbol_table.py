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

"""Logo VM parser symbol table implementation."""


# Hold the parser symbol table
symtable = {}


def add_symbol(symbol, sym_type, lineno=0, **kwargs):
    """Create new symbol in the symbol table."""
    if symbol in symtable:
        old_line = symtable[symbol]["line"]
        raise Exception(
            f"Redeclaration of symbol:{lineno}: '{symbol}'. "
            f"Previously declared at line {old_line}"
        )

    kwargs["name"] = symbol
    kwargs["type"] = sym_type
    kwargs["lineno"] = lineno
    symtable[symbol] = kwargs


def set_symbol(symbol, **kwargs):
    """Set values of a symbol in symbol table."""
    if "name" in kwargs:
        raise Exception("InternalError: Cannot modify symbol 'name'.")
    sym = symtable[symbol]
    if "line" in kwargs:
        if not sym["lineno"] < 0:
            raise Exception("InternalError: Cannot modify symbol 'line'.")
    sym.update(kwargs)


def get_symbol(symbol):
    """Retrieve symbol from symbol table."""
    return symtable.get(symbol)


def remove_symbol(symbol):
    """Remove symbol from symbol table."""
    del symtable[symbol]


def increment_symbol_usage(symbol, lineno, amount=1):
    """Increment symbol attribute 'usage' by the given amount."""
    sym = get_symbol(symbol)
    if sym is None:
        raise Exception(f"Unknown symbol:{lineno}:'{symbol}'")
    usage = sym.get("usage", 0) + amount
    set_symbol(symbol, usage=usage)
