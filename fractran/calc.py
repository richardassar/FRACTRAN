"""A calculator compiled to FRACTRAN.

It reads commands from the input stream as integer triples ``op a b`` and writes
each result. Everything is a fraction list underneath — the reads/writes are the
streaming-I/O waits, and the arithmetic is the register-machine macros.

  op 0: a + b        op 1: a * b        op 2: a - b (truncated at 0)
  op 3: divmod(a, b) -> writes quotient then remainder   (b >= 1)
"""

from __future__ import annotations

from . import build as B

OPS = {0: "add", 1: "mul", 2: "sub", 3: "divmod"}


def _dispatch(sel, blocks):
    """if sel==0: blocks[0]; elif sel==1: blocks[1]; ... else blocks[-1] (consumes sel)."""
    def chain(i):
        if i == len(blocks) - 1:
            return blocks[i]
        return B.if_nz(sel, B.seq(B.dec1(sel), chain(i + 1)), blocks[i])

    return chain(0)


def build_calculator():
    add_block = B.seq(B.zero("res"), B.add("res", "a", "t"), B.add("res", "b", "t"), B.write("res"))
    mul_block = B.seq(B.zero("res"), B.mul_pp("res", "a", "b", "t1", "t2"), B.write("res"))
    sub_block = B.seq(B.monus("res", "a", "b", "cb", "t"), B.write("res"))
    dm_block = B.seq(
        B.zero("work"), B.copy("work", "a", "t"),
        B.divmod_("q", "r", "work", "b", "cd", "rr", "t2"),
        B.write("q"), B.write("r"),
    )

    command = B.seq(
        B.read1("a"), B.read1("b"),
        _dispatch("op", [add_block, mul_block, sub_block, dm_block]),
    )
    # read an op-code each round (exit on EOF), then its two operands, then compute.
    return B.compile_program(B.read_until_eof("op", command))
