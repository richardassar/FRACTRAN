"""The gallery: famous external FRACTRAN programs, transcribed exactly.

  * ``LOMONT`` — Chris Lomont's 48-fraction universal self-interpreter
    (CLF-INTERPRET), plus the base-11 ``encode`` that turns an object program +
    state into the single starting integer it consumes.

Running the self-interpreter *on* another FRACTRAN program, under our own
interpreter, is the meta-circular payoff.
"""

from __future__ import annotations

from math import gcd

from .core import fraction, program

# Lomont's CLF-INTERPRET, verbatim (factored form). 48 fractions, 32 primes.
# http://lomont.org/posts/2017/fractran/
LOMONT_TEXT = """
5/19
61^10*23*19/67^11*5
37/67^10*5
47^10*19/41*5
61*47*19/67*5
43/5
43/71
41*71/47*43
61^10*67*71/23^11*43
61^10*31/23^10*43
47^10*71/13*43
61*47*71/23*43
17/43
17/29
13*29/47*17
5/17
31/53
11*23*53/7*41*31
59/41*31
59/73
7*73/23*11*59
73/41*59
89/59
47*79/31
79/83
41*83/23*79
31/79
97/7*89
101/97
7*97/11*101
97/13*101
97/47*101
7*5/101
103/13*89
103/107
7*23*107/47*103
109/103
109/113
47*113/23*109
103/13*109
127/109
127/131
131/47*127
131/11*127
67*131/61*127
2/127
5/2
3/37
"""


def _eval_factored(expr: str) -> int:
    val = 1
    for term in expr.split("*"):
        term = term.strip()
        if "^" in term:
            b, e = term.split("^")
            val *= int(b) ** int(e)
        else:
            val *= int(term)
    return val


def parse_factored(text: str):
    """Parse a block of 'numExpr/denExpr' lines (factored) into a program."""
    frs = []
    for raw in text.strip().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        num, den = line.split("/")
        frs.append(fraction(_eval_factored(num), _eval_factored(den)))
    return frs


LOMONT = parse_factored(LOMONT_TEXT)


def encode_program(fractions) -> int:
    """Encode an object program as Lomont's base-11 integer p.

    Each fraction is reduced, numerator/denominator zero-padded to equal length,
    their digits interleaved (num, den, ...), framed by a leading 0 and trailing
    10; a final 10 ends the program. The digit list is read as base 11, least
    significant first.
    """
    digits = []
    for fr in fractions:
        num, den = fr.num, fr.den
        g = gcd(num, den)
        num, den = num // g, den // g
        ns, ds = str(num), str(den)
        w = max(len(ns), len(ds))
        ns, ds = ns.zfill(w), ds.zfill(w)
        digits.append(0)
        for i in range(w):
            digits.append(int(ns[i]))
            digits.append(int(ds[i]))
        digits.append(10)
    digits.append(10)
    return sum(d * 11**i for i, d in enumerate(digits))


def encode_input(fractions, object_n: int) -> dict:
    """Starting state for CLF-INTERPRET: 5 * 7^(object state) * 67^(program)."""
    return {5: 1, 7: object_n, 67: encode_program(fractions)}


# Conway's PIGAME: from 2^n * 89 it halts at 2^d, where d is the n-th digit of pi
# (n=0 gives the leading 3). Transcribed from Jackson's MathsJam 2016 slides and
# cross-checked against web sources, which disagree on a few fractions; NOT yet
# validated by execution, because a single digit takes >10^9 steps.
PIGAME_TEXT = (
    "365/46 29/161 79/575 679/451 3159/413 83/407 473/371 638/355 434/335 89/235 "
    "17/209 79/122 31/183 41/115 517/89 111/83 305/79 23/73 73/71 61/67 37/61 19/59 "
    "89/57 41/53 833/47 53/43 86/41 13/38 23/37 67/31 71/29 83/19 475/17 59/13 41/291 "
    "1/7 1/11 1/1024 1/97 89/1"
)
PIGAME = program(PIGAME_TEXT)


def pigame_input(n: int) -> dict:
    """Start state for the n-th digit of pi: 2^n * 89."""
    return {89: 1} if n == 0 else {2: n, 89: 1}
