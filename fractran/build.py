"""Structured front-end: combinators that lower to Minsky IR.

A *block* is a callable ``(builder, next_label) -> entry_label``: it emits its
instructions into the builder, wires its own exit to ``next_label``, and returns
the label at which it should be entered. Blocks compose in continuation-passing
style, so control flow is built without hand-managing labels.

Primitives: ``inc``, ``dec1``, ``zero``, ``seq``, ``loop`` (decrement-a-register
loop), ``while_nz`` (non-destructive while), ``if_nz``. Macros built on them:
``move``, ``copy``/``add`` (preserve source), ``mul`` (dst += a*b).
"""

from __future__ import annotations

from .minsky import (
    Compiled,
    Dec,
    Halt,
    Inc,
    IO_IN,
    IO_OUT,
    IO_RF,
    IO_WF,
    ReadWait,
    WriteWait,
    assemble,
)


class Builder:
    def __init__(self):
        self.instrs: dict = {}
        self.order: list = []
        self._n = 0

    def fresh(self, hint="L") -> str:
        self._n += 1
        return f"{hint}{self._n}"

    def emit(self, label, instr):
        self.instrs[label] = instr
        self.order.append(label)


# ---- primitives -----------------------------------------------------------


def inc(reg):
    def b(bld, nxt):
        L = bld.fresh("inc")
        bld.emit(L, Inc(reg, nxt))
        return L

    return b


def dec1(reg):
    """Decrement a register that is known to be non-zero, then continue."""

    def b(bld, nxt):
        L = bld.fresh("dec")
        bld.emit(L, Dec(reg, nxt, nxt))
        return L

    return b


def zero(reg):
    """Set a register to 0 (decrement until empty)."""

    def b(bld, nxt):
        L = bld.fresh("zero")
        bld.emit(L, Dec(reg, L, nxt))
        return L

    return b


def seq(*blocks):
    def b(bld, nxt):
        entry = nxt
        for blk in reversed(blocks):
            entry = blk(bld, entry)
        return entry

    return b


def loop(reg, body):
    """Run ``body`` once per unit of ``reg``, consuming ``reg`` (for i in reg)."""

    def b(bld, nxt):
        test = bld.fresh("loop")
        body_entry = body(bld, test)  # body returns to the test
        bld.emit(test, Dec(reg, body_entry, nxt))
        return test

    return b


def while_nz(reg, body):
    """Run ``body`` while ``reg`` is non-zero, without consuming ``reg``."""

    def b(bld, nxt):
        test = bld.fresh("while")
        body_entry = body(bld, test)
        restore = bld.fresh("wrst")
        bld.emit(restore, Inc(reg, body_entry))
        bld.emit(test, Dec(reg, restore, nxt))
        return test

    return b


def if_nz(reg, then, els=None):
    """If ``reg`` is non-zero run ``then`` else ``els``, preserving ``reg``."""
    els = els or seq()

    def b(bld, nxt):
        then_entry = then(bld, nxt)
        else_entry = els(bld, nxt)
        restore = bld.fresh("irst")
        bld.emit(restore, Inc(reg, then_entry))
        test = bld.fresh("if")
        bld.emit(test, Dec(reg, restore, else_entry))
        return test

    return b


# ---- macros ---------------------------------------------------------------


def move(dst, src):
    """dst += src, consuming src."""
    return loop(src, inc(dst))


def copy(dst, src, tmp):
    """dst += src, preserving src (via scratch ``tmp``, left at 0)."""
    return seq(loop(src, seq(inc(dst), inc(tmp))), move(src, tmp))


add = copy  # dst += src, source preserved


def mul(dst, a, b, tmp):
    """dst += a*b, consuming ``a`` and preserving ``b``."""
    return loop(a, add(dst, b, tmp))


def mul_pp(dst, a, b, tmp1, tmp2):
    """dst += a*b, preserving both ``a`` and ``b``."""
    return seq(copy(tmp1, a, tmp2), loop(tmp1, add(dst, b, tmp2)))


def monus(res, a, b, cb, t):
    """res = max(a - b, 0), preserving ``a`` and ``b`` (truncated subtraction)."""
    return seq(
        zero(res), copy(res, a, t),   # res = a
        zero(cb), copy(cb, b, t),     # cb = b
        loop(cb, if_nz(res, dec1(res))),  # b times: decrement res if it's still > 0
    )


def divmod_(q, r, n, b, cd, rr, t):
    """q = n // b, r = n % b, consuming ``n`` and preserving ``b`` (b >= 1).

    No compare/underflow-restore: a countdown ``cd`` runs from b to 0; each unit
    of n decrements it and bumps a remainder counter ``rr``; when ``cd`` empties
    (a full b consumed) the quotient ticks up and both refill/reset. This is the
    divisibility+division core a FRACTRAN self-interpreter needs.
    """
    return seq(
        zero(q), zero(r), zero(rr), zero(cd),
        copy(cd, b, t),                       # cd = b
        loop(n, seq(                          # once per unit of n:
            dec1(cd),
            inc(rr),
            if_nz(cd, seq(), seq(inc(q), zero(rr), copy(cd, b, t))),  # cd hit 0: carry
        )),
        move(r, rr),                          # r = leftover
    )


# ---- streaming I/O --------------------------------------------------------


def _flag_goto(flag, target):
    """Set a flag register and jump to a fixed label (ignoring the CPS `next`)."""
    def b(bld, nxt):
        L = bld.fresh("flag")
        bld.emit(L, Inc(flag, target))
        return L

    return b


def write(x):
    """Emit the value of ``x`` on the output stream (``x`` preserved)."""
    def b(bld, nxt):
        wait = bld.fresh("wwait")
        bld.emit(wait, WriteWait(on_done=nxt))
        # OUT := x  (host clears OUT after reading, so it starts at 0), then wait
        return seq(copy(IO_OUT, x, "_iotmp"), _flag_goto(IO_WF, wait))(bld, nxt)

    return b


def read1(x, on_eof=None):
    """Read a single value into ``x`` (cleared first); jump to ``on_eof`` at EOF."""
    def b(bld, nxt):
        got = seq(zero(x), move(x, IO_IN))(bld, nxt)
        eof_entry = (on_eof or seq())(bld, nxt)
        wait = bld.fresh("rwait")
        bld.emit(wait, ReadWait(on_got=got, on_eof=eof_entry))
        top = bld.fresh("rflag")
        bld.emit(top, Inc(IO_RF, wait))
        return top

    return b


def read_until_eof(x, body):
    """Loop: read the next input into ``x`` and run ``body``; exit on EOF.

    ``x`` is cleared before each read, so ``body`` sees exactly the value read
    (a delivered 0 included). Program state in other registers persists across
    iterations.
    """
    def b(bld, nxt):
        top = bld.fresh("iotop")
        wait = bld.fresh("iowait")
        got = seq(zero(x), move(x, IO_IN), body)(bld, top)  # IN->x, run body, loop
        bld.emit(wait, ReadWait(on_got=got, on_eof=nxt))
        bld.emit(top, Inc(IO_RF, wait))  # raise read flag, then wait
        return top

    return b


# ---- entry point ----------------------------------------------------------


def compile_program(block, entry_regs=None, pin=None) -> Compiled:
    """Lower a block to IR and assemble it into a FRACTRAN program."""
    bld = Builder()
    halt = "halt"
    bld.emit(halt, Halt())
    entry = block(bld, halt)
    return assemble(bld.instrs, entry, order=bld.order, pin=pin)
