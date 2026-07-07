"""Streaming I/O for FRACTRAN via a trampoline.

FRACTRAN has no native I/O: a program is a closed map from a start integer to a
(possibly non-terminating) trajectory. To get *both* streaming input and output
we overload the one native control signal — halting — to mean three things,
told apart by which marker prime is present in the halted state:

  READ   the program wants input   -> host injects the next symbol, resumes
  WRITE  the program has output     -> host reads/clears a register, emits, resumes
  DONE   the computation is over     -> host stops

Between services it is ordinary deterministic FRACTRAN; the host only touches
the state at these marked pause points, so the whole system is deterministic
given the input stream — a stream transducer / coroutine.
"""

from __future__ import annotations

from .core import run_iter


def trampoline(prog: list, state, host, max_rounds: int | None = None):
    """Run to halt repeatedly, calling ``host(state)`` at each halt.

    ``host`` mutates ``state`` and returns True to resume or False to stop.
    Returns ``(state, rounds)``.
    """
    rounds = 0
    while True:
        for _ in run_iter(prog, state):
            pass
        if not host(state):
            return state, rounds
        rounds += 1
        if max_rounds is not None and rounds >= max_rounds:
            return state, rounds


def stream_host(
    *,
    read_marker: int,
    input_reg: int,
    delivered: int,
    eof: int,
    write_marker: int,
    out_reg: int,
    resume_marker: int,
    inputs,
    outputs: list,
):
    """A host implementing READ/WRITE/DONE for the marker convention below.

    On a READ halt (``read_marker`` present) it pops the next value from the
    ``inputs`` iterator and delivers it as ``input_reg += value`` together with a
    ``delivered`` token (so a value of 0 is still observable — an absent prime is
    indistinguishable from a zero register). When ``inputs`` is exhausted it
    delivers an ``eof`` token instead.

    On a WRITE halt (``write_marker`` present) it reads and clears ``out_reg``,
    appends the value to ``outputs``, and flips the marker to ``resume_marker``.

    Any other halt is DONE.
    """
    it = iter(inputs)

    def host(state):
        if read_marker in state:
            try:
                v = next(it)
            except StopIteration:
                state[eof] = 1
                return True
            if v < 0:
                raise ValueError("stream inputs must be non-negative")
            if v:
                state[input_reg] = state.get(input_reg, 0) + v
            state[delivered] = 1
            return True
        if write_marker in state:
            val = state.pop(out_reg, 0)
            outputs.append(val)
            del state[write_marker]
            state[resume_marker] = 1
            return True
        return False  # DONE

    return host


def io_host(*, rf, wf, in_reg, out_reg, dl, ef, wd, inputs, outputs):
    """Host for compiled programs that use ``read``/``write`` (flag-based).

    Keys off the read/write *flag* primes (not the program counter), so any
    number of I/O sites work: the PC label carries the resume location. On a
    read it deposits the next value into ``in_reg`` plus a ``dl`` token (or an
    ``ef`` token at end of stream); on a write it drains ``out_reg`` and drops a
    ``wd`` token. It never touches the PC — the compiled resume fractions consume
    the flag and token themselves.
    """
    it = iter(inputs)

    def host(state):
        if rf in state:  # a read is waiting
            try:
                v = next(it)
            except StopIteration:
                state[ef] = 1
                return True
            if v < 0:
                raise ValueError("stream inputs must be non-negative")
            if v:
                state[in_reg] = state.get(in_reg, 0) + v
            state[dl] = 1
            return True
        if wf in state:  # a write is waiting
            outputs.append(state.pop(out_reg, 0))
            state[wd] = 1
            return True
        return False  # DONE

    return host
