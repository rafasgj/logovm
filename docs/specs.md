LogoVM Specification
====================

LogoVM aims to provide a set of tools for teaching compiler design and implementation. It currently provides a virtual machine (VM) with a high lever and easier to understand and code assembly language, and an assembler program to transform mnemonic code into VM bytecode. This document is the specification of the virtual machine.

The LogoVM virtual machine was loosely inspired by the [Java Virtual Machine](https://docs.oracle.com/javase/specs/jvms/se19/html/index.html), it is a stack machine, and has a small set of operations. Contrary to the Java Virtual Machine, LogoVM makes little to no assumption about data types, and, as of this version, has no support for objects, arrays, or direct memory address access. The heap access is done in a very high level, with every heap position mapping to a whole object (number, string).


Execution environment
---------------------

The LogoVM is a stack machine, where any computation requires data to be put into the machine stack. It also provides a _heap_, to store program data, and support for flags and interruptions which are used by extension environments.

Program code uses a separate memory which does not overlap with the data area.

Extensions can be created to the LogoVM, providing some more functionality. An extension to the LogoVM is similar to an operating system, as they provide extra, higher level, services, but in much more limited way, and at a lower level than a proper operating system. The services are available through interruption requests (INTR), configured by the extensions.


LogoVM Memory and Registers
---------------------------

Memory is divided in two areas, the stack and the heap. For simplicity, LogoVM does not use the concept of "word", but treat every data as "values", so, for example, a multiline string is "one value", and an 8-bit integer, is also "one value", consuming, both, the same amount of memory: 1 memory unit (event though, they'll use different memory space from the host machine).

The stack is limited to 16384 values, and any modification to it must be done by pushing and popping values to/from it. It does not provide randomized access to its data. The heap size is only limited by the amount of host memory available, and allows random access to the stored values using indexes to the values (not individual bytes or words).

The LogoVM also provides 8 special use registers, that cannot be directly manipulated, as of this version. Register 0 is used for tests. Register 7 is the program counter (PC).


Bytecode format
---------------

LogoVM loads and execute a program from a file in a bytecode format. The bytecode file is byte-aligned, little-endian, and is organized as specified in this section.

### LogoVM Bytecode header

The LogoVM Bytecode header is composed of 8-bytes, the first four bytes are a _magic number_ composed by characters `LOGO` in 7-bit ASCII. The fifth byte is the VM major version, and the sixth byte is the VM minor version. The last two bytes are a 16-bit unsigned integer with the size of the **extension header**.

> `Bytecode header: |L|O|G|O|Major version|Minor Version|`

### Extension Header

Each extension defines its own header for the bytecode file. The length of the extension header is set by the last field of the LogoVM Bytecode Header.

#### LogoOS, the console extension

LogoOS is the extension for LogoVM that adds calls for READ and WRITE from/to a character console. WRITE is interruption 1 and READ is interruption 2.

The LogoOS header length is 8 bytes, with the first 6 bytes being the _magic_ `LogoOS`, and the other two bytes the major and minor version required from the LogoVM.

> `Extension header: |0x0008|L|O|G|O|O|S|OS Major|OS Minor|`

#### TurtleOS, the graphic extension

TurtleOS is the extension for LogoVM that inherits LogoOS functions, and adds graphical primitives to the VM. It also adds to flags PEN (1) and DRAW (2).

The extensions added are:

    3. set_pixel: set a pixel in the drawing screen;
    4. move: move the drawing cursor;
    5. move_to: move the drawing cursor to a given position;
    6. get_pos: retrieve the current drawing cursor position;
    7. clear_screen: clear the drawing screen.

The shutdown (INTR 0) is modified to save the drawing screen to a file when the machine closes.

The TurtleOS header is composed of the magic number `TurtleOS`, two bytes for the major and minor version required from the LogoVM. Then the header has the following fields:
    * the drawing screen width (16-bit unsigned int)
    * the drawing screen height (16-bit unsigned int)
    * the initial horizontal position of the drawing cursor (16-bit unsigned int)
    * the initial vertical position of the drawing cursor (16-bit unsigned int)
    * the initial angle of the drawing cursor in hundredths of a degree (16-bit unsigned int)
    * the image format to save (1 byte).
        * 0: automatically choose between PNG or PGM
        * 1: PGM (text)
        * 2: PNG
        * 3: JPEG

`File header: |L|O|G|O|O|S|VM Major version|VM Minor Version|W|H|X|Y|theta|Fmt|`


### Code section

The code section starts right after the extension header, starts with the _magic_ '.CODE', followed by a 64-bit integer representing the code size, immediately followed by the code stream. The code stream is byte-aligned.


### Data section

The optional data section define all the variables used by the program. It starts with the _magic_ '.DATA' and the number of bytes of the data section.

After the section header, each element is defined as a character and the initial data value. The available data types are:
    * `i`: 64-bit integer number
    * `d`: 64-bit float-point number
    * `s`: UTF-8 null terminated string


Instruction Set
---------------

The instructions of the virtual machine may have two formats, one without any argument, one with an argument. The bytecode for the instruction itself is always one byte (8-bits), the argument will have 8-bytes (64-bits) if it is a number, and a variable number of bytes if it is a string. String arguments are defined as null-terminated UTF-8 strings.

In the following sections, the description of the VM instructions will be presented, in tables, containing:

* Mnemonic: The instruction mnemonic.
* Bytecode: The instruction bytecode (one byte size). The table will show the decimal and hexadecimal (in parenthesis) value of the bytecode.
* Arguments: The type of the arguments for the instruction.
* Input: The number or list of type of the values popped from the stack by the instruction.
* Output: The number or list of types of the values pushed to the stack by the instruction.
* Registers: The machine registers affected by the instruction.
* Description: A description of the instruction behavior.

If some extra behavior is expected, they'll be explained on the section notes.

### No operation

Operations that do not change any state on the machine, except for the PC register:

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :----- | :-------: | :---------- |
|  NOP     | 0 (00)   | None      | None  | None   | None      | No-op instruction. Do nothing. |


### Stack manipulation

Instructions that manipulate the machine stack:

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :------| :-------: | :---------- |
|  POP     | 8        | None      | One   | None   | R1        | Remove the value in the top of the stack. |
|  DUP     | 9 (09)   | None      | One   | Two    | R1        | Duplicate the value on the top of the stack. |
|  SWAP    | 24 (18)  | None      | Two   | Two    | R1        | Invert the order of the two values in the top of the stack. |
|  PUSHI   | 160 (A0) | Integer   | None  | Integer | None      | Push a new integer value (INT/UINT/ADDR) to the stack. |
|  PUSHD   | 192 (C0) | Double    | None  | Double | None      | Push a new double value to the stack. |
|  PUSHS   | 224 (E0) | String    | None  | String | None      | Push a new string value to the stack. |

### Heap manipulation

Instructions that manipulate the machine stack and heap:

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :----- | :-------: | :---------- |
| LOAD     | 128 (80) | Address   | None  | One    | None      | Push a new value to the stack, from the heap. |
| STORE    | 140 (8C) | Address   | One   | None   | R1        | Pop a value from the stack and store into the heap. |

#### Data conversion

Instructions that convert data types:

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :----- | :-------: | :---------- |
| INT      |  10 (0A) | None      | One   | Integer | R1, EXP  | Convert the value on the top of the stack to integer. If the value is a float, its truncated at the integer part. |
| FLOAT    |  11 (0B) | None      | One   | Float  | R1, EXP   | Convert the value on the top of the stack to float. |
| STRING   |  12 (0C) | None      | One   | String | R1        | Convert the value on the top of the stack to string. |

> The INT and FLOAT instructions may raise an exception if the value on the top of the stack cannot be converted.

### Arithmetic operators

All arithmetic operators act on numbers (Integers or Doubles), with automatic coercion of data type if needed. The order of the data on the stack might be important depending on the operation, and is the same for all the instructions. So, for an infix operation `lhs OPER rhs`, the equivalent instructions are:

```
PUSH <lhs>
PUSH <lhs>
<OPER>
```

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :----- | :-------: | :---------- |
| ABS      | 16 (10)  | None      | One   | One    | R1        | Change the value on top of the stack by its value without a signal. |
| ADD      | 30 (1E)  | None      | Two   | One    | R1, R2    | Add two numbers. |
| SUB      | 31 (1F)  | None      | Two   | One    | R1, R2    | Subtract two numbers. |
| MUL      | 32 (20)  | None      | Two   | One    | R1, R2    | Multiply two numbers. |
| DIV      | 33 (21)  | None      | Two   | One    | R1, R2    | Divide two numbers, with float result. |
| IDIV     | 34 (22)  | None      | Two   | Two    | R1, R2, R3 | Integer division of two numbers. The remainder  and the quotient are pushed to the stack, in this order. |
| POW      | 35 (23)  | None      | Two   | One    | R1, R2    | Exponentiation of two numbers (\<lhs> to the power of \<rhs>). |

### Bitwise operators

All bitwise operators work only on Integer values:

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :----- | :-------: | :---------- |
|  NOT     | 17 (11)  | None      | One   | One    | R1, R2    | Invert bits. |
|  AND     | 41 (29)  | None      | Two   | One    | R1, R2    | Bitwise AND. |
|  OR      | 42 (2A)  | None      | Two   | One    | R1, R2    | Bitwise OR. |
|  XOR     | 43 (2B)  | None      | Two   | One    | R1, R2    | Bitwise XOR. |
|  SHFTR   | 44 (2C)  | None      | Two   | One    | R1, R2    | Shift Right. |
|  SHFTL   | 45 (2D)  | None      | Two   | One    | R1, R2    | Shift Left. |
|  ROLLR   | 46 (2E)  | None      | Two   | One    | R1, R2    | Roll Right. |

### String operators

The available string operations are:

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :----- | :-------: | :---------- |
|  CAT     | 125 (7D) | None      | Two Strings | String | R1, R2 | Concatenate two strings. |
|  SCHOP   | 126 (7E) | None      | String, UINT | Two | R1, R2 | Split string at the given index, and push the first and the second part of the string to the stack. |
|  SOFF    | 127 (7F) | None      | String, UINT | One | R1, R2 | Retrieve the character at the given index of the string and push it to the stack. |

### Test instruction

All tests in LogoVM are based on the TEST register (R0). The single CMP instruction can compare any value type (number or string) and set R0:

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :----- | :-------: | :---------- |
|  CMP     | 25 (19)  | None      | Two   | None   | R0, R1    | Compare two values, and store the result in R0 (-1 if lhs < rhs, +1 if lhs > rhs, 0 if lhs == rhs). |

### Branch/Jump instructions

These are the instructions that manipulate the PC, they may change the PC register (R7). The conditional branches tests are executed against R0:

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :----- | :-------: | :---------- |
| SKIPZ    | 6 (06)  | None       | None  | None   | R0(r), R7 | Skip next instruction if R0 is Zero. | 
| SKIPNZ   | 7 (07)  | None       | None  | None   | R0(r), R7 | Skip next instruction if R0 is not Zero. |
| JP       | 129 (81) | Address   | None  | None   | R7        | Unconditional jump to the given address. |
| JLESS    | 130 (82) | Address   | None  | None   | R0(r), R7 | Jump to the given address if R0 is less than zero. | 
| JMORE    | 131 (83) | Address   | None  | None   | R0(r), R7 | Jump to the given address if R0 is more than zero. | 
| JZ       | 132 (84) | Address   | None  | None   | R0(r), R7 | Jump to the given address if R0 is equal to zero. | 
| JNZ      | 132 (85) | Address   | None  | None   | R0(r), R7 | Jump to the given address if R0 is different than zero. | 
| JR       | 161 (A1) | Integer   | None  | None   | R7        | Unconditional relative jump from the current PC position. Negative numbers move backwards. |

### Subroutine instructions

Jumping into subroutines is similar to regular jumps, but in case of subroutine jump, the PC stack (call stack) is changed:

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :----- | :-------: | :---------- |
| CALL     | 134 (86) | ADDR      | None  | None   | None      | Push PC to call stack and jump to given address. |
| RET      | 2 (02)   | None      | None  | None   | None      | Pop and address from the call stack and jump into that address. |

### Extension manipulation

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :----- | :-------: | :---------- |
| SETF     | 156 (9C) |  UINT     | None  | None   | None      | Set the flag defined by the argument. |
| UNSETF   | 157 (9D) |  UINT     | None  | None   | None      | Unset the flag defined by the argument. |
| ISSETF   | 158 (9E) |  UINT     | None  | None   | R0 (TEST) | Check if the flag defined by the argument is set (non zero). |
| INTR     | 159 (9F) |  UINT     | Variable | Variable | Variable | Call an extension routine. |

> The VM state changes are variable in the case of executing an extension routine. See the extension documentation for inputs, outputs and state changes.

### Other instructions

Miscellaneous instructions that do not fit in the previous categories:

| Mnemonic | Bytecode | Arguments | Input | Output | Registers | Description |
| :------: | :------: | :-------: | :---- | :----- | :-------: | :---------- |
| RAND     | 3 (03)   | None      | None  | Float  | None      | Push a random number in the range [0;1) to the stack. |
| HALT     | 1 (01)   | None      | None  | None   | None      | Halt execution of the program. |

