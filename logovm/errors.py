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

"""Exception definitions for LogoVM."""


class LogoVMError(Exception):
    """Base class for all LogoVM Errors."""


class EmptyStackError(LogoVMError):
    """Empty stack error."""

    def __init__(self):
        """Initialize with proper message."""
        super().__init__("No values on stack.")


class StackOverflowError(LogoVMError):
    """Stack overflow error."""

    def __init__(self):
        """Initialize with proper message."""
        super().__init__("Stack Overflow.")


class InvalidAddress(LogoVMError):
    """Tried to access an invalid address."""

    def __init__(self, value):
        """Initialize with proper message."""
        super().__init__(f"Invalid address: {value}")


class TypeMismatch(LogoVMError):
    """Value type mismach for instruction."""

    def __init__(self, instruction, expected, observed):
        """Initialize with proper message."""
        super().__init__(
            f"Type mismatch: '{instruction}':'{expected}':'{observed}'"
        )
