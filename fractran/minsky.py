"""Minsky register-machine IR and its compilation to FRACTRAN.

The IR has three instruction kinds, keyed by label:

    Inc(reg, goto)              increment reg, jump to goto
    Dec(reg, nonzero, zero)     if reg>0: decrement, jump nonzero; else jump zero
    Halt()                      stop

Compilation assigns a distinct prime ``q_r`` to each register and ``s_L`` to
each label, and keeps the invariant that exactly one label prime (a one-hot
program counter) is present at a time:

    L: Inc(r) -> M          (q_r * s_M) / s_L
    L: Dec(r) -> M else N    s_M / (s_L * q_r)   then   s_N / s_L
    L: Halt                 (no fraction: the machine halts while s_L is present)

The Dec pair relies on FRACTRAN's first-applicable rule: the decrement fraction
(needing both s_L and q_r) is listed before the fall-through, so it fires iff
the register is non-zero. Because every fraction's denominator carries a unique
label prime, ordering across labels is irrelevant to correctness.
"""

from __future__ import annotations

from dataclasses import dataclass

from .core import Fraction, factorize


@dataclass
class Inc:
    reg: str
    goto: str


@dataclass
class Dec:
    reg: str
    nonzero: str
    zero: str


@dataclass
class Halt:
    pass


# I/O wait states. The machine halts in one of these (flag up, no token yet); the
# host recognizes the flag, services the channel, and drops a token to resume.
@dataclass
class ReadWait:
    on_got: str  # a value was delivered
    on_eof: str  # the input stream ended


@dataclass
class WriteWait:
    on_done: str  # the value was consumed by the host


# Reserved I/O register/token names (auto-allocated primes when I/O is present).
IO_IN, IO_OUT = "_IN", "_OUT"
IO_RF, IO_WF = "_RF", "_WF"          # read / write flags the host keys on
IO_DL, IO_EF, IO_WD = "_DL", "_EF", "_WD"  # delivered / eof / write-done tokens
IO_NAMES = (IO_IN, IO_OUT, IO_RF, IO_WF, IO_DL, IO_EF, IO_WD)


def _primes():
    """Infinite generator of primes by incremental trial division."""
    found = []
    c = 2
    while True:
        if all(c % p for p in found if p * p <= c):
            found.append(c)
            yield c
        c += 1


@dataclass
class Compiled:
    fractions: list  # list[Fraction]
    reg_prime: dict  # register name -> prime
    label_prime: dict  # label name -> prime
    entry: str
    names: dict  # prime -> "regname" or "@label", for rendering
    io: dict | None = None  # I/O channel/token name -> prime (when the program does I/O)

    def start(self, **regs):
        """Build a start state: entry label plus the given register values."""
        st = {self.label_prime[self.entry]: 1}
        for r, v in regs.items():
            if v:
                st[self.reg_prime[r]] = v
        return st

    def io_config(self) -> dict:
        """Prime assignments for the I/O host, keyed by role."""
        m = {IO_IN: "in_reg", IO_OUT: "out_reg", IO_RF: "rf", IO_WF: "wf",
             IO_DL: "dl", IO_EF: "ef", IO_WD: "wd"}
        return {role: self.reg_prime[name] for name, role in m.items()}

    def read(self, state, reg):
        """Exponent of a register in a state."""
        return state.get(self.reg_prime[reg], 0)


def assemble(instrs: dict, entry: str, order=None, pin: dict | None = None) -> Compiled:
    """Compile an IR program (``label -> instruction``) into a Compiled program.

    ``order`` optionally fixes label emission order (defaults to dict order).
    ``pin`` optionally forces specific primes for named registers.
    """
    order = order or list(instrs)
    pin = pin or {}

    regs = []
    for ins in instrs.values():
        if isinstance(ins, (Inc, Dec)) and ins.reg not in regs:
            regs.append(ins.reg)
    if any(isinstance(i, (ReadWait, WriteWait)) for i in instrs.values()):
        for name in IO_NAMES:  # reserve the I/O channel/token primes
            if name not in regs:
                regs.append(name)

    gen = _primes()
    used = set(pin.values())

    def fresh():
        while True:
            p = next(gen)
            if p not in used:
                used.add(p)
                return p

    reg_prime = {}
    for r in regs:
        reg_prime[r] = pin[r] if r in pin else fresh()
    label_prime = {L: fresh() for L in order}

    names = {p: r for r, p in reg_prime.items()}
    names.update({p: "@" + L for L, p in label_prime.items()})

    fractions = []

    def frac(num_primes, den_primes):
        num = den = 1
        nf, df = {}, {}
        for p, e in num_primes.items():
            num *= p**e
            nf[p] = e
        for p, e in den_primes.items():
            den *= p**e
            df[p] = e
        fractions.append(Fraction(num, den, nf, df))

    for L in order:
        ins = instrs[L]
        sL = label_prime[L]
        if isinstance(ins, Inc):
            frac({reg_prime[ins.reg]: 1, label_prime[ins.goto]: 1}, {sL: 1})
        elif isinstance(ins, Dec):
            frac({label_prime[ins.nonzero]: 1}, {sL: 1, reg_prime[ins.reg]: 1})
            frac({label_prime[ins.zero]: 1}, {sL: 1})
        elif isinstance(ins, ReadWait):
            # halts here (RF up, no token) until the host delivers or signals EOF
            frac({label_prime[ins.on_got]: 1}, {sL: 1, reg_prime[IO_DL]: 1, reg_prime[IO_RF]: 1})
            frac({label_prime[ins.on_eof]: 1}, {sL: 1, reg_prime[IO_EF]: 1, reg_prime[IO_RF]: 1})
        elif isinstance(ins, WriteWait):
            frac({label_prime[ins.on_done]: 1}, {sL: 1, reg_prime[IO_WD]: 1, reg_prime[IO_WF]: 1})
        elif isinstance(ins, Halt):
            pass
        else:
            raise TypeError(f"unknown instruction {ins!r}")

    io = {n: reg_prime[n] for n in IO_NAMES if n in reg_prime}
    return Compiled(fractions, reg_prime, label_prime, entry, names, io=io)
