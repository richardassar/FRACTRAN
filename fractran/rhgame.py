"""RHGAME -- the Riemann Hypothesis as a FRACTRAN halting problem.

Robin (1984): RH  <=>  sigma(n) < e^gamma * n * ln ln n  for all n > 5040,
where sigma is the sum-of-divisors function. So a machine that enumerates
n > 5040, computes sigma(n), and halts iff the inequality is violated **halts iff
RH is false**. This is the FRACTRAN sibling of the explicit RH Turing machines
(Yedidia-Aaronson) and the Davis-Matiyasevich-Robinson Diophantine encoding.

sigma(n) is a clean integer computation and compiles to a real fraction list
(``make_sigma``); the transcendental bound e^gamma * n * ln ln n is the subtlety
-- a rigorous machine brackets it with rational upper bounds of increasing
precision, so that halting still implies a genuine violation (see explorations.md
Sec. 5). This module gives the Python reference search plus the compiled kernel.
"""

from __future__ import annotations

import math

from . import build as B
from .core import run

EULER_GAMMA = 0.57721566490153286060651209
E_GAMMA = math.exp(EULER_GAMMA)  # ~ 1.7810724179901979

# Robin's inequality fails at exactly these 27 integers, all <= 5040:
ROBIN_EXCEPTIONS = [3, 4, 5, 6, 8, 9, 10, 12, 16, 18, 20, 24, 30, 36, 48, 60,
                    72, 84, 120, 180, 240, 360, 720, 840, 2520, 5040]


def sigma(n: int) -> int:
    """Sum of divisors of n (sqrt method)."""
    s, i = 0, 1
    while i * i <= n:
        if n % i == 0:
            s += i
            j = n // i
            if j != i:
                s += j
        i += 1
    return s


def sigma_upto(N: int):
    """sigma(n) for all n <= N by a divisor sieve (fast, for the search)."""
    s = [0] * (N + 1)
    for d in range(1, N + 1):
        for m in range(d, N + 1, d):
            s[m] += d
    return s


def robin_ratio(n: int) -> float:
    """sigma(n) / (n ln ln n); Robin's inequality says this stays below e^gamma."""
    return sigma(n) / (n * math.log(math.log(n)))


def is_violation(n: int, sig: int | None = None) -> bool:
    """Would RHGAME halt at n? (n > 5040 and Robin's inequality fails.)"""
    if n <= 5040:
        return False
    sig = sigma(n) if sig is None else sig
    return sig >= E_GAMMA * n * math.log(math.log(n))


def search(hi: int = 1_000_000):
    """Scan the Robin regime 5040 < n <= hi for a violation; track the record ratio.

    Returns (record_n, record_ratio, first_violation_or_None). The record ratio
    is over n > 5040, where it climbs toward e^gamma from below (the colossally
    abundant champions); a value reaching e^gamma is a violation.
    """
    s = sigma_upto(hi)
    best_n, best_r = 0, 0.0
    violation = None
    for n in range(5041, hi + 1):
        r = s[n] / (n * math.log(math.log(n)))
        if r > best_r:
            best_n, best_r = n, r
        if s[n] >= E_GAMMA * n * math.log(math.log(n)):
            violation = n
            break
    return best_n, best_r, violation


# --- the FRACTRAN kernel: sigma(n) as a fraction list ---------------------

def make_sigma():
    """Compile sigma(n) to FRACTRAN: for d=1..n, if d | n add d to sig."""
    blk = B.seq(
        B.zero("sig"), B.zero("d"),
        B.zero("nc"), B.copy("nc", "n", "t"),
        B.loop("nc", B.seq(
            B.inc("d"),
            B.zero("work"), B.copy("work", "n", "t"),
            B.divmod_("q", "r", "work", "d", "cd", "rr", "t2"),
            B.if_nz("r", B.seq(), B.add("sig", "d", "t")),   # r==0 => d | n => sig += d
        )),
    )
    return B.compile_program(blk, pin={"n": 2})


def fractran_sigma(compiled, n: int) -> int:
    state, *_ = run(compiled.fractions, compiled.start(n=n), max_steps=50_000_000)
    return compiled.read(state, "sig")
