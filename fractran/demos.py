"""A gallery of interactive/graphical FRACTRAN programs, compiled from the
structured front-end. Each is a plain fraction list; all logic is fractions, and
output is a stream of numbers over the I/O boundary. For the graphical ones the
host renders each number as a character (`chr`), with code 12 reserved as
"new animation frame" (clear screen). Numeric ones just print the values.

Char codes used: 10 newline, 12 clear-frame, 32 space, 35 '#', 42 '*'.
"""

from __future__ import annotations

from . import build as B


def set_const(reg, c):
    """reg := c (a compile-time constant)."""
    return B.seq(B.zero(reg), *[B.inc(reg) for _ in range(c)])


def emit_char(code):
    """Write one character code to the output stream."""
    return B.seq(set_const("_ch", code), B.write("_ch"))


def emit_n(code, count_reg, kc="_kc", t="_kt"):
    """Write `count_reg` copies of a character (count_reg preserved)."""
    return B.seq(B.zero(kc), B.copy(kc, count_reg, t), B.loop(kc, emit_char(code)))


# --- graphics --------------------------------------------------------------

def pyramid():
    """Read n; draw a centred pyramid of '#': row i has (n-i) spaces, 2i-1 hashes."""
    row = B.seq(
        B.inc("i"),                                   # i = 1..n
        B.monus("sp", "n", "i", "cb", "t"),           # sp = n - i
        emit_n(32, "sp"),
        B.zero("st"), B.add("st", "i", "t"), B.add("st", "i", "t"), B.dec1("st"),  # st = 2i-1
        emit_n(35, "st"),
        emit_char(10),
    )
    return B.compile_program(B.seq(
        B.read1("n"),
        B.zero("i"), B.zero("nc"), B.copy("nc", "n", "t"),
        B.loop("nc", row),
    ))


def bars():
    """Read numbers until EOF; draw a horizontal '#' bar for each (a bar chart)."""
    return B.compile_program(
        B.read_until_eof("x", B.seq(emit_n(35, "x"), emit_char(10)))
    )


def march():
    """Read width w; animate a '*' walking across the line (w frames)."""
    frame = B.seq(
        emit_char(12),          # clear -> new frame
        emit_n(32, "p"),        # p leading spaces
        emit_char(42),          # the marcher
        emit_char(10),
        B.inc("p"),             # advance one column
    )
    return B.compile_program(B.seq(
        B.read1("w"),
        B.zero("p"), B.zero("wc"), B.copy("wc", "w", "t"),
        B.loop("wc", frame),
    ))


# --- numeric I/O -----------------------------------------------------------

def collatz():
    """Read n; emit the Collatz trajectory n, ..., 1 (3n+1 / n/2)."""
    step = B.seq(
        B.zero("work"), B.copy("work", "n", "t"),
        B.divmod_("q", "r", "work", "two", "cd", "rr", "t2"),   # r = n mod 2, q = n/2
        B.if_nz("r",
                B.seq(B.zero("nn"), B.mul_pp("nn", "n", "three", "t1", "t2"),
                      B.inc("nn"), B.zero("n"), B.move("n", "nn")),   # odd: n = 3n+1
                B.seq(B.zero("n"), B.move("n", "q"))),               # even: n = n/2
    )
    return B.compile_program(B.seq(
        B.read1("n"),
        set_const("two", 2), set_const("three", 3),
        B.inc("cont"),
        B.while_nz("cont", B.seq(
            B.write("n"),
            B.zero("mm"), B.copy("mm", "n", "t"), B.dec1("mm"),      # mm = n - 1
            B.if_nz("mm", step, B.zero("cont")),                    # n>1 step, else stop
        )),
    ))


def gcd():
    """Read a, b; emit gcd(a, b) by Euclid's algorithm."""
    return B.compile_program(B.seq(
        B.read1("a"), B.read1("b"),
        B.while_nz("b", B.seq(                                      # while b != 0:
            B.zero("work"), B.copy("work", "a", "t"),
            B.divmod_("q", "r", "work", "b", "cd", "rr", "t2"),     # r = a mod b
            B.zero("a"), B.move("a", "b"),                          # a = b
            B.zero("b"), B.move("b", "r"),                          # b = r
        )),
        B.write("a"),
    ))


def make_rule30(width=31):
    """Elementary cellular automaton Rule 30: new = left XOR (center OR right).

    A row of `width` cells lives in registers c0..c{width-1}; each generation is
    unrolled over the cells (boundaries read a permanently-zero register `z`).
    Seeded with a single centre cell, it prints one row per generation — the
    famous chaotic triangle. Reads the number of generations from input.
    """
    def orb(dst, a, b):  # dst = a OR b (bits)
        return B.seq(B.zero(dst), B.if_nz(a, B.inc(dst), B.if_nz(b, B.inc(dst))))

    def xorb(dst, a, b):  # dst = a XOR b (bits)
        return B.seq(B.zero(dst),
                     B.if_nz(a, B.if_nz(b, B.seq(), B.inc(dst)),
                             B.if_nz(b, B.inc(dst), B.seq())))

    def cell(i):
        left = f"c{i-1}" if i > 0 else "z"
        right = f"c{i+1}" if i < width - 1 else "z"
        return B.seq(orb("cor", f"c{i}", right), xorb(f"n{i}", left, "cor"))

    emit_row = B.seq(
        *[B.if_nz(f"c{i}", B.write("hash"), B.write("space")) for i in range(width)],
        B.write("nl"),
    )
    compute = B.seq(*[cell(i) for i in range(width)])
    commit = B.seq(*[B.seq(B.zero(f"c{i}"), B.move(f"c{i}", f"n{i}")) for i in range(width)])
    generation = B.seq(emit_row, compute, commit)

    return B.compile_program(B.seq(
        set_const("hash", 35), set_const("space", 32), set_const("nl", 10),
        B.zero("z"),
        B.inc(f"c{width // 2}"),   # single seed cell
        B.read1("g"),
        B.loop("g", generation),
    ))


REGISTRY = {
    "pyramid": (pyramid, "char", 1),
    "rule30": (lambda: make_rule30(31), "char", 1),
    "bars": (bars, "char", "stdin"),
    "march": (march, "anim", 1),
    "collatz": (collatz, "int", 1),
    "gcd": (gcd, "int", 2),
}
