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

"""LogoVM implementation."""

import logging

import sys
import operator
from random import random

from logovm.errors import LogoVMError, ExtensionError


class LogoVMInvalidAccess(LogoVMError):
    """Invalid data access."""


class LogoVMEmptyStack(LogoVMInvalidAccess):
    """Stack underflow error."""


class LogoVMStackOverflow(LogoVMError):
    """Stack overflow error."""


class LogoMemory:
    """Implement the LogoVM memory handling operations."""

    def __init__(self, maxstack=2**14):
        """Initialize object with a maximum stack size."""
        self.heap = []
        self.stack = []
        self.maxstack = maxstack
        self.debug = []

    def get_heap(self, addr):  # pragma: no cover
        """Retrieve data from the heap."""
        if not 0 <= addr < len(self.heap):
            raise LogoVMInvalidAccess(f"Invalid heap address: {addr}")
        return self.heap[addr]

    def set_heap(self, addr, value):  # pragma: no cover
        """Set data on the heap."""
        if not 0 <= addr < len(self.heap):
            raise LogoVMInvalidAccess(f"Invalid heap address: {addr}")
        self.heap[addr] = value

    def peek(self):
        """Check the value on the top of the stack, without removing it."""
        return self.stack[-1]

    def pop(self):
        """Pop value from the stack."""
        if not self.stack:  # pragma: no cover
            raise LogoVMEmptyStack("Empty stack")
        return self.stack.pop()

    def push(self, value):
        """Push value onto the stack."""
        if len(self.stack) - 1 >= self.maxstack:  # pragma: no cover
            raise LogoVMStackOverflow("Stack overflow")
        self.stack.append(value)


class LogoVM:
    """Implements a stack machine to run Logo-like programs.."""

    __version__ = (0, 2)

    def __init__(self, **options):
        """
        Initialize machine.

        Available options:

            maxstack: Maximum stack size. (Default to 2**14)
            stdin: Standard input stream.
            stdout: Standard output stream.
            stderr: Standard error stream.
        """
        self.regs = [0] * 8
        self.flags = 0
        self.code = []
        self.intr = [lambda logo_vm: None] * 16
        self.callstack = []
        self.mem = LogoMemory(maxstack=options.get("maxstack", 2**14))
        self.running = False
        self.console = (
            options.get("stdin", sys.stdin),
            options.get("stdout", sys.stdout),
            options.get("stderr", sys.stderr),
        )

    def setup(self, code, data=None, debug=None):
        """Set VM with code, data and debug records."""
        self.code = code
        self.mem.heap = data
        self.mem.debug = debug

    @staticmethod
    def __check_type(values, type_list):
        if not isinstance(values, (list, tuple)):
            values = [values]
        for value in values:
            if not isinstance(value, type_list):  # pragma: no cover
                raise ValueError("Invalid data type for operation.")

    def pop(self):
        """Pop a value from the machine stack."""
        self.regs[1] = self.mem.pop()
        return self.regs[1]

    def push(self, value):
        """Push a value to the machine stack."""
        self.mem.push(value)

    def pop_type(self, type_list):
        """Pop a value with a specific type from machine stack."""
        self.__check_type(self.mem.peek(), type_list)
        return self.pop()

    def set_flag(self, flag):
        """Set flag."""
        self.flags |= 1 << flag

    def unset_flag(self, flag):
        """Unset flag."""
        self.flags &= ~(1 << flag)

    def is_set(self, flag):
        """Return state of the selected flag."""
        self.regs[0] = self.flags & (1 << flag)
        return self.regs[0] != 0

    def __jump_cond(self, target, cond):
        if cond:
            self.pc = target - 1

    def __cmp(self):  # pragma: no cover
        rhs = self.pop()
        lhs = self.pop()
        if lhs < rhs:
            self.regs[0] = -1
        elif lhs > rhs:
            self.regs[0] = +1
        else:  # ==
            self.regs[0] = 0

    def __binop(self, oper):
        operation = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "**": operator.pow,
        }
        self.regs[2] = self.pop_type((int, float))  # rhs
        self.regs[1] = self.pop_type((int, float))  # lhs
        self.regs[1] = operation[oper](self.regs[1], self.regs[2])
        self.push(self.regs[1])

    def __bitop(self, oper):  # pragma: no cover
        operation = {
            "&": operator.and_,
            "|": operator.or_,
            "^": operator.xor,
            "<<": operator.lshift,
            ">>": operator.rshift,
        }
        self.regs[2] = self.pop_type(int)  # rhs
        self.regs[1] = self.pop_type(int)  # lhs
        self.regs[1] = operation[oper](self.regs[1], self.regs[2])
        self.push(self.regs[1])

    def __idiv(self):  # pragma: no cover
        self.regs[2] = self.pop_type((int, float))  # rhs
        self.regs[1] = self.pop_type((int, float))  # lhs
        self.regs[3] = self.regs[1] % self.regs[2]
        self.regs[1] = self.regs[1] // self.regs[2]
        self.push(int(self.regs[3]))
        self.push(self.regs[1])

    def __invert(self):  # pragma: no cover
        self.regs[1] = operator.invert(self.pop_type(int))
        self.push(self.regs[1])

    def __roll_right(self):  # pragma: no cover
        self.regs[1] = self.pop_type(int)
        mask = (self.regs[1] & 0x01) << 63
        self.regs[1] = (self.regs[1] >> 1) | mask
        self.push(self.regs[1])

    def __cat(self):  # pragma: no cover
        self.regs[2] = self.pop_type(str)  # lhs
        self.regs[1] = self.pop_type(str)  # rhs
        self.regs[1] = f"{self.regs[1]}{self.regs[2]}"
        self.push(self.regs[1])

    def __str_chop(self):  # pragma: no cover
        self.regs[1] = self.pop_type(int)
        self.regs[2] = self.pop_type(str)
        if not 0 <= self.regs[1] < len(self.regs[2]):
            raise ValueError("Invalid value for SCHOP.")
        self.push((self.regs[2])[self.regs[1] :])  # pylint: disable=E1136
        self.push((self.regs[2])[: self.regs[1]])  # pylint: disable=E1136

    def __str_offset(self):  # pragma: no cover
        self.regs[2] = self.pop_type(str)
        self.regs[1] = self.pop_type(int)
        if not 0 <= self.regs[1] < len(self.regs[2]):
            raise ValueError("Invalid value for SOFF.")
        self.push((self.regs[2])[self.regs[1]])  # pylint: disable=E1136)

    def __intr(self, intr):
        if not 0 <= intr < len(self.intr):  # pragma: no cover
            raise ExtensionError(f"Invalid interruption: {intr}")
        logging.debug("LogoVM: INTR: %d", intr)
        logging.debug("LogoVM: INTR Function: %s", repr(self.intr[intr]))
        self.intr[intr](self)

    def __halt(self):
        self.running = False

    def __ret(self):  # pragma: no cover
        self.pc = self.callstack.pop()[0]

    # operations
    def __get_op(self, command):
        __commands = {
            # No arg, no Stack
            0: lambda: None,  # NOP
            1: self.__halt,  # HALT
            2: self.__ret,  # RET
            3: random,  # RAND
            6: lambda: self.__jump_cond(  # SKIPZ
                self.pc + 2, self.regs[0] == 0
            ),
            7: lambda: self.__jump_cond(  # SKIPNZ
                self.pc + 2, self.regs[0] != 0
            ),
            # No arg, One Stack
            8: self.pop,  # POP
            9: lambda: [self.push(value) for value in [self.pop()] * 2],  # DUP
            10: lambda: self.push(int(self.pop())),  # INT (TRUNC)
            11: lambda: self.push(float(self.pop())),  # FLOAT
            12: lambda: self.push(str(self.pop())),  # STRING
            16: lambda: self.push(abs(self.pop())),  # ABS
            17: self.__invert,  # NOT
            # No arg, Two Stack
            24: lambda: [  # SWAP
                self.push(value) for value in [self.pop(), self.pop()]
            ],
            25: self.__cmp,  # CMP
            # No arg, Two Stack NUMBER
            30: lambda: self.__binop("+"),  # ADD
            31: lambda: self.__binop("-"),  # SUB
            32: lambda: self.__binop("*"),  # MUL
            33: lambda: self.__binop("+"),  # DIV
            34: self.__idiv,  # IDIV
            35: lambda: self.__binop("**"),  # POW
            # No arg, Two Stack INT
            41: lambda: self.__bitop("&"),  # AND
            42: lambda: self.__bitop("|"),  # OR
            43: lambda: self.__bitop("^"),  # XOR
            44: lambda: self.__bitop(">>"),  # SHFTR
            45: lambda: self.__bitop("<<"),  # SHFTL
            46: self.__roll_right,  # ROLLR
            # No arg, two stack (string)
            125: self.__cat,  # CAT
            # No arg, two stack (string + UINT)
            126: self.__str_chop,  # SCHOP - Chop string at offset
            127: self.__str_offset,  # SOFF - Character at string offset
            # One ADDR argument, no required stack
            128: lambda addr: self.push(self.mem.get_heap(addr)),  # LOAD
            129: lambda addr: self.__jump_cond(addr, True),  # JP
            130: lambda addr: self.__jump_cond(  # JLESS
                addr, self.regs[0] < 0
            ),
            131: lambda addr: self.__jump_cond(  # JMORE
                addr, self.regs[0] > 0
            ),
            132: lambda addr: self.__jump_cond(addr, self.regs[0] == 0),  # JZ
            133: lambda addr: self.__jump_cond(addr, self.regs[0] != 0),  # JNZ
            134: lambda addr: (  # CALL
                self.callstack.append(self.pc),
                self.__jump_cond(addr, True),
            ),
            # One ADDR argument, one stack
            140: lambda addr: (  # STORE
                # pylint: disable=C2801
                self.mem.set_heap(addr, self.pop())
                # pylint: enable=C2801
            ),
            # One UINT arg, no stack
            156: self.set_flag,  # SETF
            157: self.unset_flag,  # UNSETF
            158: self.is_set,  # ISSETF
            159: self.__intr,  # INTR
            # One INT argument, no stack
            160: self.push,  # PUSHI
            161: lambda value: self.__jump_cond(self.pc + value, True),  # JR
            # One DOUBLE arg
            192: self.push,  # PUSHD
            # One STRING arg
            224: self.push,  # PUSHS
        }
        # Flags
        return __commands.get(command)

    def set_interrupt(self, index, function):
        """Set one of the machine interrupt callbacks."""
        logging.debug("LogoVM: Setting INTR %d to %s", index, repr(function))
        self.intr[index] = function

    @property
    def pc(self):
        """Retrieve program counter."""
        return self.regs[-1]

    @pc.setter
    def pc(self, value):
        """Set program counter."""
        self.regs[-1] = value

    def execute(self, *args, **kwargs):
        """Execute a loaded program."""
        logging.info("LogoVM: Execute program")
        try:
            self.__execute(*args, **kwargs)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"{str(exception)} - PC={self.pc}", file=sys.stderr)
            if self.callstack:  # pragma: no cover
                print("Stack trace:", file=sys.stderr)
                print(
                    "\n".join(f"    {x}" for x in self.callstack),
                    file=sys.stderr,
                )

    def __execute(self, *args, **kwargs):
        """Execute a loaded program."""
        self.console = (
            kwargs.get("stdin", self.console[0]),
            kwargs.get("stdout", self.console[1]),
            kwargs.get("stderr", self.console[2]),
        )
        sys.stdin = self.console[0]
        # Load argumens to the Stack
        for arg in args:  # pragma: no cover
            try:
                arg = int(arg)
            except ValueError:
                try:
                    arg = float(arg)
                except ValueError:
                    pass
            self.push(arg)
        # start program
        self.running = True
        self.pc = -1
        while self.running:
            self.pc += 1
            if not 0 <= self.pc < len(self.code):
                raise LogoVMError(f"Invalid PC: {self.pc}")  # pragma: no cover
            cmd, *args = self.code[self.pc]
            logging.debug("LogoVM Instruction: %s - %s", cmd, repr(args))
            ops = self.__get_op(cmd)
            if ops:
                self.__exec_ops(ops, *args)
            else:
                raise LogoVMError(
                    f"Invalid command: {cmd}"
                )  # pragma: no cover
        self.intr[0](self)  # shutdown

    def __exec_ops(self, operation, *args):
        """Execute a single operation."""
        # Here is were "DEBUG" can be implemented.
        operation(*args)
