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

"""Implement an interpreter for the Logo VM."""

import logging

from ply import yacc

from logoasm import lexer
from logoasm.symbol_table import (
    add_symbol,
    set_symbol,
    get_symbol,
    increment_symbol_usage,
)


parser_error = False  # pylint: disable=invalid-name


class ParserObject(object):  # pylint: disable=R0205, R0903
    """Provides an object with arbitrary attributes."""

    def __init__(self, *_, **kwargs):
        """Initialize object with default attributes."""
        for k, v in kwargs.items():
            setattr(self, k, v)


def p_empty(_p):  # noqa: D205, D400, D403, D415
    """empty :"""


def p_program(p):  # noqa: D205, D400, D403, D415
    """program : start init data code"""
    p[0] = p[1] if not parser_error else None


def p_start(p):  # noqa: D205, D400, D403, D415
    """start : START ID"""
    logging.log(5, "START: %s", p[2])
    add_symbol(p[2], "FUNC", usage=1)
    p[0] = p[2]


def p_init(p):  # noqa: D205, D400, D403, D415
    """
    init : INIT NUMBER NUMBER NUMBER NUMBER
         | empty
    """
    if p[1] is None:
        return
    logging.log(5, "INIT parsed.")
    nums = []
    for i in range(2, len(p)):
        if isinstance(p[i], int):
            nums.append(p[i])
        else:
            raise Exception("INIT: InvalidType: Required INT got FLOAT.")

    add_symbol(
        "__turtle",
        "OBJECT",
        lineno=p.lineno(4),
        value=ParserObject(x=nums[0], y=nums[1], draw=True),
    )
    add_symbol(
        "__window",
        "OBJECT",
        lineno=p.lineno(2),
        value=ParserObject(w=nums[2], h=nums[3]),
    )


def p_data(_p):  # noqa: D205, D400, D403, D415, D401
    """
    data : DATA var_decl data_list
         | empty
    """


def p_var_decl(p):  # noqa: D205, D400, D403, D415
    """var_decl : ID value"""
    logging.log(5, "VAR: %s", p[1])
    add_symbol(
        p[1], "VAR", lineno=p.lineno(1), value=p[2].value, var_type=p[2].type
    )


def p_data_list(_p):  # noqa: D205, D400, D403, D415
    """
    data_list : var_decl data_list
              | empty
    """


def p_value(p):  # noqa: D205, D400, D403, D415
    """
    value : STRING
          | NUMBER
    """
    p[0] = ParserObject(value=p[1], type=type(p[1]).__name__)


def p_code(_p):  # noqa: D205, D400, D403, D415
    """code : CODE procedures"""


def p_procedures(_p):  # noqa: D205, D400, D403, D415
    """
    procedures : procedure procedures
               | empty
    """


def p_procedure(p):  # noqa: D205, D400, D403, D415
    """procedure : DEF ID COLON statements"""
    logging.log(5, "Procedure: %s", p[2])
    symbol = get_symbol(p[2])
    if symbol is None:
        add_symbol(p[2], "FUNC", lineno=p.lineno(2), code=p[4], usage=0)
    else:
        set_symbol(p[2], lineno=p.lineno(2), code=p[4])


def p_statements(p):  # noqa: D205, D400, D403, D415
    """statements : statement other_statements"""
    logging.log(5, "Statement(s): %s", p[1])
    logging.log(5, "Statements: %s", repr(p[2]))
    statement = p[1]
    other = []
    if len(p) > 2:
        other = p[2] or []
    st_list = [statement]
    st_list.extend(other)
    p[0] = st_list


def p_other_statements(p):  # noqa: D205, D400, D403, D415
    """
    other_statements : statement other_statements
                     | empty
    """
    logging.log(5, "Statement(o): %s", p[1])
    statement = p[1]
    if statement:
        other = []
        if len(p) > 2:
            other = p[2] or []
        st_list = [statement]
        st_list.extend(other)
        p[0] = st_list
    else:
        p[0] = []


def p_statement(p):  # noqa: D205, D400, D403, D415
    """
    statement : var_op
              | push_op
              | pop_op
              | call_op
              | end_op
              | jump
              | compare
              | label
              | DUP
              | operators
              | flag_ops
              | draw_ops
    """
    p[0] = "\n".join([p[i] for i in range(1, len(p))])
    logging.log(5, p[0])


def p_var_op(p):  # noqa: D205, D400, D403, D415
    """
    var_op : LOAD ID
        | STOR ID
    """
    if get_symbol(p[2]) is None:
        raise Exception(f"Undefined symbol:{p.lineno(2)}:'{p[2]}' ")
    p[0] = " ".join([p[1], p[2]])


def p_push_op(p):  # noqa: D205, D400, D403, D415
    """push_op : PUSH value"""
    p[0] = f"{p[1]} {p[2].value}"


def p_push_op_no_value(p):  # noqa: D205, D400, D403, D415
    """push_op : PUSH ID"""
    logging.warning(
        "Expected value instead of ID: %d. Did you mean 'LOAD'?", p.lineno(2)
    )
    p[0] = " ".join([p[1], "$ERR"])


def p_pop_op(p):  # noqa: D205, D400, D403, D415
    """pop_op : POP"""
    p[0] = p[1]


def p_call_op(p):  # noqa: D205, D400, D403, D415
    """call_op : CALL ID"""
    function = get_symbol(p[2])
    if not function:
        add_symbol(p[2], "FUNC", code=None, usage=1)
    elif function["type"] not in ["FUNC", "INT"]:
        raise Exception(
            f"Unexpected symbol type:'FUNC or INT':'{function['type']}' "
        )
    increment_symbol_usage(p[2], p.lineno(2))
    p[0] = f"{p[1]} {p[2]}"


def p_end_op(p):  # noqa: D205, D400, D403, D415
    """
    end_op : RET
        | HALT
    """
    p[0] = p[1]


def p_compare(p):  # noqa: D205, D400, D403, D415
    """
    compare : CMP value
            | CMP ID
    """
    if isinstance(p[2], str):
        if get_symbol(p[2]) is None:
            raise Exception(f"Undefined symbol:{p.lineno(2)}:{p[2]}")
        value = p[2]
    else:
        value = p[2].value
    p[0] = f"{p[1]} {value}"


def p_jump(p):  # noqa: D205, D400, D403, D415
    """
    jump : JP jmp_target
         | JZ jmp_target
         | JNZ jmp_target
         | JMORE jmp_target
         | JLESS jmp_target
    """
    p[0] = " ".join([p[1], p[2]])


def p_jmp_target(p):  # noqa: D205, D400, D403, D415
    """
    jmp_target : LABEL
               | NUMBER
    """
    if p.slice[1].type == "LABEL":
        label = get_symbol(p[1])
        if not label:
            add_symbol(p[1], "LABEL", usage=1)
        else:
            if label["type"] != "LABEL":
                raise Exception(
                    f"Unexpected Symbol Type:{p.lineno(1)}: '{p[1]}'"
                )
            increment_symbol_usage(p[1], p.lineno(1))
    else:
        if not isinstance(p[1], int):
            raise Exception("Jump require INT values or labels.")
    p[0] = p[1]


def p_label(p):  # noqa: D205, D400, D403, D415
    """label : LABEL"""
    lineno = p.lineno(1)
    sym = get_symbol(p[1])
    if sym is None:
        add_symbol(p[1], "LABEL", lineno=lineno, usage=0)
    else:
        if sym["type"] != "LABEL":
            raise Exception(f"Not a label:{lineno}: '{p[1]}'")
        set_symbol(p[1], lineno=lineno)
    logging.debug(
        "LABEL: %d: '%s' (%s)", lineno, p[1], "used" if sym else "unused"
    )
    p[0] = f"LABEL {p[1]}"


def p_operators(p):  # noqa: D205, D400, D403, D415
    """
    operators : ADD
        | SUB
        | MUL
        | DIV
        | IDIV
        | POW
        | TRUNC
        | RAND
    """
    p[0] = p[1]


def p_flag_ops(p):  # noqa: D205, D400, D403, D415
    """
    flag_ops : SET NUMBER
             | UNSET NUMBER
    """
    logging.log(5, "FLAG: %s: %s", p[1], p[2].value)
    if not isinstance(p[2], int):
        raise TypeError(f"Expected an integer value: {p[2].value}")
    p[0] = f"{p[1]} {p[2]}"


def p_drow_ops(p):  # noqa: D205, D400, D403, D415
    """
    draw_ops : MVTO
             | SETPX
    """
    logging.log(5, "DRAW_CMD: %s", p[1])
    p[0] = p[1]


def p_error(p):
    """Provide a simple error message."""
    global parser_error  # pylint: disable=global-statement,invalid-name
    parser_error = True
    if p:
        logging.critical("Unexpected token:%d: '%s'", p.lineno, p)
    else:
        logging.error("Syntax error at EOF.")


def parse_program(source):
    """Parse LogoASM program."""
    # Variables 'tokens' and 'symtable' will be provide by lexer and logovm.
    # pylint: disable=global-variable-not-assigned, invalid-name
    global symtable
    global tokens  # pylint: disable=global-variable-undefined, invalid-name
    # pylint: enable=global-variable-not-assigned, invalid-name
    tokens = lexer.tokens
    logolex = lexer.lexer()
    parser = yacc.yacc(start="program", debug=True)
    with open(source, "rt") as input_file:
        data = "\n".join(input_file.readlines())
    return parser.parse(data, lexer=logolex, tracking=False)
