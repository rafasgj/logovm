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

"""LogoVM program loader implementation."""

import logging

import struct
from io import BytesIO  # pylint: disable=no-name-in-module

from logovm.errors import InvalidLogoFile


class DataTranslator:
    """Provide methods to handle machine data."""

    @staticmethod
    def autoconvert(value):
        """Automatically convert 'value' in an int, float or str."""
        try:
            return int(value)
        except ValueError:  # pragma: no cover
            try:
                return float(value)
            except ValueError:
                return value

    @staticmethod
    def translate_data(data, datatype):
        """Get packed data and next data position."""
        if datatype == "raw":
            return data
        return struct.unpack(f"<{datatype}", data)[0]

    @staticmethod
    def read_number(datastream, datatype):
        """Read a number from datastream with the specified datatype."""
        if not isinstance(datatype, str):
            datatype = datatype.decode("utf-8")
        data_sizes = {
            "B": 1,
            "b": 1,
            "H": 2,
            "Q": 8,
            "q": 8,
            "d": 8,
        }
        datasz = data_sizes[datatype]
        return (
            DataTranslator.translate_data(datastream.read(datasz), datatype),
            datasz,
        )

    @staticmethod
    def read_string(datastream):
        """Read a zero-terminated string from datastream."""
        string = bytearray()
        bytes_read = 0
        while True:
            char = datastream.read(1)
            bytes_read += 1
            if char == b"":  # pragma: no cover
                raise ValueError("Unterminated String data.")
            if char == b"\0":
                break
            string.extend(char)
        return bytes(string).decode("utf-8"), bytes_read

    @staticmethod
    def parse_data(data, records):
        """Parse data given with the record definitions."""
        _res = {}
        with BytesIO(data) as datastream:
            for name, datatype in records:
                logging.debug("Data load: %s - %s", name, datatype)
                if datatype == "s":
                    _res[name], _ = DataTranslator.read_string(datastream)
                else:
                    _res[name], _ = DataTranslator.read_number(
                        datastream, datatype
                    )
        return _res


class LogoVMLoader:
    """Methods to parse LogoVM executable files."""

    @staticmethod
    def load_program(inputstream, min_version):
        """Load program data from stream."""
        with BytesIO(inputstream.read()) as datastream:
            LogoVMLoader.__load_header(datastream, min_version)
            vm_extension = LogoVMLoader.__load_extension(datastream)
            # read '.code' data
            if not LogoVMLoader.check_mark(datastream, ".CODE", "Code mark"):
                raise InvalidLogoFile("No .CODE section.")  # pragma: no cover
            code = LogoVMLoader.__load_code(datastream)
            # read '.data' data
            data = LogoVMLoader.__load_data(datastream)
            # read '.debg' data, if available
            debug = LogoVMLoader.__load_debug(datastream)
            # check if all data was read.
            if datastream.read(1):  # pragma: no cover
                raise InvalidLogoFile("Extra data on file.")
        #
        return vm_extension, code, data, debug

    @staticmethod
    def check_mark(datastream, mark, name):
        """Check daastream against a specific string mark."""
        if isinstance(mark, str):
            mark = mark.encode("utf-8")
        value = DataTranslator.translate_data(
            datastream.read(len(mark)), "raw"
        )
        if value:
            if value != mark:  # pragma: no cover
                raise InvalidLogoFile(f"{name} did not match: '{value}'")
            return True
        return False

    @staticmethod
    def check_version(candidate, target):
        """Compare versions."""
        major, minor = candidate
        vmajor, vminor = target
        return not (major > vmajor or (major == vmajor and minor > vminor))

    @staticmethod
    def __load_header(datastream, check_version):
        # magic
        LogoVMLoader.check_mark(datastream, "LOGO", "Magic")
        # machine header
        records = [
            ("version_major", "B"),
            ("version_minor", "B"),
        ]
        header = DataTranslator.parse_data(datastream.read(2), records)
        # version
        version = {header["version_major"], header["version_minor"]}
        if not LogoVMLoader.check_version(version, check_version):
            raise (  # pragma: no cover
                InvalidLogoFile(f"Cannot provide version: {version}")
            )

    @staticmethod
    def __load_extension(datastream):
        header = DataTranslator.parse_data(
            datastream.read(2), [("ext_size", "H")]
        )
        logging.debug("LogoVM: Extension header size: %d", header["ext_size"])
        return (
            datastream.read(header["ext_size"])
            if header["ext_size"] > 0
            else None
        )

    @staticmethod
    def __load_code(datastream):
        code_sz, _ = DataTranslator.read_number(datastream, "Q")
        code = []
        while code_sz > 0:
            cmd = datastream.read(1)[0]
            bread = 0
            data_type = None
            match cmd:
                case cmd if cmd < 128:  # no args
                    arg = None
                case cmd if cmd < 160:  # UINT/ADDR arg
                    data_type = "Q"
                case cmd if cmd < 192:  # INT arg
                    data_type = "q"
                case cmd if cmd < 224:  # DOUBLE arg
                    data_type = "d"  # pragma: no cover
                case _:  # STRING arg
                    arg, bread = DataTranslator.read_string(datastream)
            if data_type:
                arg, bread = DataTranslator.read_number(datastream, data_type)
            code.append((cmd, arg) if arg is not None else (cmd,))
            code_sz -= 1 + bread
        return code

    @staticmethod
    def __load_data(datastream):
        if not LogoVMLoader.check_mark(datastream, ".DATA", "Data mark"):
            return []
        data_sz, _ = DataTranslator.read_number(datastream, "Q")
        data = []
        while data_sz > 0:
            data_type = datastream.read(1)
            bread = 8
            match data_type:
                case dtype if dtype in [b"i", b"d"]:  # pylint: disable=E0601
                    data.append(
                        DataTranslator.read_number(datastream, data_type)[0]
                    )
                case b"s":  # string
                    string, bread = DataTranslator.read_string(datastream)
                    data.append(string)
                case _:  # pragma: no cover
                    raise InvalidLogoFile(
                        f"Invalid data type: {data_type.encode('utf-8')}"
                    )
            data_sz -= 1 + bread
        return data

    @staticmethod
    def __load_debug(datastream):
        if not LogoVMLoader.check_mark(datastream, ".DBUG", "Debug mark"):
            return []
        debug_sz, _ = DataTranslator.read_number(datastream, "Q")
        # TODO: load debug data
        datastream.seek(debug_sz, 1)
        return []
