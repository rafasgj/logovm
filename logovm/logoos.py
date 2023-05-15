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

"""LogoOS is the base for 'OS' implementation for LogoVM."""

import logging

from logovm import register_extension
from logovm.loader import DataTranslator
from logovm.errors import InvalidOS


class LogoOS:  # pylint: disable=too-few-public-methods
    """Implement basic functions provided by an OS for the LogoVM."""

    __version__ = (0, 2)

    def __init__(self, logo_vm, init):
        """Initialize LogoVM OS."""
        logging.debug("Initialize LogoOS")
        self.ready = False
        LogoOS.__set_interrupts(self, logo_vm)
        try:
            records = [
                ("osname", "s"),
                ("version_major", "B"),
                ("version_minor", "B"),
            ]
            LogoOS.configure(self, DataTranslator.parse_data(init, records))
        except Exception:  # pylint: disable=broad-except
            self.ready = False
        else:
            self.ready = True

    def __set_interrupts(self, logo_vm):
        logo_vm.set_interrupt(0, lambda _: None)  # Shutdown
        logo_vm.set_interrupt(
            1,  # WRITE
            lambda machine: (
                print(
                    "".join(
                        [str(machine.pop()) for y in range(machine.pop())][
                            ::-1
                        ]
                    ),
                    end="",
                    file=machine.console[1],
                ),
            ),
        )
        logo_vm.set_interrupt(
            2,  # READ
            lambda machine: machine.push(DataTranslator.autoconvert(input())),
        )

    # def __decode_init(self, logo_vm, header_data):
    #    with io.BytesIO(header_data) as infile:
    #        check_header_mark(infile, "LogoOS", "OS Name")
    #        check_version(infile, LogoOS.__version__)
    #    return namedtuple("Config", "")()._asdict()

    def configure(self, config_data):
        """Configure OS."""
        if config_data["osname"] != "LogoOS":
            raise InvalidOS(f"Unsupported OS: {config_data['osname']}")
        logging.debug("Configured LogoOS: %s", repr(config_data))


# Register extension
register_extension("LogoOS", LogoOS)
