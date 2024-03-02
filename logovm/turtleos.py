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

"""TurtleOS implementation."""

import logging

import math
from collections import namedtuple
from datetime import datetime

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    HAS_PIL_IMAGE = False
else:  # pragma: no cover
    HAS_PIL_IMAGE = True

from logovm import register_extension
from logovm.loader import LogoVMLoader, DataTranslator
from logovm.logoos import LogoOS
from logovm.errors import InvalidOS, LogoVMOSError


class TurtleOSError(LogoVMOSError):
    """Specific TurtleOS errors."""


class TurtleOS(LogoOS):
    """Implement a LogoOS with Turtle Graphics."""

    __version__ = (0, 1)

    PEN = 1
    DRAW = 2

    def __init__(self, logo_vm, init):
        """Initialize TurtleOS."""
        super().__init__(logo_vm, init)
        logging.debug("Initializing TurtleOS")
        self.video = None
        self.turtle = (0, 0, 0)
        self.imageformat = "png" if HAS_PIL_IMAGE else "pgm"
        self.ready = False
        # pylint: disable=duplicate-code
        self.__set_interrupts(logo_vm)
        records = [
            ("osname", "s"),
            ("version_major", "B"),
            ("version_minor", "B"),
        ]
        config = DataTranslator.parse_data(init, records)
        # pylint: enable=duplicate-code
        if config["osname"] not in ["TurtleOS", "LogoOS"]:
            raise InvalidOS(  # pragma: no cover
                f"Invalid OS request: {config['osname']}"
            )
        version = (config["version_major"], config["version_minor"])
        if config["osname"] == "LogoOS":
            if not LogoVMLoader.check_version(version, LogoOS.__version__):
                raise InvalidOS(  # pragma: no cover
                    f"LogoOS: Invalid OS version: {version}"
                )
        if config["osname"] == "TurtleOS":
            if not LogoVMLoader.check_version(
                version, TurtleOS.__version__
            ):  # pragma: no cover
                raise InvalidOS(f"TurtleOS: Invalid OS version: {version}")
            records = [
                ("osname", "s"),
                ("version_major", "B"),
                ("version_minor", "B"),
                ("width", "H"),
                ("height", "H"),
                ("x", "H"),
                ("y", "H"),
                ("angle", "H"),
                ("imageformat", "B"),
            ]
            TurtleOS.configure(self, DataTranslator.parse_data(init, records))
            logo_vm.unset_flag(self.DRAW)
        self.ready = True
        logging.info("TurtleOS Initialized %s", repr(self.ready))

    def __set_interrupts(self, logo_vm):
        logo_vm.set_interrupt(0, self.shutdown)
        logo_vm.set_interrupt(3, self.set_pixel)
        logo_vm.set_interrupt(4, self.move)
        logo_vm.set_interrupt(5, self.move_to)
        logo_vm.set_interrupt(6, self.get_pos)
        logo_vm.set_interrupt(7, self.clear_screen)
        logo_vm.set_flag(self.PEN)

    def shutdown(self, logo_vm):
        """Shutdown TurtleOS."""
        logging.info("TurtleOS: SHUTDOWN")
        if logo_vm.is_set(self.DRAW):
            filename = datetime.now().strftime("%Y%m%d-%H%M%S")
            logging.debug("TurtleOS: HALT: %s %s", filename, self.imageformat)
            if self.imageformat.lower() in ["jpg", "png"]:
                self.__save_as_PIL(filename)  # pragma: no cover
            else:
                self.__save_as_PPM(filename)

    def __save_as_PIL(self, filename):  # pylint: disable=invalid-name
        channels, _, _, width, height, mem = self.video
        mode = "L" if channels == 1 else "RGB"
        Image.frombytes(mode, (width, height), bytes(mem)).save(
            f"{filename}.{self.imageformat}"
        )

    def __save_as_PPM(self, filename):  # pylint: disable=invalid-name
        channels, _, stride, width, height, mem = self.video
        mode = "P2" if channels == 1 else "P3"
        self.imageformat = "pgm" if channels == 1 else "ppm"
        with open(
            f"{filename}.{self.imageformat}", "wt", encoding="utf-8"
        ) as out:
            print(f"{mode}", file=out)
            print(
                f"# {filename}.{self.imageformat} "
                "generated with LogoVM/TurtleOS",
                file=out,
            )
            print(f"{width} {height}", file=out)
            print("255", file=out)
            for j in range(height):
                start = stride * j
                print(
                    " ".join(str(v) for v in mem[start : start + stride]),
                    file=out,
                )

    def configure(self, config_data):
        """Configure OS."""
        logging.debug("Configuring TurtleOS: %s", repr(config_data))
        width = config_data.get("width", 256)
        height = config_data.get("height", 192)
        # TODO: bpc and channels are not user configurable.
        bpc = config_data.get("bpc", 1)
        channels = config_data.get("channels", 1)
        self.reset_video(
            width=width, height=height, bpc=bpc, channels=channels
        )
        x, y, angle = self.turtle or (width >> 1, height >> 1, 90)
        self.turtle = (
            config_data.get("x", x),
            config_data.get("y", y),
            config_data.get("angle", angle) / 100.0,  # angle is in 100ths.
        )
        formats = {
            0: "png" if HAS_PIL_IMAGE else "pgm",
            1: "pgm",
            2: "png" if HAS_PIL_IMAGE else None,
            3: "jpg" if HAS_PIL_IMAGE else None,
        }
        self.imageformat = formats.get(config_data.get("imageformat", 0))
        logging.debug("Turtle OS image format: %s", self.imageformat)
        if not self.imageformat:  # pragma: no cover
            raise RuntimeError(
                "PIL is not available, unsupported 'imageformat'."
            )

    def reset_video(self, **kwargs):
        """Initialize video subsystem."""
        logging.info("TurtleOS: Initializing video memory.")
        VideoConfig = namedtuple(
            "VideoConfig", "channels bpc stride width height mem"
        )
        channels, bpc, _, width, height, _ = self.video or (
            1,
            1,
            0,
            256,
            192,
            None,
        )
        width = kwargs.get("width", width)
        height = kwargs.get("height", height)
        bpc = kwargs.get("bpc", bpc)
        channels = kwargs.get("channels", channels)
        stride = width * channels * bpc
        logging.info("TurtleOS: Video size: %d, %d", width, height)
        logging.info("TurtleOS: Video deght: %d, %d", channels, bpc)
        logging.info("TurtleOS: Video memory size: %d", stride * height)
        mem = [0] * (stride * height)
        self.video = VideoConfig(channels, bpc, stride, width, height, mem)

    def clear_screen(self, logo_vm):  # pragma: no cover
        """Clear graphic screen."""
        self.reset_video()
        logo_vm.unset_flag(self.DRAW)

    def __set_pixel(self, x, y, color):
        try:
            _, bpc, stride, width, height, mem = self.video
        except TypeError:  # pragma: no cover
            raise TurtleOSError("TurtleOS: Video not initialized.") from None
        if not (0 <= x < width and 0 <= y < height):  # pragma: no cover
            return
        pos = y * stride + x
        mem[pos : pos + bpc] = (color,)

    def set_pixel(self, logo_vm):
        """Set a pixel in video memory."""
        y = logo_vm.pop_type(int)  # POP
        x = logo_vm.pop_type(int)  # POP
        if logo_vm.is_set(self.PEN):
            self.__set_pixel(x, y, 255)
            logo_vm.set_flag(2)  # SETF 2

    def move(self, logo_vm):
        """Move turtle."""
        logging.info("TurtleOS: MOVE")
        angle = logo_vm.pop()
        length = logo_vm.pop()
        logging.debug("TurtleOS: move %d %g", length, angle)
        angle = 360.0 - (angle % 360)
        x0, y0, _ = self.turtle
        ang = angle * (math.pi / 180)
        x1 = int(x0 + (length - 1) * math.cos(ang))
        y1 = int(y0 + (length - 1) * math.sin(ang))
        self.turtle = (x1, y1, angle)
        if logo_vm.is_set(self.PEN):
            logging.debug(
                "TurtleOS: move: %d,%d - %d,%d @ %g", x0, y0, x1, y1, angle
            )
            self.__bresenham(logo_vm, (x0, y0), (x1, y1))

    def move_to(self, logo_vm):
        """Move turtle."""
        logging.info("TurtleOS: MOVETO")
        x0, y0, angle = self.turtle
        y1 = logo_vm.pop()
        x1 = logo_vm.pop()
        self.turtle = (x1, y1, angle)
        if logo_vm.is_set(self.PEN):
            logging.debug("TurtleOS: move_to: %d,%d - %d,%d", x0, y0, x1, y1)
            self.__bresenham(logo_vm, (x0, y0), (x1, y1))

    def get_pos(self, logo_vm):
        """Retrieve turtle position."""
        x, y, angle = self.turtle
        logo_vm.push(x)
        logo_vm.push(y)
        logo_vm.push((360.0 - angle) % 360)

    def __bresenham(self, logo_vm, start_point, end_point):
        if not self.video:  # pragma: no cover
            raise TurtleOSError("TurtleOS: Video not initialized.") from None
        if not logo_vm.is_set(self.PEN):  # pragma: no cover
            return
        # --
        x0, y0 = start_point
        x1, y1 = end_point
        dx = abs(x1 - x0)
        sx = -1 if x1 < x0 else +1
        dy = -abs(y1 - y0)
        sy = -1 if y1 < y0 else +1
        error = dx + dy
        while True:
            logo_vm.push(x0)
            logo_vm.push(y0)
            self.set_pixel(logo_vm)
            # end of LogoVM code
            if int(x0) == int(x1) and int(y0) == int(y1):
                break
            error2 = 2 * error
            if error2 >= dy:
                if int(x0) == int(x1):
                    break  # pragma: no cover
                error += dy
                x0 += sx
            if error2 <= dx:
                if int(y0) == int(y1):
                    break  # pragma: no cover
                error += dx
                y0 += sy


# Register extension
register_extension("TurtleOS", TurtleOS)
