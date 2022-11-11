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

"""Execute a LogoVM program."""

import logging
import operator
import random
from math import trunc

from logoasm.parser import get_symbol, set_symbol

from logovm import rom
from logovm.machinery import (
    reg,
    pc_stack,
    Flags,
    stack_pop,
    stack_push,
    stack_peek,
    set_flag,
    unset_flag,
    set_pos,
    set_pixel,
    halt,
)

from logovm.errors import InvalidAddress, TypeMismatch


def idiv():
    """Execute instruction: IDIV."""
    reg[2] = stack_pop()
    reg[3] = stack_pop()
    reg[0] = operator.floordiv(reg[0], reg[1])
    reg[1] = operator.mod(reg[0], reg[1])
    stack_push(reg[0])
    stack_push(reg[1])


def compare(value):
    """Execute instruction: CMP."""
    lhs = stack_peek()
    logging.debug("VALUE: %s", value)
    try:
        rhs = float(value)
    except ValueError:
        rhs = get_symbol(value)["value"]
    if not (
        isinstance(lhs, (int, float))
        and isinstance(rhs, (int, float))
        or (isinstance(lhs, str) and isinstance(rhs, str))
    ):
        raise TypeMismatch("CMP", rhs, lhs)
    if lhs < rhs:
        reg[0] = -1
    elif lhs > rhs:
        reg[0] = +1
    else:
        reg[0] = 0


def jump(target):
    """Execute jump for instructions: JP, JZ, JNZ, JMORE, JLESS."""
    reg[5] = int(get_symbol(target)["pc"])
    if reg[5] < 0:
        set_flag(Flags.EXC)
        raise InvalidAddress(reg[5])
    pc_stack[-1] = int(reg[5])


def jump_relative(value):
    """Execute instruction: JR."""
    logging.debug("JUMP: %s", value)
    try:
        reg[5] = int(value)
    except ValueError:
        reg[5] = int(get_symbol(value)["pc"])
    if reg[5] < 0:
        set_flag(Flags.EXC)
        raise InvalidAddress(reg[5])
    pc_stack[-1] += reg[5]


def jump_if(oper):
    """Implement jump operators that compare to R0."""
    logging.debug("Conditional JUMP: %s", open)
    opers = {
        "==": operator.eq,
        "!=": operator.ne,
        "<": operator.lt,
        ">": operator.gt,
    }

    def wrap_jmp(cmp):
        def do_jump(target):
            logging.debug("JUMP: R0 = %s | TST = %s", reg[0], cmp(reg[0], 0))
            if cmp(reg[0], 0):
                jump(target)

        return do_jump

    return wrap_jmp(opers[oper])


def ret():
    """Implement command RET."""
    pc_stack.pop()
    logging.debug("RET: %s", pc_stack)


def label(lbl):
    """Implement label support."""
    logging.debug("LABEL: %s", lbl)
    set_symbol(lbl, pc=pc_stack[-1])


def binop(oper):
    """Implement arithmetic binary operators."""
    logging.debug("BINOP: %s", oper)

    def binary_op(operation):
        def exec_op():
            reg[1] = stack_pop()
            reg[0] = stack_pop()
            reg[0] = operation(reg[0], reg[1])
            stack_push(reg[0])

        return exec_op

    opers = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "**": operator.pow,
    }
    return binary_op(opers[oper])


def push(value):
    """Implement command PUSH."""
    logging.debug("PUSH: %s", value)
    if isinstance(value, str):
        try:
            try:
                value = int(value)
            except ValueError:
                value = float(value)
        except ValueError:
            # What to do if value is a string? Push only pushes values.
            pass
    stack_push(value)


def pop():
    """Implement command POP."""
    logging.debug("POP")
    reg[0] = stack_pop()


def dup():
    """Implement command DUP."""
    logging.debug("DUP")
    pop()
    stack_push(reg[0])
    stack_push(reg[0])


def load(var):
    """Implement command LOAD."""
    variable = get_symbol(var)
    reg[0] = variable["value"]
    stack_push(reg[0])


def store(var):
    """Implement command STORE."""
    logging.debug("STORE: %s STACK: %s", var, stack_peek())
    variable = get_symbol(var)
    reg[0] = stack_pop()
    variable["value"] = reg[0]


def rand():
    """Implement command RAND."""
    reg[0] = random.random()
    logging.debug("RANDOM: %s", reg[0])
    push(reg[0])


def truncate():
    """Implement command TRUNC."""
    reg[0] = trunc(stack_pop())
    logging.debug("TRUNC: %s", reg[0])
    push(reg[0])


def call(function_id):
    """Implement command CALL."""
    logging.debug("CALL: %s", function_id)
    fn = get_symbol(function_id)
    if fn["type"] == "INT":
        rom.internal[fn["name"]]()
    elif fn["type"] == "FUNC":
        pc_stack.append(-1)
        call_stack_sz = len(pc_stack)
        while call_stack_sz == len(pc_stack):
            pc_stack[-1] += 1
            logging.debug("PC: %s", repr(pc_stack))
            pc = pc_stack[-1]
            if not 0 <= pc < len(fn["code"]):
                logging.critical("Invalid PC: %s: %s", function_id, pc)
                raise InvalidAddress(pc)
            execute_command(fn["code"][pc])
    else:
        raise Exception(
            f"Invalid symbol type: expected FUNC/INT, got {fn['type']}"
        )


def execute_command(cmd):
    """Execute a LogoASM command."""
    logging.debug("EXEC: %s", cmd)
    cmd, *param = cmd.split(" ", 1)
    cmd = "LABEL" if cmd == ":" else cmd
    to_call = cmds[cmd]
    if param:
        to_call(param[0])
    else:
        to_call()


cmds = {
    "PUSH": push,
    "POP": pop,
    "DUP": dup,
    "LOAD": load,
    "STOR": store,
    "CALL": call,
    "CMP": compare,
    "JR": jump_relative,
    "JP": jump,
    "JZ": jump_if("=="),
    "JNZ": jump_if("!="),
    "JMORE": jump_if(">"),
    "JLESS": jump_if("<"),
    "RET": ret,
    "HALT": halt,
    "LABEL": label,
    "ADD": binop("+"),
    "SUB": binop("-"),
    "MUL": binop("*"),
    "DIV": binop("/"),
    "IDIV": idiv,
    "POW": binop("**"),
    "TRUNC": truncate,
    "RAND": rand,
    "SET": set_flag,
    "UNSET": unset_flag,
    "MVTO": set_pos,
    "SETPX": set_pixel,
}
