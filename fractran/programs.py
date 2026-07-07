"""A gallery of FRACTRAN programs: Conway's classics, an interactive transducer,
and a few compiled from the structured front-end.
"""

from __future__ import annotations

from . import build as B
from .core import program, run_iter

# Conway's PRIMEGAME: starting at 2, the pure powers of two it passes through
# have the primes as exponents.
PRIMEGAME = program(
    "17/91 78/85 19/51 23/38 29/33 77/29 95/23 77/19 1/17 11/13 13/11 15/2 1/7 55/1"
)

# 2^a * 3^b  ->  3^(a+b)
ADD = program("3/2")

# 2^a * 3^b  ->  5^(a*b), with 7/11/13 as scratch and control.
MULTIPLY = program("455/33 11/13 1/11 3/7 11/2 1/3")


def primegame_primes(limit=8, max_steps=2_000_000):
    """Extract the first ``limit`` primes emitted by PRIMEGAME.

    Watches the trajectory for pure powers of two (states whose only prime is 2)
    after the start, yielding each such exponent.
    """
    out = []
    state = {2: 1}
    for _, s in run_iter(PRIMEGAME, state):
        if len(s) == 1 and 2 in s:
            out.append(s[2])
            if len(out) >= limit:
                break
        max_steps -= 1
        if max_steps <= 0:
            break
    return out


# --- Interactive doubler: reads n, emits 2n, forever, with EOF -------------
#
# Registers x=2 (input), y=3 (output); markers R=5 (read), A=7 (double),
# W=11 (write), T=19 (done); tokens d=13 (delivered), e=17 (EOF).
DOUBLER = program(
    [
        (7, 5 * 13),  # R: input delivered (d) -> A
        (19, 5 * 17),  # R: EOF (e) -> T (done)
        (3 * 3 * 7, 2 * 7),  # A: x-=1, y+=2, stay in A
        (11, 7),  # A: x exhausted -> W (write)
    ]
)
DOUBLER_MARKERS = dict(
    read_marker=5,
    input_reg=2,
    delivered=13,
    eof=17,
    write_marker=11,
    out_reg=3,
    resume_marker=5,  # after writing, go back to read
)


# --- Compiled programs -----------------------------------------------------


def make_add():
    """dst = a + b in register 'dst' (a,b consumed)."""
    blk = B.seq(B.move("dst", "a"), B.move("dst", "b"))
    return B.compile_program(blk, pin={"a": 2, "b": 3, "dst": 5})


def make_multiply():
    """dst = a * b (a consumed, b preserved), scratch 'tmp'."""
    blk = B.mul("dst", "a", "b", "tmp")
    return B.compile_program(blk, pin={"a": 2, "b": 3, "dst": 5})


def make_fibonacci():
    """a = fib(n): loop n times doing (a,b) <- (b, a+b)."""
    blk = B.seq(
        B.inc("b"),
        B.loop(
            "n",
            B.seq(
                B.move("t", "a"),
                B.move("a", "b"),
                B.move("b", "t"),
                B.add("b", "a", "tmp"),
            ),
        ),
    )
    return B.compile_program(blk, pin={"n": 2, "a": 3, "b": 5})


def make_factorial():
    """f = n! : while n>0: f <- f*n; n-=1."""
    blk = B.seq(
        B.inc("f"),
        B.while_nz(
            "n",
            B.seq(
                B.zero("acc"),
                B.mul_pp("acc", "f", "n", "t1", "t2"),
                B.zero("f"),
                B.move("f", "acc"),
                B.dec1("n"),
            ),
        ),
    )
    return B.compile_program(blk, pin={"n": 2, "f": 3})
