"""A FRACTRAN self-interpreter, *compiled* from our verified toolchain.

``make_interpreter(k)`` builds a FRACTRAN program that reads a k-fraction object
program and an object integer off the input stream, runs the object machine to
halt (scan fractions in order, apply the first whose denominator divides the
state, restart; stop when none applies), and writes the final state. It is a
register machine over the object state stored as a plain magnitude, so `b | n`
and `n <- (n/b)*a` are the `divmod`/`mul` macros — slow (unary), but correct by
construction, since the compiler that produced it is verified.

This is the honest form of the meta-circular bootstrap: rather than transcribe an
external hand-golfed interpreter, we build our own and *know* it is right.
"""

from __future__ import annotations

from . import build as B
from .io import io_host, trampoline


def make_interpreter(k: int):
    """Compile a universal interpreter for object programs of exactly k fractions."""
    def chain(i):
        # try object fraction i; on apply, end the pass (loop restarts the scan);
        # if none of i..k applies, clear `cont` to halt.
        if i > k:
            return B.zero("cont")
        return B.seq(
            B.zero("work"), B.copy("work", "n", "t"),
            B.divmod_("q", "r", "work", f"b{i}", "cd", "rr", "t2"),
            B.if_nz("r",
                    chain(i + 1),                                       # not divisible
                    B.seq(B.zero("n"), B.mul_pp("n", "q", f"a{i}", "t", "t2"))),  # n=(n/b)*a
        )

    reads = []
    for i in range(1, k + 1):
        reads += [B.read1(f"a{i}"), B.read1(f"b{i}")]
    reads.append(B.read1("n"))
    prog = B.seq(*reads, B.inc("cont"), B.while_nz("cont", chain(1)), B.write("n"))
    return B.compile_program(prog)


def interpret(compiled, fractions, n0, max_rounds=None):
    """Run a compiled interpreter on an object program (list of (num, den)) and n0."""
    inputs = []
    for a, b in fractions:
        inputs += [a, b]
    inputs.append(n0)
    outputs = []
    host = io_host(**compiled.io_config(), inputs=inputs, outputs=outputs)
    state = {compiled.label_prime[compiled.entry]: 1}
    trampoline(compiled.fractions, state, host, max_rounds=max_rounds)
    return outputs[0] if outputs else None
