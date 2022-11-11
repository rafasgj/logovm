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

"""Global stuff used by LogoVM."""

import logging

from math import copysign
from datetime import datetime

from logovm.errors import StackOverflowError, EmptyStackError

try:
    from PIL import Image
except ImportError:
    HAS_PIL_IMAGE = False
else:
    HAS_PIL_IMAGE = True


__turtle_default = (0, 0)
__turtle = (0, 0)
__window = None  # pylint: disable=invalid-name

flags = 0  # pylint: disable=invalid-name
reg = [None] * 6
stack = []
pc_stack = []
image_format = "PNG"  # pylint: disable=invalid-name

MAXSTACKSIZE = 256 * (2**20)  # 256MB elements stack size.


# Flag management
class Flags:  # pylint: disable=too-few-public-methods
    """Flag mappings."""

    MAXFLAG = 5
    PEN = 1
    DRAW = 2
    VERR = 3
    _UNUSED = 4
    EXC = 5


def __get_flag_index(flag):
    """Ensure flag index is valid."""
    flag = int(flag)
    if not 1 <= flag <= Flags.MAXFLAG:
        raise ValueError("Flag index must be in [1,{Flags.MAXFLAG}]")
    return flag


def set_flag(flag):
    """Set a flag."""
    global flags  # pylint: disable=global-statement, invalid-name
    logging.debug("BSET: %s: 0b%s", flag, f"{flags:0{Flags.MAXFLAG+1}b}")
    flag = __get_flag_index(flag)
    flags |= 1 << flag
    logging.debug("SET: %s: 0b%s", flag, f"{flags:0{Flags.MAXFLAG+1}b}")


def unset_flag(flag):
    """Unset a flag."""
    global flags  # pylint: disable=global-statement, invalid-name
    logging.debug("BUNSET: %s: 0b%s", flag, f"{flags:0{Flags.MAXFLAG+1}b}")
    flag = __get_flag_index(flag)
    flags &= ~(1 << flag)
    logging.debug("UNSET: %s: 0b%s", flag, f"{flags:0{Flags.MAXFLAG+1}b}")


def isset(flag):
    """Check if a flag is set."""
    logging.debug("ISSET: %d %s", flag, f"{flags:0{Flags.MAXFLAG+1}b}")
    return bool(flags & (1 << __get_flag_index(flag)))


# Video management
def __init_video(width, height):
    """Initialize video memory."""
    global __window  # pylint: disable=invalid-name, global-statement
    bpp = 1
    vidmem = [0] * (height * width * bpp)
    logging.debug(
        "width=%d  height=%d  bpp=%d  stride=%d",
        width,
        height,
        bpp,
        width * bpp,
    )
    __window = [width, height, bpp, width * bpp, vidmem]


def reset_video():
    """Reset video memory."""
    __init_video(__window[0], __window[1])
    unset_flag(Flags.DRAW)


def __save_video(filename):
    """Save video memory to a file name filename."""
    logging.debug("save_video: %s", filename)
    if isset(Flags.VERR):
        logging.warning("A video error occured.")
    if isset(Flags.DRAW):
        if HAS_PIL_IMAGE and image_format.lower() in ["jpg", "png"]:
            __save_as_PIL(filename)
        elif image_format.lower() in ["ppm", "pnm", "pgm", "netpbm", "pbm"]:
            __save_as_PPM(filename)


def __save_as_PIL(filename):  # pylint: disable=invalid-name
    """Save video memory using PIL."""
    logging.debug("Saving with PIL: %s %s", filename, image_format)
    logging.debug("WINDOW: %s", repr(__window))
    width, height, bpp, _stride, data = __window
    data = bytes(data)
    mode = "L" if bpp == 1 else "RGB"
    img = Image.frombytes(mode, (width, height), data)
    img.save(f"{filename}.{image_format.lower()}")


def __save_as_PPM(filename):  # pylint: disable=invalid-name
    """Save video memory using ASCII PPM (P2 or P3)."""
    logging.debug("Saving PNM: %s", filename)
    logging.debug("WINDOW: %s", repr(__window))
    width, height, bpp, stride, data = __window
    mode = "P2" if bpp == 1 else "P3"
    ext = "pgm" if bpp == 1 else "ppm"
    with open(f"{filename}.{ext}", "w", encoding="ascii") as out:
        print(mode, file=out)
        print(f"# {filename}.{ext}", file=out)
        print(f"{width} {height}", file=out)
        print("255", file=out)  # 8-bit per channel
        if isset(Flags.VERR):
            print("# WARNING: A video error occured.", file=out)
        for j in range(height):
            start = stride * j
            print(
                " ".join(str(v) for v in data[start : start + stride]),
                file=out,
            )
            print("".join(f"{v: 4d}" for v in data[start : start + stride]))


def __plot(x, y, color=255):
    """Set a pixel with the given color."""
    width, height, bpp, stride, vidmem = __window
    logging.debug("params: x=%s y=%s width=%s height=%s", x, y, width, height)
    if not 0 <= x < width:
        return
    if not 0 <= y < height:
        return
    if isinstance(color, (int, float)):
        color = [int(color)]
    else:
        color = [int(v) for v in color]
    if len(color) != bpp:
        set_flag(Flags.VERR)
        if bpp == 1:
            color = sum(color, 0) // len(color)
        else:
            color = color * 3
    color = color[0] if bpp == 1 else color
    x = round(x)
    y = round(y)
    position = stride * y + x * bpp
    vidmem[position] = color
    logging.debug("vidmem:x=%s y=%s c=%s pos=%s", x, y, color, position)
    set_flag(Flags.DRAW)


def set_pixel():
    """Implement instruction: SETPX."""
    __plot(*__turtle[:2], 255)


def draw_line():
    """Draw a line segment in video memory from current position to target."""
    x0, y0, x1, y1 = reg[:4]
    logging.debug("x0=%d y0=%d x1=%d y1=%d", x0, y0, x1, y1)
    if isset(Flags.PEN):
        dx = abs(x1 - x0)
        sx = copysign(1, x1 - x0)
        dy = -abs(y1 - y0)
        sy = copysign(1, y1 - y0)
        error = dx + dy

        while True:
            __plot(x0, y0)
            if round(x0) == round(x1) and round(y0) == round(y1):
                break
            error2 = 2 * error
            logging.debug("dx %s dy %s error %s e2 %s", dx, dy, error, error2)
            if error2 >= dy:
                if round(x0) == round(x1):
                    break
                error = error + dy
                x0 = x0 + sx
            if error2 <= dx:
                if round(y0) == round(y1):
                    break
                error = error + dx
                y0 = y0 + sy
    # Update turtle position.
    stack_push(x1, y1)
    set_pos()


# Turtle/Pointer management
def get_pos():
    """Get pointer position as (R0, R1)."""
    logging.debug("TURTLE: %s", repr(__turtle))
    reg[0] = __turtle[0]
    reg[1] = __turtle[1]
    return (reg[0], reg[1])


def set_pos():
    """Set pointer positon to (R0, R1)."""
    global __turtle  # pylint: disable=invalid-name, global-statement
    _, _, *extra = __turtle
    reg[1] = stack_pop()
    reg[0] = stack_pop()
    __turtle = (reg[0], reg[1], *extra)
    logging.debug("TURTLE: %s", repr(__turtle))


# Stack management
def stack_peek():
    """Peek value in the top of the stack."""
    return stack[-1] if stack else None


def stack_pop():
    """Pop a value from the stack."""
    if not stack:
        raise EmptyStackError()
    value = stack.pop()
    logging.debug("STACK: %s", repr(stack))
    return value


def stack_push(*args):
    """Push a value to the stack."""
    for value in args:
        if len(stack) < MAXSTACKSIZE:
            stack.append(value)
        else:
            raise StackOverflowError()
    logging.debug("STACK: %s", repr(stack))


# State management
def halt():
    """Shutdown machine."""
    filename = datetime.now().strftime("%Y%m%d-%H%M%S.%s")
    logging.debug("HALT: %s %s", filename, image_format)
    pc_stack.clear()
    __save_video(filename)


def init(**kwargs):
    """
    Initialize machine.

    Available options:
    - width: Graphics width in pixels. (int)
    - height: Grapics height in pixels. (int)
    """
    # pylint: disable=invalid-name
    global __turtle  # pylint: disable=global-statement
    global __turtle_default  # pylint: disable=global-statement
    width, height = kwargs.get("width", 256), kwargs.get("height", 192)
    x, y = kwargs.get("x", width // 2), kwargs.get("y", height // 2)
    __turtle_default = (x, y)
    __turtle = (x, y)
    __init_video(width, height)
    unset_flag(Flags.DRAW)
