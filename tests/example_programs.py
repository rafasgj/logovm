"""Example program generation functions."""

import io
import struct
from collections import namedtuple


LogoOSHeader = namedtuple("LogoOSHeader", ["name", "version", "types"])
TurtleOSHeader = namedtuple(
    "TurtleOSHeader",
    [
        "name",
        "version",
        "types",
        "width",
        "height",
        "x",
        "y",
        "angle",
        "imagetype",
    ],
)
__programs = {
    "hello": (
        [
            128,
            0,  # LOAD @0
            160,
            1,  # PUSHI 1
            159,
            1,  # INTR @WRITE
            1,  # HALT
        ],
        (("@literal_1", "Hello World!\n"),),
        LogoOSHeader("LogoOS", (0, 2), ""),
    ),
    "hello2": (
        [
            224,
            "Hello World!\n",  # PUSH "Hello World!\n"
            160,
            1,  # PUSHI 1
            159,
            1,  # INTR @READ
            1,  # HALT
        ],
        None,
        LogoOSHeader("LogoOS", (0, 2), ""),
    ),
    "circle_area": (
        [
            224,
            "Circle ray: ",  # PUSH "Circle ray: "
            160,
            1,  # PUSHI 1
            159,
            1,  # INTR @WRITE
            159,
            2,  # INTR @READ
            160,
            2,  # PUSHI 2
            35,  # POW
            128,
            0,  # LOAD @0
            32,  # MUL
            224,
            "Circle area: ",  # PUSHS "Circle area: "
            24,  # SWAP
            224,
            "\n",  # PUSHS "\n"
            160,
            3,  # PUSHI 3
            159,
            1,  # INTR @WRITE
            1,  # HALT
        ],
        (("pi", 3.141592),),
        LogoOSHeader("LogoOS", (0, 2), ""),
    ),
    "swap": (
        [160, 2, 160, 3, 24, 31, 160, 1, 159, 1, 1],
        None,
        LogoOSHeader("LogoOS", (0, 2), ""),
    ),
    "square": (
        [  # ; start at (0,0)
            160,
            9,  # PUSH 9
            160,
            0,  # PUSH 0
            159,
            5,  # INTR 5       ; moveto 9, 0
            160,
            9,  # PUSH 9
            160,
            9,  # PUSH 9
            159,
            5,  # INTR 5       ; moveto 9, 9
            160,
            0,  # PUSH 0
            160,
            9,  # PUSH 9
            159,
            5,  # INTR 5       ; moveto 0, 9
            160,
            0,  # PUSH 0
            160,
            0,  # PUSH 0
            159,
            5,  # INTR 5       ; moveto 0, 0
            159,
            6,  # INTR 6       ; getpos
            160,
            3,  # PUSH 3
            159,
            1,  # INTR 1       ; write
            1,  # HALT
        ],
        None,
        TurtleOSHeader("TurtleOS", (0, 1), "HHHHHB", 10, 10, 0, 0, 0, 1),
    ),
    "square2": (
        [  # ; start at (0,0)
            160,
            10,  # PUSH 10
            160,
            0,  # PUSH 0
            159,
            4,  # INTR 4       ; move 10, 0
            160,
            10,  # PUSH 10
            160,
            270,  # PUSH 270
            159,
            4,  # INTR 4       ; move 10, 270
            160,
            10,  # PUSH 10
            160,
            180,  # PUSH 180
            159,
            4,  # INTR 4       ; move 10, 180
            160,
            10,  # PUSH 10
            160,
            90,  # PUSH 90
            159,
            4,  # INTR 4       ; move 10, 90
            159,
            6,  # INTR 6       ; getpos (0, 0, 90)
            160,
            3,  # PUSH 3
            159,
            1,  # INTR 1       ; write
            1,  # HALT
        ],
        None,
        TurtleOSHeader("TurtleOS", (0, 1), "HHHHHB", 10, 10, 0, 0, 0, 1),
    ),
    "clrscr": (
        [  # ; start at (0,0)
            160,
            9,  # PUSH 9
            160,
            9,  # PUSH 9
            159,
            5,  # INTR 5       ; moveto 9, 9
            160,
            159,
            7,  # INTR 7       ; clrscr
            1,  # HALT
        ],
        None,
        TurtleOSHeader("TurtleOS", (0, 1), "HHHHHB", 10, 10, 0, 0, 0, 1),
    ),
}


def __process_code(code):
    """Process code data."""
    code_data = bytearray([])
    entry = 0
    while entry < len(code):
        cmd = code[entry]
        entry += 1
        code_data.append(cmd)
        # pylint: disable=used-before-assignment
        match cmd:
            case num if num in range(128, 160):
                code_data.extend(struct.pack("<Q", code[entry]))
            case num if num in range(160, 192):
                code_data.extend(struct.pack("<q", code[entry]))
            case num if num in range(192, 224):
                code_data.extend(struct.pack("<d", code[entry]))
            case num if num in range(224, 254):
                arg = code[entry]
                code_data.extend(
                    struct.pack(f"<{'c' * len(arg)}", *__char_encode(arg))
                )
                code_data.append(0)
            case 255:
                raise ValueError("Extension commands not available yet.")
            case _:
                # We'll increase 'entry' later, but this command has no args.
                entry -= 1
        # pylint: enable=used-before-assignment
        entry += 1
    return code_data


def __char_encode(value):
    """Encode a string or list to write a string to the file."""
    return [c.encode("utf-8") for c in value]


def __save_header(outfile, header):
    datasz = {"H": 2, "B": 1, "Q": 8, "D": 8}
    name = __char_encode(header[0]) + [b"\0"]
    data_size = len(name) + 2 + sum(datasz[x.upper()] for x in header[2])
    # save data
    outfile.write(struct.pack("<H", data_size))  # Header size.
    outfile.write(struct.pack(f"<{'c'*len(name)}", *name))
    outfile.write(bytes(header[1]))  # OS version
    for datatype, data in zip(header[2], header[3:]):
        outfile.write(struct.pack(f"<{datatype}", data))


def gen_program(code, data, header):
    """Generate program from code and data."""
    with io.BytesIO() as outfile:
        # magic
        outfile.write(struct.pack("<cccc", *__char_encode("LOGO")))
        # version = 0.2
        outfile.write(bytes((0, 2)))
        __save_header(outfile, header)
        # write code
        code_data = __process_code(code)
        outfile.write(struct.pack("<ccccc", *__char_encode(".CODE")))
        outfile.write(struct.pack("<Q", len(code_data)))
        outfile.write(bytes(code_data))

        # write data and debug
        if data:
            out_data = []
            dbg_data = []
            dtypes = {int: ("i", "q"), float: ("d", "d"), str: ("s", None)}
            for dbg, value in data:
                data_type, cvt = dtypes[type(value)]
                enc_type = data_type.encode("utf-8")[0]
                out_data.append(enc_type)
                if cvt:
                    out_data.extend(struct.pack(f"<{cvt}", value))
                else:
                    encoded = value.encode("utf-8")
                    out_data.extend(encoded)
                    out_data.append(0)
                dbg_data.append(enc_type)
                dbg_data.extend(dbg.encode("utf-8"))
                dbg_data.append(0)
            outfile.write(struct.pack("<ccccc", *__char_encode(".DATA")))
            outfile.write(struct.pack("<Q", len(out_data)))
            outfile.write(bytes(out_data))
            outfile.write(struct.pack("<ccccc", *__char_encode(".DBUG")))
            outfile.write(struct.pack("<Q", len(dbg_data)))
            outfile.write(bytes(dbg_data))
        return outfile.getvalue()


def get_example_program_and_data(name):
    """Retrieve a LogoVM compiled program code and data."""
    return __programs.get(name, ([1], None, None))  # default: (HALT, None)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Generate example program files for LogoVM/TurtleOS",
            file=sys.stderr,
        )
        print("usage: example_programs.py NAME...", file=sys.stderr)
        sys.exit(1)
    for program in sys.argv[1:]:
        with open(f"{program}.logox", "wb") as outputfile:
            outputfile.write(
                gen_program(*__programs.get(program, ([1], None, None)))
            )
