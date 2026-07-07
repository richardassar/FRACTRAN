"""FRACTRAN calculator CLI: reads integer commands from stdin, writes results to
stdout. Every computation runs as a fraction list via the I/O trampoline.

    op 0 = a+b   1 = a*b   2 = a-b (>=0)   3 = divmod(a,b) -> quotient, remainder

Usage:
    printf '0 3 4\\n1 6 7\\n3 17 5\\n' | python3 calc.py
    python3 calc.py          # interactive: type "op a b" lines, Ctrl-D to end
"""

import sys

from fractran.calc import build_calculator
from fractran.io import io_host, trampoline


def stdin_ints():
    """Yield integers from stdin, a line at a time (works interactively)."""
    while True:
        line = sys.stdin.readline()
        if not line:
            return
        for tok in line.split():
            yield int(tok)


class LivePrinter(list):
    """Collects outputs and prints each as the program writes it."""

    def append(self, value):
        print(value, flush=True)
        super().append(value)


def main():
    calc = build_calculator()
    print(f"# FRACTRAN calculator — {len(calc.fractions)} fractions. "
          f"commands: 'op a b' (op 0=add 1=mul 2=sub 3=divmod)", file=sys.stderr)
    host = io_host(**calc.io_config(), inputs=stdin_ints(), outputs=LivePrinter())
    state = {calc.label_prime[calc.entry]: 1}
    trampoline(calc.fractions, state, host)


if __name__ == "__main__":
    main()
