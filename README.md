LogoVM
======

LogoVM is an abstract stack machine, loosely inspired by JavaVM,
designed to provide a simple runtime environment to teach the design
and implementation of compilers.

The initial design of the LogoVM, and where its name came from, was to
aid in the implementation of a Logo
compiler, during a one semester undergraduate course, so it provides
some higher level functions for drawing lines, or controlling a drawing
cursor.

To achieve the original goal, all computation is done using a stack,
using a small set of low-level instructions. There is also a "high
level" heap memory, where data is stored as full objects, and not
bytes, meaning that if a huge string is on the first heap slot, the
second heap slot may hold and integer, and the third heap slot may have
a float value. A runtime environment that allows easy implementation of
_turtle graphics_ is also provided.

A specification of the LogoVM can be found on
[docs/specs.md](docs/specs.md).


Usage
-----

To run a program simply call `logovm <program>`.

Check `logovm -h` for available options.


Installation
------------

You may install the `logovm` package through `pip`:
```
pip install logovm
```

Some extra options are available:
* `graphic`: add support for graphic output (using `pillow`)
* `test`: add dependencies for running automated tests
* `lint`: add dependencies to ensure minimum code quality
* `dev`: an alias that include `lint` and `test`

For example, when implementing a feature for LogoVM, you would use:
```
(virt_env) [repo/logovm] $ pip -e install .[dev]
```

It is strongly suggested that you use a Python virtual environment.

